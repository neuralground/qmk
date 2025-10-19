"""
Unit tests for REV Segment Analyzer
"""

import unittest
from kernel.reversibility.rev_analyzer import REVAnalyzer, REVSegment


class TestREVAnalyzer(unittest.TestCase):
    """Test REV segment analysis."""
    
    def test_simple_reversible_segment(self):
        """Test identifying a simple reversible segment."""
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
        
        # Should have one reversible segment (h, x)
        rev_segs = analyzer.get_reversible_segments()
        self.assertEqual(len(rev_segs), 1)
        self.assertEqual(set(rev_segs[0].node_ids), {"h", "x"})
        self.assertTrue(rev_segs[0].is_reversible)
    
    def test_multiple_segments(self):
        """Test multiple REV segments separated by measurements."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h1", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "m1", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m1"], "deps": ["h1"]},
                {"id": "h2", "op": "H", "qubits": ["q0"], "deps": ["m1"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h2"]},
                {"id": "m2", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m2"], "deps": ["x"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m2"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        rev_segs = analyzer.get_reversible_segments()
        self.assertEqual(len(rev_segs), 2)
        
        # First segment: h1
        self.assertIn("h1", rev_segs[0].node_ids)
        
        # Second segment: h2, x
        self.assertIn("h2", rev_segs[1].node_ids)
        self.assertIn("x", rev_segs[1].node_ids)
    
    def test_cnot_reversible(self):
        """Test that CNOT gates are identified as reversible."""
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
        self.assertEqual(len(rev_segs), 1)
        self.assertIn("cnot", rev_segs[0].node_ids)
        self.assertEqual(rev_segs[0].qubits_used, {"q0", "q1"})
    
    def test_rotation_gates_reversible(self):
        """Test that rotation gates are reversible."""
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
        self.assertEqual(len(rev_segs), 1)
        self.assertIn("rz", rev_segs[0].node_ids)
        self.assertIn("ry", rev_segs[0].node_ids)
    
    def test_segment_stats(self):
        """Test segment statistics."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h"]},
                {"id": "y", "op": "Y", "qubits": ["q0"], "deps": ["x"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["y"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        analyzer.analyze()
        
        stats = analyzer.get_segment_stats()
        
        self.assertEqual(stats["total_segments"], 1)
        self.assertEqual(stats["reversible_segments"], 1)
        self.assertEqual(stats["reversible_nodes"], 3)  # h, x, y
        self.assertEqual(stats["max_segment_length"], 3)
    
    def test_get_segment_by_node(self):
        """Test finding segment containing a node."""
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
        analyzer.analyze()
        
        segment = analyzer.get_segment_by_node("h")
        self.assertIsNotNone(segment)
        self.assertIn("h", segment.node_ids)
        
        segment = analyzer.get_segment_by_node("x")
        self.assertIsNotNone(segment)
        self.assertIn("x", segment.node_ids)
        
        # Non-reversible nodes shouldn't be in segments
        segment = analyzer.get_segment_by_node("alloc")
        self.assertIsNone(segment)
    
    def test_empty_graph(self):
        """Test analyzer with empty graph."""
        graph = {"nodes": [], "edges": []}
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        self.assertEqual(len(segments), 0)
    
    def test_no_reversible_segments(self):
        """Test graph with no reversible segments."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["alloc"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        analyzer = REVAnalyzer(graph)
        segments = analyzer.analyze()
        
        rev_segs = analyzer.get_reversible_segments()
        self.assertEqual(len(rev_segs), 0)
    
    def test_validate_segment(self):
        """Test segment validation."""
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
        
        is_valid, error = analyzer.validate_segment(rev_segs[0])
        self.assertTrue(is_valid)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
