"""
Unit tests for Adaptive Policy Engine
"""

import unittest
from kernel.jit.adaptive_policy import AdaptivePolicyEngine, AdaptiveDecision


class TestAdaptivePolicyEngine(unittest.TestCase):
    """Test adaptive policy engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = AdaptivePolicyEngine()
    
    def test_analyze_high_error_rate(self):
        """Test analysis with high error rate."""
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 5.0
        }
        
        decisions = self.engine.analyze_and_decide(profile_data)
        
        # Should recommend switching QEC profile
        self.assertGreater(len(decisions), 0)
        decision_types = [d.decision_type for d in decisions]
        self.assertIn(AdaptiveDecision.SWITCH_QEC_PROFILE, decision_types)
    
    def test_analyze_high_latency(self):
        """Test analysis with high latency."""
        profile_data = {
            "avg_error_rates": {},
            "avg_duration": 15.0
        }
        
        decisions = self.engine.analyze_and_decide(profile_data)
        
        # Should recommend adjusting parallelism
        decision_types = [d.decision_type for d in decisions]
        self.assertIn(AdaptiveDecision.ADJUST_PARALLELISM, decision_types)
    
    def test_analyze_high_system_load(self):
        """Test analysis with high system load."""
        profile_data = {"avg_error_rates": {}, "avg_duration": 5.0}
        system_state = {"load": 0.9}
        
        decisions = self.engine.analyze_and_decide(profile_data, system_state)
        
        # Should recommend migration
        decision_types = [d.decision_type for d in decisions]
        self.assertIn(AdaptiveDecision.MIGRATE_JOB, decision_types)
    
    def test_recommend_variant_high_error(self):
        """Test variant recommendation for high error."""
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 5.0
        }
        
        variants = [
            {"variant_id": "v1", "estimated_error_rate": 0.001, "estimated_latency": 10.0, "score": 0.5},
            {"variant_id": "v2", "estimated_error_rate": 0.0001, "estimated_latency": 15.0, "score": 0.6},
            {"variant_id": "v3", "estimated_error_rate": 0.005, "estimated_latency": 5.0, "score": 0.4}
        ]
        
        recommended = self.engine.recommend_variant(profile_data, variants)
        
        # Should recommend lowest error variant
        self.assertEqual(recommended, "v2")
    
    def test_recommend_variant_high_latency(self):
        """Test variant recommendation for high latency."""
        profile_data = {
            "avg_error_rates": {},
            "avg_duration": 15.0
        }
        
        variants = [
            {"variant_id": "v1", "estimated_error_rate": 0.001, "estimated_latency": 10.0, "score": 0.5},
            {"variant_id": "v2", "estimated_error_rate": 0.0001, "estimated_latency": 15.0, "score": 0.6},
            {"variant_id": "v3", "estimated_error_rate": 0.005, "estimated_latency": 5.0, "score": 0.4}
        ]
        
        recommended = self.engine.recommend_variant(profile_data, variants)
        
        # Should recommend lowest latency variant
        self.assertEqual(recommended, "v3")
    
    def test_recommend_variant_balanced(self):
        """Test variant recommendation for balanced case."""
        profile_data = {
            "avg_error_rates": {},
            "avg_duration": 5.0
        }
        
        variants = [
            {"variant_id": "v1", "estimated_error_rate": 0.001, "estimated_latency": 10.0, "score": 0.5},
            {"variant_id": "v2", "estimated_error_rate": 0.0001, "estimated_latency": 15.0, "score": 0.8},
            {"variant_id": "v3", "estimated_error_rate": 0.005, "estimated_latency": 5.0, "score": 0.4}
        ]
        
        recommended = self.engine.recommend_variant(profile_data, variants)
        
        # Should recommend highest score variant
        self.assertEqual(recommended, "v2")
    
    def test_should_enable_checkpointing_long_job(self):
        """Test checkpointing recommendation for long job."""
        profile_data = {"avg_duration": 10.0}
        
        should_enable = self.engine.should_enable_checkpointing(profile_data)
        
        self.assertTrue(should_enable)
    
    def test_should_enable_checkpointing_high_priority(self):
        """Test checkpointing recommendation for high priority job."""
        profile_data = {"avg_duration": 2.0}
        job_metadata = {"priority": "high"}
        
        should_enable = self.engine.should_enable_checkpointing(
            profile_data, job_metadata
        )
        
        self.assertTrue(should_enable)
    
    def test_should_not_enable_checkpointing_short_job(self):
        """Test no checkpointing for short job."""
        profile_data = {"avg_duration": 1.0}
        job_metadata = {"priority": "normal"}
        
        should_enable = self.engine.should_enable_checkpointing(
            profile_data, job_metadata
        )
        
        self.assertFalse(should_enable)
    
    def test_decision_history(self):
        """Test decision history tracking."""
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 15.0
        }
        
        decisions = self.engine.analyze_and_decide(profile_data)
        
        self.assertEqual(len(self.engine.decision_history), len(decisions))
    
    def test_get_decision_statistics(self):
        """Test getting decision statistics."""
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 15.0
        }
        
        self.engine.analyze_and_decide(profile_data)
        self.engine.analyze_and_decide(profile_data)
        
        stats = self.engine.get_decision_statistics()
        
        self.assertGreater(stats["total_decisions"], 0)
        self.assertIn("by_type", stats)
        self.assertIn("avg_confidence", stats)
    
    def test_decision_confidence(self):
        """Test decision confidence scores."""
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 5.0
        }
        
        decisions = self.engine.analyze_and_decide(profile_data)
        
        # All decisions should have confidence scores
        self.assertTrue(all(0 <= d.confidence <= 1 for d in decisions))


if __name__ == "__main__":
    unittest.main()
