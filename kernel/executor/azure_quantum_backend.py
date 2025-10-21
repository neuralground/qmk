"""
Azure Quantum Backend for QMK Executor

Translates QVM graphs to Q# and executes on Azure Quantum.
"""

import time
from typing import Dict, Any, Optional

try:
    from azure.quantum import Workspace
    from azure.quantum.qiskit import AzureQuantumProvider
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

from .backend_interface import QuantumBackend


class AzureQuantumBackend(QuantumBackend):
    """
    Azure Quantum backend for QMK.
    
    Translates QVM graphs and executes on Azure Quantum simulators/hardware.
    Uses Qiskit as intermediate format for Azure Quantum.
    """
    
    def __init__(self, seed: Optional[int] = None, 
                 resource_id: Optional[str] = None,
                 location: Optional[str] = None,
                 backend_name: str = "ionq.simulator",
                 **kwargs):
        """
        Initialize Azure Quantum backend.
        
        Args:
            seed: Random seed for deterministic execution
            resource_id: Azure Quantum workspace resource ID
            location: Azure region
            backend_name: Target backend (e.g., "ionq.simulator", "quantinuum.sim.h1-1e")
            **kwargs: Additional configuration
        """
        if not HAS_AZURE:
            raise ImportError("Azure Quantum SDK is required for AzureQuantumBackend. "
                            "Install with: pip install azure-quantum qiskit-qir")
        
        super().__init__(seed=seed, **kwargs)
        self.resource_id = resource_id
        self.location = location
        self.backend_name = backend_name
        
        # Initialize workspace if credentials provided
        self.workspace = None
        self.backend = None
        if resource_id and location:
            self._connect()
    
    def _connect(self):
        """Connect to Azure Quantum workspace."""
        try:
            self.workspace = Workspace(
                resource_id=self.resource_id,
                location=self.location
            )
            
            # Get provider and backend
            provider = AzureQuantumProvider(self.workspace)
            self.backend = provider.get_backend(self.backend_name)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Azure Quantum: {e}")
    
    def execute_graph(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute QVM graph on Azure Quantum.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Dictionary with events, telemetry, and metadata
        """
        if not self.backend:
            raise RuntimeError("Azure Quantum backend not connected. "
                             "Provide resource_id and location.")
        
        start_time = time.time()
        
        # Translate QVM to Qiskit (Azure uses Qiskit as intermediate)
        from .qiskit_aer_backend import QiskitAerBackend
        qiskit_backend = QiskitAerBackend(seed=self.seed)
        circuit, event_map = qiskit_backend.translate_qvm_to_native(qvm_graph)
        
        # Submit to Azure Quantum
        job = self.backend.run(circuit, shots=1)
        result = job.result()
        
        # Translate results back to QVM
        events = qiskit_backend.translate_results_to_qvm(result, event_map)
        
        execution_time = time.time() - start_time
        
        return {
            "events": events,
            "telemetry": {
                "execution_time_s": execution_time,
                "backend": "azure_quantum",
                "target": self.backend_name,
                "shots": 1
            },
            "metadata": {
                "azure_job_id": job.id() if hasattr(job, 'id') else None,
                "azure_metadata": {}
            }
        }
    
    def translate_qvm_to_native(self, qvm_graph: Dict[str, Any]) -> Any:
        """
        Translate QVM graph to Azure Quantum format (via Qiskit).
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Qiskit QuantumCircuit
        """
        from .qiskit_aer_backend import QiskitAerBackend
        qiskit_backend = QiskitAerBackend(seed=self.seed)
        circuit, _ = qiskit_backend.translate_qvm_to_native(qvm_graph)
        return circuit
    
    def translate_results_to_qvm(self, native_result: Any) -> Dict[str, int]:
        """
        Translate Azure Quantum results to QVM event format.
        
        Args:
            native_result: Azure Quantum result (Qiskit format)
        
        Returns:
            Dictionary mapping event IDs to measurement outcomes
        """
        # Azure returns Qiskit-format results
        from .qiskit_aer_backend import QiskitAerBackend
        qiskit_backend = QiskitAerBackend(seed=self.seed)
        # Note: event_map would need to be passed through
        return {}
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the Azure Quantum backend."""
        return {
            "backend_type": "azure_quantum",
            "target": self.backend_name,
            "resource_id": self.resource_id,
            "location": self.location,
            "seed": self.seed,
            "connected": self.backend is not None
        }
