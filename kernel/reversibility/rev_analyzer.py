"""
REV Segment Analyzer

Identifies reversible segments in QVM graphs for uncomputation and rollback.

A REV segment is a maximal sequence of operations between irreversible boundaries
where all operations are unitary (reversible).

Irreversible operations:
- MEASURE_Z, MEASURE_X (collapse state)
- RESET (non-unitary)
- CLOSE_CHAN (destroys entanglement)
- ALLOC_LQ (creates state)
- FREE_LQ (destroys state)
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class REVSegment:
    """
    Represents a reversible segment in the graph.
    
    Attributes:
        segment_id: Unique identifier for this segment
        node_ids: List of node IDs in execution order
        entry_nodes: Node IDs that enter this segment
        exit_nodes: Node IDs that exit this segment
        qubits_used: Set of qubit IDs used in this segment
        is_reversible: Whether this segment is truly reversible
    """
    segment_id: int
    node_ids: List[str]
    entry_nodes: List[str]
    exit_nodes: List[str]
    qubits_used: Set[str]
    is_reversible: bool
    
    def __len__(self):
        """Return number of operations in segment."""
        return len(self.node_ids)


class REVAnalyzer:
    """
    Analyzes QVM graphs to identify reversible segments.
    
    Segments are bounded by irreversible operations and can be
    uncomputed for rollback or migration.
    """
    
    # Irreversible operations (create boundaries)
    IRREVERSIBLE_OPS = {
        'MEASURE_Z', 'MEASURE_X',
        'RESET',
        'CLOSE_CHAN',
        'ALLOC_LQ', 'FREE_LQ'
    }
    
    # Unitary (reversible) operations
    UNITARY_OPS = {
        'H', 'X', 'Y', 'Z', 'S',
        'RZ', 'RY', 'RX',
        'CNOT',
        'LINK'  # Creates entanglement but is unitary
    }
    
    def __init__(self, graph: Dict):
        """
        Initialize analyzer with a QVM graph.
        
        Args:
            graph: QVM graph dictionary
        """
        self.graph = graph
        self.nodes = {node['id']: node for node in graph['nodes']}
        self.segments: List[REVSegment] = []
        self._build_dependency_graph()
    
    def _build_dependency_graph(self):
        """Build forward and backward dependency maps."""
        self.forward_deps: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        self.backward_deps: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        
        # Build from explicit edges
        for edge in self.graph.get('edges', []):
            from_id = edge['from']
            to_id = edge['to']
            if from_id in self.forward_deps and to_id in self.forward_deps:
                self.forward_deps[from_id].append(to_id)
                self.backward_deps[to_id].append(from_id)
        
        # Build from deps field
        for node_id, node in self.nodes.items():
            for dep in node.get('deps', []):
                if dep in self.forward_deps:
                    self.forward_deps[dep].append(node_id)
                    self.backward_deps[node_id].append(dep)
    
    def analyze(self) -> List[REVSegment]:
        """
        Analyze graph and identify all REV segments.
        
        Returns:
            List of REVSegment objects
        """
        self.segments = []
        
        # Find all irreversible nodes
        irreversible_nodes = self._find_irreversible_nodes()
        
        # Perform topological sort
        topo_order = self._topological_sort()
        
        # Identify segments between irreversible boundaries
        current_segment_nodes = []
        segment_id = 0
        
        for node_id in topo_order:
            node = self.nodes[node_id]
            op = node.get('op', '')
            
            if op in self.IRREVERSIBLE_OPS:
                # End current segment if any
                if current_segment_nodes:
                    segment = self._create_segment(
                        segment_id,
                        current_segment_nodes,
                        irreversible_nodes
                    )
                    self.segments.append(segment)
                    segment_id += 1
                    current_segment_nodes = []
            
            elif op in self.UNITARY_OPS:
                # Add to current segment
                current_segment_nodes.append(node_id)
        
        # Handle final segment
        if current_segment_nodes:
            segment = self._create_segment(
                segment_id,
                current_segment_nodes,
                irreversible_nodes
            )
            self.segments.append(segment)
        
        return self.segments
    
    def _find_irreversible_nodes(self) -> Set[str]:
        """Find all nodes with irreversible operations."""
        return {
            node_id for node_id, node in self.nodes.items()
            if node.get('op', '') in self.IRREVERSIBLE_OPS
        }
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort of nodes.
        
        Returns:
            List of node IDs in execution order
        """
        in_degree = {nid: len(self.backward_deps[nid]) for nid in self.nodes}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for successor in self.forward_deps[node_id]:
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        
        return result
    
    def _create_segment(
        self,
        segment_id: int,
        node_ids: List[str],
        irreversible_nodes: Set[str]
    ) -> REVSegment:
        """
        Create a REVSegment from a list of node IDs.
        
        Args:
            segment_id: Unique segment identifier
            node_ids: List of node IDs in the segment
            irreversible_nodes: Set of all irreversible node IDs
        
        Returns:
            REVSegment object
        """
        # Find entry nodes (nodes with dependencies outside segment)
        node_set = set(node_ids)
        entry_nodes = []
        
        for node_id in node_ids:
            deps = self.backward_deps[node_id]
            if any(dep not in node_set for dep in deps):
                entry_nodes.append(node_id)
        
        # Find exit nodes (nodes with successors outside segment)
        exit_nodes = []
        for node_id in node_ids:
            succs = self.forward_deps[node_id]
            if any(succ not in node_set for succ in succs):
                exit_nodes.append(node_id)
        
        # Collect qubits used
        qubits_used = set()
        for node_id in node_ids:
            node = self.nodes[node_id]
            qubits_used.update(node.get('qubits', []))
        
        # Check if truly reversible (all ops are unitary)
        is_reversible = all(
            self.nodes[nid].get('op', '') in self.UNITARY_OPS
            for nid in node_ids
        )
        
        return REVSegment(
            segment_id=segment_id,
            node_ids=node_ids,
            entry_nodes=entry_nodes if not entry_nodes else entry_nodes,
            exit_nodes=exit_nodes if not exit_nodes else exit_nodes,
            qubits_used=qubits_used,
            is_reversible=is_reversible
        )
    
    def get_segment_by_node(self, node_id: str) -> Optional[REVSegment]:
        """
        Find which segment contains a given node.
        
        Args:
            node_id: Node identifier
        
        Returns:
            REVSegment containing the node, or None
        """
        for segment in self.segments:
            if node_id in segment.node_ids:
                return segment
        return None
    
    def get_reversible_segments(self) -> List[REVSegment]:
        """
        Get only the segments that are truly reversible.
        
        Returns:
            List of reversible REVSegment objects
        """
        return [seg for seg in self.segments if seg.is_reversible]
    
    def get_segment_stats(self) -> Dict:
        """
        Get statistics about segments in the graph.
        
        Returns:
            Dictionary with segment statistics
        """
        reversible_segs = self.get_reversible_segments()
        
        return {
            "total_segments": len(self.segments),
            "reversible_segments": len(reversible_segs),
            "irreversible_segments": len(self.segments) - len(reversible_segs),
            "total_nodes": sum(len(seg) for seg in self.segments),
            "reversible_nodes": sum(len(seg) for seg in reversible_segs),
            "avg_segment_length": (
                sum(len(seg) for seg in self.segments) / len(self.segments)
                if self.segments else 0
            ),
            "max_segment_length": max((len(seg) for seg in self.segments), default=0),
            "qubits_in_rev_segments": len(
                set().union(*(seg.qubits_used for seg in reversible_segs))
            ) if reversible_segs else 0
        }
    
    def validate_segment(self, segment: REVSegment) -> Tuple[bool, Optional[str]]:
        """
        Validate that a segment is properly formed and reversible.
        
        Args:
            segment: REVSegment to validate
        
        Returns:
            (is_valid, error_message) tuple
        """
        # Check all nodes exist
        for node_id in segment.node_ids:
            if node_id not in self.nodes:
                return False, f"Node {node_id} not found in graph"
        
        # Check all operations are unitary
        for node_id in segment.node_ids:
            op = self.nodes[node_id].get('op', '')
            if op not in self.UNITARY_OPS:
                return False, f"Node {node_id} has non-unitary op: {op}"
        
        # Check segment forms a connected subgraph
        if not self._is_connected_subgraph(segment.node_ids):
            return False, "Segment nodes do not form connected subgraph"
        
        return True, None
    
    def _is_connected_subgraph(self, node_ids: List[str]) -> bool:
        """Check if nodes form a connected subgraph."""
        if not node_ids:
            return True
        
        node_set = set(node_ids)
        visited = set()
        queue = [node_ids[0]]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Add neighbors that are in the segment
            for neighbor in self.forward_deps[current] + self.backward_deps[current]:
                if neighbor in node_set and neighbor not in visited:
                    queue.append(neighbor)
        
        return len(visited) == len(node_ids)
