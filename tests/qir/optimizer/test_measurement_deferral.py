#!/usr/bin/env python3
"""Tests for measurement deferral."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from qir.optimizer.passes import MeasurementDeferralPass


class TestMeasurementDeferral(unittest.TestCase):
    """Test measurement deferral optimization."""
    
    def test_defer_single_measurement(self):
        """Test deferring a single measurement."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H → MEASURE → X (on different qubit)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Measurement should be at the end
        self.assertEqual(result.instructions[-1].inst_type, InstructionType.MEASURE)
        self.assertEqual(opt_pass.metrics.custom.get('measurements_deferred', 0), 1)
    
    def test_cannot_defer_if_qubit_used_after(self):
        """Test that measurement cannot be deferred if qubit is used after."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H → MEASURE → X (on same qubit)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        # Find measurement position before
        meas_idx_before = None
        for i, inst in enumerate(circuit.instructions):
            if inst.is_measurement():
                meas_idx_before = i
                break
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Find measurement position after
        meas_idx_after = None
        for i, inst in enumerate(result.instructions):
            if inst.is_measurement():
                meas_idx_after = i
                break
        
        # Should not have moved
        self.assertEqual(meas_idx_before, meas_idx_after)
        self.assertEqual(opt_pass.metrics.custom.get('measurements_deferred', 0), 0)
    
    def test_defer_multiple_measurements(self):
        """Test deferring multiple measurements."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H(q0) → MEASURE(q0) → H(q1) → MEASURE(q1)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Both measurements should be at the end
        self.assertTrue(result.instructions[-2].is_measurement())
        self.assertTrue(result.instructions[-1].is_measurement())
        self.assertEqual(opt_pass.metrics.custom.get('measurements_deferred', 0), 2)
    
    def test_measurement_already_at_end(self):
        """Test that measurements already at end are not counted."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Should still be at end
        self.assertEqual(result.instructions[-1].inst_type, InstructionType.MEASURE)
    
    def test_mixed_deferrable_and_non_deferrable(self):
        """Test circuit with both deferrable and non-deferrable measurements."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # q0: H → MEASURE → X (cannot defer, qubit used after)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        # q1: H → MEASURE (can defer)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Only q1 measurement should be deferred
        self.assertEqual(opt_pass.metrics.custom.get('measurements_deferred', 0), 1)
    
    def test_no_measurements(self):
        """Test circuit with no measurements."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        initial_count = len(circuit.instructions)
        
        opt_pass = MeasurementDeferralPass()
        result = opt_pass.run(circuit)
        
        # Should not change anything
        self.assertEqual(len(result.instructions), initial_count)
    
    def test_enables_further_optimization(self):
        """Test that deferral enables further optimizations."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H(q0) → MEASURE(q0) → H(q1) → H(q1)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        # Run deferral then cancellation
        from qir.optimizer.passes import GateCancellationPass
        
        manager = PassManager([
            MeasurementDeferralPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # H-H should cancel, measurement at end
        self.assertEqual(result.get_gate_count(), 1)  # Just H(q0)
        self.assertTrue(result.instructions[-1].is_measurement())


if __name__ == '__main__':
    unittest.main()
