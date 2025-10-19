"""
Unit tests for Uncomputation Engine
"""

import unittest
from kernel.reversibility.rev_analyzer import REVAnalyzer, REVSegment
from kernel.reversibility.uncomputation_engine import UncomputationEngine


class TestUncomputationEngine(unittest.TestCase):
    """Test uncomputation engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = UncomputationEngine()
    
    def test_uncompute_simple_segment(self):
        """Test uncomputing a simple segment."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["x"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        self.assertEqual(len(rev_segs), 1)
        segment = rev_segs[0]
        
        nodes = {node['id']: node for node in graph['nodes']}
        inverse_ops = self.engine.uncompute_segment(segment, nodes)
        
        # Should have inverse operations in reverse order
        self.assertEqual(len(inverse_ops), 2)
        self.assertEqual(inverse_ops[0]['original_node'], "x")
        self.assertEqual(inverse_ops[1]['original_node'], "h")
    
    def test_self_inverse_gates(self):
        """Test that self-inverse gates invert correctly."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h"]},
                {"id": "y", "op": "Y", "qubits": ["q0"], "deps": ["x"]},
                {"id": "z", "op": "Z", "qubits": ["q0"], "deps": ["y"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["z"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        inverse_ops = self.engine.uncompute_segment(rev_segs[0], nodes)
        
        # All these gates are self-inverse
        for inv_op in inverse_ops:
            orig_node = nodes[inv_op['original_node']]
            self.assertEqual(inv_op['op'], orig_node['op'])
    
    def test_rotation_gate_inversion(self):
        """Test that rotation gates invert with negated angle."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "rz", "op": "RZ", "qubits": ["q0"], "params": {"theta": 1.57}, "deps": ["alloc"]},
                {"id": "ry", "op": "RY", "qubits": ["q0"], "params": {"theta": 3.14}, "deps": ["rz"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["ry"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        inverse_ops = self.engine.uncompute_segment(rev_segs[0], nodes)
        
        # Check angles are negated
        for inv_op in inverse_ops:
            orig_node = nodes[inv_op['original_node']]
            if 'params' in orig_node:
                self.assertEqual(
                    inv_op['params']['theta'],
                    -orig_node['params']['theta']
                )
    
    def test_cnot_inversion(self):
        """Test CNOT gate inversion."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["cnot"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        inverse_ops = self.engine.uncompute_segment(rev_segs[0], nodes)
        
        # CNOT is self-inverse
        cnot_inv = [op for op in inverse_ops if op['original_node'] == 'cnot'][0]
        self.assertEqual(cnot_inv['op'], 'CNOT')
        self.assertEqual(cnot_inv['qubits'], ["q0", "q1"])
    
    def test_verify_uncomputation(self):
        """Test verification of uncomputation."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["x"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        
        is_valid = self.engine.verify_uncomputation(rev_segs[0], nodes)
        self.assertTrue(is_valid)
    
    def test_uncomputation_cost(self):
        """Test cost estimation for uncomputation."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h"]},
                {"id": "x", "op": "X", "qubits": ["q1"], "deps": ["cnot"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["x"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        cost = self.engine.get_uncomputation_cost(rev_segs[0], nodes)
        
        self.assertEqual(cost["num_operations"], 3)
        self.assertIn("H", cost["operation_counts"])
        self.assertIn("CNOT", cost["operation_counts"])
        self.assertIn("X", cost["operation_counts"])
        self.assertGreater(cost["estimated_time_units"], 0)
    
    def test_can_uncompute(self):
        """Test checking if segment can be uncomputed."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["h"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        self.assertEqual(len(rev_segs), 1)
        can_uncompute, reason = self.engine.can_uncompute(rev_segs[0])
        self.assertTrue(can_uncompute)
        self.assertIsNone(reason)
    
    def test_uncomputation_log(self):
        """Test uncomputation logging."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["h"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        rev_segs = analyzer.get_reversible_segments()
        
        nodes = {node['id']: node for node in graph['nodes']}
        
        self.engine.clear_log()
        self.engine.uncompute_segment(rev_segs[0], nodes)
        
        log = self.engine.get_uncomputation_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["segment_id"], rev_segs[0].segment_id)


if __name__ == "__main__":
    unittest.main()
