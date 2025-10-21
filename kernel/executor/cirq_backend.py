"""
Cirq Backend for QMK Executor

Translates QVM graphs to Cirq circuits and executes on Cirq simulator.
"""

import time
from typing import Dict, Any, Optional
import numpy as np

try:
    import cirq
    HAS_CIRQ = True
except ImportError:
    HAS_CIRQ = False

from .backend_interface import QuantumBackend


class CirqBackend(QuantumBackend):
    """
    Cirq backend for QMK.
    
    Translates QVM graphs to Cirq circuits and executes on Cirq simulator.
    """
    
    def __init__(self, seed: Optional[int] = None, **kwargs):
        """
        Initialize Cirq backend.
        
        Args:
            seed: Random seed for deterministic execution
            **kwargs: Additional Cirq configuration
        """
        if not HAS_CIRQ:
            raise ImportError("Cirq is required for CirqBackend. "
                            "Install with: pip install cirq")
        
        super().__init__(seed=seed, **kwargs)
        self.simulator = cirq.Simulator(seed=seed)
    
    def execute_graph(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute QVM graph on Cirq simulator.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Dictionary with events, telemetry, and metadata
        """
        start_time = time.time()
        
        # Translate QVM to Cirq
        circuit, qubit_map, event_map = self.translate_qvm_to_native(qvm_graph)
        
        # Execute on Cirq (single shot)
        result = self.simulator.run(circuit, repetitions=1)
        
        # Translate results back to QVM
        events = self.translate_results_to_qvm(result, event_map)
        
        execution_time = time.time() - start_time
        
        return {
            "events": events,
            "telemetry": {
                "execution_time_s": execution_time,
                "backend": "cirq",
                "shots": 1
            },
            "metadata": {
                "cirq_metadata": {}
            }
        }
    
    def translate_qvm_to_native(self, qvm_graph: Dict[str, Any]) -> tuple:
        """
        Translate QVM graph to Cirq circuit.
        
        Args:
            qvm_graph: QVM graph in dictionary format
        
        Returns:
            Tuple of (Circuit, qubit_map, event_map)
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
        
        # Create Cirq qubits
        qubit_map = {}
        for qid in sorted(qubit_ids):
            qubit_map[qid] = cirq.NamedQubit(qid)
        
        # Build circuit
        circuit = cirq.Circuit()
        event_map = {}
        
        # Convert nodes to gates
        for node in nodes:
            op = node['op']
            qubits = node.get('qubits', node.get('vqs', []))
            params = node.get('params', node.get('args', {}))
            
            if op == 'ALLOC_LQ' or op == 'FREE_LQ':
                continue
            
            # Single-qubit gates
            elif op in ['H', 'APPLY_H']:
                circuit.append(cirq.H(qubit_map[qubits[0]]))
            elif op in ['X', 'APPLY_X']:
                circuit.append(cirq.X(qubit_map[qubits[0]]))
            elif op in ['Y', 'APPLY_Y']:
                circuit.append(cirq.Y(qubit_map[qubits[0]]))
            elif op in ['Z', 'APPLY_Z']:
                circuit.append(cirq.Z(qubit_map[qubits[0]]))
            elif op in ['S', 'APPLY_S']:
                circuit.append(cirq.S(qubit_map[qubits[0]]))
            elif op in ['T', 'APPLY_T']:
                circuit.append(cirq.T(qubit_map[qubits[0]]))
            
            # Rotation gates
            elif op in ['RX', 'APPLY_RX']:
                theta = params.get('theta', 0)
                circuit.append(cirq.rx(theta)(qubit_map[qubits[0]]))
            elif op in ['RY', 'APPLY_RY']:
                theta = params.get('theta', 0)
                circuit.append(cirq.ry(theta)(qubit_map[qubits[0]]))
            elif op in ['RZ', 'APPLY_RZ']:
                theta = params.get('theta', 0)
                circuit.append(cirq.rz(theta)(qubit_map[qubits[0]]))
            
            # Two-qubit gates
            elif op in ['CNOT', 'APPLY_CNOT', 'CX']:
                circuit.append(cirq.CNOT(qubit_map[qubits[0]], qubit_map[qubits[1]]))
            elif op in ['CZ', 'APPLY_CZ']:
                circuit.append(cirq.CZ(qubit_map[qubits[0]], qubit_map[qubits[1]]))
            elif op in ['SWAP', 'APPLY_SWAP']:
                circuit.append(cirq.SWAP(qubit_map[qubits[0]], qubit_map[qubits[1]]))
            
            # Measurements
            elif op in ['MEASURE_Z', 'MEASURE']:
                q = qubit_map[qubits[0]]
                event_ids = node.get('produces', [])
                event_id = event_ids[0] if event_ids else f"m{qubits[0]}"
                
                circuit.append(cirq.measure(q, key=event_id))
                event_map[event_id] = event_id
            
            elif op in ['MEASURE_X']:
                # X-basis measurement
                q = qubit_map[qubits[0]]
                circuit.append(cirq.H(q))
                
                event_ids = node.get('produces', [])
                event_id = event_ids[0] if event_ids else f"m{qubits[0]}"
                
                circuit.append(cirq.measure(q, key=event_id))
                event_map[event_id] = event_id
            
            elif op in ['MEASURE_Y']:
                # Y-basis measurement
                q = qubit_map[qubits[0]]
                circuit.append(cirq.S(q) ** -1)
                circuit.append(cirq.H(q))
                
                event_ids = node.get('produces', [])
                event_id = event_ids[0] if event_ids else f"m{qubits[0]}"
                
                circuit.append(cirq.measure(q, key=event_id))
                event_map[event_id] = event_id
        
        return circuit, qubit_map, event_map
    
    def translate_results_to_qvm(self, native_result: Any, event_map: Dict[str, str]) -> Dict[str, int]:
        """
        Translate Cirq results to QVM event format.
        
        Args:
            native_result: Cirq Result object
            event_map: Mapping from measurement keys to event IDs
        
        Returns:
            Dictionary mapping event IDs to measurement outcomes
        """
        events = {}
        
        for event_id in event_map.keys():
            if event_id in native_result.measurements:
                # Get measurement result (single shot)
                measurement = native_result.measurements[event_id][0]
                # Convert numpy array to Python int (handle both scalar and array)
                if hasattr(measurement, '__iter__'):
                    events[event_id] = int(measurement[0])
                else:
                    events[event_id] = int(measurement)
        
        return events
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the Cirq backend."""
        return {
            "backend_type": "cirq",
            "seed": self.seed,
            "version": "cirq",
            "supports_noise": True,
            "max_qubits": 25  # Practical limit
        }
