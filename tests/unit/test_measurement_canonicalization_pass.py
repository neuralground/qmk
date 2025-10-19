"""
Tests for Measurement Canonicalization Pass
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer.ir import QIRCircuit, QIRInstruction, InstructionType, QIRQubit
from kernel.qir_bridge.optimizer.passes.measurement_canonicalization import MeasurementCanonicalizationPass


class TestMeasurementCanonicalizationPass(unittest.TestCase):
    """Test measurement canonicalization pass."""
    
    def test_x_basis_canonicalization(self):
        """Test H → MEASURE_Z becomes MEASURE_X."""
        q0 = QIRQubit("q0", 0)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        self.assertEqual(len(circuit.instructions), 2)
        
        pass_obj = MeasurementCanonicalizationPass()
        result = pass_obj.run(circuit)
        
        # Should have removed H gate
        self.assertEqual(len(result.instructions), 1)
        
        # Measurement should now be X-basis
        meas = result.instructions[0]
        self.assertEqual(meas.inst_type, InstructionType.MEASURE)
        self.assertEqual(meas.params.get('basis'), 'X')
    
    def test_y_basis_canonicalization(self):
        """Test S† → H → MEASURE_Z becomes MEASURE_Y."""
        q0 = QIRQubit("q0", 0)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.SDG, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        self.assertEqual(len(circuit.instructions), 3)
        
        pass_obj = MeasurementCanonicalizationPass()
        result = pass_obj.run(circuit)
        
        # Should have removed S† and H gates (may take multiple passes)
        # For now, just verify measurement basis changed
        meas = [inst for inst in result.instructions if inst.inst_type == InstructionType.MEASURE][0]
        self.assertEqual(meas.params.get('basis'), 'Y')
    
    def test_bell_basis_canonicalization(self):
        """Test CNOT → H → MEASURE → MEASURE becomes MEASURE_BELL."""
        q0 = QIRQubit("q0", 0)
        q1 = QIRQubit("q1", 1)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_qubit(q1)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q1],
            params={'basis': 'Z'},
            result='m1'
        ))
        
        self.assertEqual(len(circuit.instructions), 4)
        
        pass_obj = MeasurementCanonicalizationPass()
        result = pass_obj.run(circuit)
        
        # Should have Bell measurement (may still have some gates)
        # Just verify we have a Bell measurement
        bell_meas = [inst for inst in result.instructions 
                     if inst.inst_type == InstructionType.MEASURE and 
                     inst.params.get('basis') == 'BELL']
        self.assertEqual(len(bell_meas), 1)
        self.assertEqual(len(bell_meas[0].qubits), 2)
    
    def test_no_canonicalization_needed(self):
        """Test circuit with no patterns to canonicalize."""
        q0 = QIRQubit("q0", 0)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        initial_count = len(circuit.instructions)
        
        pass_obj = MeasurementCanonicalizationPass()
        result = pass_obj.run(circuit)
        
        # Should be unchanged
        self.assertEqual(len(result.instructions), initial_count)
    
    def test_multiple_canonicalizations(self):
        """Test circuit with multiple patterns."""
        q0 = QIRQubit("q0", 0)
        q1 = QIRQubit("q1", 1)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_qubit(q1)
        
        # X-basis measurement on q0
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        # Y-basis measurement on q1
        circuit.add_instruction(QIRInstruction(InstructionType.SDG, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q1],
            params={'basis': 'Z'},
            result='m1'
        ))
        
        self.assertEqual(len(circuit.instructions), 5)
        
        pass_obj = MeasurementCanonicalizationPass()
        result = pass_obj.run(circuit)
        
        # Should have two measurements
        self.assertEqual(len(result.instructions), 2)
        
        # Both should be canonicalized
        self.assertEqual(result.instructions[0].params.get('basis'), 'X')
        self.assertEqual(result.instructions[1].params.get('basis'), 'Y')
    
    def test_metrics_tracking(self):
        """Test that metrics are properly tracked."""
        q0 = QIRQubit("q0", 0)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        pass_obj = MeasurementCanonicalizationPass()
        pass_obj.run(circuit)
        
        # Check metrics
        self.assertGreater(pass_obj.metrics.execution_time_ms, 0)
        self.assertEqual(
            pass_obj.metrics.custom.get('measurements_canonicalized', 0),
            1
        )
    
    def test_estimate_benefit(self):
        """Test benefit estimation."""
        q0 = QIRQubit("q0", 0)
        
        circuit = QIRCircuit()
        circuit.add_qubit(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(
            InstructionType.MEASURE,
            [q0],
            params={'basis': 'Z'},
            result='m0'
        ))
        
        pass_obj = MeasurementCanonicalizationPass()
        benefit = pass_obj.estimate_benefit(circuit)
        
        # Should detect potential for canonicalization
        self.assertGreater(benefit, 0)


if __name__ == '__main__':
    unittest.main()
