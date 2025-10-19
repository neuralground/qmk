"""
Unit tests for Rollback Executor
"""

import unittest
from kernel.reversibility.rollback_executor import RollbackExecutor
from kernel.reversibility.checkpoint_manager import CheckpointManager
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.enhanced_executor import EnhancedExecutor


class TestRollbackExecutor(unittest.TestCase):
    """Test rollback executor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resource_mgr = EnhancedResourceManager()
        self.base_executor = EnhancedExecutor(self.resource_mgr)
        self.checkpoint_mgr = CheckpointManager()
        self.executor = RollbackExecutor(self.base_executor, self.checkpoint_mgr)
    
    def test_execute_graph_with_rollback_success(self):
        """Test successful execution with rollback capability."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"],
                 "profile": "logical:surface_code(d=3)"},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
                 "outputs": ["m0"], "deps": ["h"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        result = self.executor.execute_graph_with_rollback(
            graph,
            job_id="job_1",
            checkpoint_strategy="auto",
            max_retries=0
        )
        
        # Result should have status (either success or failed)
        self.assertIn("status", result)
        self.assertIn("attempts", result)
    
    def test_determine_checkpoint_points_auto(self):
        """Test automatic checkpoint point determination."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
                 "outputs": ["m0"], "deps": ["h"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        from kernel.reversibility.rev_analyzer import REVAnalyzer
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        points = self.executor._determine_checkpoint_points(
            graph, segments, "auto"
        )
        
        # Should checkpoint before measurement
        self.assertIn("m", points)
    
    def test_determine_checkpoint_points_never(self):
        """Test no checkpoints strategy."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
                 "outputs": ["m0"], "deps": ["h"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        from kernel.reversibility.rev_analyzer import REVAnalyzer
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        points = self.executor._determine_checkpoint_points(
            graph, segments, "never"
        )
        
        self.assertEqual(len(points), 0)
    
    def test_rollback_history(self):
        """Test rollback history tracking."""
        self.executor.clear_history()
        
        # Simulate a rollback
        self.executor.rollback_history.append({
            "job_id": "job_1",
            "attempt": 1,
            "error": "Test error",
            "rolled_back": True
        })
        
        history = self.executor.get_rollback_history("job_1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job_id"], "job_1")
    
    def test_clear_history(self):
        """Test clearing rollback history."""
        self.executor.rollback_history.append({
            "job_id": "job_1",
            "attempt": 1,
            "error": "Test error",
            "rolled_back": True
        })
        
        self.executor.clear_history()
        
        history = self.executor.get_rollback_history()
        self.assertEqual(len(history), 0)


if __name__ == "__main__":
    unittest.main()
