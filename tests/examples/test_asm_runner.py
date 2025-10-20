#!/usr/bin/env python3
"""
Tests for ASM Runner Utility

Tests the assemble_file function and related utilities.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from asm_runner import assemble_file


class TestAssembleFile(unittest.TestCase):
    """Test assemble_file function."""
    
    def test_assemble_simple_file(self):
        """Test assembling a simple file."""
        result = assemble_file("bell_state.qasm")
        self.assertIn('program', result)
        self.assertIn('resources', result)
        self.assertIn('version', result)
    
    def test_assemble_with_params(self):
        """Test assembling with parameter overrides."""
        result = assemble_file("deutsch_jozsa.qasm", {
            "oracle_type": "balanced_x0"
        })
        self.assertIn('program', result)
    
    def test_assemble_multiple_params(self):
        """Test assembling with multiple parameters."""
        result = assemble_file("grovers_search.qasm", {
            "target_state": "11",
            "n_iterations": 1
        })
        self.assertIn('program', result)
        self.assertGreater(len(result['program']['nodes']), 10)
    
    def test_assemble_nonexistent_file(self):
        """Test error on nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            assemble_file("nonexistent.qasm")
    
    def test_assemble_invalid_params(self):
        """Test assembling with invalid parameter types."""
        # Should still work, parameters just won't match
        result = assemble_file("bell_state.qasm", {
            "invalid_param": "value"
        })
        self.assertIn('program', result)


class TestParameterSubstitution(unittest.TestCase):
    """Test parameter substitution in ASM files."""
    
    def test_numeric_param(self):
        """Test numeric parameter substitution."""
        result = assemble_file("vqe_ansatz.qasm", {
            "theta1": 0.5,
            "theta2": 1.0,
            "theta3": 1.5
        })
        self.assertIn('program', result)
    
    def test_string_param(self):
        """Test string parameter substitution."""
        result = assemble_file("deutsch_jozsa.qasm", {
            "oracle_type": "constant_0"
        })
        self.assertIn('program', result)
    
    def test_list_param(self):
        """Test list parameter substitution."""
        import math
        angles = [2 * math.asin(1 / math.sqrt(3 - i)) for i in range(2)]
        result = assemble_file("w_state.qasm", {
            "n_qubits": 3,
            "qubit_outputs": "q0, q1, q2",
            "angles": angles
        })
        self.assertIn('program', result)


class TestFileResolution(unittest.TestCase):
    """Test file path resolution."""
    
    def test_resolve_from_asm_dir(self):
        """Test that files are resolved from examples/asm/."""
        # Should find bell_state.qasm in examples/asm/
        result = assemble_file("bell_state.qasm")
        self.assertIn('program', result)
    
    def test_resolve_with_subdirs(self):
        """Test resolution doesn't break with library includes."""
        # File includes library components
        result = assemble_file("shors_full.qasm", {
            "N": 15,
            "a": 7,
            "n_count_qubits": 4
        })
        self.assertIn('program', result)


class TestOutputValidation(unittest.TestCase):
    """Test that assembled output is valid."""
    
    def test_output_has_required_fields(self):
        """Test output has all required fields."""
        result = assemble_file("bell_state.qasm")
        
        # Top-level fields
        self.assertIn('version', result)
        self.assertIn('program', result)
        self.assertIn('resources', result)
        
        # Program fields
        self.assertIn('nodes', result['program'])
        self.assertIsInstance(result['program']['nodes'], list)
        
        # Resources fields
        self.assertIn('vqs', result['resources'])
    
    def test_output_nodes_valid(self):
        """Test that output nodes are valid."""
        result = assemble_file("bell_state.qasm")
        
        for node in result['program']['nodes']:
            self.assertIn('id', node)
            self.assertIn('op', node)
    
    def test_output_resources_valid(self):
        """Test that output resources are valid."""
        result = assemble_file("bell_state.qasm")
        
        vqs = result['resources']['vqs']
        self.assertIsInstance(vqs, list)
        self.assertGreater(len(vqs), 0)


def run_asm_runner_tests():
    """Run all ASM runner tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestAssembleFile))
    suite.addTests(loader.loadTestsFromTestCase(TestParameterSubstitution))
    suite.addTests(loader.loadTestsFromTestCase(TestFileResolution))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_asm_runner_tests()
    sys.exit(0 if success else 1)
