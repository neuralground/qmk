#!/usr/bin/env python3
"""Tests for optimization framework."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, QIRQubit,
    InstructionType, OptimizationPass, PassManager,
    OptimizationMetrics
)


class TestQIRCircuit(unittest.TestCase):
    """Test IR circuit representation."""
    
    def test_create_circuit(self):
        """Test creating a basic circuit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        self.assertEqual(len(circuit.qubits), 2)
        self.assertIsNotNone(circuit.get_qubit('q0'))
        self.assertIsNotNone(circuit.get_qubit('q1'))
    
    def test_add_instructions(self):
        """Test adding instructions."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        h_inst = QIRInstruction(InstructionType.H, [q0])
        circuit.add_instruction(h_inst)
        
        self.assertEqual(len(circuit.instructions), 1)
        self.assertEqual(circuit.get_gate_count(), 1)
    
    def test_gate_count(self):
        """Test gate counting."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        self.assertEqual(circuit.get_gate_count(), 2)  # H and CNOT
        self.assertEqual(circuit.get_cnot_count(), 1)
    
    def test_circuit_depth(self):
        """Test depth calculation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Sequential gates on same qubit
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        # Parallel gate on different qubit
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        depth = circuit.get_depth()
        self.assertGreater(depth, 0)
    
    def test_clone_circuit(self):
        """Test circuit cloning."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        cloned = circuit.clone()
        
        self.assertEqual(len(cloned.qubits), len(circuit.qubits))
        self.assertEqual(len(cloned.instructions), len(circuit.instructions))
        self.assertIsNot(cloned, circuit)


class TestQIRInstruction(unittest.TestCase):
    """Test IR instruction representation."""
    
    def test_instruction_properties(self):
        """Test instruction property checks."""
        q0 = QIRQubit('q0', 0)
        q1 = QIRQubit('q1', 1)
        
        h_inst = QIRInstruction(InstructionType.H, [q0])
        self.assertTrue(h_inst.is_gate())
        self.assertTrue(h_inst.is_single_qubit_gate())
        self.assertFalse(h_inst.is_two_qubit_gate())
        
        cnot_inst = QIRInstruction(InstructionType.CNOT, [q0, q1])
        self.assertTrue(cnot_inst.is_gate())
        self.assertFalse(cnot_inst.is_single_qubit_gate())
        self.assertTrue(cnot_inst.is_two_qubit_gate())
        
        meas_inst = QIRInstruction(InstructionType.MEASURE, [q0], result='m0')
        self.assertFalse(meas_inst.is_gate())
        self.assertTrue(meas_inst.is_measurement())
    
    def test_instruction_inverse(self):
        """Test getting instruction inverses."""
        q0 = QIRQubit('q0', 0)
        
        # Self-inverse gates
        h_inst = QIRInstruction(InstructionType.H, [q0])
        h_inv = h_inst.inverse()
        self.assertIsNotNone(h_inv)
        self.assertEqual(h_inv.inst_type, InstructionType.H)
        
        # S and S†
        s_inst = QIRInstruction(InstructionType.S, [q0])
        s_inv = s_inst.inverse()
        self.assertEqual(s_inv.inst_type, InstructionType.SDG)
        
        # T and T†
        t_inst = QIRInstruction(InstructionType.T, [q0])
        t_inv = t_inst.inverse()
        self.assertEqual(t_inv.inst_type, InstructionType.TDG)


class DummyPass(OptimizationPass):
    """Dummy pass for testing."""
    
    def __init__(self):
        super().__init__("DummyPass")
        self.run_count = 0
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        self.run_count += 1
        self.metrics.gates_removed = 1
        return circuit


class TestPassManager(unittest.TestCase):
    """Test pass manager."""
    
    def test_add_pass(self):
        """Test adding passes."""
        manager = PassManager()
        pass1 = DummyPass()
        
        manager.add_pass(pass1)
        self.assertEqual(len(manager.passes), 1)
    
    def test_run_passes(self):
        """Test running passes."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        pass1 = DummyPass()
        manager = PassManager([pass1])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        self.assertEqual(pass1.run_count, 1)
        self.assertIsNotNone(result)
    
    def test_disable_pass(self):
        """Test disabling passes."""
        circuit = QIRCircuit()
        
        pass1 = DummyPass()
        manager = PassManager([pass1])
        manager.disable_pass("DummyPass")
        
        manager.run(circuit)
        
        self.assertEqual(pass1.run_count, 0)  # Should not run


class TestOptimizationMetrics(unittest.TestCase):
    """Test metrics tracking."""
    
    def test_metrics_creation(self):
        """Test creating metrics."""
        metrics = OptimizationMetrics()
        self.assertEqual(metrics.gates_removed, 0)
        self.assertEqual(metrics.gates_added, 0)
    
    def test_net_changes(self):
        """Test calculating net changes."""
        metrics = OptimizationMetrics()
        metrics.gates_removed = 5
        metrics.gates_added = 2
        
        self.assertEqual(metrics.net_gate_change(), -3)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dict."""
        metrics = OptimizationMetrics()
        metrics.gates_removed = 3
        
        d = metrics.to_dict()
        self.assertIn('gates_removed', d)
        self.assertEqual(d['gates_removed'], 3)


if __name__ == '__main__':
    unittest.main()
