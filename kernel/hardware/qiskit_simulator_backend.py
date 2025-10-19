"""
Qiskit Simulator Backend

Integrates Qiskit's Aer simulator as a QMK hardware backend.
This allows comparing native Qiskit execution vs. QIR→QVM→QMK path.
"""

import time
import uuid
from typing import Dict, List, Optional
from .hal_interface import (
    HardwareBackend, HardwareStatus, JobStatus,
    HardwareCapabilities, CalibrationData, JobResult
)

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    from qiskit.transpiler import PassManager
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class QiskitSimulatorBackend(HardwareBackend):
    """
    Qiskit Aer simulator backend.
    
    Provides a bridge between QMK's QVM format and Qiskit's native execution.
    Useful for:
    - Comparing QMK execution with native Qiskit
    - Validating QIR→QVM conversion correctness
    - Benchmarking performance differences
    """
    
    def __init__(self, method='statevector', noise_model=None):
        """
        Initialize Qiskit simulator backend.
        
        Args:
            method: Simulation method ('statevector', 'density_matrix', 'stabilizer', 'mps')
            noise_model: Optional noise model for realistic simulation
        """
        super().__init__(
            backend_name=f"Qiskit Aer Simulator ({method})",
            backend_id=f"qiskit_aer_{method}"
        )
        
        if not HAS_QISKIT:
            raise ImportError("Qiskit not installed. Install with: pip install qiskit qiskit-aer")
        
        self.method = method
        self.noise_model = noise_model
        self.simulator = None
        self.jobs = {}  # Track submitted jobs
    
    def connect(self, credentials: Optional[Dict] = None) -> bool:
        """Connect to Qiskit simulator (always succeeds)."""
        try:
            self.simulator = AerSimulator(method=self.method)
            if self.noise_model:
                self.simulator.set_options(noise_model=self.noise_model)
            
            self._status = HardwareStatus.ONLINE
            return True
        except Exception as e:
            print(f"Failed to initialize Qiskit simulator: {e}")
            self._status = HardwareStatus.OFFLINE
            return False
    
    def disconnect(self):
        """Disconnect from simulator."""
        self.simulator = None
        self._status = HardwareStatus.OFFLINE
    
    def get_capabilities(self) -> HardwareCapabilities:
        """Get simulator capabilities."""
        # Qiskit Aer supports large qubit counts
        max_qubits = 30 if self.method == 'statevector' else 100
        
        return HardwareCapabilities(
            max_qubits=max_qubits,
            supported_gates=[
                'H', 'X', 'Y', 'Z', 'S', 'T', 'CNOT', 'CZ',
                'RX', 'RY', 'RZ', 'U', 'SWAP', 'MEASURE'
            ],
            native_gates=['U', 'CX'],  # Qiskit's native gate set
            connectivity={i: list(range(max_qubits)) for i in range(max_qubits)},  # All-to-all
            has_mid_circuit_measurement=True,
            has_reset=True,
            has_conditional=True,
            qec_capable=False  # Simulator doesn't need QEC
        )
    
    def get_calibration_data(self) -> CalibrationData:
        """Get calibration data (ideal for simulator)."""
        return CalibrationData(
            timestamp=time.time(),
            qubit_t1={i: float('inf') for i in range(30)},  # Infinite coherence
            qubit_t2={i: float('inf') for i in range(30)},
            gate_fidelities={'all': 1.0},  # Perfect gates
            readout_fidelities={i: 1.0 for i in range(30)},  # Perfect readout
            gate_times={'all': 0.0}  # Instantaneous
        )
    
    def _qvm_to_qiskit(self, qvm_graph: Dict) -> QuantumCircuit:
        """
        Convert QVM graph to Qiskit circuit.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Qiskit QuantumCircuit
        """
        # Handle both flat and nested structure
        if 'program' in qvm_graph:
            nodes = qvm_graph['program'].get('nodes', [])
        else:
            nodes = qvm_graph.get('nodes', [])
        
        # Determine number of qubits needed
        qubit_ids = set()
        for node in nodes:
            qubits = node.get('qubits', node.get('vqs', []))
            if qubits:
                qubit_ids.update(qubits)
        
        # Create circuit
        num_qubits = len(qubit_ids)
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
        
        # Map qubit IDs to indices
        qubit_map = {qid: i for i, qid in enumerate(sorted(qubit_ids))}
        
        # Convert nodes to gates
        for node in nodes:
            op = node['op']
            qubits = node.get('qubits', node.get('vqs', []))
            params = node.get('params', node.get('args', {}))
            
            if op == 'ALLOC_LQ':
                # Allocation is implicit in Qiskit
                continue
            elif op == 'FREE_LQ':
                # Deallocation is implicit in Qiskit
                continue
            elif op == 'H' or op == 'APPLY_H':
                circuit.h(qr[qubit_map[qubits[0]]])
            elif op == 'X' or op == 'APPLY_X':
                circuit.x(qr[qubit_map[qubits[0]]])
            elif op == 'Y' or op == 'APPLY_Y':
                circuit.y(qr[qubit_map[qubits[0]]])
            elif op == 'Z' or op == 'APPLY_Z':
                circuit.z(qr[qubit_map[qubits[0]]])
            elif op == 'S' or op == 'APPLY_S':
                circuit.s(qr[qubit_map[qubits[0]]])
            elif op == 'T' or op == 'APPLY_T':
                circuit.t(qr[qubit_map[qubits[0]]])
            elif op == 'CNOT' or op == 'APPLY_CNOT':
                circuit.cx(qr[qubit_map[qubits[0]]], qr[qubit_map[qubits[1]]])
            elif op == 'RZ':
                theta = params.get('theta', 0)
                circuit.rz(theta, qr[qubit_map[qubits[0]]])
            elif op == 'RY':
                theta = params.get('theta', 0)
                circuit.ry(theta, qr[qubit_map[qubits[0]]])
            elif op == 'RX':
                theta = params.get('theta', 0)
                circuit.rx(theta, qr[qubit_map[qubits[0]]])
            elif op == 'MEASURE_Z':
                # Measure to classical register
                circuit.measure(qr[qubit_map[qubits[0]]], cr[qubit_map[qubits[0]]])
            elif op == 'FENCE_EPOCH':
                # Barrier in Qiskit
                circuit.barrier()
        
        return circuit
    
    def submit_job(
        self,
        job_id: str,
        circuit: Dict,
        shots: int = 1000
    ) -> str:
        """
        Submit job to Qiskit simulator.
        
        Args:
            job_id: QMK job ID
            circuit: QVM graph
            shots: Number of shots
        
        Returns:
            Backend job ID
        """
        if not self.simulator:
            raise RuntimeError("Simulator not connected")
        
        # Convert QVM to Qiskit circuit
        qiskit_circuit = self._qvm_to_qiskit(circuit)
        
        # Generate backend job ID
        backend_job_id = f"qiskit_{uuid.uuid4().hex[:8]}"
        
        # Submit to simulator
        start_time = time.time()
        job = self.simulator.run(qiskit_circuit, shots=shots)
        result = job.result()
        execution_time = time.time() - start_time
        
        # Store result
        counts = result.get_counts()
        
        # Convert counts to measurement format
        measurements = {}
        for bitstring, count in counts.items():
            # Qiskit returns bitstrings in reverse order
            bitstring_rev = bitstring[::-1]
            for i, bit in enumerate(bitstring_rev):
                if i not in measurements:
                    measurements[i] = []
                measurements[i].extend([int(bit)] * count)
        
        self.jobs[backend_job_id] = JobResult(
            job_id=backend_job_id,
            status=JobStatus.COMPLETED,
            measurements=measurements,
            execution_time=execution_time,
            metadata={
                'qmk_job_id': job_id,
                'shots': shots,
                'method': self.method,
                'counts': counts
            }
        )
        
        return backend_job_id
    
    def get_job_status(self, backend_job_id: str) -> JobStatus:
        """Get job status (always completed for simulator)."""
        if backend_job_id in self.jobs:
            return self.jobs[backend_job_id].status
        return JobStatus.FAILED
    
    def get_job_result(self, backend_job_id: str) -> JobResult:
        """Get job result."""
        if backend_job_id not in self.jobs:
            return JobResult(
                job_id=backend_job_id,
                status=JobStatus.FAILED,
                error_message="Job not found"
            )
        
        return self.jobs[backend_job_id]
    
    def cancel_job(self, backend_job_id: str) -> bool:
        """Cancel job (not applicable for immediate simulator)."""
        return False
    
    def compare_with_qmk(
        self,
        qvm_graph: Dict,
        qmk_result: Dict,
        shots: int = 1000
    ) -> Dict:
        """
        Compare Qiskit native execution with QMK execution.
        
        Args:
            qvm_graph: QVM graph
            qmk_result: QMK execution result
            shots: Number of shots
        
        Returns:
            Comparison statistics
        """
        # Run on Qiskit
        backend_job_id = self.submit_job("comparison", qvm_graph, shots)
        qiskit_result = self.get_job_result(backend_job_id)
        
        # Compare results
        comparison = {
            'qiskit_execution_time': qiskit_result.execution_time,
            'qmk_execution_time': qmk_result.get('execution_time', 0),
            'qiskit_counts': qiskit_result.metadata.get('counts', {}),
            'qmk_measurements': qmk_result.get('events', {}),
            'match': True,  # Will be computed
            'differences': []
        }
        
        # TODO: Implement detailed comparison logic
        
        return comparison
