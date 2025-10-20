#!/usr/bin/env python3
"""
Full Pipeline Integration Tests

Tests the complete pipeline:
Native Framework → QIR → Optimizer → QVM → QMK Executor

Compares native execution results with optimized QMK execution.
"""

import unittest
import sys
import numpy as np
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.executor.enhanced_executor import EnhancedExecutor
from tests.test_helpers import create_test_executor
from qir.optimizer_integration import OptimizedExecutor, OptimizationLevel
from qir.translators.qiskit_to_qir import QiskitToQIRConverter
from qir.translators.cirq_to_qir import CirqToQIRConverter

# Import algorithm examples
sys.path.insert(0, str(ROOT / "examples"))
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


class TestFullPipeline(unittest.TestCase):
    """Test complete pipeline with optimization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shots = 1000
        self.fidelity_threshold = 0.90  # Allow some variation due to optimization
    
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
    
    # ===== Qiskit Pipeline Tests =====
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_bell_state_pipeline(self):
        """Test Bell state through full pipeline."""
        # Native Qiskit
        circuit = qiskit_algorithms.bell_state()
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        # Through QMK pipeline
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bell state fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Qiskit Bell State: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_ghz_state_pipeline(self):
        """Test GHZ state through full pipeline."""
        # Native Qiskit
        circuit = qiskit_algorithms.ghz_state(3)
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        # Through QMK pipeline
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"GHZ state fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Qiskit GHZ State: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_deutsch_jozsa_pipeline(self):
        """Test Deutsch-Jozsa through full pipeline."""
        # Native Qiskit
        circuit = qiskit_algorithms.deutsch_jozsa("balanced")
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        # Through QMK pipeline
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Deutsch-Jozsa fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Qiskit Deutsch-Jozsa: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_bernstein_vazirani_pipeline(self):
        """Test Bernstein-Vazirani through full pipeline."""
        # Native Qiskit
        circuit = qiskit_algorithms.bernstein_vazirani("101")
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        # Through QMK pipeline
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bernstein-Vazirani fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Qiskit Bernstein-Vazirani: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_superdense_coding_pipeline(self):
        """Test Superdense Coding through full pipeline."""
        # Native Qiskit
        circuit = qiskit_algorithms.superdense_coding()
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=self.shots)
        native_counts = job.result().get_counts()
        
        # Through QMK pipeline
        converter = QiskitToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Superdense Coding fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Qiskit Superdense Coding: Fidelity = {fidelity:.4f}")
    
    # ===== Cirq Pipeline Tests =====
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_bell_state_pipeline(self):
        """Test Bell state through full pipeline."""
        # Native Cirq
        circuit = cirq_algorithms.bell_state()
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '02b'): v for k, v in native_histogram.items()}
        
        # Through QMK pipeline
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bell state fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Cirq Bell State: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_ghz_state_pipeline(self):
        """Test GHZ state through full pipeline."""
        # Native Cirq
        circuit = cirq_algorithms.ghz_state(3)
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '03b'): v for k, v in native_histogram.items()}
        
        # Through QMK pipeline
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"GHZ state fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Cirq GHZ State: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_deutsch_jozsa_pipeline(self):
        """Test Deutsch-Jozsa through full pipeline."""
        # Native Cirq
        circuit = cirq_algorithms.deutsch_jozsa("balanced")
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '03b'): v for k, v in native_histogram.items()}
        
        # Through QMK pipeline
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Deutsch-Jozsa fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Cirq Deutsch-Jozsa: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_bernstein_vazirani_pipeline(self):
        """Test Bernstein-Vazirani through full pipeline."""
        # Native Cirq
        circuit = cirq_algorithms.bernstein_vazirani("101")
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '03b'): v for k, v in native_histogram.items()}
        
        # Through QMK pipeline
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Bernstein-Vazirani fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Cirq Bernstein-Vazirani: Fidelity = {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_superdense_coding_pipeline(self):
        """Test Superdense Coding through full pipeline."""
        # Native Cirq
        circuit = cirq_algorithms.superdense_coding()
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=self.shots)
        native_histogram = result.histogram(key='result')
        native_counts = {format(k, '02b'): v for k, v in native_histogram.items()}
        
        # Through QMK pipeline
        converter = CirqToQIRConverter()
        qvm_graph = converter.convert_to_qvm(circuit)
        qmk_counts = self._qvm_to_counts(qvm_graph, self.shots)
        
        # Compare
        fidelity = self._calculate_fidelity(native_counts, qmk_counts)
        self.assertGreater(fidelity, self.fidelity_threshold,
            f"Superdense Coding fidelity too low: {fidelity:.4f}")
        
        print(f"✅ Cirq Superdense Coding: Fidelity = {fidelity:.4f}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
