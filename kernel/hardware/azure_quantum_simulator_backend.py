"""
Azure Quantum Simulator Backend

Integrates Azure Quantum's simulators as QMK hardware backends.
Supports both local simulators and cloud-based Azure Quantum service.
"""

import time
import uuid
from typing import Dict, List, Optional
from .hal_interface import (
    HardwareBackend, HardwareStatus, JobStatus,
    HardwareCapabilities, CalibrationData, JobResult
)

try:
    from azure.quantum import Workspace
    from azure.quantum.qiskit import AzureQuantumProvider
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

# Fallback to Qiskit Aer for local simulation
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class AzureQuantumSimulatorBackend(HardwareBackend):
    """
    Azure Quantum simulator backend.
    
    Provides integration with Azure Quantum's simulators:
    - ionq.simulator (IonQ simulator)
    - quantinuum.sim.h1-1e (Quantinuum emulator)
    - rigetti.sim.qvm (Rigetti QVM)
    """
    
    def __init__(
        self,
        resource_id: Optional[str] = None,
        location: Optional[str] = None,
        target: str = "ionq.simulator",
        use_local: bool = False
    ):
        """
        Initialize Azure Quantum backend.
        
        Args:
            resource_id: Azure Quantum workspace resource ID
            location: Azure location
            target: Target simulator name
            use_local: Use local Qiskit simulator instead of Azure (for testing)
        """
        super().__init__(
            backend_name=f"Azure Quantum ({target})" + (" [Local]" if use_local else ""),
            backend_id=f"azure_{target.replace('.', '_')}"
        )
        
        self.resource_id = resource_id
        self.location = location
        self.target = target
        self.use_local = use_local or not HAS_AZURE
        self.workspace = None
        self.provider = None
        self.backend = None
        self.local_simulator = None
        self.jobs = {}
        
        if not self.use_local and not HAS_AZURE:
            raise ImportError(
                "Azure Quantum SDK not installed. "
                "Install with: pip install azure-quantum qiskit-qir"
            )
        
        if self.use_local and not HAS_QISKIT:
            raise ImportError(
                "Qiskit not installed for local simulation. "
                "Install with: pip install qiskit qiskit-aer"
            )
    
    def connect(self, credentials: Optional[Dict] = None) -> bool:
        """Connect to Azure Quantum workspace or local simulator."""
        try:
            # Use credentials if provided
            if credentials:
                self.resource_id = credentials.get('resource_id', self.resource_id)
                self.location = credentials.get('location', self.location)
            
            # Use local mode if requested or no credentials
            if self.use_local or not self.resource_id or not self.location:
                if HAS_QISKIT:
                    self.local_simulator = AerSimulator(method='statevector')
                    self._status = HardwareStatus.ONLINE
                    return True
                else:
                    raise ImportError("Qiskit not available for local simulation")
            
            # Connect to Azure Quantum workspace
            if HAS_AZURE:
                self.workspace = Workspace(
                    resource_id=self.resource_id,
                    location=self.location
                )
                
                # Get Qiskit provider
                self.provider = AzureQuantumProvider(self.workspace)
                self.backend = self.provider.get_backend(self.target)
                
                self._status = HardwareStatus.ONLINE
                return True
            else:
                raise ImportError("Azure Quantum SDK not available")
            
        except Exception as e:
            print(f"Failed to connect to Azure Quantum: {e}")
            self._status = HardwareStatus.OFFLINE
            return False
    
    def disconnect(self):
        """Disconnect from Azure Quantum."""
        self.workspace = None
        self.provider = None
        self.backend = None
        self._status = HardwareStatus.OFFLINE
    
    def get_capabilities(self) -> HardwareCapabilities:
        """Get simulator capabilities."""
        # Capabilities vary by target
        if 'ionq' in self.target:
            max_qubits = 29
            supported_gates = ['H', 'X', 'Y', 'Z', 'S', 'T', 'CNOT', 'RX', 'RY', 'RZ', 'SWAP']
            native_gates = ['RX', 'RY', 'RZ', 'XX']
        elif 'quantinuum' in self.target:
            max_qubits = 20
            supported_gates = ['H', 'X', 'Y', 'Z', 'S', 'T', 'CNOT', 'RZ', 'RX', 'RY']
            native_gates = ['RZ', 'ZZ']
        elif 'rigetti' in self.target:
            max_qubits = 40
            supported_gates = ['H', 'X', 'Y', 'Z', 'S', 'T', 'CNOT', 'RX', 'RY', 'RZ', 'CZ']
            native_gates = ['RX', 'RZ', 'CZ']
        else:
            max_qubits = 30
            supported_gates = ['H', 'X', 'Y', 'Z', 'CNOT']
            native_gates = ['H', 'CNOT']
        
        return HardwareCapabilities(
            max_qubits=max_qubits,
            supported_gates=supported_gates,
            native_gates=native_gates,
            connectivity={i: list(range(max_qubits)) for i in range(max_qubits)},
            has_mid_circuit_measurement=True,
            has_reset=True,
            has_conditional=False,
            qec_capable=False
        )
    
    def get_calibration_data(self) -> CalibrationData:
        """Get calibration data."""
        # Simulators have ideal calibration
        return CalibrationData(
            timestamp=time.time(),
            qubit_t1={i: float('inf') for i in range(30)},
            qubit_t2={i: float('inf') for i in range(30)},
            gate_fidelities={'all': 1.0},
            readout_fidelities={i: 1.0 for i in range(30)},
            gate_times={'all': 0.0}
        )
    
    def _qvm_to_azure(self, qvm_graph: Dict):
        """
        Convert QVM graph to Azure Quantum format.
        
        For now, this converts to Qiskit circuit which Azure Quantum accepts.
        """
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        
        # Handle both flat and nested structure
        if 'program' in qvm_graph:
            nodes = qvm_graph['program'].get('nodes', [])
        else:
            nodes = qvm_graph.get('nodes', [])
        
        # Determine qubits
        qubit_ids = set()
        for node in nodes:
            qubits = node.get('qubits', node.get('vqs', []))
            if qubits:
                qubit_ids.update(qubits)
        
        num_qubits = len(qubit_ids)
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
        
        qubit_map = {qid: i for i, qid in enumerate(sorted(qubit_ids))}
        
        # Convert nodes
        for node in nodes:
            op = node['op']
            qubits = node.get('qubits', node.get('vqs', []))
            params = node.get('params', node.get('args', {}))
            
            if op in ['ALLOC_LQ', 'FREE_LQ']:
                continue
            elif op in ['H', 'APPLY_H']:
                circuit.h(qr[qubit_map[qubits[0]]])
            elif op in ['X', 'APPLY_X']:
                circuit.x(qr[qubit_map[qubits[0]]])
            elif op in ['Y', 'APPLY_Y']:
                circuit.y(qr[qubit_map[qubits[0]]])
            elif op in ['Z', 'APPLY_Z']:
                circuit.z(qr[qubit_map[qubits[0]]])
            elif op in ['S', 'APPLY_S']:
                circuit.s(qr[qubit_map[qubits[0]]])
            elif op in ['T', 'APPLY_T']:
                circuit.t(qr[qubit_map[qubits[0]]])
            elif op in ['CNOT', 'APPLY_CNOT']:
                circuit.cx(qr[qubit_map[qubits[0]]], qr[qubit_map[qubits[1]]])
            elif op == 'RZ':
                circuit.rz(params.get('theta', 0), qr[qubit_map[qubits[0]]])
            elif op == 'RY':
                circuit.ry(params.get('theta', 0), qr[qubit_map[qubits[0]]])
            elif op == 'RX':
                circuit.rx(params.get('theta', 0), qr[qubit_map[qubits[0]]])
            elif op == 'MEASURE_Z':
                circuit.measure(qr[qubit_map[qubits[0]]], cr[qubit_map[qubits[0]]])
        
        return circuit
    
    def submit_job(
        self,
        job_id: str,
        circuit: Dict,
        shots: int = 1000
    ) -> str:
        """Submit job to Azure Quantum or local simulator."""
        if not (self.backend or self.local_simulator):
            raise RuntimeError("Backend not connected")
        
        # Convert to Qiskit circuit
        qiskit_circuit = self._qvm_to_azure(circuit)
        
        # Submit job
        backend_job_id = f"azure_{uuid.uuid4().hex[:8]}"
        
        try:
            start_time = time.time()
            
            # Use local simulator or Azure backend
            if self.local_simulator:
                job = self.local_simulator.run(qiskit_circuit, shots=shots)
            else:
                job = self.backend.run(qiskit_circuit, shots=shots)
            
            result = job.result()
            execution_time = time.time() - start_time
            
            # Extract measurements
            counts = result.get_counts()
            measurements = {}
            for bitstring, count in counts.items():
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
                    'target': self.target,
                    'mode': 'local' if self.local_simulator else 'azure',
                    'counts': counts
                }
            )
            
        except Exception as e:
            self.jobs[backend_job_id] = JobResult(
                job_id=backend_job_id,
                status=JobStatus.FAILED,
                error_message=str(e)
            )
        
        return backend_job_id
    
    def get_job_status(self, backend_job_id: str) -> JobStatus:
        """Get job status."""
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
        """Cancel job."""
        return False
