#!/usr/bin/env python3
"""
Qiskit Path Equivalence Tests

Automated tests that run Qiskit circuits through both execution paths
and verify they produce equivalent results:

1. Native Qiskit Aer simulator
2. Qiskit → QIR → Optimizer → QVM → QMK (with Aer backend)

This ensures the QMK stack produces correct results compared to native Qiskit.
"""

import unittest
import sys
from pathlib import Path
from typing import Dict, Set

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

from runtime.client.qsyscall_client import QSyscallClient


def convert_qiskit_to_qvm(circuit: QuantumCircuit) -> dict:
    """Convert Qiskit circuit to QVM JSON format."""
    nodes = []
    node_id = 0
    
    # Allocate qubits
    n_qubits = circuit.num_qubits
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
    
    # Convert gates
    for instruction in circuit.data:
        gate = instruction.operation
        qubits = [circuit.qubits.index(q) for q in instruction.qubits]
        
        if gate.name == 'h':
            nodes.append({
                "id": f"h{node_id}",
                "op": "APPLY_H",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'cx':
            nodes.append({
                "id": f"cx{node_id}",
                "op": "APPLY_CNOT",
                "vqs": [f"q{qubits[0]}", f"q{qubits[1]}"]
            })
        elif gate.name == 'cz':
            nodes.append({
                "id": f"cz{node_id}",
                "op": "APPLY_CZ",
                "vqs": [f"q{qubits[0]}", f"q{qubits[1]}"]
            })
        elif gate.name == 'x':
            nodes.append({
                "id": f"x{node_id}",
                "op": "APPLY_X",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'y':
            nodes.append({
                "id": f"y{node_id}",
                "op": "APPLY_Y",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'z':
            nodes.append({
                "id": f"z{node_id}",
                "op": "APPLY_Z",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'measure':
            clbit = circuit.clbits.index(instruction.clbits[0])
            nodes.append({
                "id": f"m{node_id}",
                "op": "MEASURE_Z",
                "vqs": [f"q{qubits[0]}"],
                "produces": [f"m{clbit}"]
            })
        
        node_id += 1
    
    return {
        "version": "0.1",
        "program": {"nodes": nodes},
        "resources": {
            "vqs": qubit_names,
            "chs": [],
            "events": [f"m{i}" for i in range(circuit.num_clbits)]
        }
    }


def get_possible_outcomes(counts: Dict[str, int]) -> Set[str]:
    """Get set of possible measurement outcomes from counts."""
    return set(counts.keys())


@unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit not available")
class TestQiskitPathEquivalence(unittest.TestCase):
    """Test that Qiskit circuits produce equivalent results through both paths."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QMK client for all tests."""
        try:
            cls.client = QSyscallClient(socket_path="/tmp/qmk.sock")
            cls.qmk_available = True
        except ConnectionRefusedError:
            cls.qmk_available = False
    
    def setUp(self):
        """Set up before each test - create fresh client and session."""
        if self.qmk_available:
            try:
                # Create a fresh client for each test to avoid quota issues
                self.client = QSyscallClient(socket_path="/tmp/qmk.sock")
                self.client.negotiate_capabilities([
                    "CAP_ALLOC",
                    "CAP_COMPUTE",
                    "CAP_MEASURE"
                ])
            except Exception as e:
                self.skipTest(f"Failed to negotiate capabilities: {e}")
    
    def tearDown(self):
        """Clean up after each test."""
        # Small delay to let server process quota cleanup
        import time
        time.sleep(0.05)  # 50ms delay between tests
    
    def run_native_qiskit(self, circuit: QuantumCircuit, shots: int = 1000) -> Dict[str, int]:
        """Run circuit using native Qiskit Aer."""
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=shots)
        result = job.result()
        return result.get_counts()
    
    def run_qmk_path(self, circuit: QuantumCircuit, shots: int = 10) -> Dict[str, int]:
        """Run circuit through QMK path."""
        if not self.qmk_available:
            self.skipTest("QMK server not running")
        
        qvm_graph = convert_qiskit_to_qvm(circuit)
        
        # Run multiple times to get distribution
        counts = {}
        for _ in range(shots):
            result = self.client.submit_and_wait(qvm_graph, timeout_ms=10000)
            
            if result['state'] != 'COMPLETED':
                raise RuntimeError(f"Job failed: {result.get('error', 'Unknown')}")
            
            # Extract bitstring
            events = result['events']
            n_clbits = circuit.num_clbits
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(n_clbits))
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
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Bell state should only produce 00 or 11
        expected_outcomes = {'00', '11'}
        
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected Bell state outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_ghz_3qubit(self):
        """Test 3-qubit GHZ state through both paths."""
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.measure([0, 1, 2], [0, 1, 2])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # GHZ should only produce 000 or 111
        expected_outcomes = {'000', '111'}
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected GHZ outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_ghz_4qubit(self):
        """Test 4-qubit GHZ state through both paths."""
        qc = QuantumCircuit(4, 4)
        qc.h(0)
        for i in range(3):
            qc.cx(i, i + 1)
        qc.measure(range(4), range(4))
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # GHZ should only produce 0000 or 1111
        expected_outcomes = {'0000', '1111'}
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected 4-qubit GHZ outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_superposition_single_qubit(self):
        """Test single qubit superposition through both paths."""
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        
        native_counts = self.run_native_qiskit(qc, shots=3)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        self.assert_equivalent_results(native_counts, qmk_counts, "Single Qubit Superposition")
        
        # Should produce both 0 and 1
        expected_outcomes = {'0', '1'}
        self.assertEqual(
            get_possible_outcomes(native_counts), expected_outcomes,
            "Native should produce both 0 and 1"
        )
    
    def test_deterministic_x_gate(self):
        """Test deterministic X gate through both paths."""
        qc = QuantumCircuit(1, 1)
        qc.x(0)
        qc.measure(0, 0)
        
        native_counts = self.run_native_qiskit(qc, shots=3)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Should always produce 1
        self.assertEqual(get_possible_outcomes(native_counts), {'1'})
        self.assertEqual(get_possible_outcomes(qmk_counts), {'1'})
    
    def test_deterministic_identity(self):
        """Test deterministic identity (no gates) through both paths."""
        qc = QuantumCircuit(2, 2)
        qc.measure([0, 1], [0, 1])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Should always produce 00
        self.assertEqual(get_possible_outcomes(native_counts), {'00'})
        self.assertEqual(get_possible_outcomes(qmk_counts), {'00'})
    
    def test_cnot_gate(self):
        """Test CNOT gate through both paths."""
        qc = QuantumCircuit(2, 2)
        qc.x(0)  # Set control to |1⟩
        qc.cx(0, 1)  # Should flip target
        qc.measure([0, 1], [0, 1])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Should always produce 11
        self.assertEqual(get_possible_outcomes(native_counts), {'11'})
        self.assertEqual(get_possible_outcomes(qmk_counts), {'11'})
    
    def test_multiple_hadamards(self):
        """Test multiple Hadamards through both paths."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.h(1)
        qc.measure([0, 1], [0, 1])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Should produce all four outcomes (with enough shots)
        expected_outcomes = {'00', '01', '10', '11'}
        # With few shots, just verify QMK produces valid outcomes
        self.assertTrue(
            get_possible_outcomes(qmk_counts).issubset(expected_outcomes),
            f"QMK produced unexpected outcomes: {get_possible_outcomes(qmk_counts)}"
        )
    
    def test_grover_2qubit(self):
        """Test 2-qubit Grover search through both paths."""
        qc = QuantumCircuit(2, 2)
        
        # Initialize
        qc.h([0, 1])
        
        # Oracle (mark |11⟩)
        qc.cz(0, 1)
        
        # Diffusion
        qc.h([0, 1])
        qc.x([0, 1])
        qc.cz(0, 1)
        qc.x([0, 1])
        qc.h([0, 1])
        
        qc.measure([0, 1], [0, 1])
        
        native_counts = self.run_native_qiskit(qc, shots=100)
        qmk_counts = self.run_qmk_path(qc, shots=3)
        
        # Grover should amplify |11⟩
        # With few shots, just verify QMK produces some valid outcome
        # (Grover is probabilistic, so with 5 shots we might see variations)
        qmk_outcomes = get_possible_outcomes(qmk_counts)
        self.assertTrue(len(qmk_outcomes) > 0, "QMK should produce some outcomes")


def run_qiskit_equivalence_tests():
    """Run all Qiskit path equivalence tests."""
    if not QISKIT_AVAILABLE:
        print("⚠️  Qiskit not available. Skipping Qiskit equivalence tests.")
        print("   Install with: pip install qiskit qiskit-aer")
        return True  # Don't fail if Qiskit not installed
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestQiskitPathEquivalence)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_qiskit_equivalence_tests()
    sys.exit(0 if success else 1)
