"""
Hardware Abstraction Layer (HAL) Interface

Defines the interface for quantum hardware backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class HardwareStatus(Enum):
    """Hardware backend status."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"


class JobStatus(Enum):
    """Job execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class HardwareCapabilities:
    """
    Hardware backend capabilities.
    
    Attributes:
        max_qubits: Maximum number of qubits
        supported_gates: List of supported gate operations
        native_gates: Native gate set
        connectivity: Qubit connectivity graph
        has_mid_circuit_measurement: Supports mid-circuit measurements
        has_reset: Supports reset operations
        has_conditional: Supports conditional operations
        qec_capable: Supports quantum error correction
    """
    max_qubits: int
    supported_gates: List[str]
    native_gates: List[str]
    connectivity: Dict[int, List[int]]
    has_mid_circuit_measurement: bool = False
    has_reset: bool = False
    has_conditional: bool = False
    qec_capable: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "max_qubits": self.max_qubits,
            "supported_gates": self.supported_gates,
            "native_gates": self.native_gates,
            "connectivity": self.connectivity,
            "has_mid_circuit_measurement": self.has_mid_circuit_measurement,
            "has_reset": self.has_reset,
            "has_conditional": self.has_conditional,
            "qec_capable": self.qec_capable
        }


@dataclass
class CalibrationData:
    """
    Hardware calibration data.
    
    Attributes:
        timestamp: Calibration timestamp
        qubit_t1: T1 coherence times (μs)
        qubit_t2: T2 coherence times (μs)
        gate_fidelities: Gate fidelity data
        readout_fidelities: Measurement fidelity data
        gate_times: Gate execution times (μs)
    """
    timestamp: float
    qubit_t1: Dict[int, float] = field(default_factory=dict)
    qubit_t2: Dict[int, float] = field(default_factory=dict)
    gate_fidelities: Dict[str, float] = field(default_factory=dict)
    readout_fidelities: Dict[int, float] = field(default_factory=dict)
    gate_times: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "qubit_t1": self.qubit_t1,
            "qubit_t2": self.qubit_t2,
            "gate_fidelities": self.gate_fidelities,
            "readout_fidelities": self.readout_fidelities,
            "gate_times": self.gate_times
        }


@dataclass
class JobResult:
    """
    Job execution result.
    
    Attributes:
        job_id: Job identifier
        status: Job status
        measurements: Measurement results
        execution_time: Execution time (seconds)
        error_message: Error message if failed
        metadata: Additional metadata
    """
    job_id: str
    status: JobStatus
    measurements: Dict[str, List[int]] = field(default_factory=dict)
    execution_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "measurements": self.measurements,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class HardwareBackend(ABC):
    """
    Abstract base class for hardware backends.
    
    All hardware adapters must implement this interface.
    """
    
    def __init__(self, backend_name: str, backend_id: str):
        """
        Initialize hardware backend.
        
        Args:
            backend_name: Human-readable backend name
            backend_id: Unique backend identifier
        """
        self.backend_name = backend_name
        self.backend_id = backend_id
        self._status = HardwareStatus.OFFLINE
    
    @abstractmethod
    def connect(self, credentials: Optional[Dict] = None) -> bool:
        """
        Connect to hardware backend.
        
        Args:
            credentials: Authentication credentials
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from hardware backend."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> HardwareCapabilities:
        """
        Get hardware capabilities.
        
        Returns:
            HardwareCapabilities object
        """
        pass
    
    @abstractmethod
    def get_calibration_data(self) -> CalibrationData:
        """
        Get current calibration data.
        
        Returns:
            CalibrationData object
        """
        pass
    
    @abstractmethod
    def submit_job(
        self,
        job_id: str,
        circuit: Dict,
        shots: int = 1000
    ) -> str:
        """
        Submit a job for execution.
        
        Args:
            job_id: Job identifier
            circuit: Circuit to execute (QVM graph format)
            shots: Number of shots
        
        Returns:
            Backend job ID
        """
        pass
    
    @abstractmethod
    def get_job_status(self, backend_job_id: str) -> JobStatus:
        """
        Get job status.
        
        Args:
            backend_job_id: Backend job identifier
        
        Returns:
            JobStatus
        """
        pass
    
    @abstractmethod
    def get_job_result(self, backend_job_id: str) -> JobResult:
        """
        Get job result.
        
        Args:
            backend_job_id: Backend job identifier
        
        Returns:
            JobResult object
        """
        pass
    
    @abstractmethod
    def cancel_job(self, backend_job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            backend_job_id: Backend job identifier
        
        Returns:
            True if cancellation successful
        """
        pass
    
    def get_status(self) -> HardwareStatus:
        """
        Get backend status.
        
        Returns:
            HardwareStatus
        """
        return self._status
    
    def is_available(self) -> bool:
        """
        Check if backend is available.
        
        Returns:
            True if backend is online
        """
        return self._status == HardwareStatus.ONLINE
    
    def get_info(self) -> Dict:
        """
        Get backend information.
        
        Returns:
            Dictionary with backend info
        """
        return {
            "backend_name": self.backend_name,
            "backend_id": self.backend_id,
            "status": self._status.value,
            "available": self.is_available()
        }
