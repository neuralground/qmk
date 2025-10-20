#!/usr/bin/env python3
"""
Tests for QVM Assembly Examples

Tests all example circuits in examples/asm/ to ensure:
- Examples assemble correctly
- No syntax errors
- Valid QVM graphs generated
- Reasonable node counts
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from asm_runner import assemble_file


class TestBasicExamples(unittest.TestCase):
    """Test basic example circuits."""
    
    def test_bell_state(self):
        """Test Bell state example."""
        result = assemble_file("bell_state.qasm")
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Bell state: alloc, H, CNOT, 2 measures = 5 nodes
        self.assertEqual(len(result['program']['nodes']), 5)
    
    def test_ghz_state(self):
        """Test GHZ state example with different qubit counts."""
        for n_qubits in [3, 4, 5]:
            with self.subTest(n_qubits=n_qubits):
                qubit_outputs = ", ".join([f"q{i}" for i in range(n_qubits)])
                result = assemble_file("ghz_state.qasm", {
                    "n_qubits": n_qubits,
                    "qubit_outputs": qubit_outputs
                })
                self.assertIn('program', result)
                # Should at least have some nodes
                self.assertGreaterEqual(len(result['program']['nodes']), 1)
    
    def test_w_state(self):
        """Test W state example."""
        import math
        n_qubits = 3
        qubit_outputs = ", ".join([f"q{i}" for i in range(n_qubits)])
        angles = []
        for i in range(n_qubits - 1):
            angle = 2 * math.asin(1 / math.sqrt(n_qubits - i))
            angles.append(angle)
        
        result = assemble_file("w_state.qasm", {
            "n_qubits": n_qubits,
            "qubit_outputs": qubit_outputs,
            "angles": angles
        })
        self.assertIn('program', result)
        self.assertGreaterEqual(len(result['program']['nodes']), 1)


class TestAlgorithmExamples(unittest.TestCase):
    """Test quantum algorithm examples."""
    
    def test_deutsch_jozsa(self):
        """Test Deutsch-Jozsa with all oracle types."""
        oracle_types = ["constant_0", "constant_1", "balanced_x0", "balanced_x1", "balanced_xor"]
        
        for oracle_type in oracle_types:
            with self.subTest(oracle_type=oracle_type):
                result = assemble_file("deutsch_jozsa.qasm", {"oracle_type": oracle_type})
                self.assertIn('program', result)
                self.assertGreater(len(result['program']['nodes']), 8)
    
    def test_grovers_search(self):
        """Test Grover's search with different targets."""
        target_states = ["00", "01", "10", "11"]
        
        for target_state in target_states:
            with self.subTest(target_state=target_state):
                result = assemble_file("grovers_search.qasm", {
                    "target_state": target_state,
                    "n_iterations": 1
                })
                self.assertIn('program', result)
                self.assertGreater(len(result['program']['nodes']), 15)
    
    def test_vqe_ansatz(self):
        """Test VQE ansatz example."""
        result = assemble_file("vqe_ansatz.qasm", {
            "theta1": 0.5,
            "theta2": 1.0,
            "theta3": 1.5
        })
        self.assertIn('program', result)
        self.assertGreater(len(result['program']['nodes']), 5)


class TestAdaptiveExamples(unittest.TestCase):
    """Test adaptive circuit examples."""
    
    def test_adaptive_simple(self):
        """Test simple adaptive circuit."""
        result = assemble_file("adaptive_simple.qasm")
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Should have syndrome measurement and conditional correction
        self.assertGreaterEqual(len(result['program']['nodes']), 8)
    
    def test_adaptive_multi_round(self):
        """Test multi-round adaptive circuit."""
        result = assemble_file("adaptive_multi_round.qasm")
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Should have multiple syndrome measurements and corrections
        # After fixing syndrome extraction: 13 nodes (was 17)
        self.assertGreaterEqual(len(result['program']['nodes']), 13)


class TestShorsExamples(unittest.TestCase):
    """Test Shor's algorithm examples."""
    
    def test_shors_period_finding(self):
        """Test simplified Shor's period finding."""
        result = assemble_file("shors_period_finding.qasm", {
            "n_count_qubits": 3,
            "N": 15,
            "a": 7
        })
        self.assertIn('program', result)
        self.assertGreater(len(result['program']['nodes']), 10)
    
    def test_shors_full(self):
        """Test full Shor's algorithm."""
        result = assemble_file("shors_full.qasm", {
            "N": 15,
            "a": 7,
            "n_count_qubits": 4
        })
        self.assertIn('program', result)
        # Full Shor's should have many nodes (QFT + modular exp)
        self.assertGreater(len(result['program']['nodes']), 40)


class TestMeasurementExamples(unittest.TestCase):
    """Test measurement basis examples."""
    
    def test_measurement_bases(self):
        """Test measurement in different bases."""
        bases = ["X", "Y", "Z"]
        
        for basis in bases:
            with self.subTest(basis=basis):
                result = assemble_file("measurement_bases.qasm", {"basis": basis})
                self.assertIn('program', result)
                self.assertGreater(len(result['program']['nodes']), 2)


class TestExampleValidation(unittest.TestCase):
    """Validate example circuit properties."""
    
    def test_all_examples_have_resources(self):
        """Test that all examples define resources."""
        examples = [
            ("bell_state.qasm", {}),
            ("ghz_state.qasm", {"n_qubits": 3, "qubit_outputs": "q0, q1, q2"}),
            ("deutsch_jozsa.qasm", {"oracle_type": "balanced_x0"}),
        ]
        
        for filename, params in examples:
            with self.subTest(filename=filename):
                result = assemble_file(filename, params)
                self.assertIn('resources', result)
                self.assertIn('vqs', result['resources'])
    
    def test_all_examples_have_version(self):
        """Test that all examples specify version."""
        examples = [
            ("bell_state.qasm", {}),
            ("grovers_search.qasm", {"target_state": "11", "n_iterations": 1}),
        ]
        
        for filename, params in examples:
            with self.subTest(filename=filename):
                result = assemble_file(filename, params)
                self.assertIn('version', result)


def run_example_tests():
    """Run all example tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicExamples))
    suite.addTests(loader.loadTestsFromTestCase(TestAlgorithmExamples))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveExamples))
    suite.addTests(loader.loadTestsFromTestCase(TestShorsExamples))
    suite.addTests(loader.loadTestsFromTestCase(TestMeasurementExamples))
    suite.addTests(loader.loadTestsFromTestCase(TestExampleValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_example_tests()
    sys.exit(0 if success else 1)
