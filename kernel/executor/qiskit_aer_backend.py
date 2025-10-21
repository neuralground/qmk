"""
Qiskit Aer Backend for QMK Executor

Translates QVM graphs to Qiskit circuits and executes on Aer simulator.
"""

import time
from typing import Dict, Any, Optional

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

from .backend_interface import QuantumBackend


class QiskitAerBackend(QuantumBackend):
    """
    Qiskit Aer backend for QMK.
    
    Translates QVM graphs to Qiskit circuits and executes on AerSimulator.
    Provides high-fidelity simulation with correct quantum mechanics.
    """
    
    def __init__(self, seed: Optional[int] = None, method: str = 'automatic', **kwargs):
        """
        Initialize Qiskit Aer backend.
        
        Args:
            seed: Random seed for deterministic execution
            method: Aer simulation method ('automatic', 'statevector', 'density_matrix', etc.)
            **kwargs: Additional Aer configuration
        """
        if not HAS_QISKIT:
            raise ImportError("Qiskit and qiskit-aer are required for QiskitAerBackend. "
                            "Install with: pip install qiskit qiskit-aer")
        
        super().__init__(seed=seed, **kwargs)
        self.method = method
        self.simulator = AerSimulator(method=method)
        if seed is not None:
            self.simulator.set_options(seed_simulator=seed)
    
    def execute_graph(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute QVM graph on Qiskit Aer simulator.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Dictionary with events, telemetry, and metadata
        """
        start_time = time.time()
        
        # Translate QVM to Qiskit
        circuit, event_map = self.translate_qvm_to_native(qvm_graph)
        
        # Execute on Aer
        job = self.simulator.run(circuit, shots=1)
        result = job.result()
        
        # Translate results back to QVM
        events = self.translate_results_to_qvm(result, event_map)
        
        execution_time = time.time() - start_time
        
        return {
            "events": events,
            "telemetry": {
                "execution_time_s": execution_time,
                "backend": "qiskit_aer",
                "method": self.method,
                "shots": 1
            },
            "metadata": {
                "qiskit_metadata": result.to_dict() if hasattr(result, 'to_dict') else {}
            }
        }
    
    def translate_qvm_to_native(self, qvm_graph: Dict[str, Any]) -> tuple:
        """
        Translate QVM graph to Qiskit circuit.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Tuple of (QuantumCircuit, event_map)
            event_map: Dict mapping classical bit indices to event IDs
        """
        # Extract nodes
        if 'program' in qvm_graph:
            nodes = qvm_graph['program'].get('nodes', [])
        else:
            nodes = qvm_graph.get('nodes', [])
        
        # Find all qubits
        qubit_ids = set()
        for node in nodes:
            qubits = node.get('qubits', node.get('vqs', []))
            if qubits:
                qubit_ids.update(qubits)
        
        # Create circuit
        num_qubits = len(qubit_ids)
        if num_qubits == 0:
            num_qubits = 1  # At least one qubit
        
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        circuit = QuantumCircuit(qr, cr)
        
        # Map qubit IDs to indices
        qubit_map = {qid: i for i, qid in enumerate(sorted(qubit_ids))}
        
        # Map classical bits to event IDs
        event_map = {}
        classical_bit_counter = 0
        
        # Convert nodes to gates
        for node in nodes:
            op = node['op']
            qubits = node.get('qubits', node.get('vqs', []))
            params = node.get('params', node.get('args', {}))
            
            if op == 'ALLOC_LQ' or op == 'FREE_LQ':
                # Allocation is implicit in Qiskit
                continue
            
            # Single-qubit gates
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
            
            # Rotation gates
            elif op in ['RX', 'APPLY_RX']:
                theta = params.get('theta', 0)
                circuit.rx(theta, qr[qubit_map[qubits[0]]])
            elif op in ['RY', 'APPLY_RY']:
                theta = params.get('theta', 0)
                circuit.ry(theta, qr[qubit_map[qubits[0]]])
            elif op in ['RZ', 'APPLY_RZ']:
                theta = params.get('theta', 0)
                circuit.rz(theta, qr[qubit_map[qubits[0]]])
            
            # Two-qubit gates
            elif op in ['CNOT', 'APPLY_CNOT', 'CX']:
                circuit.cx(qr[qubit_map[qubits[0]]], qr[qubit_map[qubits[1]]])
            elif op in ['CZ', 'APPLY_CZ']:
                circuit.cz(qr[qubit_map[qubits[0]]], qr[qubit_map[qubits[1]]])
            elif op in ['SWAP', 'APPLY_SWAP']:
                circuit.swap(qr[qubit_map[qubits[0]]], qr[qubit_map[qubits[1]]])
            
            # Measurements
            elif op in ['MEASURE_Z', 'MEASURE']:
                qubit_idx = qubit_map[qubits[0]]
                circuit.measure(qr[qubit_idx], cr[classical_bit_counter])
                
                # Map classical bit to event ID
                event_ids = node.get('produces', [])
                if event_ids:
                    event_map[classical_bit_counter] = event_ids[0]
                else:
                    event_map[classical_bit_counter] = f"m{qubit_idx}"
                
                classical_bit_counter += 1
            
            elif op in ['MEASURE_X']:
                # X-basis measurement: H then measure
                qubit_idx = qubit_map[qubits[0]]
                circuit.h(qr[qubit_idx])
                circuit.measure(qr[qubit_idx], cr[classical_bit_counter])
                
                event_ids = node.get('produces', [])
                if event_ids:
                    event_map[classical_bit_counter] = event_ids[0]
                else:
                    event_map[classical_bit_counter] = f"m{qubit_idx}"
                
                classical_bit_counter += 1
            
            elif op in ['MEASURE_Y']:
                # Y-basis measurement: S†H then measure
                qubit_idx = qubit_map[qubits[0]]
                circuit.sdg(qr[qubit_idx])
                circuit.h(qr[qubit_idx])
                circuit.measure(qr[qubit_idx], cr[classical_bit_counter])
                
                event_ids = node.get('produces', [])
                if event_ids:
                    event_map[classical_bit_counter] = event_ids[0]
                else:
                    event_map[classical_bit_counter] = f"m{qubit_idx}"
                
                classical_bit_counter += 1
            
            # Barriers
            elif op in ['FENCE_EPOCH', 'BARRIER']:
                circuit.barrier()
        
        return circuit, event_map
    
    def translate_results_to_qvm(self, native_result: Any, event_map: Dict[int, str]) -> Dict[str, int]:
        """
        Translate Qiskit results to QVM event format.
        
        Args:
            native_result: Qiskit Result object
            event_map: Mapping from classical bit indices to event IDs
        
        Returns:
            Dictionary mapping event IDs to measurement outcomes
        """
        # Get counts (should be single shot)
        counts = native_result.get_counts()
        
        # Extract the single measurement result
        bitstring = list(counts.keys())[0]
        
        # Qiskit returns bitstrings in reverse order (rightmost = qubit 0)
        bitstring_rev = bitstring[::-1]
        
        # Map to events
        events = {}
        for bit_idx, event_id in event_map.items():
            if bit_idx < len(bitstring_rev):
                events[event_id] = int(bitstring_rev[bit_idx])
        
        return events
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the Qiskit Aer backend."""
        return {
            "backend_type": "qiskit_aer",
            "method": self.method,
            "seed": self.seed,
            "version": "qiskit-aer",
            "supports_noise": True,
            "supports_density_matrix": True,
            "max_qubits": 30  # Practical limit for statevector
        }
