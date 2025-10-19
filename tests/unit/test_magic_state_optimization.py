#!/usr/bin/env python3
"""Tests for magic state optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType
)
from kernel.qir_bridge.optimizer.passes import MagicStateOptimizationPass


class TestMagicStateOptimization(unittest.TestCase):
    """Test magic state optimization."""
    
    def test_count_magic_states(self):
        """Test counting magic states needed."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # 5 T gates = 5 magic states
        for _ in range(5):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(opt_pass.metrics.custom['initial_magic_states'], 5)
    
    def test_parallel_t_gates(self):
        """Test identifying parallel T gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # T gates on different qubits can be parallel
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q2]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should identify as one parallel group
        self.assertEqual(opt_pass.metrics.custom['parallel_groups'], 1)
        self.assertEqual(opt_pass.metrics.custom['max_parallel_t_gates'], 3)
    
    def test_sequential_t_gates(self):
        """Test sequential T gates on same qubit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Sequential T gates cannot be parallel
        for _ in range(3):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should be 3 separate groups
        self.assertEqual(opt_pass.metrics.custom['parallel_groups'], 3)
        self.assertEqual(opt_pass.metrics.custom['max_parallel_t_gates'], 1)
    
    def test_mixed_parallel_sequential(self):
        """Test mix of parallel and sequential T gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Round 1: T(q0), T(q1) - parallel
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        # Round 2: T(q0), T(q1) - parallel
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have 2 parallel groups
        self.assertGreaterEqual(opt_pass.metrics.custom['parallel_groups'], 2)
    
    def test_distillation_rounds(self):
        """Test distillation round calculation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # 4 T gates on 2 qubits
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should track distillation rounds
        self.assertIn('distillation_rounds', opt_pass.metrics.custom)
        self.assertGreater(opt_pass.metrics.custom['distillation_rounds'], 0)
    
    def test_factory_efficiency(self):
        """Test magic state factory efficiency calculation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Parallel T gates are more efficient
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should calculate efficiency
        self.assertIn('factory_efficiency', opt_pass.metrics.custom)
        self.assertGreater(opt_pass.metrics.custom['factory_efficiency'], 0)
    
    def test_no_t_gates(self):
        """Test circuit with no T gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have zero magic states
        self.assertEqual(opt_pass.metrics.custom['initial_magic_states'], 0)
    
    def test_dependency_blocking_parallelization(self):
        """Test that dependencies block parallelization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # T(q0) → CNOT(q0,q1) → T(q1)
        # CNOT creates dependency, cannot parallelize
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        opt_pass = MagicStateOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should be separate groups due to dependency
        self.assertGreater(opt_pass.metrics.custom['parallel_groups'], 1)


if __name__ == '__main__':
    unittest.main()
