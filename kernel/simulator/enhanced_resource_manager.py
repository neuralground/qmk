"""
Enhanced Resource Manager with Logical Qubit Support

Manages allocation and tracking of logical qubits with QEC profiles.
"""

from typing import Dict, List, Optional, Tuple
from .logical_qubit import LogicalQubit
from .qec_profiles import QECProfile, parse_profile_string


class EnhancedResourceManager:
    """
    Resource manager with logical qubit simulation.
    
    Tracks:
    - Logical qubit allocation and deallocation
    - Virtual -> Logical qubit mapping
    - Physical qubit usage (from QEC profiles)
    - Channel handles
    """
    
    def __init__(self, max_physical_qubits: int = 10000, seed: Optional[int] = None):
        """
        Initialize resource manager.
        
        Args:
            max_physical_qubits: Maximum physical qubits available
            seed: Random seed for deterministic simulation
        """
        self.max_physical_qubits = max_physical_qubits
        self.seed = seed
        self.seed_counter = 0  # For generating unique seeds per qubit
        
        # Virtual qubit ID -> LogicalQubit instance
        self.logical_qubits: Dict[str, LogicalQubit] = {}
        
        # Track physical qubit usage
        self.physical_qubits_used = 0
        
        # Channel tracking
        self.channels: Dict[str, Dict] = {}
        
        # Current simulation time
        self.current_time_us = 0.0
    
    def reset(self):
        """
        Reset the resource manager to initial state.
        
        Clears all allocated qubits and channels. Useful for running
        multiple independent jobs with the same manager.
        """
        self.logical_qubits.clear()
        self.physical_qubits_used = 0
        self.channels.clear()
        self.current_time_us = 0.0
        self.seed_counter = 0
    
    def alloc_logical_qubits(self, vq_ids: List[str], profile: QECProfile) -> List[Tuple[str, int]]:
        """
        Allocate logical qubits with specified QEC profile.
        
        Args:
            vq_ids: List of virtual qubit IDs to allocate
            profile: QEC profile to use
        
        Returns:
            List of (vq_id, physical_qubit_count) tuples
        
        Raises:
            RuntimeError: If insufficient physical qubits available
        """
        # Check if we have enough physical qubits
        required_physical = len(vq_ids) * profile.physical_qubit_count
        
        if self.physical_qubits_used + required_physical > self.max_physical_qubits:
            raise RuntimeError(
                f"Insufficient physical qubits: need {required_physical}, "
                f"have {self.max_physical_qubits - self.physical_qubits_used} available"
            )
        
        allocated = []
        
        for vq_id in vq_ids:
            if vq_id in self.logical_qubits:
                raise RuntimeError(f"Virtual qubit '{vq_id}' already allocated")
            
            # Create logical qubit with unique seed
            qubit_seed = None if self.seed is None else self.seed + self.seed_counter
            self.seed_counter += 1
            
            logical_qubit = LogicalQubit(vq_id, profile, seed=qubit_seed)
            self.logical_qubits[vq_id] = logical_qubit
            
            # Track physical qubit usage
            self.physical_qubits_used += profile.physical_qubit_count
            
            allocated.append((vq_id, profile.physical_qubit_count))
        
        return allocated
    
    def free_logical_qubits(self, vq_ids: List[str]):
        """
        Free logical qubits and reclaim physical resources.
        
        Args:
            vq_ids: List of virtual qubit IDs to free
        """
        for vq_id in vq_ids:
            if vq_id not in self.logical_qubits:
                # Silently ignore (already freed or never allocated)
                continue
            
            logical_qubit = self.logical_qubits[vq_id]
            
            # Reclaim physical qubits
            self.physical_qubits_used -= logical_qubit.profile.physical_qubit_count
            
            # Remove from tracking
            del self.logical_qubits[vq_id]
    
    def get_logical_qubit(self, vq_id: str) -> LogicalQubit:
        """
        Get logical qubit instance.
        
        Args:
            vq_id: Virtual qubit ID
        
        Returns:
            LogicalQubit instance
        
        Raises:
            KeyError: If qubit not allocated
        """
        if vq_id not in self.logical_qubits:
            raise KeyError(f"Virtual qubit '{vq_id}' not allocated")
        
        return self.logical_qubits[vq_id]
    
    def open_channel(self, channel_id: str, vq_a: str, vq_b: str, fidelity: float = 0.99):
        """
        Open an entanglement channel between two qubits.
        
        Args:
            channel_id: Channel identifier
            vq_a: First qubit ID
            vq_b: Second qubit ID
            fidelity: Target fidelity
        """
        if channel_id in self.channels:
            raise RuntimeError(f"Channel '{channel_id}' already open")
        
        # Verify qubits exist
        self.get_logical_qubit(vq_a)
        self.get_logical_qubit(vq_b)
        
        self.channels[channel_id] = {
            "vq_a": vq_a,
            "vq_b": vq_b,
            "fidelity": fidelity,
            "uses": 0,
        }
    
    def close_channel(self, channel_id: str):
        """
        Close an entanglement channel.
        
        Args:
            channel_id: Channel identifier
        """
        if channel_id in self.channels:
            del self.channels[channel_id]
    
    def get_resource_usage(self) -> Dict:
        """
        Get current resource usage statistics.
        
        Returns:
            Dictionary with resource usage info
        """
        return {
            "logical_qubits_allocated": len(self.logical_qubits),
            "physical_qubits_used": self.physical_qubits_used,
            "physical_qubits_available": self.max_physical_qubits - self.physical_qubits_used,
            "utilization": self.physical_qubits_used / self.max_physical_qubits,
            "channels_open": len(self.channels),
        }
    
    def get_telemetry(self) -> Dict:
        """
        Get comprehensive telemetry for all logical qubits.
        
        Returns:
            Dictionary with telemetry data
        """
        qubit_telemetry = {}
        
        for vq_id, qubit in self.logical_qubits.items():
            qubit_telemetry[vq_id] = qubit.get_telemetry()
        
        return {
            "resource_usage": self.get_resource_usage(),
            "qubits": qubit_telemetry,
            "channels": dict(self.channels),
            "simulation_time_us": self.current_time_us,
        }
    
    def advance_time(self, delta_us: float):
        """
        Advance simulation time.
        
        Args:
            delta_us: Time increment in microseconds
        """
        self.current_time_us += delta_us
    
    def reset(self):
        """Reset resource manager to initial state."""
        self.logical_qubits.clear()
        self.channels.clear()
        self.physical_qubits_used = 0
        self.current_time_us = 0.0
        self.seed_counter = 0
