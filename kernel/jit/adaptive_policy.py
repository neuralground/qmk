"""
Adaptive Policy Engine

Makes runtime decisions based on execution profiles and system state.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AdaptiveDecision(Enum):
    """Types of adaptive decisions."""
    SWITCH_QEC_PROFILE = "switch_qec_profile"
    ADJUST_PARALLELISM = "adjust_parallelism"
    ENABLE_CHECKPOINTING = "enable_checkpointing"
    MIGRATE_JOB = "migrate_job"
    RETRY_WITH_VARIANT = "retry_with_variant"


@dataclass
class PolicyDecision:
    """
    Represents an adaptive policy decision.
    
    Attributes:
        decision_type: Type of decision
        reason: Reason for decision
        parameters: Decision parameters
        confidence: Confidence score (0-1)
    """
    decision_type: AdaptiveDecision
    reason: str
    parameters: Dict
    confidence: float = 1.0


class AdaptivePolicyEngine:
    """
    Makes adaptive runtime decisions.
    
    Provides:
    - Profile-based decision making
    - Dynamic optimization
    - Failure recovery strategies
    - Resource adaptation
    """
    
    def __init__(self):
        """Initialize adaptive policy engine."""
        self.decision_history: List[PolicyDecision] = []
        
        # Thresholds
        self.error_threshold = 0.01  # 1%
        self.latency_threshold = 10.0  # seconds
        self.retry_threshold = 3
    
    def analyze_and_decide(
        self,
        profile_data: Dict,
        system_state: Optional[Dict] = None
    ) -> List[PolicyDecision]:
        """
        Analyze profile and make decisions.
        
        Args:
            profile_data: Execution profile data
            system_state: Current system state
        
        Returns:
            List of PolicyDecision objects
        """
        decisions = []
        system_state = system_state or {}
        
        # Check error rates
        error_decision = self._check_error_rates(profile_data)
        if error_decision:
            decisions.append(error_decision)
        
        # Check latency
        latency_decision = self._check_latency(profile_data)
        if latency_decision:
            decisions.append(latency_decision)
        
        # Check resource usage
        resource_decision = self._check_resources(profile_data, system_state)
        if resource_decision:
            decisions.append(resource_decision)
        
        # Check failure patterns
        failure_decision = self._check_failures(profile_data)
        if failure_decision:
            decisions.append(failure_decision)
        
        # Store decisions
        self.decision_history.extend(decisions)
        
        return decisions
    
    def _check_error_rates(self, profile_data: Dict) -> Optional[PolicyDecision]:
        """Check if error rates are too high."""
        avg_error_rates = profile_data.get("avg_error_rates", {})
        
        if not avg_error_rates:
            return None
        
        max_error = max(avg_error_rates.values())
        
        if max_error > self.error_threshold:
            return PolicyDecision(
                decision_type=AdaptiveDecision.SWITCH_QEC_PROFILE,
                reason=f"High error rate detected: {max_error:.4f}",
                parameters={
                    "current_error": max_error,
                    "suggested_profile": "surface_code_d7"
                },
                confidence=0.9
            )
        
        return None
    
    def _check_latency(self, profile_data: Dict) -> Optional[PolicyDecision]:
        """Check if latency is too high."""
        avg_duration = profile_data.get("avg_duration", 0)
        
        if avg_duration > self.latency_threshold:
            return PolicyDecision(
                decision_type=AdaptiveDecision.ADJUST_PARALLELISM,
                reason=f"High latency detected: {avg_duration:.2f}s",
                parameters={
                    "current_duration": avg_duration,
                    "suggested_parallelism": 4
                },
                confidence=0.8
            )
        
        return None
    
    def _check_resources(
        self,
        profile_data: Dict,
        system_state: Dict
    ) -> Optional[PolicyDecision]:
        """Check resource usage."""
        # Check if system is under load
        system_load = system_state.get("load", 0.5)
        
        if system_load > 0.8:
            return PolicyDecision(
                decision_type=AdaptiveDecision.MIGRATE_JOB,
                reason=f"High system load: {system_load:.2f}",
                parameters={
                    "current_load": system_load,
                    "target_context": "remote"
                },
                confidence=0.7
            )
        
        return None
    
    def _check_failures(self, profile_data: Dict) -> Optional[PolicyDecision]:
        """Check for failure patterns."""
        # Check recent decision history for retries
        recent_retries = sum(
            1 for d in self.decision_history[-10:]
            if d.decision_type == AdaptiveDecision.RETRY_WITH_VARIANT
        )
        
        if recent_retries >= self.retry_threshold:
            return PolicyDecision(
                decision_type=AdaptiveDecision.ENABLE_CHECKPOINTING,
                reason=f"Multiple retries detected: {recent_retries}",
                parameters={
                    "checkpoint_strategy": "before_measure"
                },
                confidence=0.85
            )
        
        return None
    
    def recommend_variant(
        self,
        profile_data: Dict,
        available_variants: List[Dict]
    ) -> Optional[str]:
        """
        Recommend best variant based on profile.
        
        Args:
            profile_data: Profile data
            available_variants: List of available variants
        
        Returns:
            Recommended variant ID or None
        """
        if not available_variants:
            return None
        
        # Analyze profile to determine priority
        avg_error = profile_data.get("avg_error_rates", {})
        avg_duration = profile_data.get("avg_duration", 0)
        
        # High error -> prioritize low error variants
        if avg_error and max(avg_error.values()) > self.error_threshold:
            best = min(
                available_variants,
                key=lambda v: v.get("estimated_error_rate", 1.0)
            )
            return best.get("variant_id")
        
        # High latency -> prioritize low latency variants
        if avg_duration > self.latency_threshold:
            best = min(
                available_variants,
                key=lambda v: v.get("estimated_latency", 100.0)
            )
            return best.get("variant_id")
        
        # Otherwise, use highest score
        best = max(
            available_variants,
            key=lambda v: v.get("score", 0.0)
        )
        return best.get("variant_id")
    
    def should_enable_checkpointing(
        self,
        profile_data: Dict,
        job_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Decide if checkpointing should be enabled.
        
        Args:
            profile_data: Profile data
            job_metadata: Job metadata
        
        Returns:
            True if checkpointing recommended
        """
        job_metadata = job_metadata or {}
        
        # Enable for long-running jobs
        avg_duration = profile_data.get("avg_duration", 0)
        if avg_duration > 5.0:
            return True
        
        # Enable for high-value jobs
        if job_metadata.get("priority") == "high":
            return True
        
        # Enable if recent failures
        recent_failures = sum(
            1 for d in self.decision_history[-5:]
            if "failure" in d.reason.lower()
        )
        if recent_failures > 0:
            return True
        
        return False
    
    def get_decision_statistics(self) -> Dict:
        """
        Get statistics about decisions.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.decision_history)
        
        by_type = {}
        for decision in self.decision_history:
            dtype = decision.decision_type.value
            by_type[dtype] = by_type.get(dtype, 0) + 1
        
        avg_confidence = (
            sum(d.confidence for d in self.decision_history) / total
            if total > 0 else 0
        )
        
        return {
            "total_decisions": total,
            "by_type": by_type,
            "avg_confidence": avg_confidence
        }
