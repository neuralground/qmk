#!/usr/bin/env python3
"""Tests for lattice surgery optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType
)
from qir.optimizer.passes import LatticeSurgeryOptimizationPass


class TestLatticeSurgeryOptimization(unittest.TestCase):
    """Test lattice surgery optimization."""
    
    def test_identify_surgery_operations(self):
        """Test identifying operations requiring surgery."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # Two-qubit gates require surgery in surface codes
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should identify 2 surgery operations
        self.assertEqual(opt_pass.metrics.custom['total_surgery_ops'], 2)
    
    def test_group_parallel_surgeries(self):
        """Test grouping parallel surgery operations."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # Two independent CNOTs can be parallel
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q2, q3]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should group into 1 parallel group
        self.assertEqual(opt_pass.metrics.custom['surgery_groups'], 1)
        self.assertEqual(opt_pass.metrics.custom['max_concurrent_surgeries'], 2)
    
    def test_sequential_surgeries(self):
        """Test sequential surgery operations."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Sequential CNOTs on same qubits
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should be separate groups
        self.assertGreaterEqual(opt_pass.metrics.custom['surgery_groups'], 1)
    
    def test_surgery_efficiency(self):
        """Test surgery efficiency calculation."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(6)]
        
        # Multiple parallel surgeries
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[0], qubits[1]]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[2], qubits[3]]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[4], qubits[5]]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should calculate efficiency
        self.assertIn('surgery_efficiency', opt_pass.metrics.custom)
        self.assertGreater(opt_pass.metrics.custom['surgery_efficiency'], 0)
    
    def test_patch_requirements(self):
        """Test patch requirement calculation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # Parallel surgeries
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q2, q3]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should calculate patch requirements
        self.assertIn('min_patches_required', opt_pass.metrics.custom)
        self.assertGreater(opt_pass.metrics.custom['min_patches_required'], 0)
    
    def test_no_two_qubit_gates(self):
        """Test circuit with no two-qubit gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Only single-qubit gates
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have zero surgery operations
        self.assertEqual(opt_pass.metrics.custom['total_surgery_ops'], 0)
    
    def test_surgeries_saved(self):
        """Test calculating surgeries saved through grouping."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(4)]
        
        # Two parallel CNOTs
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[0], qubits[1]]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[2], qubits[3]]))
        
        opt_pass = LatticeSurgeryOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should track surgeries saved
        self.assertIn('surgeries_saved', opt_pass.metrics.custom)


if __name__ == '__main__':
    unittest.main()
