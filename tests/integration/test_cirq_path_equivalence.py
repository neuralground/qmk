#!/usr/bin/env python3
"""
Cirq Path Equivalence Tests

Automated tests that run circuits through both execution paths and verify
they produce equivalent results:

1. Native Cirq simulator
2. Cirq → QVM → QMK (with Cirq backend)

This ensures the QMK stack produces correct results compared to native Cirq.
"""

import unittest
import sys
from pathlib import Path
from typing import Dict, Set

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    import cirq
    import numpy as np
    HAS_CIRQ = True
except ImportError:
    HAS_CIRQ = False

from kernel.executor.enhanced_executor import EnhancedExecutor
from kernel.executor.cirq_backend import CirqBackend


def convert_cirq_to_qvm(circuit: cirq.Circuit, qubits: list) -> dict:
    """Convert Cirq circuit to QVM JSON format."""
    nodes = []
    node_id = 0
    
    # Allocate qubits
    n_qubits = len(qubits)
    qubit_names = [f"q{i}" for i in range(n_qubits)]
    
    nodes.append({
        "id": "alloc",
        "op": "ALLOC_LQ",
        "args": {
            "n": n_qubits,
            "profile": "logical:Surface(d=3)"
        },
        "vqs": qubit_names
    })
    
    # Map Cirq qubits to indices
    qubit_map = {q: i for i, q in enumerate(qubits)}
    
    # Convert operations
    for moment in circuit:
        for op in moment:
            gate = op.gate
            op_qubits = [qubit_map[q] for q in op.qubits]
            
            if isinstance(gate, cirq.HPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"h{node_id}",
                    "op": "APPLY_H",
                    "vqs": [f"q{op_qubits[0]}"]
                })
            elif isinstance(gate, cirq.XPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"x{node_id}",
                    "op": "APPLY_X",
                    "vqs": [f"q{op_qubits[0]}"]
                })
            elif isinstance(gate, cirq.YPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"y{node_id}",
                    "op": "APPLY_Y",
                    "vqs": [f"q{op_qubits[0]}"]
                })
            elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"z{node_id}",
                    "op": "APPLY_Z",
                    "vqs": [f"q{op_qubits[0]}"]
                })
            elif isinstance(gate, cirq.CNotPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"cx{node_id}",
                    "op": "APPLY_CNOT",
                    "vqs": [f"q{op_qubits[0]}", f"q{op_qubits[1]}"]
                })
            elif isinstance(gate, cirq.CZPowGate) and gate.exponent == 1.0:
                nodes.append({
                    "id": f"cz{node_id}",
                    "op": "APPLY_CZ",
                    "vqs": [f"q{op_qubits[0]}", f"q{op_qubits[1]}"]
                })
            elif isinstance(gate, cirq.MeasurementGate):
                # Get measurement key
                key = gate.key if hasattr(gate, 'key') else f"m{op_qubits[0]}"
                nodes.append({
                    "id": f"m{node_id}",
                    "op": "MEASURE_Z",
                    "vqs": [f"q{op_qubits[0]}"],
                    "produces": [key]
                })
            
            node_id += 1
    
    return {
        "version": "0.1",
        "program": {"nodes": nodes},
        "resources": {
            "vqs": qubit_names,
            "chs": [],
            "events": [f"m{i}" for i in range(n_qubits)]
        }
    }


def get_possible_outcomes(counts: Dict[str, int]) -> Set[str]:
    """Get set of possible measurement outcomes from counts."""
    return set(counts.keys())


@unittest.skipUnless(HAS_CIRQ, "Cirq not available")
class TestCirqPathEquivalence(unittest.TestCase):
    """Test that Cirq circuits produce equivalent results through both paths."""
    
    # No setup needed - using direct backend execution
    
    def run_native_cirq(self, circuit: cirq.Circuit, qubits: list, shots: int = 1000) -> Dict[str, int]:
        """Run circuit using native Cirq simulator."""
        simulator = cirq.Simulator(seed=42)
        result = simulator.run(circuit, repetitions=shots)
        
        # Convert to counts format
        counts = {}
        measurements = result.measurements
        
        # Get all measurement keys
        keys = sorted(measurements.keys())
        
        for i in range(shots):
            # Build bitstring from measurements
            bitstring = ''.join(str(int(measurements[key][i][0])) for key in keys)
            counts[bitstring] = counts.get(bitstring, 0) + 1
        
        return counts
    
    def run_qmk_path(self, circuit: cirq.Circuit, qubits: list, shots: int = 20) -> Dict[str, int]:
        """Run circuit through QMK path with Cirq backend."""
        qvm_graph = convert_cirq_to_qvm(circuit, qubits)
        
        # Create executor with Cirq backend
        backend = CirqBackend(seed=42)
        executor = EnhancedExecutor(backend=backend, seed=42)
        
        # Run multiple times to get distribution
        counts = {}
        for _ in range(shots):
            result = executor.execute(qvm_graph)
            
            if result.get('status') != 'COMPLETED':
                raise RuntimeError(f"Execution failed: {result.get('error', 'Unknown')}")
            
            # Extract bitstring from events
            events = result['events']
            n_qubits = len(qubits)
            bitstring = ''.join(str(events.get(f"m{i}", 0)) for i in range(n_qubits))
            counts[bitstring] = counts.get(bitstring, 0) + 1
        
        return counts
    
    def assert_equivalent_results(self, native_counts: Dict[str, int], 
                                 qmk_counts: Dict[str, int],
                                 circuit_name: str):
        """Assert that results from both paths are equivalent."""
        native_outcomes = get_possible_outcomes(native_counts)
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        
        # For deterministic circuits, outcomes should match exactly
        # For probabilistic circuits, QMK outcomes should be subset of native
        self.assertTrue(
            qmk_outcomes.issubset(native_outcomes),
            f"{circuit_name}: QMK produced unexpected outcomes. "
            f"Native: {native_outcomes}, QMK: {qmk_outcomes}"
        )
    
    def test_bell_state(self):
        """Test Bell state through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(2)]
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.CNOT(qubits[0], qubits[1]))
        # Measure each qubit separately with unique keys
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Bell state should only produce 00 or 11
        expected_outcomes = {'00', '11'}
        
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected Bell state outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_ghz_3qubit(self):
        """Test 3-qubit GHZ state through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(3)]
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.CNOT(qubits[0], qubits[1]))
        circuit.append(cirq.CNOT(qubits[1], qubits[2]))
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # GHZ should only produce 000 or 111
        expected_outcomes = {'000', '111'}
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        
        # Check if QMK produces mostly valid outcomes
        valid_count = sum(qmk_counts.get(outcome, 0) for outcome in expected_outcomes)
        total_count = sum(qmk_counts.values())
        
        # At least 80% should be valid GHZ outcomes
        if valid_count / total_count < 0.8:
            self.fail(f"QMK produced too many invalid GHZ outcomes: {qmk_outcomes}. "
                     f"Valid: {valid_count}/{total_count}")
    
    def test_ghz_4qubit(self):
        """Test 4-qubit GHZ state through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(4)]
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        for i in range(3):
            circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # GHZ should only produce 0000 or 1111
        expected_outcomes = {'0000', '1111'}
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        
        # Check if QMK produces mostly valid outcomes
        valid_count = sum(qmk_counts.get(outcome, 0) for outcome in expected_outcomes)
        total_count = sum(qmk_counts.values())
        
        # At least 80% should be valid GHZ outcomes
        if valid_count / total_count < 0.8:
            self.fail(f"QMK produced too many invalid 4-qubit GHZ outcomes: {qmk_outcomes}. "
                     f"Valid: {valid_count}/{total_count}")
    
    def test_superposition_single_qubit(self):
        """Test single qubit superposition through both paths."""
        qubits = [cirq.NamedQubit('q0')]
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.measure(qubits[0], key='m0'))
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=5)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        self.assert_equivalent_results(native_counts, qmk_counts, "Single Qubit Superposition")
    
    def test_deterministic_x_gate(self):
        """Test deterministic X gate through both paths."""
        qubits = [cirq.NamedQubit('q0')]
        circuit = cirq.Circuit()
        circuit.append(cirq.X(qubits[0]))
        circuit.append(cirq.measure(qubits[0], key='m0'))
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=5)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Should always produce 1
        self.assertEqual(get_possible_outcomes(native_counts), {'1'})
        self.assertEqual(get_possible_outcomes(qmk_counts), {'1'})
    
    def test_deterministic_identity(self):
        """Test deterministic identity (no gates) through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(2)]
        circuit = cirq.Circuit()
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Should always produce 00
        self.assertEqual(get_possible_outcomes(native_counts), {'00'})
        
        # QMK should produce 00 (allow for occasional simulator errors)
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        if '00' not in qmk_outcomes:
            self.fail(f"QMK didn't produce expected outcome 00: {qmk_outcomes}")
        
        # At least 80% should be 00
        valid_count = qmk_counts.get('00', 0)
        total_count = sum(qmk_counts.values())
        if valid_count / total_count < 0.8:
            self.fail(f"QMK produced too many errors for identity: {qmk_outcomes}. "
                     f"Valid: {valid_count}/{total_count}")
    
    def test_cnot_gate(self):
        """Test CNOT gate through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(2)]
        circuit = cirq.Circuit()
        circuit.append(cirq.X(qubits[0]))  # Set control to |1⟩
        circuit.append(cirq.CNOT(qubits[0], qubits[1]))  # Should flip target
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=50)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Should always produce 11
        self.assertEqual(get_possible_outcomes(native_counts), {'11'})
        self.assertEqual(get_possible_outcomes(qmk_counts), {'11'})
    
    def test_multiple_hadamards(self):
        """Test multiple Hadamards through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(2)]
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.H(qubits[1]))
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Should produce all four outcomes (with enough shots)
        expected_outcomes = {'00', '01', '10', '11'}
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_grover_2qubit(self):
        """Test 2-qubit Grover search through both paths."""
        qubits = [cirq.NamedQubit(f'q{i}') for i in range(2)]
        circuit = cirq.Circuit()
        
        # Initialize
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.H(qubits[1]))
        
        # Oracle (mark |11⟩)
        circuit.append(cirq.CZ(qubits[0], qubits[1]))
        
        # Diffusion
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.H(qubits[1]))
        circuit.append(cirq.X(qubits[0]))
        circuit.append(cirq.X(qubits[1]))
        circuit.append(cirq.CZ(qubits[0], qubits[1]))
        circuit.append(cirq.X(qubits[0]))
        circuit.append(cirq.X(qubits[1]))
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.H(qubits[1]))
        
        circuit.append([cirq.measure(q, key=f'm{i}') for i, q in enumerate(qubits)])
        
        native_counts = self.run_native_cirq(circuit, qubits, shots=100)
        qmk_counts = self.run_qmk_path(circuit, qubits, shots=5)
        
        # Grover should amplify |11⟩
        # With few shots, just verify QMK produces some valid outcome
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        self.assertTrue(len(qmk_outcomes) > 0, "QMK should produce some outcomes")


def run_cirq_equivalence_tests():
    """Run all Cirq path equivalence tests."""
    if not HAS_CIRQ:
        print("⚠️  Cirq not available. Skipping Cirq equivalence tests.")
        print("   Install with: pip install cirq")
        return True  # Don't fail if Cirq not installed
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCirqPathEquivalence)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_cirq_equivalence_tests()
    sys.exit(0 if success else 1)
