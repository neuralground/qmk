#!/usr/bin/env python3
"""Tests for SWAP insertion."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import QIRCircuit, QIRInstruction, InstructionType
from kernel.qir_bridge.optimizer.topology import HardwareTopology
from kernel.qir_bridge.optimizer.passes import SWAPInsertionPass


class TestHardwareTopology(unittest.TestCase):
    """Test hardware topology representation."""
    
    def test_linear_topology(self):
        """Test linear topology creation."""
        topo = HardwareTopology.linear(5)
        
        self.assertEqual(topo.num_qubits, 5)
        self.assertTrue(topo.are_connected(0, 1))
        self.assertTrue(topo.are_connected(1, 2))
        self.assertFalse(topo.are_connected(0, 2))
    
    def test_all_to_all_topology(self):
        """Test all-to-all topology."""
        topo = HardwareTopology.all_to_all(4)
        
        # Every qubit should be connected to every other
        for i in range(4):
            for j in range(4):
                if i != j:
                    self.assertTrue(topo.are_connected(i, j))
    
    def test_grid_topology(self):
        """Test 2D grid topology."""
        topo = HardwareTopology.grid(2, 3)  # 2x3 grid
        
        self.assertEqual(topo.num_qubits, 6)
        # Horizontal connections
        self.assertTrue(topo.are_connected(0, 1))
        self.assertTrue(topo.are_connected(1, 2))
        # Vertical connections
        self.assertTrue(topo.are_connected(0, 3))
        self.assertTrue(topo.are_connected(1, 4))
        # No diagonal
        self.assertFalse(topo.are_connected(0, 4))
    
    def test_distance_calculation(self):
        """Test shortest path distance."""
        topo = HardwareTopology.linear(5)
        
        self.assertEqual(topo.get_distance(0, 0), 0)
        self.assertEqual(topo.get_distance(0, 1), 0)  # Adjacent
        self.assertEqual(topo.get_distance(0, 2), 1)  # One SWAP needed
        self.assertEqual(topo.get_distance(0, 4), 3)  # Three SWAPs needed
    
    def test_find_path(self):
        """Test path finding."""
        topo = HardwareTopology.linear(5)
        
        path = topo.find_path(0, 3)
        self.assertEqual(path, [0, 1, 2, 3])
        
        path = topo.find_path(2, 2)
        self.assertEqual(path, [2])


class TestSWAPInsertion(unittest.TestCase):
    """Test SWAP insertion optimization."""
    
    def test_no_swaps_needed_all_to_all(self):
        """Test that no SWAPs are needed for all-to-all topology."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        topo = HardwareTopology.all_to_all(2)
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # Should not add any SWAPs
        self.assertEqual(opt_pass.metrics.swap_gates_added, 0)
        self.assertEqual(result.get_gate_count(), 1)
    
    def test_swap_insertion_linear_topology(self):
        """Test SWAP insertion for linear topology."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # CNOT between q0 and q2 (not adjacent in linear topology)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        topo = HardwareTopology.linear(3)  # 0-1-2
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # Should add SWAPs
        self.assertGreater(opt_pass.metrics.swap_gates_added, 0)
        self.assertGreater(result.get_gate_count(), 1)
    
    def test_adjacent_qubits_no_swap(self):
        """Test that adjacent qubits don't need SWAPs."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        topo = HardwareTopology.linear(2)
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # No SWAPs needed
        self.assertEqual(opt_pass.metrics.swap_gates_added, 0)
    
    def test_multiple_two_qubit_gates(self):
        """Test SWAP insertion with multiple two-qubit gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # Multiple CNOTs on linear topology
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))  # Adjacent
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q3]))  # Not adjacent
        
        topo = HardwareTopology.linear(4)
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # Should add SWAPs for second CNOT
        self.assertGreater(opt_pass.metrics.swap_gates_added, 0)
    
    def test_single_qubit_gates_unchanged(self):
        """Test that single-qubit gates are not affected."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        initial_count = circuit.get_gate_count()
        
        topo = HardwareTopology.linear(2)
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # Gate count should be unchanged
        self.assertEqual(result.get_gate_count(), initial_count)
    
    def test_grid_topology(self):
        """Test SWAP insertion on grid topology."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # CNOT on opposite corners of 2x2 grid (0 and 3 are diagonal)
        # Grid layout: 0-1
        #              2-3
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q3]))
        
        topo = HardwareTopology.grid(2, 2)
        opt_pass = SWAPInsertionPass(topo)
        result = opt_pass.run(circuit)
        
        # Should add SWAPs (diagonal not connected)
        self.assertGreater(opt_pass.metrics.swap_gates_added, 0)


if __name__ == '__main__':
    unittest.main()
