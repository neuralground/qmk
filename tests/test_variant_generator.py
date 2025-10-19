"""
Unit tests for Variant Generator
"""

import unittest
from kernel.jit.variant_generator import VariantGenerator, OptimizationStrategy


class TestVariantGenerator(unittest.TestCase):
    """Test variant generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = VariantGenerator()
    
    def test_generate_variants(self):
        """Test generating variants."""
        variants = self.generator.generate_variants(
            graph_id="graph_1",
            strategies=[OptimizationStrategy.BALANCED],
            qec_profiles=["surface_code_d3", "surface_code_d5"],
            max_variants=5
        )
        
        self.assertEqual(len(variants), 2)
        self.assertTrue(all(v.graph_id == "graph_1" for v in variants))
    
    def test_variant_scoring(self):
        """Test variant scoring."""
        variants = self.generator.generate_variants(
            graph_id="graph_1",
            max_variants=3
        )
        
        # All variants should have scores
        self.assertTrue(all(v.score > 0 for v in variants))
        
        # Should be sorted by score (highest first)
        scores = [v.score for v in variants]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_select_best_variant(self):
        """Test selecting best variant."""
        variants = self.generator.generate_variants("graph_1", max_variants=5)
        
        best = self.generator.select_best_variant(variants)
        
        self.assertIsNotNone(best)
        self.assertEqual(best.score, max(v.score for v in variants))
    
    def test_select_best_with_custom_weights(self):
        """Test selecting best variant with custom weights."""
        variants = self.generator.generate_variants("graph_1", max_variants=5)
        
        # Prioritize error minimization
        best = self.generator.select_best_variant(
            variants,
            weights={"latency": 0.2, "error": 0.6, "resources": 0.2}
        )
        
        self.assertIsNotNone(best)
    
    def test_optimization_strategies(self):
        """Test different optimization strategies."""
        strategies = [
            OptimizationStrategy.MINIMIZE_LATENCY,
            OptimizationStrategy.MINIMIZE_ERROR,
            OptimizationStrategy.MINIMIZE_RESOURCES,
            OptimizationStrategy.BALANCED
        ]
        
        variants = self.generator.generate_variants(
            "graph_1",
            strategies=strategies,
            qec_profiles=["surface_code_d3"],
            max_variants=10
        )
        
        self.assertEqual(len(variants), 4)
        
        # Check that different strategies produce different metrics
        latencies = [v.estimated_latency for v in variants]
        self.assertGreater(len(set(latencies)), 1)
    
    def test_profile_guided_generation(self):
        """Test profile-guided variant generation."""
        # High error rate profile
        profile_data = {
            "avg_error_rates": {"CNOT": 0.02},
            "avg_duration": 5.0
        }
        
        variants = self.generator.generate_profile_guided_variants(
            "graph_1",
            profile_data,
            max_variants=5
        )
        
        self.assertGreater(len(variants), 0)
        
        # Should prioritize error minimization
        strategies = [v.optimization_strategy for v in variants]
        self.assertIn(OptimizationStrategy.MINIMIZE_ERROR, strategies)
    
    def test_profile_guided_high_latency(self):
        """Test profile-guided generation for high latency."""
        profile_data = {
            "avg_error_rates": {},
            "avg_duration": 15.0
        }
        
        variants = self.generator.generate_profile_guided_variants(
            "graph_1",
            profile_data
        )
        
        strategies = [v.optimization_strategy for v in variants]
        self.assertIn(OptimizationStrategy.MINIMIZE_LATENCY, strategies)
    
    def test_get_variants_for_graph(self):
        """Test getting variants for a graph."""
        self.generator.generate_variants("graph_1", max_variants=3)
        self.generator.generate_variants("graph_2", max_variants=2)
        
        graph1_variants = self.generator.get_variants_for_graph("graph_1")
        
        self.assertEqual(len(graph1_variants), 3)
        self.assertTrue(all(v.graph_id == "graph_1" for v in graph1_variants))
    
    def test_compare_variants(self):
        """Test comparing variants."""
        variants = self.generator.generate_variants("graph_1", max_variants=3)
        variant_ids = [v.variant_id for v in variants]
        
        comparison = self.generator.compare_variants(variant_ids)
        
        self.assertIn("variants", comparison)
        self.assertIn("best_latency", comparison)
        self.assertIn("best_error", comparison)
        self.assertIn("best_resources", comparison)
        self.assertIn("best_overall", comparison)
    
    def test_variant_calculate_score(self):
        """Test variant score calculation."""
        variants = self.generator.generate_variants("graph_1", max_variants=1)
        variant = variants[0]
        
        # Recalculate with different weights
        new_score = variant.calculate_score(
            weights={"latency": 0.5, "error": 0.3, "resources": 0.2}
        )
        
        self.assertGreater(new_score, 0)


if __name__ == "__main__":
    unittest.main()
