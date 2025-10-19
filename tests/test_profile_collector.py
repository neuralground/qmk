"""
Unit tests for Profile Collector
"""

import unittest
import time
from kernel.jit.profile_collector import ProfileCollector


class TestProfileCollector(unittest.TestCase):
    """Test profile collection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProfileCollector()
    
    def test_start_profiling(self):
        """Test starting profiling."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        
        self.assertIsNotNone(profile_id)
        self.assertIn(profile_id, self.collector.active_sessions)
    
    def test_record_node_execution(self):
        """Test recording node execution."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        
        self.collector.record_node_execution(
            profile_id, "node_1", 0.5, gate_type="H"
        )
        
        session = self.collector.active_sessions[profile_id]
        self.assertEqual(session["node_timings"]["node_1"], 0.5)
        self.assertEqual(session["gate_counts"]["H"], 1)
    
    def test_record_qubit_usage(self):
        """Test recording qubit usage."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        
        self.collector.record_qubit_usage(profile_id, "q0", 3)
        
        session = self.collector.active_sessions[profile_id]
        self.assertEqual(session["qubit_usage"]["q0"], 3)
    
    def test_record_error_rate(self):
        """Test recording error rate."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        
        self.collector.record_error_rate(profile_id, "CNOT", 0.01)
        
        session = self.collector.active_sessions[profile_id]
        self.assertEqual(session["error_rates"]["CNOT"], 0.01)
    
    def test_end_profiling(self):
        """Test ending profiling."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        self.collector.record_node_execution(profile_id, "node_1", 0.5)
        
        profile = self.collector.end_profiling(profile_id)
        
        self.assertEqual(profile.job_id, "job_1")
        self.assertEqual(profile.graph_id, "graph_1")
        self.assertIn("node_1", profile.node_timings)
        self.assertNotIn(profile_id, self.collector.active_sessions)
    
    def test_get_profile(self):
        """Test getting a profile."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        profile = self.collector.end_profiling(profile_id)
        
        retrieved = self.collector.get_profile(profile_id)
        
        self.assertEqual(retrieved.profile_id, profile_id)
    
    def test_get_profiles_for_job(self):
        """Test getting profiles for a job."""
        p1 = self.collector.start_profiling("job_1", "graph_1")
        p2 = self.collector.start_profiling("job_1", "graph_2")
        p3 = self.collector.start_profiling("job_2", "graph_1")
        
        self.collector.end_profiling(p1)
        self.collector.end_profiling(p2)
        self.collector.end_profiling(p3)
        
        profiles = self.collector.get_profiles_for_job("job_1")
        
        self.assertEqual(len(profiles), 2)
    
    def test_get_profiles_for_graph(self):
        """Test getting profiles for a graph."""
        p1 = self.collector.start_profiling("job_1", "graph_1")
        p2 = self.collector.start_profiling("job_2", "graph_1")
        
        self.collector.end_profiling(p1)
        self.collector.end_profiling(p2)
        
        profiles = self.collector.get_profiles_for_graph("graph_1")
        
        self.assertEqual(len(profiles), 2)
    
    def test_aggregate_profiles(self):
        """Test aggregating profiles."""
        p1 = self.collector.start_profiling("job_1", "graph_1")
        self.collector.record_node_execution(p1, "node_1", 1.0, "H")
        self.collector.end_profiling(p1)
        
        p2 = self.collector.start_profiling("job_2", "graph_1")
        self.collector.record_node_execution(p2, "node_1", 2.0, "H")
        self.collector.end_profiling(p2)
        
        stats = self.collector.aggregate_profiles()
        
        self.assertEqual(stats["num_profiles"], 2)
        self.assertEqual(stats["total_gate_counts"]["H"], 2)
    
    def test_get_hotspots(self):
        """Test getting hotspots."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        self.collector.record_node_execution(profile_id, "node_1", 1.0)
        self.collector.record_node_execution(profile_id, "node_2", 5.0)
        self.collector.record_node_execution(profile_id, "node_3", 2.0)
        
        profile = self.collector.end_profiling(profile_id)
        hotspots = profile.get_hotspots(top_n=2)
        
        self.assertEqual(len(hotspots), 2)
        self.assertEqual(hotspots[0][0], "node_2")  # Slowest
    
    def test_identify_optimization_opportunities(self):
        """Test identifying optimization opportunities."""
        profile_id = self.collector.start_profiling("job_1", "graph_1")
        self.collector.record_node_execution(profile_id, "node_1", 5.0, "H")
        self.collector.record_error_rate(profile_id, "CNOT", 0.02)
        
        profile = self.collector.end_profiling(profile_id)
        opportunities = self.collector.identify_optimization_opportunities(profile_id)
        
        self.assertGreater(len(opportunities), 0)


if __name__ == "__main__":
    unittest.main()
