#!/usr/bin/env python3
"""Tests for gate teleportation."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType
)
from kernel.qir_bridge.optimizer.topology import HardwareTopology
from kernel.qir_bridge.optimizer.passes import GateTeleportationPass


class TestGateTeleportation(unittest.TestCase):
    """Test gate teleportation."""
    
    def test_identify_long_range_gates(self):
        """Test identifying long-range gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        q3 = circuit.add_qubit('q3')
        
        # CNOT between distant qubits
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q3]))
        
        # Linear topology: 0-1-2-3
        topo = HardwareTopology.linear(4)
        
        # Set up mapping
        circuit.metadata['qubit_mapping'] = {q0: 0, q1: 1, q2: 2, q3: 3}
        
        opt_pass = GateTeleportationPass(topo, distance_threshold=2)
        result = opt_pass.run(circuit)
        
        # Should identify as teleportation candidate
        self.assertGreater(opt_pass.metrics.custom['teleportation_candidates'], 0)
    
    def test_no_teleportation_for_adjacent(self):
        """Test that adjacent qubits don't trigger teleportation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        topo = HardwareTopology.linear(2)
        circuit.metadata['qubit_mapping'] = {q0: 0, q1: 1}
        
        opt_pass = GateTeleportationPass(topo, distance_threshold=2)
        result = opt_pass.run(circuit)
        
        # Should not identify as candidate (distance = 0)
        self.assertEqual(opt_pass.metrics.custom['teleportation_candidates'], 0)
    
    def test_all_to_all_no_teleportation(self):
        """Test that all-to-all topology doesn't need teleportation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q3 = circuit.add_qubit('q3')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q3]))
        
        topo = HardwareTopology.all_to_all(4)
        circuit.metadata['qubit_mapping'] = {q0: 0, q3: 3}
        
        opt_pass = GateTeleportationPass(topo, distance_threshold=2)
        result = opt_pass.run(circuit)
        
        # All-to-all has distance 0 everywhere
        self.assertEqual(opt_pass.metrics.custom['teleportation_candidates'], 0)
    
    def test_without_topology(self):
        """Test behavior without topology information."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = GateTeleportationPass(topology=None)
        result = opt_pass.run(circuit)
        
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_multiple_long_range_gates(self):
        """Test multiple long-range gates."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(5)]
        
        # Multiple long-range CNOTs
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[0], qubits[4]]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[1], qubits[4]]))
        
        topo = HardwareTopology.linear(5)
        circuit.metadata['qubit_mapping'] = {q: i for i, q in enumerate(qubits)}
        
        opt_pass = GateTeleportationPass(topo, distance_threshold=2)
        result = opt_pass.run(circuit)
        
        # Should identify both as candidates
        self.assertGreaterEqual(opt_pass.metrics.custom['teleportation_candidates'], 2)
    
    def test_distance_threshold(self):
        """Test distance threshold parameter."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q2 = circuit.add_qubit('q2')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        topo = HardwareTopology.linear(3)
        circuit.metadata['qubit_mapping'] = {q0: 0, q2: 2}
        
        # With threshold=3, distance=1 should not trigger
        opt_pass = GateTeleportationPass(topo, distance_threshold=3)
        result = opt_pass.run(circuit)
        
        self.assertEqual(opt_pass.metrics.custom['teleportation_candidates'], 0)
        
        # With threshold=1, distance=1 should trigger
        opt_pass2 = GateTeleportationPass(topo, distance_threshold=1)
        result2 = opt_pass2.run(circuit)
        
        self.assertGreater(opt_pass2.metrics.custom['teleportation_candidates'], 0)


if __name__ == '__main__':
    unittest.main()
