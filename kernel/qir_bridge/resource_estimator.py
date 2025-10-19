"""
Resource Estimator

Estimates resource requirements for QIR programs before execution.
"""

from typing import Dict, List
from dataclasses import dataclass

from .qir_parser import QIRFunction, QIRInstructionType
from kernel.simulator.qec_profiles import QECProfile, surface_code


@dataclass
class ResourceEstimate:
    """
    Resource estimate for a QIR program.
    
    Attributes:
        logical_qubits: Number of logical qubits
        physical_qubits: Number of physical qubits (with QEC)
        gate_count: Total gate count
        gate_breakdown: Gates by type
        t_count: Number of T gates (expensive)
        depth: Circuit depth estimate
        execution_time_us: Estimated execution time
    """
    logical_qubits: int
    physical_qubits: int
    gate_count: int
    gate_breakdown: Dict[str, int]
    t_count: int
    depth: int
    execution_time_us: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "logical_qubits": self.logical_qubits,
            "physical_qubits": self.physical_qubits,
            "gate_count": self.gate_count,
            "gate_breakdown": self.gate_breakdown,
            "t_count": self.t_count,
            "depth": self.depth,
            "execution_time_us": self.execution_time_us
        }


class ResourceEstimator:
    """
    Estimates resource requirements for QIR programs.
    
    Provides:
    - Qubit count estimation
    - Gate count analysis
    - T-gate count (for magic state requirements)
    - Execution time estimation
    """
    
    def __init__(self, qec_profile: QECProfile = None):
        """
        Initialize resource estimator.
        
        Args:
            qec_profile: QEC profile to use for physical qubit estimation
        """
        self.qec_profile = qec_profile or surface_code(9)
    
    def estimate(self, qir_function: QIRFunction) -> ResourceEstimate:
        """
        Estimate resources for a QIR function.
        
        Args:
            qir_function: Parsed QIR function
        
        Returns:
            ResourceEstimate object
        """
        # Count logical qubits
        logical_qubits = qir_function.qubit_count
        
        # Estimate physical qubits
        physical_qubits = logical_qubits * self.qec_profile.physical_qubit_count
        
        # Count gates
        gate_breakdown = {}
        t_count = 0
        
        for inst in qir_function.instructions:
            if inst.inst_type == QIRInstructionType.GATE:
                gate_name = inst.operation
                gate_breakdown[gate_name] = gate_breakdown.get(gate_name, 0) + 1
                
                if gate_name in ['T', 'T_DAG']:
                    t_count += 1
        
        gate_count = sum(gate_breakdown.values())
        
        # Estimate depth (simplified: assume some parallelism)
        depth = self._estimate_depth(qir_function)
        
        # Estimate execution time
        execution_time_us = depth * self.qec_profile.logical_cycle_time_us
        
        return ResourceEstimate(
            logical_qubits=logical_qubits,
            physical_qubits=physical_qubits,
            gate_count=gate_count,
            gate_breakdown=gate_breakdown,
            t_count=t_count,
            depth=depth,
            execution_time_us=execution_time_us
        )
    
    def _estimate_depth(self, qir_function: QIRFunction) -> int:
        """
        Estimate circuit depth.
        
        Simplified model: assumes sequential execution with some parallelism.
        """
        # Count gate operations
        gate_count = sum(
            1 for inst in qir_function.instructions
            if inst.inst_type == QIRInstructionType.GATE
        )
        
        # Assume 50% parallelism for multi-qubit circuits
        if qir_function.qubit_count > 1:
            depth = int(gate_count * 0.6)
        else:
            depth = gate_count
        
        return max(depth, 1)
    
    def compare_profiles(
        self,
        qir_function: QIRFunction,
        profiles: List[QECProfile]
    ) -> Dict[str, ResourceEstimate]:
        """
        Compare resource estimates across different QEC profiles.
        
        Args:
            qir_function: QIR function to estimate
            profiles: List of QEC profiles to compare
        
        Returns:
            Dictionary of profile name -> ResourceEstimate
        """
        estimates = {}
        
        for profile in profiles:
            original_profile = self.qec_profile
            self.qec_profile = profile
            
            estimate = self.estimate(qir_function)
            estimates[profile.code_family] = estimate
            
            self.qec_profile = original_profile
        
        return estimates
    
    def estimate_magic_state_requirements(
        self,
        qir_function: QIRFunction
    ) -> Dict:
        """
        Estimate magic state factory requirements.
        
        Args:
            qir_function: QIR function
        
        Returns:
            Dictionary with magic state requirements
        """
        t_count = 0
        rotation_count = 0
        
        for inst in qir_function.instructions:
            if inst.inst_type == QIRInstructionType.GATE:
                if inst.operation in ['T', 'T_DAG']:
                    t_count += 1
                elif inst.operation in ['RZ', 'RY', 'RX']:
                    rotation_count += 1
        
        # Estimate production time (assuming factory throughput)
        t_state_throughput = 100.0  # states/second
        rotation_throughput = 50.0  # states/second
        
        t_production_time = t_count / t_state_throughput if t_count > 0 else 0
        rotation_production_time = rotation_count / rotation_throughput if rotation_count > 0 else 0
        
        return {
            "t_states_needed": t_count,
            "rotation_states_needed": rotation_count,
            "t_production_time_s": t_production_time,
            "rotation_production_time_s": rotation_production_time,
            "total_production_time_s": max(t_production_time, rotation_production_time)
        }
