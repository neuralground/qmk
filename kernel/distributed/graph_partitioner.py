"""
Graph Partitioner

Partitions QVM graphs for distributed execution across multiple nodes.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import copy


@dataclass
class Partition:
    """
    Represents a graph partition.
    
    Attributes:
        partition_id: Unique partition identifier
        nodes: List of node IDs in this partition
        qubits: Set of qubits used in this partition
        dependencies: Partitions this depends on
        estimated_time: Estimated execution time
        estimated_memory: Estimated memory usage
    """
    partition_id: str
    nodes: List[str] = field(default_factory=list)
    qubits: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    estimated_time: float = 0.0
    estimated_memory: int = 0


@dataclass
class PartitionPlan:
    """
    Complete partitioning plan.
    
    Attributes:
        plan_id: Plan identifier
        partitions: List of partitions
        communication_cost: Estimated communication overhead
        parallelism: Maximum parallelism level
    """
    plan_id: str
    partitions: List[Partition]
    communication_cost: float = 0.0
    parallelism: int = 1


class GraphPartitioner:
    """
    Partitions QVM graphs for distributed execution.
    
    Strategies:
    - Qubit-based partitioning
    - Time-based partitioning
    - Load-balanced partitioning
    """
    
    def __init__(self, num_partitions: int = 4):
        """
        Initialize graph partitioner.
        
        Args:
            num_partitions: Target number of partitions
        """
        self.num_partitions = num_partitions
    
    def partition_by_qubits(
        self,
        graph: Dict,
        plan_id: str = "qubit_partition"
    ) -> PartitionPlan:
        """
        Partition graph by qubit locality.
        
        Groups operations on same qubits together.
        
        Args:
            graph: QVM graph
            plan_id: Plan identifier
        
        Returns:
            PartitionPlan
        """
        nodes = graph.get("nodes", [])
        
        # Group nodes by primary qubit
        qubit_groups: Dict[str, List[Dict]] = {}
        
        for node in nodes:
            qubits = node.get("qubits", [])
            if qubits:
                primary_qubit = qubits[0]
                if primary_qubit not in qubit_groups:
                    qubit_groups[primary_qubit] = []
                qubit_groups[primary_qubit].append(node)
        
        # Create partitions from qubit groups
        partitions = []
        partition_idx = 0
        
        # Distribute qubit groups across partitions
        qubit_list = list(qubit_groups.keys())
        partition_size = max(1, len(qubit_list) // self.num_partitions)
        
        for i in range(0, len(qubit_list), partition_size):
            partition_qubits = qubit_list[i:i + partition_size]
            
            partition_nodes = []
            partition_qubit_set = set()
            
            for qubit in partition_qubits:
                partition_nodes.extend(qubit_groups[qubit])
                partition_qubit_set.add(qubit)
            
            if partition_nodes:
                partition = Partition(
                    partition_id=f"p{partition_idx}",
                    nodes=[n["node_id"] for n in partition_nodes],
                    qubits=partition_qubit_set,
                    estimated_time=len(partition_nodes) * 0.001  # 1ms per node
                )
                partitions.append(partition)
                partition_idx += 1
        
        # Compute dependencies
        self._compute_dependencies(partitions, nodes)
        
        # Estimate communication cost
        comm_cost = self._estimate_communication_cost(partitions)
        
        # Compute parallelism
        parallelism = self._compute_parallelism(partitions)
        
        return PartitionPlan(
            plan_id=plan_id,
            partitions=partitions,
            communication_cost=comm_cost,
            parallelism=parallelism
        )
    
    def partition_by_time(
        self,
        graph: Dict,
        plan_id: str = "time_partition"
    ) -> PartitionPlan:
        """
        Partition graph by execution time slices.
        
        Groups operations that can execute in parallel.
        
        Args:
            graph: QVM graph
            plan_id: Plan identifier
        
        Returns:
            PartitionPlan
        """
        nodes = graph.get("nodes", [])
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(nodes)
        
        # Compute levels (time slices)
        levels = self._compute_levels(nodes, dependencies)
        
        # Create partitions from levels
        partitions = []
        
        for level_idx, level_nodes in enumerate(levels):
            if not level_nodes:
                continue
            
            # Split level into sub-partitions if too large
            sub_partition_size = max(1, len(level_nodes) // self.num_partitions)
            
            for i in range(0, len(level_nodes), sub_partition_size):
                sub_nodes = level_nodes[i:i + sub_partition_size]
                
                partition_qubits = set()
                for node_id in sub_nodes:
                    node = next(n for n in nodes if n["node_id"] == node_id)
                    partition_qubits.update(node.get("qubits", []))
                
                partition = Partition(
                    partition_id=f"p{level_idx}_{i // sub_partition_size}",
                    nodes=sub_nodes,
                    qubits=partition_qubits,
                    estimated_time=len(sub_nodes) * 0.001
                )
                partitions.append(partition)
        
        # Compute dependencies
        self._compute_dependencies(partitions, nodes)
        
        comm_cost = self._estimate_communication_cost(partitions)
        parallelism = self._compute_parallelism(partitions)
        
        return PartitionPlan(
            plan_id=plan_id,
            partitions=partitions,
            communication_cost=comm_cost,
            parallelism=parallelism
        )
    
    def partition_balanced(
        self,
        graph: Dict,
        plan_id: str = "balanced_partition"
    ) -> PartitionPlan:
        """
        Create load-balanced partitions.
        
        Distributes work evenly across partitions.
        
        Args:
            graph: QVM graph
            plan_id: Plan identifier
        
        Returns:
            PartitionPlan
        """
        nodes = graph.get("nodes", [])
        
        # Simple round-robin distribution
        partitions = [
            Partition(partition_id=f"p{i}", nodes=[], qubits=set())
            for i in range(self.num_partitions)
        ]
        
        for idx, node in enumerate(nodes):
            partition_idx = idx % self.num_partitions
            partition = partitions[partition_idx]
            
            partition.nodes.append(node["node_id"])
            partition.qubits.update(node.get("qubits", []))
            partition.estimated_time += 0.001  # 1ms per node
        
        # Remove empty partitions
        partitions = [p for p in partitions if p.nodes]
        
        # Compute dependencies
        self._compute_dependencies(partitions, nodes)
        
        comm_cost = self._estimate_communication_cost(partitions)
        parallelism = self._compute_parallelism(partitions)
        
        return PartitionPlan(
            plan_id=plan_id,
            partitions=partitions,
            communication_cost=comm_cost,
            parallelism=parallelism
        )
    
    def _build_dependency_graph(
        self,
        nodes: List[Dict]
    ) -> Dict[str, Set[str]]:
        """Build dependency graph from nodes."""
        dependencies: Dict[str, Set[str]] = {
            node["node_id"]: set() for node in nodes
        }
        
        # Track last writer for each qubit
        last_writer: Dict[str, str] = {}
        
        for node in nodes:
            node_id = node["node_id"]
            qubits = node.get("qubits", [])
            
            # Add dependencies on previous operations on same qubits
            for qubit in qubits:
                if qubit in last_writer:
                    dependencies[node_id].add(last_writer[qubit])
                last_writer[qubit] = node_id
        
        return dependencies
    
    def _compute_levels(
        self,
        nodes: List[Dict],
        dependencies: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """Compute execution levels (time slices)."""
        levels: List[List[str]] = []
        remaining = set(node["node_id"] for node in nodes)
        completed = set()
        
        while remaining:
            # Find nodes with all dependencies satisfied
            ready = []
            for node_id in remaining:
                if dependencies[node_id].issubset(completed):
                    ready.append(node_id)
            
            if not ready:
                # Circular dependency or error
                break
            
            levels.append(ready)
            remaining -= set(ready)
            completed.update(ready)
        
        return levels
    
    def _compute_dependencies(
        self,
        partitions: List[Partition],
        nodes: List[Dict]
    ):
        """Compute inter-partition dependencies."""
        # Build node to partition map
        node_to_partition: Dict[str, str] = {}
        for partition in partitions:
            for node_id in partition.nodes:
                node_to_partition[node_id] = partition.partition_id
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(nodes)
        
        # Compute partition dependencies
        for partition in partitions:
            partition_deps = set()
            
            for node_id in partition.nodes:
                for dep_node_id in dependencies.get(node_id, []):
                    if dep_node_id in node_to_partition:
                        dep_partition = node_to_partition[dep_node_id]
                        if dep_partition != partition.partition_id:
                            partition_deps.add(dep_partition)
            
            partition.dependencies = partition_deps
    
    def _estimate_communication_cost(
        self,
        partitions: List[Partition]
    ) -> float:
        """Estimate communication overhead."""
        # Count inter-partition qubit transfers
        total_transfers = 0
        
        for partition in partitions:
            # Each dependency requires qubit state transfer
            total_transfers += len(partition.dependencies) * len(partition.qubits)
        
        # Assume 1ms per qubit transfer
        return total_transfers * 0.001
    
    def _compute_parallelism(
        self,
        partitions: List[Partition]
    ) -> int:
        """Compute maximum parallelism level."""
        if not partitions:
            return 0
        
        # Build dependency graph
        dep_graph: Dict[str, Set[str]] = {
            p.partition_id: p.dependencies for p in partitions
        }
        
        # Compute levels
        levels = self._compute_levels(
            [{"node_id": p.partition_id} for p in partitions],
            dep_graph
        )
        
        # Maximum parallelism is max partitions in any level
        return max(len(level) for level in levels) if levels else 1
    
    def get_partition_stats(self, plan: PartitionPlan) -> Dict:
        """
        Get statistics for partition plan.
        
        Args:
            plan: Partition plan
        
        Returns:
            Dictionary with statistics
        """
        total_nodes = sum(len(p.nodes) for p in plan.partitions)
        total_qubits = len(set().union(*[p.qubits for p in plan.partitions]))
        
        return {
            "num_partitions": len(plan.partitions),
            "total_nodes": total_nodes,
            "total_qubits": total_qubits,
            "avg_nodes_per_partition": total_nodes / len(plan.partitions) if plan.partitions else 0,
            "communication_cost": plan.communication_cost,
            "parallelism": plan.parallelism,
            "estimated_speedup": plan.parallelism * 0.8  # Account for overhead
        }
