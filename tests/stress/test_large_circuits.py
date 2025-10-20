#!/usr/bin/env python3
"""
Stress tests for large quantum circuits.

Tests QMK's ability to handle large-scale quantum computations.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer.ir import QIRCircuit, QIRInstruction, InstructionType


class TestLargeCircuits(unittest.TestCase):
    """Test handling of large circuits."""
    
    def test_100_qubit_circuit(self):
        """Test circuit with 100 qubits."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(100)]
        
        # Add gates
        for q in qubits:
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        self.assertEqual(len(circuit.instructions), 100)
        self.assertEqual(len(circuit.qubits), 100)
    
    def test_1000_gate_circuit(self):
        """Test circuit with 1000 gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Add 1000 gates alternating H and CNOT
        for i in range(500):
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
            circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        self.assertEqual(len(circuit.instructions), 1000)
    
    def test_deep_circuit(self):
        """Test circuit with deep gate sequence."""
        circuit = QIRCircuit()
        q = circuit.add_qubit('q0')
        
        # Create a deep circuit (1000 sequential gates)
        for _ in range(1000):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q]))
        
        self.assertEqual(len(circuit.instructions), 1000)
    
    def test_wide_circuit(self):
        """Test circuit with many parallel qubits."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(100)]
        
        # Apply H to all qubits (wide parallelism)
        for q in qubits:
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        # Apply CNOT chain
        for i in range(len(qubits) - 1):
            circuit.add_instruction(QIRInstruction(
                InstructionType.CNOT, 
                [qubits[i], qubits[i+1]]
            ))
        
        self.assertEqual(len(circuit.instructions), 199)  # 100 H + 99 CNOT


class TestComplexTopologies(unittest.TestCase):
    """Test complex circuit topologies."""
    
    def test_all_to_all_connectivity(self):
        """Test all-to-all qubit connectivity."""
        n_qubits = 10
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(n_qubits)]
        
        # Create all-to-all CNOT connectivity
        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                circuit.add_instruction(QIRInstruction(
                    InstructionType.CNOT,
                    [qubits[i], qubits[j]]
                ))
        
        expected_cnots = n_qubits * (n_qubits - 1) // 2
        self.assertEqual(len(circuit.instructions), expected_cnots)
    
    def test_grid_topology(self):
        """Test 2D grid topology."""
        rows, cols = 5, 5
        circuit = QIRCircuit()
        
        # Create grid of qubits
        grid = [[circuit.add_qubit(f'q{i}_{j}') 
                for j in range(cols)] 
                for i in range(rows)]
        
        # Horizontal connections
        for i in range(rows):
            for j in range(cols - 1):
                circuit.add_instruction(QIRInstruction(
                    InstructionType.CNOT,
                    [grid[i][j], grid[i][j+1]]
                ))
        
        # Vertical connections
        for i in range(rows - 1):
            for j in range(cols):
                circuit.add_instruction(QIRInstruction(
                    InstructionType.CNOT,
                    [grid[i][j], grid[i+1][j]]
                ))
        
        expected_edges = (rows * (cols - 1)) + ((rows - 1) * cols)
        self.assertEqual(len(circuit.instructions), expected_edges)


class TestMemoryUsage(unittest.TestCase):
    """Test memory efficiency."""
    
    def test_circuit_memory_footprint(self):
        """Test that circuits don't use excessive memory."""
        import sys
        
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(100)]
        
        # Add 1000 gates
        for i in range(1000):
            q = qubits[i % 100]
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        # Check size is reasonable (should be < 1MB for this circuit)
        size = sys.getsizeof(circuit)
        self.assertLess(size, 1_000_000, 
                       f"Circuit uses {size} bytes, expected < 1MB")


if __name__ == '__main__':
    unittest.main()
