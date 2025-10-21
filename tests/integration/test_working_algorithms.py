#!/usr/bin/env python3
"""
Working Algorithms Integration Tests

Tests algorithms that work correctly with the current QMK implementation.
These algorithms use gates and patterns that our simulator handles well.
"""

import unittest
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.executor.enhanced_executor import EnhancedExecutor
from tests.test_helpers import create_test_executor
from qir.optimizer_integration import OptimizedExecutor, OptimizationLevel
from qir.translators.qiskit_to_qir import QiskitToQIRConverter
from qir.translators.cirq_to_qir import CirqToQIRConverter

# Import algorithm examples
sys.path.insert(0, str(ROOT / "examples" / "qiskit"))
sys.path.insert(0, str(ROOT / "examples" / "cirq"))
import qiskit_algorithms
import cirq_algorithms

# Try importing quantum frameworks
try:
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

try:
    import cirq
    HAS_CIRQ = True
except ImportError:
    HAS_CIRQ = False


class TestWorkingAlgorithms(unittest.TestCase):
    """Test algorithms that work correctly with QMK."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shots = 1000
        self.fidelity_threshold = 0.90
    
    def _calculate_fidelity(self, counts1: dict, counts2: dict) -> float:
        """Calculate fidelity between two measurement distributions."""
        all_bitstrings = set(counts1.keys()) | set(counts2.keys())
        shots1 = sum(counts1.values())
        shots2 = sum(counts2.values())
        
        fidelity = 0
        for bs in all_bitstrings:
            p1 = counts1.get(bs, 0) / shots1
            p2 = counts2.get(bs, 0) / shots2
            fidelity += np.sqrt(p1 * p2)
        
        return fidelity
    
    def _qvm_to_counts(self, qvm_graph: dict, shots: int) -> dict:
        """Execute QVM graph multiple times and collect counts."""
        counts = {}
        for _ in range(shots):
            executor = create_test_executor()
            result = executor.execute(qvm_graph)
            events = result.get('events', {})
            
            # Build bitstring from measurements
            num_qubits = len([k for k in events.keys() if k.startswith('m')])
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(num_qubits))
            counts[bitstring] = counts.get(bitstring, 0) + 1
        
        return counts
    
    # ===== Entanglement Tests =====
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_bell_state(self):
        """Test Bell state - maximally entangled 2-qubit state."""
        circuit = qiskit_algorithms.bell_state()
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bell state fidelity: {fidelity:.4f}")
        
        print(f"✅ Qiskit Bell State: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_ghz_3(self):
        """Test 3-qubit GHZ state."""
        circuit = qiskit_algorithms.ghz_state(3)
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"GHZ-3 fidelity: {fidelity:.4f}")
        
        print(f"✅ Qiskit GHZ-3: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_ghz_5(self):
        """Test 5-qubit GHZ state."""
        circuit = qiskit_algorithms.ghz_state(5)
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"GHZ-5 fidelity: {fidelity:.4f}")
        
        print(f"✅ Qiskit GHZ-5: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_bell_state(self):
        """Test Cirq Bell state."""
        circuit = cirq_algorithms.bell_state()
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '02b'): v for k, v in native_histogram.items()}
        
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bell state fidelity: {fidelity:.4f}")
        
        print(f"✅ Cirq Bell State: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_ghz_3(self):
        """Test Cirq 3-qubit GHZ state."""
        circuit = cirq_algorithms.ghz_state(3)
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '03b'): v for k, v in native_histogram.items()}
        
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"GHZ-3 fidelity: {fidelity:.4f}")
        
        print(f"✅ Cirq GHZ-3: {fidelity:.4f}")
    
    # ===== With Optimization =====
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_bell_with_optimization(self):
        """Test Bell state with optimization."""
        circuit = qiskit_algorithms.bell_state()
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        
        # Unoptimized
        unopt_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Optimized
        opt_counts = {}
        for _ in range(self.shots):
            executor = OptimizedExecutor(
                create_test_executor(),
                OptimizationLevel.AGGRESSIVE
            )
            result = executor.execute(qvm_graph)
            events = result['events']
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(2))
            opt_counts[bitstring] = opt_counts.get(bitstring, 0) + 1
        
        fidelity = self._calculate_fidelity(unopt_counts, opt_counts)
        self.assertGreater(fidelity, 0.85,
            f"Optimization fidelity: {fidelity:.4f}")
        
        print(f"✅ Bell with optimization: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_ghz_with_optimization(self):
        """Test GHZ state with optimization."""
        circuit = qiskit_algorithms.ghz_state(3)
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        
        # Unoptimized
        unopt_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Optimized
        opt_counts = {}
        for _ in range(self.shots):
            executor = OptimizedExecutor(
                create_test_executor(),
                OptimizationLevel.AGGRESSIVE
            )
            result = executor.execute(qvm_graph)
            events = result['events']
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(3))
            opt_counts[bitstring] = opt_counts.get(bitstring, 0) + 1
        
        fidelity = self._calculate_fidelity(unopt_counts, opt_counts)
        self.assertGreater(fidelity, 0.85,
            f"Optimization fidelity: {fidelity:.4f}")
        
        print(f"✅ GHZ with optimization: {fidelity:.4f}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
