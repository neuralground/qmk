"""
Simulated Hardware Backend

Simulates a quantum hardware backend for testing and development.
"""

import time
import random
from typing import Dict, List, Optional

from .hal_interface import (
    HardwareBackend, HardwareStatus, JobStatus, HardwareCapabilities,
    CalibrationData, JobResult
)


class SimulatedBackend(HardwareBackend):
    """
    Simulated quantum hardware backend.
    
    Provides a realistic simulation of hardware behavior including:
    - Queue delays
    - Execution time
    - Calibration data
    - Error injection
    """
    
    def __init__(
        self,
        backend_name: str = "Simulated QPU",
        backend_id: str = "sim_qpu_001",
        num_qubits: int = 20,
        error_rate: float = 0.001
    ):
        """
        Initialize simulated backend.
        
        Args:
            backend_name: Backend name
            backend_id: Backend identifier
            num_qubits: Number of qubits
            error_rate: Simulated error rate
        """
        super().__init__(backend_name, backend_id)
        self.num_qubits = num_qubits
        self.error_rate = error_rate
        
        # Job tracking
        self.jobs: Dict[str, Dict] = {}
        self.job_counter = 0
        
        # Simulate calibration data
        self._calibration_data = self._generate_calibration_data()
    
    def connect(self, credentials: Optional[Dict] = None) -> bool:
        """Connect to simulated backend."""
        # Simulate connection delay
        time.sleep(0.1)
        self._status = HardwareStatus.ONLINE
        return True
    
    def disconnect(self):
        """Disconnect from simulated backend."""
        self._status = HardwareStatus.OFFLINE
    
    def get_capabilities(self) -> HardwareCapabilities:
        """Get simulated hardware capabilities."""
        # All-to-all connectivity for simulation
        connectivity = {
            i: [j for j in range(self.num_qubits) if j != i]
            for i in range(self.num_qubits)
        }
        
        return HardwareCapabilities(
            max_qubits=self.num_qubits,
            supported_gates=["H", "X", "Y", "Z", "S", "T", "CNOT", "RZ", "RY", "RX"],
            native_gates=["RZ", "RY", "CNOT"],
            connectivity=connectivity,
            has_mid_circuit_measurement=True,
            has_reset=True,
            has_conditional=False,
            qec_capable=False
        )
    
    def get_calibration_data(self) -> CalibrationData:
        """Get simulated calibration data."""
        return self._calibration_data
    
    def submit_job(
        self,
        job_id: str,
        circuit: Dict,
        shots: int = 1000
    ) -> str:
        """Submit job to simulated backend."""
        backend_job_id = f"{self.backend_id}_job_{self.job_counter}"
        self.job_counter += 1
        
        # Store job info
        self.jobs[backend_job_id] = {
            "job_id": job_id,
            "circuit": circuit,
            "shots": shots,
            "status": JobStatus.QUEUED,
            "submit_time": time.time(),
            "start_time": None,
            "end_time": None
        }
        
        # Simulate async execution
        self._simulate_execution(backend_job_id)
        
        return backend_job_id
    
    def get_job_status(self, backend_job_id: str) -> JobStatus:
        """Get job status."""
        if backend_job_id not in self.jobs:
            raise KeyError(f"Job '{backend_job_id}' not found")
        
        return self.jobs[backend_job_id]["status"]
    
    def get_job_result(self, backend_job_id: str) -> JobResult:
        """Get job result."""
        if backend_job_id not in self.jobs:
            raise KeyError(f"Job '{backend_job_id}' not found")
        
        job = self.jobs[backend_job_id]
        
        if job["status"] != JobStatus.COMPLETED:
            return JobResult(
                job_id=job["job_id"],
                status=job["status"],
                error_message="Job not completed" if job["status"] == JobStatus.FAILED else None
            )
        
        return JobResult(
            job_id=job["job_id"],
            status=JobStatus.COMPLETED,
            measurements=job["measurements"],
            execution_time=job["end_time"] - job["start_time"],
            metadata={
                "backend": self.backend_id,
                "shots": job["shots"]
            }
        )
    
    def cancel_job(self, backend_job_id: str) -> bool:
        """Cancel job."""
        if backend_job_id not in self.jobs:
            return False
        
        job = self.jobs[backend_job_id]
        
        if job["status"] in [JobStatus.QUEUED, JobStatus.RUNNING]:
            job["status"] = JobStatus.CANCELLED
            return True
        
        return False
    
    def _simulate_execution(self, backend_job_id: str):
        """Simulate job execution."""
        job = self.jobs[backend_job_id]
        
        # Simulate queue delay
        time.sleep(0.05)
        
        job["status"] = JobStatus.RUNNING
        job["start_time"] = time.time()
        
        # Simulate execution time
        circuit = job["circuit"]
        num_nodes = len(circuit.get("nodes", []))
        execution_time = num_nodes * 0.001  # 1ms per node
        time.sleep(min(execution_time, 0.1))  # Cap at 100ms for demo
        
        # Generate simulated measurements
        shots = job["shots"]
        measurements = self._generate_measurements(circuit, shots)
        
        job["measurements"] = measurements
        job["status"] = JobStatus.COMPLETED
        job["end_time"] = time.time()
    
    def _generate_measurements(self, circuit: Dict, shots: int) -> Dict[str, List[int]]:
        """Generate simulated measurement results."""
        # Find measurement nodes
        measure_nodes = [
            node for node in circuit.get("nodes", [])
            if node["op"] in ["MEASURE_Z", "MEASURE_X"]
        ]
        
        measurements = {}
        
        for node in measure_nodes:
            qubit = node["qubits"][0]
            result_key = node.get("params", {}).get("result", qubit)
            
            # Generate random measurements with bias
            # Simulate 50/50 distribution with some error
            results = []
            for _ in range(shots):
                if random.random() < 0.5 + self.error_rate:
                    results.append(0)
                else:
                    results.append(1)
            
            measurements[result_key] = results
        
        return measurements
    
    def _generate_calibration_data(self) -> CalibrationData:
        """Generate simulated calibration data."""
        # Simulate realistic calibration values
        qubit_t1 = {i: random.uniform(50, 100) for i in range(self.num_qubits)}
        qubit_t2 = {i: random.uniform(30, 80) for i in range(self.num_qubits)}
        
        gate_fidelities = {
            "single_qubit": 0.999,
            "two_qubit": 0.99,
            "readout": 0.98
        }
        
        readout_fidelities = {i: random.uniform(0.97, 0.99) for i in range(self.num_qubits)}
        
        gate_times = {
            "single_qubit": 0.02,  # 20ns
            "two_qubit": 0.1,      # 100ns
            "readout": 1.0         # 1μs
        }
        
        return CalibrationData(
            timestamp=time.time(),
            qubit_t1=qubit_t1,
            qubit_t2=qubit_t2,
            gate_fidelities=gate_fidelities,
            readout_fidelities=readout_fidelities,
            gate_times=gate_times
        )
