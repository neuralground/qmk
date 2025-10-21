#!/usr/bin/env python3
"""
Validation tests for optimizations.

Ensures optimized circuits produce the same results as unoptimized circuits
when executed through both native and QMK paths.
"""

import unittest
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager,
    IRToQVMConverter
)
from qir.optimizer.passes import GateCancellationPass, GateCommutationPass
from kernel.executor.enhanced_executor import EnhancedExecutor
from tests.test_helpers import create_test_executor

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class TestGateCancellationValidation(unittest.TestCase):
    """Validate gate cancellation against native execution."""
    
    @unittest.skip("Qiskit to QVM conversion has verification errors - needs fixing")
    def test_bell_state_with_redundancy(self):
        """
        Test Bell state with redundant gates.
        
        Validates that optimization doesn't change measurement distribution.
        """
        # Create circuit with redundancy
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Redundant H → H at start (should cancel)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # Actual Bell state
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        # Measurements
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        # Run unoptimized
        unopt_counts = self._run_qmk(circuit, shots=500)
        
        # Run optimized
        opt_circuit = circuit.clone()
        manager = PassManager([GateCancellationPass()])
        manager.verbose = False
        opt_circuit = manager.run(opt_circuit)
        
        opt_counts = self._run_qmk(opt_circuit, shots=500)
        
        # Calculate fidelity
        fidelity = self._calculate_fidelity(unopt_counts, opt_counts)
        
        # Should be very high fidelity
        self.assertGreater(fidelity, 0.95, 
            f"Fidelity too low: {fidelity:.4f}")
        
        # Check correlation (Bell state should be 00 or 11)
        unopt_corr = self._check_correlation(unopt_counts, ['00', '11'])
        opt_corr = self._check_correlation(opt_counts, ['00', '11'])
        
        self.assertGreater(unopt_corr, 0.90, "Unoptimized correlation too low")
        self.assertGreater(opt_corr, 0.90, "Optimized correlation too low")
    
    @unittest.skip("Qiskit to QVM conversion has verification errors - needs fixing")
    def test_optimized_vs_qiskit(self):
        """
        Compare optimized QMK execution with Qiskit.
        
        Validates that optimization maintains correctness.
        """
        # Create Qiskit circuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.h(0)  # Redundant
        qc.h(0)  # Actual
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        # Run on Qiskit
        simulator = AerSimulator()
        job = simulator.run(qc, shots=500)
        qiskit_counts = job.result().get_counts()
        
        # Create equivalent IR circuit
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        # Optimize
        manager = PassManager([GateCancellationPass()])
        manager.verbose = False
        opt_circuit = manager.run(circuit)
        
        # Run on QMK
        qmk_counts = self._run_qmk(opt_circuit, shots=500)
        
        # Compare
        fidelity = self._calculate_fidelity(qiskit_counts, qmk_counts)
        
        self.assertGreater(fidelity, 0.90,
            f"Qiskit vs QMK fidelity too low: {fidelity:.4f}")
    
    def test_gate_count_reduction(self):
        """Test that optimization actually reduces gate count."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Add many redundant gates
        for _ in range(5):
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        initial_count = circuit.get_gate_count()
        self.assertEqual(initial_count, 10)
        
        # Optimize
        manager = PassManager([GateCancellationPass()])
        manager.verbose = False
        opt_circuit = manager.run(circuit)
        
        final_count = opt_circuit.get_gate_count()
        self.assertEqual(final_count, 0)
        
        # Check metrics
        summary = manager.get_summary()
        self.assertEqual(summary['passes'][0]['metrics']['gates_removed'], 10)
    
    # Helper methods
    
    def _run_qmk(self, circuit: QIRCircuit, shots: int = 500) -> dict:
        """Run circuit on QMK."""
        # Convert to QVM
        converter = IRToQVMConverter()
        qvm_graph = converter.convert(circuit)
        
        # Execute
        executor = create_test_executor()
        counts = {}
        
        for _ in range(shots):
            result = executor.execute(qvm_graph)
            events = result.get('events', {})
            bitstring = ''.join(str(events.get(f'm{i}', 0)) 
                              for i in range(len(events)))
            counts[bitstring] = counts.get(bitstring, 0) + 1
        
        return counts
    
    def _calculate_fidelity(self, counts1: dict, counts2: dict) -> float:
        """Calculate fidelity between two distributions."""
        all_bitstrings = set(counts1.keys()) | set(counts2.keys())
        shots1 = sum(counts1.values())
        shots2 = sum(counts2.values())
        
        fidelity = 0
        for bs in all_bitstrings:
            p1 = counts1.get(bs, 0) / shots1
            p2 = counts2.get(bs, 0) / shots2
            fidelity += np.sqrt(p1 * p2)
        
        return fidelity
    
    def _check_correlation(self, counts: dict, expected_states: list) -> float:
        """Check correlation for expected states."""
        total = sum(counts.values())
        correlated = sum(counts.get(state, 0) for state in expected_states)
        return correlated / total


if __name__ == '__main__':
    unittest.main()
