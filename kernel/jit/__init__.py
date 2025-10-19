"""
JIT and Adaptivity

Implements profile-guided optimization and adaptive execution.
"""

from .profile_collector import ProfileCollector, ExecutionProfile
from .variant_generator import VariantGenerator, ExecutionVariant, OptimizationStrategy
from .teleportation_planner import TeleportationPlanner, TeleportationPlan, TeleportationSite
from .adaptive_policy import AdaptivePolicyEngine, PolicyDecision, AdaptiveDecision

__all__ = [
    "ProfileCollector",
    "ExecutionProfile",
    "VariantGenerator",
    "ExecutionVariant",
    "OptimizationStrategy",
    "TeleportationPlanner",
    "TeleportationPlan",
    "TeleportationSite",
    "AdaptivePolicyEngine",
    "PolicyDecision",
    "AdaptiveDecision",
]
