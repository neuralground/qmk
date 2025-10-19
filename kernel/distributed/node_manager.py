"""
Node Manager

Manages compute nodes in a distributed quantum computing cluster.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class NodeStatus(Enum):
    """Node status."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


@dataclass
class NodeCapabilities:
    """
    Node capabilities.
    
    Attributes:
        max_qubits: Maximum qubits
        max_memory_mb: Maximum memory in MB
        cpu_cores: Number of CPU cores
        has_gpu: Has GPU acceleration
        network_bandwidth_mbps: Network bandwidth
    """
    max_qubits: int
    max_memory_mb: int
    cpu_cores: int
    has_gpu: bool = False
    network_bandwidth_mbps: float = 1000.0


@dataclass
class ComputeNode:
    """
    Represents a compute node.
    
    Attributes:
        node_id: Unique node identifier
        hostname: Node hostname
        port: Node port
        status: Current status
        capabilities: Node capabilities
        current_load: Current load (0.0-1.0)
        active_jobs: Set of active job IDs
    """
    node_id: str
    hostname: str
    port: int
    status: NodeStatus = NodeStatus.OFFLINE
    capabilities: Optional[NodeCapabilities] = None
    current_load: float = 0.0
    active_jobs: Set[str] = field(default_factory=set)
    last_heartbeat: float = 0.0


class NodeManager:
    """
    Manages cluster of compute nodes.
    
    Provides:
    - Node registration and discovery
    - Health monitoring
    - Load tracking
    - Node selection
    """
    
    def __init__(self):
        """Initialize node manager."""
        self.nodes: Dict[str, ComputeNode] = {}
        self.heartbeat_timeout = 30.0  # seconds
    
    def register_node(
        self,
        node_id: str,
        hostname: str,
        port: int,
        capabilities: NodeCapabilities
    ) -> ComputeNode:
        """
        Register a compute node.
        
        Args:
            node_id: Node identifier
            hostname: Node hostname
            port: Node port
            capabilities: Node capabilities
        
        Returns:
            ComputeNode instance
        """
        node = ComputeNode(
            node_id=node_id,
            hostname=hostname,
            port=port,
            status=NodeStatus.ONLINE,
            capabilities=capabilities,
            last_heartbeat=time.time()
        )
        
        self.nodes[node_id] = node
        return node
    
    def unregister_node(self, node_id: str):
        """
        Unregister a node.
        
        Args:
            node_id: Node identifier
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def update_node_status(
        self,
        node_id: str,
        status: NodeStatus,
        load: Optional[float] = None
    ):
        """
        Update node status.
        
        Args:
            node_id: Node identifier
            status: New status
            load: Current load (optional)
        """
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found")
        
        node = self.nodes[node_id]
        node.status = status
        node.last_heartbeat = time.time()
        
        if load is not None:
            node.current_load = load
    
    def heartbeat(self, node_id: str, load: float):
        """
        Process node heartbeat.
        
        Args:
            node_id: Node identifier
            load: Current load
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.last_heartbeat = time.time()
            node.current_load = load
            
            # Update status based on load
            if load > 0.9:
                node.status = NodeStatus.BUSY
            elif node.status == NodeStatus.BUSY and load < 0.7:
                node.status = NodeStatus.ONLINE
    
    def check_node_health(self):
        """Check health of all nodes."""
        current_time = time.time()
        
        for node in self.nodes.values():
            if node.status == NodeStatus.OFFLINE:
                continue
            
            # Check if heartbeat timeout
            if current_time - node.last_heartbeat > self.heartbeat_timeout:
                node.status = NodeStatus.OFFLINE
    
    def get_available_nodes(
        self,
        min_qubits: Optional[int] = None,
        min_memory_mb: Optional[int] = None
    ) -> List[ComputeNode]:
        """
        Get available nodes matching requirements.
        
        Args:
            min_qubits: Minimum qubits required
            min_memory_mb: Minimum memory required
        
        Returns:
            List of available nodes
        """
        available = []
        
        for node in self.nodes.values():
            # Check status
            if node.status not in [NodeStatus.ONLINE, NodeStatus.BUSY]:
                continue
            
            # Check capabilities
            if node.capabilities:
                if min_qubits and node.capabilities.max_qubits < min_qubits:
                    continue
                if min_memory_mb and node.capabilities.max_memory_mb < min_memory_mb:
                    continue
            
            available.append(node)
        
        return available
    
    def select_best_node(
        self,
        requirements: Optional[Dict] = None
    ) -> Optional[ComputeNode]:
        """
        Select best node for job.
        
        Args:
            requirements: Job requirements
        
        Returns:
            Best node or None
        """
        min_qubits = requirements.get("qubits", 0) if requirements else 0
        min_memory = requirements.get("memory_mb", 0) if requirements else 0
        
        available = self.get_available_nodes(min_qubits, min_memory)
        
        if not available:
            return None
        
        # Select node with lowest load
        return min(available, key=lambda n: n.current_load)
    
    def assign_job(self, node_id: str, job_id: str):
        """
        Assign job to node.
        
        Args:
            node_id: Node identifier
            job_id: Job identifier
        """
        if node_id in self.nodes:
            self.nodes[node_id].active_jobs.add(job_id)
    
    def complete_job(self, node_id: str, job_id: str):
        """
        Mark job as complete on node.
        
        Args:
            node_id: Node identifier
            job_id: Job identifier
        """
        if node_id in self.nodes:
            self.nodes[node_id].active_jobs.discard(job_id)
    
    def get_cluster_stats(self) -> Dict:
        """
        Get cluster statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_nodes = len(self.nodes)
        online_nodes = sum(
            1 for n in self.nodes.values()
            if n.status == NodeStatus.ONLINE
        )
        busy_nodes = sum(
            1 for n in self.nodes.values()
            if n.status == NodeStatus.BUSY
        )
        
        total_qubits = sum(
            n.capabilities.max_qubits for n in self.nodes.values()
            if n.capabilities and n.status == NodeStatus.ONLINE
        )
        
        avg_load = (
            sum(n.current_load for n in self.nodes.values()) / total_nodes
            if total_nodes > 0 else 0.0
        )
        
        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "busy_nodes": busy_nodes,
            "offline_nodes": total_nodes - online_nodes - busy_nodes,
            "total_qubits": total_qubits,
            "average_load": avg_load
        }
    
    def list_nodes(self) -> List[Dict]:
        """
        List all nodes with their info.
        
        Returns:
            List of node info dictionaries
        """
        return [
            {
                "node_id": node.node_id,
                "hostname": node.hostname,
                "port": node.port,
                "status": node.status.value,
                "load": node.current_load,
                "active_jobs": len(node.active_jobs),
                "max_qubits": node.capabilities.max_qubits if node.capabilities else 0
            }
            for node in self.nodes.values()
        ]
