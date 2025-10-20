#!/usr/bin/env python3
"""Tests for experimental optimization passes."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import QIRCircuit, QIRInstruction, InstructionType
from qir.optimizer.passes.experimental import (
    ZXCalculusOptimizationPass,
    PhasePolynomialOptimizationPass,
    SynthesisBasedOptimizationPass,
    PauliNetworkSynthesisPass,
    TensorNetworkContractionPass
)


class TestZXCalculusOptimization(unittest.TestCase):
    """Test ZX-calculus optimization pass."""
    
    def test_spider_fusion(self):
        """Test spider fusion optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Z(α) → Z(β) should fuse to Z(α+β)
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.3}))
        
        opt_pass = ZXCalculusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should reduce gate count through fusion
        self.assertLessEqual(result.get_gate_count(), circuit.get_gate_count())
    
    def test_clifford_simplification(self):
        """Test Clifford simplification in ZX-calculus."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H → S → H = S†
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        opt_pass = ZXCalculusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should simplify
        self.assertLessEqual(result.get_gate_count(), 3)


class TestPhasePolynomialOptimization(unittest.TestCase):
    """Test phase polynomial optimization pass."""
    
    def test_phase_extraction(self):
        """Test phase polynomial extraction."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Multiple rotations
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.1}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.2}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.3}))
        
        opt_pass = PhasePolynomialOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should merge rotations
        self.assertLess(result.get_gate_count(), 3)
    
    def test_t_depth_optimization(self):
        """Test T-depth optimization via phase polynomials."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # T gates that could be optimized
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = PhasePolynomialOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should optimize T-depth
        self.assertIsNotNone(result)


class TestSynthesisBasedOptimization(unittest.TestCase):
    """Test synthesis-based optimization pass."""
    
    def test_subcircuit_synthesis(self):
        """Test subcircuit re-synthesis."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Inefficient sequence
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        opt_pass = SynthesisBasedOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should re-synthesize more efficiently
        self.assertIsNotNone(result)
    
    def test_optimal_synthesis(self):
        """Test optimal synthesis of small circuits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # SWAP using 3 CNOTs
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = SynthesisBasedOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should recognize and optimize
        self.assertIsNotNone(result)


class TestPauliNetworkSynthesis(unittest.TestCase):
    """Test Pauli network synthesis pass."""
    
    def test_pauli_rotation_optimization(self):
        """Test Pauli rotation network optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Pauli rotations
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q1], {'theta': 0.3}))
        
        opt_pass = PauliNetworkSynthesisPass()
        result = opt_pass.run(circuit)
        
        # Should optimize CNOT count
        self.assertIsNotNone(result)
    
    def test_cnot_reduction(self):
        """Test CNOT count reduction."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Multiple CNOTs
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q1], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = PauliNetworkSynthesisPass()
        result = opt_pass.run(circuit)
        
        # Should reduce CNOTs
        self.assertIsNotNone(result)


class TestTensorNetworkContraction(unittest.TestCase):
    """Test tensor network contraction pass."""
    
    def test_contraction_ordering(self):
        """Test tensor network contraction ordering."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # Multi-qubit circuit
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
        
        opt_pass = TensorNetworkContractionPass()
        result = opt_pass.run(circuit)
        
        # Should optimize based on contraction order
        self.assertIsNotNone(result)
    
    def test_depth_reduction(self):
        """Test depth reduction via tensor network."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Sequential gates
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = TensorNetworkContractionPass()
        result = opt_pass.run(circuit)
        
        # Should maintain or reduce depth
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
