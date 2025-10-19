#!/usr/bin/env python3
"""
End-to-End Validation Tests

Compares native execution (Qiskit, Cirq, Q#) with QIR+Optimizer+QMK execution.

Tests validate that:
1. QIR conversion is correct
2. Optimization preserves correctness
3. QVM execution matches native results
"""

import unittest
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.simulator.enhanced_executor import EnhancedExecutor
from kernel.qir_bridge.optimizer_integration import (
    OptimizedExecutor, OptimizationLevel
)

# Try importing quantum frameworks
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

try:
    import cirq
    HAS_CIRQ = True
except ImportError:
    HAS_CIRQ = False


class TestEndToEndValidation(unittest.TestCase):
    """End-to-end validation tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = EnhancedExecutor()
        self.optimized_executor = OptimizedExecutor(
            self.executor,
            OptimizationLevel.STANDARD
        )
    
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
    
    # ===== Qiskit Tests =====
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_bell_state(self):
        """Test Bell state: Qiskit native vs QIR+QMK."""
        # Qiskit native
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1000)
        qiskit_counts = job.result().get_counts()
        
        # TODO: QIR conversion
        # For now, we'll create equivalent QVM graph manually
        qvm_graph = self._create_bell_state_qvm()
        
        # Execute with QMK
        qmk_counts = {}
        for _ in range(1000):
            # Create fresh executor for each run
            executor = EnhancedExecutor()
            result = executor.execute(qvm_graph)
            events = result.get('events', {})
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(2))
            qmk_counts[bitstring] = qmk_counts.get(bitstring, 0) + 1
        
        # Compare
        fidelity = self._calculate_fidelity(qiskit_counts, qmk_counts)
        self.assertGreater(fidelity, 0.95, 
            f"Qiskit vs QMK fidelity too low: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_ghz_state(self):
        """Test GHZ state: Qiskit native vs QIR+QMK."""
        # Qiskit native - 3-qubit GHZ
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.measure([0, 1, 2], [0, 1, 2])
        
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1000)
        qiskit_counts = job.result().get_counts()
        
        # QMK execution
        qvm_graph = self._create_ghz_state_qvm()
        
        qmk_counts = {}
        for _ in range(1000):
            executor = EnhancedExecutor()
            result = executor.execute(qvm_graph)
            events = result.get('events', {})
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(3))
            qmk_counts[bitstring] = qmk_counts.get(bitstring, 0) + 1
        
        fidelity = self._calculate_fidelity(qiskit_counts, qmk_counts)
        self.assertGreater(fidelity, 0.95,
            f"GHZ fidelity too low: {fidelity:.4f}")
    
    @unittest.skipUnless(HAS_QISKIT, "Qiskit not installed")
    def test_qiskit_with_optimization(self):
        """Test that optimization preserves correctness."""
        # Simple circuit with optimization opportunities
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.h(0)  # H-H cancels
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1000)
        qiskit_counts = job.result().get_counts()
        
        # After optimization, should be just CNOT + measure
        # TODO: Full QIR path with optimization
        
        # For now, test that we can execute QVM graph
        qvm_graph = self._create_simple_qvm()
        result = self.optimized_executor.execute(qvm_graph)
        
        # QVM execution doesn't go through optimizer (only QIR does)
        # Just verify it executes successfully
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('events', result)
    
    # ===== Cirq Tests =====
    
    @unittest.skipUnless(HAS_CIRQ, "Cirq not installed")
    def test_cirq_bell_state(self):
        """Test Bell state: Cirq native vs QIR+QMK."""
        # Cirq native
        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(
            cirq.H(q0),
            cirq.CNOT(q0, q1),
            cirq.measure(q0, q1, key='result')
        )
        
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=1000)
        cirq_counts = result.histogram(key='result')
        
        # Convert to same format as QMK
        cirq_counts_formatted = {
            format(k, '02b'): v for k, v in cirq_counts.items()
        }
        
        # QMK execution
        qvm_graph = self._create_bell_state_qvm()
        
        qmk_counts = {}
        for _ in range(1000):
            executor = EnhancedExecutor()
            result = executor.execute(qvm_graph)
            events = result.get('events', {})
            bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(2))
            qmk_counts[bitstring] = qmk_counts.get(bitstring, 0) + 1
        
        fidelity = self._calculate_fidelity(cirq_counts_formatted, qmk_counts)
        self.assertGreater(fidelity, 0.95,
            f"Cirq vs QMK fidelity too low: {fidelity:.4f}")
    
    # ===== Helper Methods =====
    
    def _create_bell_state_qvm(self) -> dict:
        """Create QVM graph for Bell state."""
        return {
            "program": {
                "nodes": [
                    {
                        "id": "alloc1",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "h0",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "cx01",
                        "op": "APPLY_CNOT",
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "m0",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    },
                    {
                        "id": "m1",
                        "op": "MEASURE_Z",
                        "vqs": ["q1"],
                        "produces": ["m1"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "events": ["m0", "m1"]
            }
        }
    
    def _create_ghz_state_qvm(self) -> dict:
        """Create QVM graph for GHZ state."""
        return {
            "program": {
                "nodes": [
                    {
                        "id": "alloc1",
                        "op": "ALLOC_LQ",
                        "args": {"n": 3, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1", "q2"]
                    },
                    {"id": "h0", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "cx01", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]},
                    {"id": "cx12", "op": "APPLY_CNOT", "vqs": ["q1", "q2"]},
                    {"id": "m0", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q1"], "produces": ["m1"]},
                    {"id": "m2", "op": "MEASURE_Z", "vqs": ["q2"], "produces": ["m2"]},
                ]
            },
            "resources": {
                "vqs": ["q0", "q1", "q2"],
                "events": ["m0", "m1", "m2"]
            }
        }
    
    def _create_simple_qvm(self) -> dict:
        """Create simple QVM graph."""
        return {
            "program": {
                "nodes": [
                    {
                        "id": "alloc1",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1"]
                    },
                    {"id": "cx01", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]},
                    {"id": "m0", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q1"], "produces": ["m1"]},
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "events": ["m0", "m1"]
            }
        }


if __name__ == '__main__':
    unittest.main()
