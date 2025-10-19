#!/usr/bin/env python3
"""Tests for qubit mapping."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import QIRCircuit, QIRInstruction, InstructionType
from kernel.qir_bridge.optimizer.topology import HardwareTopology
from kernel.qir_bridge.optimizer.passes import QubitMappingPass


class TestQubitMapping(unittest.TestCase):
    """Test qubit mapping optimization."""
    
    def test_identity_mapping_no_interactions(self):
        """Test that without interactions, uses identity mapping."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # No two-qubit gates
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        topo = HardwareTopology.linear(2)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        # Should create a mapping
        self.assertIn('qubit_mapping', result.metadata)
        mapping = result.metadata['qubit_mapping']
        self.assertEqual(len(mapping), 2)
    
    def test_adjacent_placement_for_interacting_qubits(self):
        """Test that interacting qubits are placed adjacent."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # q0 and q1 interact
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        topo = HardwareTopology.linear(2)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        mapping = result.metadata['qubit_mapping']
        phys0 = mapping[q0]
        phys1 = mapping[q1]
        
        # Should be adjacent (distance 0)
        self.assertEqual(topo.get_distance(phys0, phys1), 0)
    
    def test_frequent_interactions_prioritized(self):
        """Test that frequently interacting qubits are prioritized."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # q0-q1 interact 3 times
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        # q1-q2 interact 1 time
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
        
        topo = HardwareTopology.linear(3)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        mapping = result.metadata['qubit_mapping']
        
        # q0 and q1 should be adjacent (most frequent)
        self.assertEqual(topo.get_distance(mapping[q0], mapping[q1]), 0)
    
    def test_total_distance_metric(self):
        """Test that total distance metric is calculated."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        topo = HardwareTopology.linear(2)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        # Should track distance metrics
        self.assertIn('total_distance', opt_pass.metrics.custom)
        self.assertIn('avg_distance', opt_pass.metrics.custom)
    
    def test_all_to_all_topology(self):
        """Test mapping on all-to-all topology."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        topo = HardwareTopology.all_to_all(3)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        mapping = result.metadata['qubit_mapping']
        
        # All qubits should be mapped
        self.assertEqual(len(mapping), 3)
        
        # All distances should be 0 (fully connected)
        self.assertEqual(opt_pass.metrics.custom['total_distance'], 0)
    
    def test_grid_topology(self):
        """Test mapping on grid topology."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # Interactions
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q2, q3]))
        
        topo = HardwareTopology.grid(2, 2)
        opt_pass = QubitMappingPass(topo)
        result = opt_pass.run(circuit)
        
        mapping = result.metadata['qubit_mapping']
        self.assertEqual(len(mapping), 4)
    
    def test_more_logical_than_physical_qubits(self):
        """Test handling when circuit has more qubits than hardware."""
        circuit = QIRCircuit()
        for i in range(5):
            circuit.add_qubit(f'q{i}')
        
        topo = HardwareTopology.linear(3)  # Only 3 physical qubits
        opt_pass = QubitMappingPass(topo)
        
        # Should handle gracefully (map what fits)
        result = opt_pass.run(circuit)
        mapping = result.metadata['qubit_mapping']
        
        # Should map at least some qubits
        self.assertGreater(len(mapping), 0)


if __name__ == '__main__':
    unittest.main()
