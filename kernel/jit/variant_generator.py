"""
Variant Generator

Generates execution variants with different QEC codes and optimization strategies.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class OptimizationStrategy(Enum):
    """Optimization strategies."""
    MINIMIZE_LATENCY = "minimize_latency"
    MINIMIZE_ERROR = "minimize_error"
    MINIMIZE_RESOURCES = "minimize_resources"
    BALANCED = "balanced"


@dataclass
class ExecutionVariant:
    """
    Represents an execution variant.
    
    Attributes:
        variant_id: Unique variant identifier
        graph_id: Source graph ID
        qec_profile: QEC profile to use
        optimization_strategy: Optimization strategy
        estimated_latency: Estimated execution time
        estimated_error_rate: Estimated error rate
        estimated_resources: Estimated resource usage
        score: Overall variant score
        metadata: Additional metadata
    """
    variant_id: str
    graph_id: str
    qec_profile: str
    optimization_strategy: OptimizationStrategy
    estimated_latency: float
    estimated_error_rate: float
    estimated_resources: int
    score: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def calculate_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate variant score based on weights.
        
        Args:
            weights: Weights for latency, error, resources
        
        Returns:
            Calculated score (higher is better)
        """
        if weights is None:
            weights = {
                "latency": 0.33,
                "error": 0.33,
                "resources": 0.34
            }
        
        # Normalize metrics (lower is better, so invert)
        latency_score = 1.0 / (1.0 + self.estimated_latency)
        error_score = 1.0 / (1.0 + self.estimated_error_rate * 100)
        resource_score = 1.0 / (1.0 + self.estimated_resources / 1000)
        
        self.score = (
            weights["latency"] * latency_score +
            weights["error"] * error_score +
            weights["resources"] * resource_score
        )
        
        return self.score


class VariantGenerator:
    """
    Generates execution variants with different configurations.
    
    Provides:
    - QEC profile selection
    - Optimization strategy application
    - Variant scoring and ranking
    - Profile-guided variant generation
    """
    
    # Available QEC profiles
    QEC_PROFILES = [
        "surface_code_d3",
        "surface_code_d5",
        "surface_code_d7",
        "color_code_d3",
        "color_code_d5",
        "bacon_shor_d3"
    ]
    
    def __init__(self):
        """Initialize variant generator."""
        self.variants: Dict[str, ExecutionVariant] = {}
        self.variant_counter = 0
    
    def generate_variants(
        self,
        graph_id: str,
        strategies: Optional[List[OptimizationStrategy]] = None,
        qec_profiles: Optional[List[str]] = None,
        max_variants: int = 10
    ) -> List[ExecutionVariant]:
        """
        Generate execution variants for a graph.
        
        Args:
            graph_id: Graph identifier
            strategies: Optimization strategies to try
            qec_profiles: QEC profiles to try
            max_variants: Maximum variants to generate
        
        Returns:
            List of ExecutionVariant objects
        """
        if strategies is None:
            strategies = list(OptimizationStrategy)
        
        if qec_profiles is None:
            qec_profiles = self.QEC_PROFILES[:3]  # Use top 3 by default
        
        variants = []
        
        for strategy in strategies:
            for qec_profile in qec_profiles:
                if len(variants) >= max_variants:
                    break
                
                variant = self._create_variant(
                    graph_id, qec_profile, strategy
                )
                variants.append(variant)
                self.variants[variant.variant_id] = variant
        
        # Score and sort variants
        for variant in variants:
            variant.calculate_score()
        
        variants.sort(key=lambda v: v.score, reverse=True)
        
        return variants
    
    def _create_variant(
        self,
        graph_id: str,
        qec_profile: str,
        strategy: OptimizationStrategy
    ) -> ExecutionVariant:
        """
        Create a single variant.
        
        Args:
            graph_id: Graph identifier
            qec_profile: QEC profile
            strategy: Optimization strategy
        
        Returns:
            ExecutionVariant object
        """
        variant_id = f"variant_{self.variant_counter}"
        self.variant_counter += 1
        
        # Estimate metrics based on QEC profile and strategy
        latency, error_rate, resources = self._estimate_metrics(
            qec_profile, strategy
        )
        
        variant = ExecutionVariant(
            variant_id=variant_id,
            graph_id=graph_id,
            qec_profile=qec_profile,
            optimization_strategy=strategy,
            estimated_latency=latency,
            estimated_error_rate=error_rate,
            estimated_resources=resources
        )
        
        return variant
    
    def _estimate_metrics(
        self,
        qec_profile: str,
        strategy: OptimizationStrategy
    ) -> tuple:
        """
        Estimate metrics for a configuration.
        
        Args:
            qec_profile: QEC profile
            strategy: Optimization strategy
        
        Returns:
            (latency, error_rate, resources) tuple
        """
        # Base metrics from QEC profile
        if "d3" in qec_profile:
            base_latency = 1.0
            base_error = 0.001
            base_resources = 100
        elif "d5" in qec_profile:
            base_latency = 2.0
            base_error = 0.0001
            base_resources = 250
        elif "d7" in qec_profile:
            base_latency = 3.5
            base_error = 0.00001
            base_resources = 500
        else:
            base_latency = 1.5
            base_error = 0.0005
            base_resources = 150
        
        # Adjust based on strategy
        if strategy == OptimizationStrategy.MINIMIZE_LATENCY:
            latency = base_latency * 0.8
            error = base_error * 1.2
            resources = base_resources * 1.1
        elif strategy == OptimizationStrategy.MINIMIZE_ERROR:
            latency = base_latency * 1.2
            error = base_error * 0.7
            resources = base_resources * 1.3
        elif strategy == OptimizationStrategy.MINIMIZE_RESOURCES:
            latency = base_latency * 1.1
            error = base_error * 1.1
            resources = base_resources * 0.8
        else:  # BALANCED
            latency = base_latency
            error = base_error
            resources = base_resources
        
        return latency, error, resources
    
    def select_best_variant(
        self,
        variants: List[ExecutionVariant],
        weights: Optional[Dict[str, float]] = None
    ) -> ExecutionVariant:
        """
        Select best variant based on weights.
        
        Args:
            variants: List of variants
            weights: Weights for scoring
        
        Returns:
            Best ExecutionVariant
        """
        if not variants:
            raise ValueError("No variants provided")
        
        # Recalculate scores with custom weights
        for variant in variants:
            variant.calculate_score(weights)
        
        return max(variants, key=lambda v: v.score)
    
    def generate_profile_guided_variants(
        self,
        graph_id: str,
        profile_data: Dict,
        max_variants: int = 5
    ) -> List[ExecutionVariant]:
        """
        Generate variants guided by profile data.
        
        Args:
            graph_id: Graph identifier
            profile_data: Profile data with metrics
            max_variants: Maximum variants to generate
        
        Returns:
            List of ExecutionVariant objects
        """
        variants = []
        
        # Analyze profile to determine best strategies
        avg_error = profile_data.get("avg_error_rates", {})
        avg_duration = profile_data.get("avg_duration", 0)
        
        # High error rate -> prioritize error minimization
        if avg_error and max(avg_error.values()) > 0.01:
            strategies = [
                OptimizationStrategy.MINIMIZE_ERROR,
                OptimizationStrategy.BALANCED
            ]
            qec_profiles = ["surface_code_d5", "surface_code_d7"]
        # Long duration -> prioritize latency
        elif avg_duration > 10.0:
            strategies = [
                OptimizationStrategy.MINIMIZE_LATENCY,
                OptimizationStrategy.BALANCED
            ]
            qec_profiles = ["surface_code_d3", "color_code_d3"]
        # Otherwise balanced
        else:
            strategies = [OptimizationStrategy.BALANCED]
            qec_profiles = ["surface_code_d3", "surface_code_d5"]
        
        return self.generate_variants(
            graph_id,
            strategies=strategies,
            qec_profiles=qec_profiles,
            max_variants=max_variants
        )
    
    def get_variant(self, variant_id: str) -> ExecutionVariant:
        """
        Get a variant.
        
        Args:
            variant_id: Variant identifier
        
        Returns:
            ExecutionVariant object
        """
        if variant_id not in self.variants:
            raise KeyError(f"Variant '{variant_id}' not found")
        
        return self.variants[variant_id]
    
    def get_variants_for_graph(self, graph_id: str) -> List[ExecutionVariant]:
        """
        Get all variants for a graph.
        
        Args:
            graph_id: Graph identifier
        
        Returns:
            List of ExecutionVariant objects
        """
        return [
            v for v in self.variants.values()
            if v.graph_id == graph_id
        ]
    
    def compare_variants(
        self,
        variant_ids: List[str]
    ) -> Dict:
        """
        Compare multiple variants.
        
        Args:
            variant_ids: List of variant IDs
        
        Returns:
            Comparison dictionary
        """
        variants = [self.get_variant(vid) for vid in variant_ids]
        
        return {
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "qec_profile": v.qec_profile,
                    "strategy": v.optimization_strategy.value,
                    "latency": v.estimated_latency,
                    "error_rate": v.estimated_error_rate,
                    "resources": v.estimated_resources,
                    "score": v.score
                }
                for v in variants
            ],
            "best_latency": min(variants, key=lambda v: v.estimated_latency).variant_id,
            "best_error": min(variants, key=lambda v: v.estimated_error_rate).variant_id,
            "best_resources": min(variants, key=lambda v: v.estimated_resources).variant_id,
            "best_overall": max(variants, key=lambda v: v.score).variant_id
        }
