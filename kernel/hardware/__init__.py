"""
Hardware Adapters

Provides Hardware Abstraction Layer (HAL) for quantum backends.
"""

from .hal_interface import (
    HardwareBackend, HardwareStatus, JobStatus, HardwareCapabilities,
    CalibrationData, JobResult
)
from .simulated_backend import SimulatedBackend
from .azure_backend import AzureQuantumBackend
from .backend_manager import BackendManager

__all__ = [
    "HardwareBackend",
    "HardwareStatus",
    "JobStatus",
    "HardwareCapabilities",
    "CalibrationData",
    "JobResult",
    "SimulatedBackend",
    "AzureQuantumBackend",
    "BackendManager",
]
