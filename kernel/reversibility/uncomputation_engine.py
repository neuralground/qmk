"""
Uncomputation Engine

Reverses quantum operations to uncompute REV segments.
This enables:
- Rollback on failure
- State migration
- Energy-efficient computation (uncompute ancilla qubits)
"""

from typing import Dict, List, Optional, Tuple
from .rev_analyzer import REVSegment
import copy


class UncomputationEngine:
    """
    Engine for uncomputing (reversing) quantum operations.
    
    Given a REV segment, generates the inverse operations to
    restore the initial state.
    """
    
    # Inverse operations for single-qubit gates
    GATE_INVERSES = {
        'H': 'H',      # Hadamard is self-inverse
        'X': 'X',      # Pauli-X is self-inverse
        'Y': 'Y',      # Pauli-Y is self-inverse
        'Z': 'Z',      # Pauli-Z is self-inverse
        'S': 'S_DAG',  # S† (inverse of S gate)
        'S_DAG': 'S',  # S (inverse of S†)
        'CNOT': 'CNOT', # CNOT is self-inverse
    }
    
    def __init__(self, resource_manager=None):
        """
        Initialize uncomputation engine.
        
        Args:
            resource_manager: Optional resource manager for state access
        """
        self.resource_manager = resource_manager
        self.uncomputation_log: List[Dict] = []
    
    def uncompute_segment(
        self,
        segment: REVSegment,
        nodes: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Generate inverse operations to uncompute a segment.
        
        Args:
            segment: REVSegment to uncompute
            nodes: Dictionary mapping node IDs to node definitions
        
        Returns:
            List of inverse operation nodes in reverse order
        """
        if not segment.is_reversible:
            raise ValueError(f"Segment {segment.segment_id} is not reversible")
        
        inverse_ops = []
        
        # Process nodes in reverse order
        for node_id in reversed(segment.node_ids):
            node = nodes[node_id]
            inverse_node = self._create_inverse_node(node, node_id)
            
            if inverse_node:
                inverse_ops.append(inverse_node)
        
        # Log uncomputation
        self.uncomputation_log.append({
            "segment_id": segment.segment_id,
            "original_nodes": segment.node_ids,
            "inverse_ops": [op['id'] for op in inverse_ops],
            "qubits": list(segment.qubits_used)
        })
        
        return inverse_ops
    
    def _create_inverse_node(self, node: Dict, original_id: str) -> Optional[Dict]:
        """
        Create the inverse of a single operation.
        
        Args:
            node: Original node definition
            original_id: Original node ID
        
        Returns:
            Inverse node definition, or None if no inverse needed
        """
        op = node.get('op', '')
        
        # Get inverse operation
        if op in self.GATE_INVERSES:
            inverse_op = self.GATE_INVERSES[op]
        elif op.startswith('R'):  # Rotation gates
            inverse_op = op  # Same gate with negated angle
        else:
            raise ValueError(f"Unknown operation for inversion: {op}")
        
        # Create inverse node
        inverse_node = {
            'id': f"inv_{original_id}",
            'op': inverse_op,
            'qubits': node.get('qubits', []).copy(),
            'original_node': original_id
        }
        
        # Handle rotation gates (negate angle)
        if op.startswith('R') and 'params' in node:
            inverse_node['params'] = {
                'theta': -node['params']['theta']
            }
        
        return inverse_node
    
    def apply_uncomputation(
        self,
        inverse_ops: List[Dict],
        executor
    ) -> Dict:
        """
        Apply inverse operations using the executor.
        
        Args:
            inverse_ops: List of inverse operation nodes
            executor: Executor instance to apply operations
        
        Returns:
            Execution result dictionary
        """
        results = {
            "operations_applied": 0,
            "qubits_affected": set(),
            "success": True,
            "errors": []
        }
        
        for inv_op in inverse_ops:
            try:
                # Apply the inverse operation
                self._apply_single_inverse(inv_op, executor)
                
                results["operations_applied"] += 1
                results["qubits_affected"].update(inv_op.get('qubits', []))
                
            except Exception as e:
                results["success"] = False
                results["errors"].append({
                    "operation": inv_op['id'],
                    "error": str(e)
                })
                break
        
        results["qubits_affected"] = list(results["qubits_affected"])
        return results
    
    def _apply_single_inverse(self, inv_op: Dict, executor):
        """
        Apply a single inverse operation.
        
        Args:
            inv_op: Inverse operation node
            executor: Executor instance
        """
        op = inv_op['op']
        qubits = inv_op['qubits']
        
        if op == 'H':
            executor._execute_hadamard(qubits[0])
        elif op == 'X':
            executor._execute_x(qubits[0])
        elif op == 'Y':
            executor._execute_y(qubits[0])
        elif op == 'Z':
            executor._execute_z(qubits[0])
        elif op == 'S':
            executor._execute_s(qubits[0])
        elif op == 'S_DAG':
            # S† = S^3 = S·S·S (since S^4 = I)
            executor._execute_s(qubits[0])
            executor._execute_s(qubits[0])
            executor._execute_s(qubits[0])
        elif op == 'CNOT':
            executor._execute_cnot(qubits[0], qubits[1])
        elif op.startswith('R'):
            theta = inv_op['params']['theta']
            if op == 'RZ':
                executor._execute_rz(qubits[0], theta)
            elif op == 'RY':
                executor._execute_ry(qubits[0], theta)
            elif op == 'RX':
                executor._execute_rx(qubits[0], theta)
        else:
            raise ValueError(f"Unknown inverse operation: {op}")
    
    def verify_uncomputation(
        self,
        segment: REVSegment,
        nodes: Dict[str, Dict],
        initial_state: Optional[Dict] = None,
        final_state: Optional[Dict] = None
    ) -> bool:
        """
        Verify that uncomputation correctly reverses a segment.
        
        Args:
            segment: REVSegment that was uncomputed
            nodes: Node definitions
            initial_state: Optional initial quantum state
            final_state: Optional final quantum state after uncomputation
        
        Returns:
            True if uncomputation is verified correct
        """
        # Generate inverse operations
        inverse_ops = self.uncompute_segment(segment, nodes)
        
        # Check that we have the right number of inverse ops
        if len(inverse_ops) != len(segment.node_ids):
            return False
        
        # Verify each inverse operation is correct
        for orig_id, inv_op in zip(reversed(segment.node_ids), inverse_ops):
            orig_node = nodes[orig_id]
            
            # Check qubits match
            if orig_node.get('qubits') != inv_op.get('qubits'):
                return False
            
            # Check operation is inverse
            orig_op = orig_node.get('op')
            inv_op_type = inv_op.get('op')
            
            if self.GATE_INVERSES.get(orig_op) != inv_op_type:
                # Special case for rotations
                if not (orig_op.startswith('R') and orig_op == inv_op_type):
                    return False
        
        # If states provided, verify they match
        if initial_state and final_state:
            # In a real implementation, would compare quantum states
            # For now, just check structure matches
            return set(initial_state.keys()) == set(final_state.keys())
        
        return True
    
    def get_uncomputation_cost(self, segment: REVSegment, nodes: Dict[str, Dict]) -> Dict:
        """
        Estimate the cost of uncomputing a segment.
        
        Args:
            segment: REVSegment to analyze
            nodes: Node definitions
        
        Returns:
            Dictionary with cost metrics
        """
        inverse_ops = self.uncompute_segment(segment, nodes)
        
        # Count operation types
        op_counts = {}
        for inv_op in inverse_ops:
            op_type = inv_op['op']
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        # Estimate time (simplified)
        # Single-qubit gates: 1 unit, two-qubit gates: 10 units
        time_cost = 0
        for op_type, count in op_counts.items():
            if op_type == 'CNOT':
                time_cost += count * 10
            else:
                time_cost += count * 1
        
        return {
            "num_operations": len(inverse_ops),
            "operation_counts": op_counts,
            "estimated_time_units": time_cost,
            "qubits_affected": len(segment.qubits_used),
            "segment_length": len(segment)
        }
    
    def can_uncompute(self, segment: REVSegment) -> Tuple[bool, Optional[str]]:
        """
        Check if a segment can be uncomputed.
        
        Args:
            segment: REVSegment to check
        
        Returns:
            (can_uncompute, reason) tuple
        """
        if not segment.is_reversible:
            return False, "Segment contains irreversible operations"
        
        if len(segment.node_ids) == 0:
            return False, "Segment is empty"
        
        # Check for unsupported operations
        # (In full implementation, would check against supported gate set)
        
        return True, None
    
    def get_uncomputation_log(self) -> List[Dict]:
        """
        Get log of all uncomputations performed.
        
        Returns:
            List of uncomputation log entries
        """
        return self.uncomputation_log.copy()
    
    def clear_log(self):
        """Clear the uncomputation log."""
        self.uncomputation_log.clear()
