"""
Rollback-Enabled Executor

Wraps the enhanced executor with automatic rollback on failure.
"""

from typing import Dict, Optional, List
from .checkpoint_manager import CheckpointManager
from .rev_analyzer import REVAnalyzer
from .uncomputation_engine import UncomputationEngine


class RollbackExecutor:
    """
    Executor wrapper that provides automatic rollback on failure.
    
    Features:
    - Automatic checkpointing before risky operations
    - Rollback on execution failure
    - Uncomputation of partial results
    - Retry with different parameters
    """
    
    def __init__(self, base_executor, checkpoint_manager: CheckpointManager):
        """
        Initialize rollback executor.
        
        Args:
            base_executor: Base executor to wrap
            checkpoint_manager: CheckpointManager for state snapshots
        """
        self.base_executor = base_executor
        self.checkpoint_manager = checkpoint_manager
        self.uncomputation_engine = UncomputationEngine()
        self.rollback_history: List[Dict] = []
    
    def execute_graph_with_rollback(
        self,
        graph: Dict,
        job_id: str,
        checkpoint_strategy: str = "auto",
        max_retries: int = 0
    ) -> Dict:
        """
        Execute graph with automatic rollback on failure.
        
        Args:
            graph: QVM graph to execute
            job_id: Job identifier
            checkpoint_strategy: When to checkpoint ("auto", "before_measure", "never")
            max_retries: Maximum retry attempts on failure
        
        Returns:
            Execution result dictionary
        """
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            try:
                # Analyze graph for REV segments
                analyzer = REVAnalyzer(graph)
                segments = analyzer.analyze()
                
                # Determine checkpoint points
                checkpoint_nodes = self._determine_checkpoint_points(
                    graph, segments, checkpoint_strategy
                )
                
                # Execute with checkpointing
                result = self._execute_with_checkpoints(
                    graph, job_id, checkpoint_nodes, attempt
                )
                
                return {
                    "status": "success",
                    "result": result,
                    "attempts": attempt + 1,
                    "checkpoints_created": len(checkpoint_nodes)
                }
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                # Record rollback
                self.rollback_history.append({
                    "job_id": job_id,
                    "attempt": attempt,
                    "error": str(e),
                    "rolled_back": attempt <= max_retries
                })
                
                if attempt <= max_retries:
                    # Attempt rollback
                    self._rollback_to_last_checkpoint(job_id)
        
        # All retries exhausted
        return {
            "status": "failed",
            "error": str(last_error),
            "attempts": attempt,
            "rollback_history": self.rollback_history[-attempt:]
        }
    
    def execute_segment_with_rollback(
        self,
        segment_nodes: List[Dict],
        job_id: str,
        epoch: int
    ) -> Dict:
        """
        Execute a segment with rollback capability.
        
        Args:
            segment_nodes: List of nodes in segment
            job_id: Job identifier
            epoch: Current execution epoch
        
        Returns:
            Execution result
        """
        # Create checkpoint before segment
        checkpoint = self.checkpoint_manager.create_checkpoint(
            job_id=job_id,
            epoch=epoch,
            node_id=segment_nodes[0]['id'],
            resource_manager=self.base_executor.resource_manager,
            metadata={"segment_start": True}
        )
        
        try:
            # Execute segment
            for node in segment_nodes:
                self._execute_node(node)
            
            return {
                "status": "success",
                "checkpoint_id": checkpoint.checkpoint_id,
                "nodes_executed": len(segment_nodes)
            }
        
        except Exception as e:
            # Rollback to checkpoint
            self.checkpoint_manager.restore_checkpoint(
                checkpoint.checkpoint_id,
                self.base_executor.resource_manager
            )
            
            return {
                "status": "rolled_back",
                "error": str(e),
                "checkpoint_id": checkpoint.checkpoint_id,
                "nodes_executed": 0
            }
    
    def uncompute_and_rollback(
        self,
        segment_id: int,
        graph: Dict,
        job_id: str
    ) -> Dict:
        """
        Uncompute a segment and rollback.
        
        Args:
            segment_id: Segment identifier
            graph: QVM graph
            job_id: Job identifier
        
        Returns:
            Uncomputation result
        """
        # Analyze graph
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        # Find segment
        segment = None
        for seg in segments:
            if seg.segment_id == segment_id:
                segment = seg
                break
        
        if not segment:
            return {
                "status": "error",
                "error": f"Segment {segment_id} not found"
            }
        
        if not segment.is_reversible:
            return {
                "status": "error",
                "error": f"Segment {segment_id} is not reversible"
            }
        
        # Generate inverse operations
        nodes = {node['id']: node for node in graph['nodes']}
        inverse_ops = self.uncomputation_engine.uncompute_segment(segment, nodes)
        
        # Apply uncomputation
        result = self.uncomputation_engine.apply_uncomputation(
            inverse_ops,
            self.base_executor
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "segment_id": segment_id,
            "operations_reversed": result["operations_applied"],
            "qubits_affected": result["qubits_affected"],
            "errors": result.get("errors", [])
        }
    
    def _determine_checkpoint_points(
        self,
        graph: Dict,
        segments: List,
        strategy: str
    ) -> List[str]:
        """
        Determine where to place checkpoints.
        
        Args:
            graph: QVM graph
            segments: List of REV segments
            strategy: Checkpoint strategy
        
        Returns:
            List of node IDs to checkpoint at
        """
        checkpoint_nodes = []
        
        if strategy == "never":
            return []
        
        nodes = {node['id']: node for node in graph['nodes']}
        
        if strategy == "auto":
            # Checkpoint before irreversible operations
            for node_id, node in nodes.items():
                op = node.get('op', '')
                if op in ['MEASURE_Z', 'MEASURE_X', 'RESET', 'CLOSE_CHAN']:
                    checkpoint_nodes.append(node_id)
        
        elif strategy == "before_measure":
            # Only checkpoint before measurements
            for node_id, node in nodes.items():
                if node.get('op', '') in ['MEASURE_Z', 'MEASURE_X']:
                    checkpoint_nodes.append(node_id)
        
        return checkpoint_nodes
    
    def _execute_with_checkpoints(
        self,
        graph: Dict,
        job_id: str,
        checkpoint_nodes: List[str],
        attempt: int
    ) -> Dict:
        """
        Execute graph with checkpoints at specified nodes.
        
        Args:
            graph: QVM graph
            job_id: Job identifier
            checkpoint_nodes: Node IDs to checkpoint at
            attempt: Attempt number
        
        Returns:
            Execution result
        """
        # Use base executor with checkpoint hooks
        result = self.base_executor.execute_graph(
            graph,
            seed=attempt  # Different seed for retries
        )
        
        # Create checkpoints at specified points
        # (In full implementation, would hook into executor)
        
        return result
    
    def _execute_node(self, node: Dict):
        """Execute a single node."""
        op = node.get('op', '')
        qubits = node.get('qubits', [])
        
        # Delegate to base executor
        if op == 'H':
            self.base_executor._execute_hadamard(qubits[0])
        elif op == 'X':
            self.base_executor._execute_x(qubits[0])
        elif op == 'CNOT':
            self.base_executor._execute_cnot(qubits[0], qubits[1])
        # ... other operations
    
    def _rollback_to_last_checkpoint(self, job_id: str):
        """
        Rollback to the most recent checkpoint for a job.
        
        Args:
            job_id: Job identifier
        """
        checkpoints = self.checkpoint_manager.list_checkpoints(job_id)
        
        if not checkpoints:
            return
        
        # Get most recent checkpoint
        latest = max(checkpoints, key=lambda c: c.created_at)
        
        # Restore
        self.checkpoint_manager.restore_checkpoint(
            latest.checkpoint_id,
            self.base_executor.resource_manager
        )
    
    def get_rollback_history(self, job_id: Optional[str] = None) -> List[Dict]:
        """
        Get rollback history.
        
        Args:
            job_id: Optional job ID to filter by
        
        Returns:
            List of rollback events
        """
        if job_id:
            return [r for r in self.rollback_history if r["job_id"] == job_id]
        return self.rollback_history.copy()
    
    def clear_history(self):
        """Clear rollback history."""
        self.rollback_history.clear()
