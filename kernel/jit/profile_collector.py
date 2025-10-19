"""
Profile Collector

Collects execution profiles for performance analysis and optimization.
"""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ExecutionProfile:
    """
    Execution profile for a job or graph.
    
    Attributes:
        profile_id: Unique profile identifier
        job_id: Associated job ID
        graph_id: Associated graph ID
        start_time: Profile start timestamp
        end_time: Profile end timestamp
        total_duration: Total execution time
        node_timings: Per-node execution times
        gate_counts: Gate operation counts
        qubit_usage: Qubit usage statistics
        error_rates: Observed error rates
        resource_usage: Resource consumption
        metadata: Additional metadata
    """
    profile_id: str
    job_id: str
    graph_id: str
    start_time: float
    end_time: float
    total_duration: float
    node_timings: Dict[str, float] = field(default_factory=dict)
    gate_counts: Dict[str, int] = field(default_factory=dict)
    qubit_usage: Dict[str, int] = field(default_factory=dict)
    error_rates: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def get_hotspots(self, top_n: int = 10) -> List[tuple]:
        """
        Get top N hotspots (slowest nodes).
        
        Args:
            top_n: Number of hotspots to return
        
        Returns:
            List of (node_id, duration) tuples
        """
        sorted_nodes = sorted(
            self.node_timings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_nodes[:top_n]
    
    def get_most_frequent_gates(self, top_n: int = 10) -> List[tuple]:
        """
        Get most frequently used gates.
        
        Args:
            top_n: Number of gates to return
        
        Returns:
            List of (gate_type, count) tuples
        """
        sorted_gates = sorted(
            self.gate_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_gates[:top_n]


class ProfileCollector:
    """
    Collects and manages execution profiles.
    
    Provides:
    - Profile collection during execution
    - Performance metrics tracking
    - Hotspot identification
    - Historical profile analysis
    """
    
    def __init__(self, max_profiles: int = 1000):
        """
        Initialize profile collector.
        
        Args:
            max_profiles: Maximum profiles to keep
        """
        self.max_profiles = max_profiles
        self.profiles: Dict[str, ExecutionProfile] = {}
        self.profile_counter = 0
        
        # Active profiling sessions
        self.active_sessions: Dict[str, Dict] = {}
    
    def start_profiling(
        self,
        job_id: str,
        graph_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Start profiling a job execution.
        
        Args:
            job_id: Job identifier
            graph_id: Graph identifier
            metadata: Optional metadata
        
        Returns:
            Profile ID
        """
        profile_id = f"profile_{self.profile_counter}"
        self.profile_counter += 1
        
        self.active_sessions[profile_id] = {
            "job_id": job_id,
            "graph_id": graph_id,
            "start_time": time.time(),
            "node_timings": {},
            "gate_counts": defaultdict(int),
            "qubit_usage": defaultdict(int),
            "error_rates": {},
            "metadata": metadata or {}
        }
        
        return profile_id
    
    def record_node_execution(
        self,
        profile_id: str,
        node_id: str,
        duration: float,
        gate_type: Optional[str] = None
    ):
        """
        Record execution of a node.
        
        Args:
            profile_id: Profile identifier
            node_id: Node identifier
            duration: Execution duration
            gate_type: Optional gate type
        """
        if profile_id not in self.active_sessions:
            return
        
        session = self.active_sessions[profile_id]
        session["node_timings"][node_id] = duration
        
        if gate_type:
            session["gate_counts"][gate_type] += 1
    
    def record_qubit_usage(
        self,
        profile_id: str,
        qubit_id: str,
        usage_count: int = 1
    ):
        """
        Record qubit usage.
        
        Args:
            profile_id: Profile identifier
            qubit_id: Qubit identifier
            usage_count: Usage count
        """
        if profile_id not in self.active_sessions:
            return
        
        session = self.active_sessions[profile_id]
        session["qubit_usage"][qubit_id] += usage_count
    
    def record_error_rate(
        self,
        profile_id: str,
        operation: str,
        error_rate: float
    ):
        """
        Record observed error rate.
        
        Args:
            profile_id: Profile identifier
            operation: Operation name
            error_rate: Error rate
        """
        if profile_id not in self.active_sessions:
            return
        
        session = self.active_sessions[profile_id]
        session["error_rates"][operation] = error_rate
    
    def end_profiling(self, profile_id: str) -> ExecutionProfile:
        """
        End profiling and create profile.
        
        Args:
            profile_id: Profile identifier
        
        Returns:
            ExecutionProfile object
        """
        if profile_id not in self.active_sessions:
            raise KeyError(f"Profile '{profile_id}' not found")
        
        session = self.active_sessions[profile_id]
        end_time = time.time()
        
        profile = ExecutionProfile(
            profile_id=profile_id,
            job_id=session["job_id"],
            graph_id=session["graph_id"],
            start_time=session["start_time"],
            end_time=end_time,
            total_duration=end_time - session["start_time"],
            node_timings=dict(session["node_timings"]),
            gate_counts=dict(session["gate_counts"]),
            qubit_usage=dict(session["qubit_usage"]),
            error_rates=dict(session["error_rates"]),
            metadata=session["metadata"]
        )
        
        # Store profile
        self.profiles[profile_id] = profile
        
        # Cleanup session
        del self.active_sessions[profile_id]
        
        # Enforce max profiles
        if len(self.profiles) > self.max_profiles:
            oldest = min(self.profiles.keys())
            del self.profiles[oldest]
        
        return profile
    
    def get_profile(self, profile_id: str) -> ExecutionProfile:
        """
        Get a profile.
        
        Args:
            profile_id: Profile identifier
        
        Returns:
            ExecutionProfile object
        """
        if profile_id not in self.profiles:
            raise KeyError(f"Profile '{profile_id}' not found")
        
        return self.profiles[profile_id]
    
    def get_profiles_for_job(self, job_id: str) -> List[ExecutionProfile]:
        """
        Get all profiles for a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            List of ExecutionProfile objects
        """
        return [
            p for p in self.profiles.values()
            if p.job_id == job_id
        ]
    
    def get_profiles_for_graph(self, graph_id: str) -> List[ExecutionProfile]:
        """
        Get all profiles for a graph.
        
        Args:
            graph_id: Graph identifier
        
        Returns:
            List of ExecutionProfile objects
        """
        return [
            p for p in self.profiles.values()
            if p.graph_id == graph_id
        ]
    
    def aggregate_profiles(
        self,
        profile_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Aggregate statistics across profiles.
        
        Args:
            profile_ids: Optional list of profile IDs (None = all)
        
        Returns:
            Dictionary with aggregated statistics
        """
        if profile_ids:
            profiles = [self.profiles[pid] for pid in profile_ids if pid in self.profiles]
        else:
            profiles = list(self.profiles.values())
        
        if not profiles:
            return {}
        
        # Aggregate gate counts
        total_gate_counts = defaultdict(int)
        for profile in profiles:
            for gate, count in profile.gate_counts.items():
                total_gate_counts[gate] += count
        
        # Aggregate error rates (average)
        error_rates = defaultdict(list)
        for profile in profiles:
            for op, rate in profile.error_rates.items():
                error_rates[op].append(rate)
        
        avg_error_rates = {
            op: sum(rates) / len(rates)
            for op, rates in error_rates.items()
        }
        
        # Aggregate durations
        total_duration = sum(p.total_duration for p in profiles)
        avg_duration = total_duration / len(profiles)
        
        return {
            "num_profiles": len(profiles),
            "total_duration": total_duration,
            "avg_duration": avg_duration,
            "total_gate_counts": dict(total_gate_counts),
            "avg_error_rates": avg_error_rates
        }
    
    def identify_optimization_opportunities(
        self,
        profile_id: str
    ) -> List[Dict]:
        """
        Identify optimization opportunities from profile.
        
        Args:
            profile_id: Profile identifier
        
        Returns:
            List of optimization suggestions
        """
        profile = self.get_profile(profile_id)
        opportunities = []
        
        # Check for hotspots
        hotspots = profile.get_hotspots(top_n=5)
        if hotspots:
            opportunities.append({
                "type": "hotspot",
                "description": "Optimize slow nodes",
                "nodes": [node_id for node_id, _ in hotspots],
                "potential_savings": sum(duration for _, duration in hotspots)
            })
        
        # Check for high error rates
        high_error_ops = [
            op for op, rate in profile.error_rates.items()
            if rate > 0.01  # 1% error rate threshold
        ]
        if high_error_ops:
            opportunities.append({
                "type": "error_mitigation",
                "description": "High error rates detected",
                "operations": high_error_ops
            })
        
        # Check for frequently used gates
        frequent_gates = profile.get_most_frequent_gates(top_n=3)
        if frequent_gates:
            opportunities.append({
                "type": "gate_optimization",
                "description": "Optimize frequently used gates",
                "gates": [gate for gate, _ in frequent_gates]
            })
        
        return opportunities
    
    def get_statistics(self) -> Dict:
        """
        Get collector statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_profiles = len(self.profiles)
        active_sessions = len(self.active_sessions)
        
        if total_profiles > 0:
            avg_duration = sum(p.total_duration for p in self.profiles.values()) / total_profiles
        else:
            avg_duration = 0
        
        return {
            "total_profiles": total_profiles,
            "active_sessions": active_sessions,
            "avg_duration": avg_duration
        }
