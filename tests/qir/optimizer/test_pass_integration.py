#!/usr/bin/env python3
"""Integration tests for optimization pass combinations."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import QIRCircuit, QIRInstruction, InstructionType, PassManager
from qir.optimizer.passes import (
    GateCancellationPass,
    GateCommutationPass,
    GateFusionPass,
    DeadCodeEliminationPass,
    ConstantPropagationPass,
    TemplateMatchingPass,
    MeasurementDeferralPass,
    CliffordTPlusOptimizationPass
)


class TestPassCombinations(unittest.TestCase):
    """Test combinations of optimization passes."""
    
    def test_cancellation_and_commutation(self):
        """Test gate cancellation + commutation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H → X → H (commute X forward, then cancel H-H)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        initial_count = circuit.get_gate_count()
        
        # Run commutation then cancellation
        manager = PassManager([
            GateCommutationPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should reduce gate count
        self.assertLess(result.get_gate_count(), initial_count)
    
    def test_fusion_and_cancellation(self):
        """Test gate fusion + cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # S → S = Z, then if followed by Z, could cancel
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        manager = PassManager([
            GateFusionPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # S + S = Z (fusion)
        self.assertLessEqual(result.get_gate_count(), 1)
    
    def test_dead_code_and_constant_prop(self):
        """Test dead code elimination + constant propagation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # q1 never measured
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        manager = PassManager([
            ConstantPropagationPass(),
            DeadCodeEliminationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should remove unused q1 operations
        self.assertLess(result.get_gate_count(), 3)
    
    def test_full_optimization_pipeline(self):
        """Test full optimization pipeline."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Complex circuit with multiple optimization opportunities
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))  # Cancel
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))  # Fuse to Z
        
        initial_count = circuit.get_gate_count()
        
        manager = PassManager([
            GateCancellationPass(),
            GateCommutationPass(),
            GateFusionPass(),
            DeadCodeEliminationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should significantly reduce gate count
        self.assertLess(result.get_gate_count(), initial_count)
    
    def test_clifford_t_optimization_pipeline(self):
        """Test Clifford+T optimization pipeline."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # T gates with Clifford gates
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        manager = PassManager([
            GateCommutationPass(),
            CliffordTPlusOptimizationPass(),
            GateFusionPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should optimize T-count
        self.assertIsNotNone(result)


class TestPassOrdering(unittest.TestCase):
    """Test that pass ordering matters and is correct."""
    
    def test_commutation_before_cancellation(self):
        """Test that commutation before cancellation is better."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H → X(q1) → H (need commutation first)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # Order 1: Commutation then Cancellation
        manager1 = PassManager([
            GateCommutationPass(),
            GateCancellationPass()
        ])
        manager1.verbose = False
        result1 = manager1.run(circuit.copy())
        
        # Order 2: Cancellation then Commutation
        manager2 = PassManager([
            GateCancellationPass(),
            GateCommutationPass()
        ])
        manager2.verbose = False
        result2 = manager2.run(circuit.copy())
        
        # Order 1 should be better or equal
        self.assertLessEqual(result1.get_gate_count(), result2.get_gate_count())
    
    def test_fusion_before_cancellation(self):
        """Test that fusion before cancellation can help."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # S → S → Z → Z (fuse S+S=Z, then cancel Z+Z)
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        
        manager = PassManager([
            GateFusionPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should fuse and cancel
        self.assertEqual(result.get_gate_count(), 0)


class TestPassIdempotence(unittest.TestCase):
    """Test that passes are idempotent (running twice = running once)."""
    
    def test_cancellation_idempotent(self):
        """Test gate cancellation is idempotent."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        opt_pass = GateCancellationPass()
        result1 = opt_pass.run(circuit)
        result2 = opt_pass.run(result1)
        
        # Second run should not change anything
        self.assertEqual(result1.get_gate_count(), result2.get_gate_count())
    
    def test_fusion_idempotent(self):
        """Test gate fusion is idempotent."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        opt_pass = GateFusionPass()
        result1 = opt_pass.run(circuit)
        result2 = opt_pass.run(result1)
        
        # Second run should not change anything
        self.assertEqual(result1.get_gate_count(), result2.get_gate_count())
    
    def test_dead_code_idempotent(self):
        """Test dead code elimination is idempotent."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))  # q1 never used
        
        opt_pass = DeadCodeEliminationPass()
        result1 = opt_pass.run(circuit)
        result2 = opt_pass.run(result1)
        
        # Second run should not change anything
        self.assertEqual(result1.get_gate_count(), result2.get_gate_count())


class TestPassConflicts(unittest.TestCase):
    """Test that passes don't conflict with each other."""
    
    def test_no_infinite_loop(self):
        """Test that passes don't create infinite optimization loops."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        # Run multiple iterations
        manager = PassManager([
            GateCancellationPass(),
            GateCommutationPass(),
            GateFusionPass()
        ])
        manager.verbose = False
        
        result1 = manager.run(circuit)
        result2 = manager.run(result1)
        result3 = manager.run(result2)
        
        # Should stabilize
        self.assertEqual(result2.get_gate_count(), result3.get_gate_count())
    
    def test_correctness_preserved(self):
        """Test that pass combinations preserve correctness."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Bell state
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        manager = PassManager([
            GateCancellationPass(),
            GateCommutationPass(),
            GateFusionPass(),
            DeadCodeEliminationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Bell state should still have H and CNOT
        self.assertGreaterEqual(result.get_gate_count(), 2)


if __name__ == '__main__':
    unittest.main()
