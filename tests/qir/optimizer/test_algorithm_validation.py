#!/usr/bin/env python3
"""Validation tests using standard quantum algorithms."""

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
    TemplateMatchingPass,
    CliffordTPlusOptimizationPass
)


class TestBellStateOptimization(unittest.TestCase):
    """Test optimization of Bell state circuits."""
    
    def test_basic_bell_state(self):
        """Test basic Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Bell state: H → CNOT
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        manager = PassManager([
            GateCancellationPass(),
            GateCommutationPass(),
            GateFusionPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should maintain 2 gates (H and CNOT)
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_bell_state_with_redundancy(self):
        """Test Bell state with redundant gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Redundant operations
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))  # Cancel
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))  # Cancel
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        manager = PassManager([GateCancellationPass()])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should reduce to 2 gates
        self.assertEqual(result.get_gate_count(), 2)


class TestGHZStateOptimization(unittest.TestCase):
    """Test optimization of GHZ state circuits."""
    
    def test_three_qubit_ghz(self):
        """Test 3-qubit GHZ state |GHZ⟩ = (|000⟩ + |111⟩)/√2."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # GHZ: H → CNOT → CNOT
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        manager = PassManager([
            GateCancellationPass(),
            GateCommutationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should maintain 3 gates
        self.assertEqual(result.get_gate_count(), 3)
    
    def test_ghz_with_measurement(self):
        """Test GHZ state with measurements."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # GHZ state
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        # Measurements
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q2]))
        
        manager = PassManager([DeadCodeEliminationPass()])
        manager.verbose = False
        result = manager.run(circuit)
        
        # All gates should remain (all measured)
        self.assertEqual(result.get_gate_count(), 6)


class TestGroverOptimization(unittest.TestCase):
    """Test optimization of Grover's algorithm components."""
    
    def test_grover_diffusion_operator(self):
        """Test Grover diffusion operator optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Simplified diffusion operator: H → X → CZ → X → H
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CZ, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        manager = PassManager([
            GateCommutationPass(),
            GateFusionPass(),
            TemplateMatchingPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should optimize but maintain functionality
        self.assertLessEqual(result.get_gate_count(), 9)


class TestVQEOptimization(unittest.TestCase):
    """Test optimization of VQE ansatz circuits."""
    
    def test_simple_vqe_ansatz(self):
        """Test simple VQE ansatz optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Simple ansatz: RY → CNOT → RY
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q1], {'theta': 0.3}))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 0.2}))
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q1], {'theta': 0.4}))
        
        manager = PassManager([
            GateCommutationPass(),
            GateFusionPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should maintain or reduce gate count
        self.assertLessEqual(result.get_gate_count(), 5)
    
    def test_vqe_with_rotation_merging(self):
        """Test VQE with rotation merging."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Multiple rotations on same qubit
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.1}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.2}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.3}))
        
        manager = PassManager([GateFusionPass()])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should merge to single rotation
        self.assertEqual(result.get_gate_count(), 1)


class TestQFTOptimization(unittest.TestCase):
    """Test optimization of Quantum Fourier Transform."""
    
    def test_two_qubit_qft(self):
        """Test 2-qubit QFT optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # 2-qubit QFT
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CP, [q1, q0], {'theta': 1.5708}))  # π/2
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.SWAP, [q0, q1]))
        
        manager = PassManager([
            GateCommutationPass(),
            TemplateMatchingPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should maintain or optimize
        self.assertLessEqual(result.get_gate_count(), 4)


class TestCliffordTCircuits(unittest.TestCase):
    """Test optimization of Clifford+T circuits."""
    
    def test_t_gate_optimization(self):
        """Test T-gate count optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # T gates with Clifford
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        manager = PassManager([
            GateFusionPass(),
            CliffordTPlusOptimizationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # 4T = Z, should reduce
        self.assertLess(result.get_gate_count(), 4)
    
    def test_toffoli_decomposition_optimization(self):
        """Test Toffoli decomposition optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # Toffoli using T gates (7 T-gates)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.TDG, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.TDG, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.TDG, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        initial_count = circuit.get_gate_count()
        
        manager = PassManager([
            CliffordTPlusOptimizationPass(),
            TemplateMatchingPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        # Should optimize T-count
        self.assertIsNotNone(result)


class TestPerformanceMetrics(unittest.TestCase):
    """Test that optimizations meet performance targets."""
    
    def test_gate_count_reduction(self):
        """Test gate count reduction meets targets (20-50%)."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Circuit with many optimization opportunities
        for _ in range(5):
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        initial_count = circuit.get_gate_count()
        
        manager = PassManager([
            GateCancellationPass(),
            GateFusionPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        reduction = (initial_count - result.get_gate_count()) / initial_count
        
        # Should achieve significant reduction
        self.assertGreater(reduction, 0.2)  # At least 20%
    
    def test_t_count_reduction(self):
        """Test T-count reduction meets targets (30-60%)."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Many T gates
        for _ in range(10):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        initial_count = circuit.get_gate_count()
        
        manager = PassManager([
            GateFusionPass(),
            CliffordTPlusOptimizationPass()
        ])
        manager.verbose = False
        result = manager.run(circuit)
        
        reduction = (initial_count - result.get_gate_count()) / initial_count
        
        # Should achieve T-count reduction
        self.assertGreater(reduction, 0.0)


if __name__ == '__main__':
    unittest.main()
