"""
Logical Qubit Backend for QMK Executor

Wraps the existing simplified LogicalQubit simulator as a backend.
This is the default backend for backward compatibility.
"""

from typing import Dict, Any, Optional
from .backend_interface import QuantumBackend


class LogicalQubitBackend(QuantumBackend):
    """
    Logical qubit backend for QMK.
    
    This wraps the existing simplified simulator for backward compatibility.
    Note: This simulator has known limitations with multi-qubit entanglement.
    For accurate results, use QiskitAerBackend instead.
    """
    
    def __init__(self, seed: Optional[int] = None, 
                 max_physical_qubits: int = 10000,
                 **kwargs):
        """
        Initialize logical qubit backend.
        
        Args:
            seed: Random seed for deterministic execution
            max_physical_qubits: Maximum physical qubits available
            **kwargs: Additional configuration
        """
        super().__init__(seed=seed, **kwargs)
        self.max_physical_qubits = max_physical_qubits
        
        # Import here to avoid circular dependency
        from ..simulator.enhanced_resource_manager import EnhancedResourceManager
        self.resource_manager = EnhancedResourceManager(
            max_physical_qubits=max_physical_qubits,
            seed=seed
        )
        self.events = {}
    
    def execute_graph(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute QVM graph using simplified logical qubit simulator.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Dictionary with events, telemetry, and metadata
        
        Note:
            This backend has known limitations. See KNOWN_ISSUES.md.
            For accurate results, use QiskitAerBackend.
        """
        # This would call the existing executor logic
        # For now, raise an error directing to use the full executor
        raise NotImplementedError(
            "LogicalQubitBackend should not be called directly. "
            "Use EnhancedExecutor without a backend parameter for the default behavior, "
            "or use QiskitAerBackend for accurate simulation."
        )
    
    def translate_qvm_to_native(self, qvm_graph: Dict[str, Any]) -> Any:
        """QVM is the native format for this backend."""
        return qvm_graph
    
    def translate_results_to_qvm(self, native_result: Any) -> Dict[str, int]:
        """Results are already in QVM format."""
        return native_result
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the logical qubit backend."""
        return {
            "backend_type": "logical_qubit",
            "seed": self.seed,
            "max_physical_qubits": self.max_physical_qubits,
            "note": "Simplified simulator with known limitations. Use QiskitAerBackend for accuracy."
        }
