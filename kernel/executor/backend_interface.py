"""
Backend Interface for QMK Executor

Defines the Hardware Abstraction Layer (HAL) for quantum backends.
Backends translate QVM graphs to their native format and execute them.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class BackendType(Enum):
    """Supported backend types."""
    LOGICAL_QUBIT = "logical_qubit"  # Simplified simulator (default)
    QISKIT_AER = "qiskit_aer"        # Qiskit Aer simulator
    CIRQ = "cirq"                     # Google Cirq simulator
    AZURE_QUANTUM = "azure_quantum"   # Microsoft Azure Quantum
    IBM_QUANTUM = "ibm_quantum"       # IBM Quantum hardware
    IONQ = "ionq"                     # IonQ hardware


class QuantumBackend(ABC):
    """
    Abstract base class for quantum backends.
    
    Backends are responsible for:
    1. Translating QVM graphs to their native format
    2. Executing circuits on their simulator/hardware
    3. Translating results back to QVM format
    """
    
    def __init__(self, seed: Optional[int] = None, **kwargs):
        """
        Initialize backend.
        
        Args:
            seed: Random seed for deterministic execution
            **kwargs: Backend-specific configuration
        """
        self.seed = seed
        self.config = kwargs
    
    @abstractmethod
    def execute_graph(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a QVM graph and return results.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Dictionary with:
            - events: Dict[str, int] - Measurement outcomes
            - telemetry: Dict - Execution telemetry
            - metadata: Dict - Backend-specific metadata
        
        Raises:
            RuntimeError: If execution fails
        """
        pass
    
    @abstractmethod
    def translate_qvm_to_native(self, qvm_graph: Dict[str, Any]) -> Any:
        """
        Translate QVM graph to backend's native circuit format.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Native circuit object (e.g., QuantumCircuit, Circuit, etc.)
        """
        pass
    
    @abstractmethod
    def translate_results_to_qvm(self, native_result: Any) -> Dict[str, int]:
        """
        Translate backend results to QVM event format.
        
        Args:
            native_result: Backend-specific result object
        
        Returns:
            Dictionary mapping event IDs to measurement outcomes
        """
        pass
    
    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend.
        
        Returns:
            Dictionary with backend metadata
        """
        pass
    
    def supports_operation(self, operation: str) -> bool:
        """
        Check if backend supports a specific operation.
        
        Args:
            operation: Operation name (e.g., "APPLY_H", "MEASURE_Z")
        
        Returns:
            True if supported, False otherwise
        """
        # Default: support common operations
        common_ops = {
            "ALLOC_LQ", "FREE_LQ",
            "APPLY_H", "APPLY_X", "APPLY_Y", "APPLY_Z",
            "APPLY_S", "APPLY_T", "APPLY_CNOT", "APPLY_CZ",
            "APPLY_RX", "APPLY_RY", "APPLY_RZ",
            "MEASURE_Z", "MEASURE_X", "MEASURE_Y"
        }
        return operation in common_ops
