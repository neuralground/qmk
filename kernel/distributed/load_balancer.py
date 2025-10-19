"""
Load Balancer

Balances workload across compute nodes in distributed cluster.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import random

from .node_manager import NodeManager, ComputeNode


class BalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    CAPABILITY_BASED = "capability_based"


@dataclass
class WorkloadMetrics:
    """
    Workload metrics for a job.
    
    Attributes:
        estimated_qubits: Estimated qubits needed
        estimated_memory_mb: Estimated memory needed
        estimated_time_s: Estimated execution time
        priority: Job priority
    """
    estimated_qubits: int = 0
    estimated_memory_mb: int = 0
    estimated_time_s: float = 0.0
    priority: int = 0


class LoadBalancer:
    """
    Balances load across compute nodes.
    
    Strategies:
    - Round-robin
    - Least-loaded
    - Capability-based
    """
    
    def __init__(
        self,
        node_manager: NodeManager,
        strategy: BalancingStrategy = BalancingStrategy.LEAST_LOADED
    ):
        """
        Initialize load balancer.
        
        Args:
            node_manager: Node manager instance
            strategy: Balancing strategy
        """
        self.node_manager = node_manager
        self.strategy = strategy
        self.round_robin_index = 0
    
    def select_node(
        self,
        workload: WorkloadMetrics
    ) -> Optional[ComputeNode]:
        """
        Select best node for workload.
        
        Args:
            workload: Workload metrics
        
        Returns:
            Selected node or None
        """
        if self.strategy == BalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin()
        elif self.strategy == BalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded(workload)
        elif self.strategy == BalancingStrategy.CAPABILITY_BASED:
            return self._select_capability_based(workload)
        else:  # RANDOM
            return self._select_random()
    
    def _select_round_robin(self) -> Optional[ComputeNode]:
        """Select node using round-robin."""
        available = self.node_manager.get_available_nodes()
        
        if not available:
            return None
        
        node = available[self.round_robin_index % len(available)]
        self.round_robin_index += 1
        
        return node
    
    def _select_least_loaded(
        self,
        workload: WorkloadMetrics
    ) -> Optional[ComputeNode]:
        """Select least loaded node."""
        available = self.node_manager.get_available_nodes(
            min_qubits=workload.estimated_qubits,
            min_memory_mb=workload.estimated_memory_mb
        )
        
        if not available:
            return None
        
        # Select node with lowest load
        return min(available, key=lambda n: n.current_load)
    
    def _select_capability_based(
        self,
        workload: WorkloadMetrics
    ) -> Optional[ComputeNode]:
        """Select node based on capabilities."""
        available = self.node_manager.get_available_nodes(
            min_qubits=workload.estimated_qubits,
            min_memory_mb=workload.estimated_memory_mb
        )
        
        if not available:
            return None
        
        # Score nodes based on capability match
        scored_nodes = []
        
        for node in available:
            if not node.capabilities:
                continue
            
            # Calculate capability score
            qubit_score = min(1.0, workload.estimated_qubits / node.capabilities.max_qubits)
            memory_score = min(1.0, workload.estimated_memory_mb / node.capabilities.max_memory_mb)
            load_score = 1.0 - node.current_load
            
            # Weighted score
            score = (qubit_score * 0.4 + memory_score * 0.3 + load_score * 0.3)
            scored_nodes.append((score, node))
        
        if not scored_nodes:
            return None
        
        # Return highest scoring node
        return max(scored_nodes, key=lambda x: x[0])[1]
    
    def _select_random(self) -> Optional[ComputeNode]:
        """Select random node."""
        available = self.node_manager.get_available_nodes()
        
        if not available:
            return None
        
        return random.choice(available)
    
    def balance_workload(
        self,
        workloads: List[WorkloadMetrics]
    ) -> Dict[str, List[int]]:
        """
        Balance multiple workloads across nodes.
        
        Args:
            workloads: List of workload metrics
        
        Returns:
            Dictionary mapping node_id to workload indices
        """
        assignments: Dict[str, List[int]] = {}
        
        for idx, workload in enumerate(workloads):
            node = self.select_node(workload)
            
            if node:
                if node.node_id not in assignments:
                    assignments[node.node_id] = []
                assignments[node.node_id].append(idx)
        
        return assignments
    
    def get_balance_stats(self) -> Dict:
        """
        Get load balancing statistics.
        
        Returns:
            Statistics dictionary
        """
        cluster_stats = self.node_manager.get_cluster_stats()
        
        # Calculate load distribution
        loads = [
            node.current_load for node in self.node_manager.nodes.values()
            if node.status.value == "online"
        ]
        
        if loads:
            load_variance = sum((l - cluster_stats["average_load"]) ** 2 for l in loads) / len(loads)
        else:
            load_variance = 0.0
        
        return {
            "strategy": self.strategy.value,
            "average_load": cluster_stats["average_load"],
            "load_variance": load_variance,
            "balance_quality": 1.0 - min(1.0, load_variance)  # 1.0 = perfectly balanced
        }
