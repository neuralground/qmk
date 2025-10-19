#!/usr/bin/env python3
"""Tests for gate fusion optimization."""

import unittest
import sys
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from qir.optimizer.passes import (
    GateFusionPass, GateCancellationPass, GateCommutationPass
)


class TestGateFusion(unittest.TestCase):
    """Test gate fusion optimization."""
    
    def test_s_s_fusion(self):
        """Test S → S = Z fusion."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # S → S
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 2)
        
        # Run fusion
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should fuse to Z
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.Z)
    
    def test_t_t_fusion(self):
        """Test T → T = S fusion."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # T → T
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should fuse to S
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.S)
    
    def test_rz_fusion(self):
        """Test RZ(θ₁) → RZ(θ₂) = RZ(θ₁+θ₂) fusion."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # RZ(π/4) → RZ(π/4)
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': math.pi/4}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': math.pi/4}))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should fuse to RZ(π/2)
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.RZ)
        self.assertAlmostEqual(result.instructions[0].params['theta'], math.pi/2, places=10)
    
    def test_rx_fusion(self):
        """Test RX fusion."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.RX, [q0], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.RX, [q0], {'theta': 0.3}))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 1)
        self.assertAlmostEqual(result.instructions[0].params['theta'], 0.8, places=10)
    
    def test_ry_fusion(self):
        """Test RY fusion."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 1.0}))
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 0.5}))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 1)
        self.assertAlmostEqual(result.instructions[0].params['theta'], 1.5, places=10)
    
    def test_no_fusion_different_qubits(self):
        """Test that gates on different qubits don't fuse."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q1]))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should not fuse
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_no_fusion_different_gates(self):
        """Test that different gate types don't fuse."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should not fuse
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_multiple_fusions(self):
        """Test multiple fusion opportunities."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # S → S on q0 (fuse to Z)
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        # T → T on q1 (fuse to S)
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        self.assertEqual(circuit.get_gate_count(), 4)
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should have 2 gates (Z and S)
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_iterative_fusion(self):
        """Test that fusion can happen iteratively."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # T → T → T → T should become S → S then Z
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 4)
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should fuse to Z
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.Z)
    
    def test_rotation_angle_normalization(self):
        """Test that rotation angles are normalized."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # RZ(π) → RZ(π) = RZ(2π) which should normalize
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': math.pi}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': math.pi}))
        
        opt_pass = GateFusionPass()
        result = opt_pass.run(circuit)
        
        # Should still have 1 gate with normalized angle
        self.assertEqual(result.get_gate_count(), 1)


class TestFusionWithOtherPasses(unittest.TestCase):
    """Test fusion combined with other optimization passes."""
    
    def test_fusion_with_cancellation(self):
        """Test fusion enabling cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # S → S → Z → Z
        # After fusion: Z → Z
        # After cancellation: (empty)
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 4)
        
        # Run fusion then cancellation
        manager = PassManager([
            GateFusionPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # After fusion: Z → Z → Z (S→S fuses to Z, plus two existing Z)
        # After cancellation: Z (two Z's cancel, one remains)
        self.assertEqual(result.get_gate_count(), 1)
    
    def test_full_phase1_pipeline(self):
        """Test all Phase 1 passes together."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Complex circuit with multiple optimization opportunities
        # S → S (fuse to Z)
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        # X on different qubit
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        # Z → Z (cancel)
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        
        # H → H (cancel)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        self.assertEqual(circuit.get_gate_count(), 7)
        
        # Run all Phase 1 passes
        manager = PassManager([
            GateCommutationPass(),
            GateFusionPass(),
            GateCancellationPass(),
            # Run again for more opportunities
            GateCommutationPass(),
            GateFusionPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # Should significantly reduce
        self.assertLess(result.get_gate_count(), 7)


if __name__ == '__main__':
    unittest.main()
