"""
Backend Manager

Manages multiple hardware backends and provides unified interface.
"""

from typing import Dict, List, Optional
from .hal_interface import HardwareBackend, HardwareStatus, JobStatus, JobResult


class BackendManager:
    """
    Manages hardware backends.
    
    Provides:
    - Backend registration and discovery
    - Backend selection
    - Job routing
    - Health monitoring
    """
    
    def __init__(self):
        """Initialize backend manager."""
        self.backends: Dict[str, HardwareBackend] = {}
        self.default_backend: Optional[str] = None
    
    def register_backend(
        self,
        backend: HardwareBackend,
        set_as_default: bool = False
    ):
        """
        Register a hardware backend.
        
        Args:
            backend: HardwareBackend instance
            set_as_default: Set as default backend
        """
        self.backends[backend.backend_id] = backend
        
        if set_as_default or self.default_backend is None:
            self.default_backend = backend.backend_id
    
    def unregister_backend(self, backend_id: str):
        """
        Unregister a backend.
        
        Args:
            backend_id: Backend identifier
        """
        if backend_id in self.backends:
            backend = self.backends[backend_id]
            backend.disconnect()
            del self.backends[backend_id]
            
            if self.default_backend == backend_id:
                self.default_backend = None
    
    def get_backend(self, backend_id: Optional[str] = None) -> HardwareBackend:
        """
        Get a backend.
        
        Args:
            backend_id: Backend identifier (uses default if None)
        
        Returns:
            HardwareBackend instance
        
        Raises:
            KeyError: If backend not found
        """
        if backend_id is None:
            backend_id = self.default_backend
        
        if backend_id is None:
            raise KeyError("No default backend set")
        
        if backend_id not in self.backends:
            raise KeyError(f"Backend '{backend_id}' not found")
        
        return self.backends[backend_id]
    
    def list_backends(self, available_only: bool = False) -> List[Dict]:
        """
        List all backends.
        
        Args:
            available_only: Only list available backends
        
        Returns:
            List of backend info dictionaries
        """
        backends = []
        
        for backend in self.backends.values():
            if available_only and not backend.is_available():
                continue
            
            info = backend.get_info()
            info["is_default"] = (backend.backend_id == self.default_backend)
            backends.append(info)
        
        return backends
    
    def submit_job(
        self,
        job_id: str,
        circuit: Dict,
        shots: int = 1000,
        backend_id: Optional[str] = None
    ) -> tuple:
        """
        Submit job to a backend.
        
        Args:
            job_id: Job identifier
            circuit: Circuit to execute
            shots: Number of shots
            backend_id: Backend to use (default if None)
        
        Returns:
            (backend_id, backend_job_id) tuple
        """
        backend = self.get_backend(backend_id)
        
        if not backend.is_available():
            raise RuntimeError(f"Backend '{backend.backend_id}' is not available")
        
        backend_job_id = backend.submit_job(job_id, circuit, shots)
        
        return (backend.backend_id, backend_job_id)
    
    def get_job_status(
        self,
        backend_id: str,
        backend_job_id: str
    ) -> JobStatus:
        """
        Get job status.
        
        Args:
            backend_id: Backend identifier
            backend_job_id: Backend job ID
        
        Returns:
            JobStatus
        """
        backend = self.get_backend(backend_id)
        return backend.get_job_status(backend_job_id)
    
    def get_job_result(
        self,
        backend_id: str,
        backend_job_id: str
    ) -> JobResult:
        """
        Get job result.
        
        Args:
            backend_id: Backend identifier
            backend_job_id: Backend job ID
        
        Returns:
            JobResult
        """
        backend = self.get_backend(backend_id)
        return backend.get_job_result(backend_job_id)
    
    def cancel_job(
        self,
        backend_id: str,
        backend_job_id: str
    ) -> bool:
        """
        Cancel a job.
        
        Args:
            backend_id: Backend identifier
            backend_job_id: Backend job ID
        
        Returns:
            True if cancellation successful
        """
        backend = self.get_backend(backend_id)
        return backend.cancel_job(backend_job_id)
    
    def get_health_status(self) -> Dict:
        """
        Get health status of all backends.
        
        Returns:
            Dictionary with health status
        """
        total = len(self.backends)
        online = sum(1 for b in self.backends.values() if b.is_available())
        
        backend_status = {
            backend_id: backend.get_status().value
            for backend_id, backend in self.backends.items()
        }
        
        return {
            "total_backends": total,
            "online_backends": online,
            "offline_backends": total - online,
            "backend_status": backend_status,
            "default_backend": self.default_backend
        }
    
    def select_best_backend(
        self,
        requirements: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Select best backend based on requirements.
        
        Args:
            requirements: Job requirements (qubits, gates, etc.)
        
        Returns:
            Backend ID or None if no suitable backend
        """
        if not requirements:
            # Return default backend
            return self.default_backend
        
        required_qubits = requirements.get("qubits", 0)
        required_gates = set(requirements.get("gates", []))
        
        # Find backends that meet requirements
        suitable_backends = []
        
        for backend_id, backend in self.backends.items():
            if not backend.is_available():
                continue
            
            caps = backend.get_capabilities()
            
            # Check qubit count
            if caps.max_qubits < required_qubits:
                continue
            
            # Check gate support
            if not required_gates.issubset(set(caps.supported_gates)):
                continue
            
            suitable_backends.append(backend_id)
        
        # Return first suitable backend (could add more sophisticated selection)
        return suitable_backends[0] if suitable_backends else None
