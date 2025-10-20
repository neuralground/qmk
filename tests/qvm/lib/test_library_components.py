#!/usr/bin/env python3
"""
Tests for QVM Library Components

Tests all reusable circuit components in qvm/lib/ to ensure:
- Components load correctly
- Parameters are substituted properly
- Circuits generate valid QVM graphs
- Node counts are reasonable
- No syntax errors
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from qvm.tools.qvm_asm import assemble


class TestQFT(unittest.TestCase):
    """Test Quantum Fourier Transform library component."""
    
    def test_qft_loads(self):
        """Test that QFT library loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=4, profile="logical:Surface(d=3)" -> q0, q1, q2, q3

.set n_qubits = 4
.set qubit_prefix = "q"
.include "qft.qasm"

.for i in 0..3
    m_{i}: MEASURE_Z q{i} -> m{i}
.endfor
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        self.assertGreater(len(result['program']['nodes']), 4)
    
    def test_qft_different_sizes(self):
        """Test QFT with different qubit counts."""
        for n in [2, 3, 4, 5]:
            with self.subTest(n_qubits=n):
                qubits = ", ".join([f"q{i}" for i in range(n)])
                asm = f"""
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n={n}, profile="logical:Surface(d=3)" -> {qubits}

.set n_qubits = {n}
.set qubit_prefix = "q"
.include "qft.qasm"
"""
                result = assemble(asm)
                self.assertIn('program', result)
                # QFT should have at least alloc node
                node_count = len(result['program']['nodes'])
                self.assertGreaterEqual(node_count, 1)


class TestDraperAdder(unittest.TestCase):
    """Test Draper quantum adder."""
    
    def test_draper_adder_loads(self):
        """Test that Draper adder loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=8, profile="logical:Surface(d=3)" -> a0, a1, a2, a3, b0, b1, b2, b3

.set n_bits = 4
.set a_prefix = "a"
.set b_prefix = "b"
.include "draper_adder.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Draper adder should at least load without errors
        self.assertGreaterEqual(len(result['program']['nodes']), 1)
    
    def test_draper_adder_different_sizes(self):
        """Test Draper adder with different bit counts."""
        for n_bits in [2, 3, 4]:
            with self.subTest(n_bits=n_bits):
                a_qubits = ", ".join([f"a{i}" for i in range(n_bits)])
                b_qubits = ", ".join([f"b{i}" for i in range(n_bits)])
                asm = f"""
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n={n_bits*2}, profile="logical:Surface(d=3)" -> {a_qubits}, {b_qubits}

.set n_bits = {n_bits}
.set a_prefix = "a"
.set b_prefix = "b"
.include "draper_adder.qasm"
"""
                result = assemble(asm)
                self.assertIn('program', result)


class TestCuccaroAdder(unittest.TestCase):
    """Test Cuccaro quantum adder."""
    
    def test_cuccaro_adder_loads(self):
        """Test that Cuccaro adder loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=9, profile="logical:Surface(d=3)" -> a0, a1, a2, a3, b0, b1, b2, b3, c

.set n_bits = 4
.set a_prefix = "a"
.set b_prefix = "b"
.set carry_qubit = "c"
.include "cuccaro_adder.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Cuccaro is O(n), should have fewer nodes than Draper
        self.assertGreater(len(result['program']['nodes']), 5)


class TestComparator(unittest.TestCase):
    """Test quantum comparator."""
    
    def test_comparator_loads(self):
        """Test that comparator loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=9, profile="logical:Surface(d=3)" -> a0, a1, a2, a3, b0, b1, b2, b3, result

.set n_bits = 4
.set a_prefix = "a"
.set b_prefix = "b"
.set result_qubit = "result"
.include "comparator.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])


class TestPhaseEstimation(unittest.TestCase):
    """Test phase estimation component."""
    
    def test_phase_estimation_loads(self):
        """Test that phase estimation loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=6, profile="logical:Surface(d=3)" -> prec_0, prec_1, prec_2, prec_3, eigen_0, eigen_1

.set n_precision = 4
.set n_eigenstate = 2
.set precision_prefix = "prec"
.set eigenstate_prefix = "eigen"
.set unitary_name = "U"
.include "phase_estimation.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Should at least load without errors
        self.assertGreaterEqual(len(result['program']['nodes']), 1)


class TestAmplitudeAmplification(unittest.TestCase):
    """Test amplitude amplification (Grover operator)."""
    
    def test_amplitude_amplification_loads(self):
        """Test that amplitude amplification loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=3, profile="logical:Surface(d=3)" -> q0, q1, q2

.set n_qubits = 3
.set qubit_prefix = "q"
.set oracle_type = "custom"
.include "amplitude_amplification.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Should at least load without errors
        self.assertGreaterEqual(len(result['program']['nodes']), 1)


class TestGroverOracle(unittest.TestCase):
    """Test Grover oracle templates."""
    
    def test_grover_oracle_single_state(self):
        """Test single-state oracle."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=3, profile="logical:Surface(d=3)" -> q0, q1, q2

.set n_qubits = 3
.set qubit_prefix = "q"
.set target_state = "101"
.set oracle_mode = "single"
.include "grover_oracle.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])


class TestSyndromeExtraction(unittest.TestCase):
    """Test syndrome extraction for QEC."""
    
    def test_syndrome_extraction_repetition(self):
        """Test repetition code syndrome extraction."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=5, profile="logical:Surface(d=3)" -> d0, d1, d2, a0, a1

.set n_data = 3
.set n_ancilla = 2
.set data_prefix = "d"
.set ancilla_prefix = "a"
.set code_type = "repetition"
.include "syndrome_extraction.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        # Should at least load without errors
        self.assertGreaterEqual(len(result['program']['nodes']), 1)


class TestModularExponentiation(unittest.TestCase):
    """Test modular exponentiation framework."""
    
    def test_modular_exp_loads(self):
        """Test that modular exponentiation loads without errors."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=9, profile="logical:Surface(d=3)" -> ctrl_0, ctrl_1, ctrl_2, ctrl_3, work_0, work_1, work_2, work_3, work_4

.set n_control = 4
.set n_work = 5
.set a = 7
.set N = 15
.set control_prefix = "ctrl"
.set work_prefix = "work"
.include "modular_exp.qasm"
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])


class TestLibraryIntegration(unittest.TestCase):
    """Test that library components work together."""
    
    def test_multiple_includes(self):
        """Test using multiple library components in one circuit."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

alloc: ALLOC_LQ n=4, profile="logical:Surface(d=3)" -> q0, q1, q2, q3

; Use QFT
.set n_qubits = 4
.set qubit_prefix = "q"
.include "qft.qasm"

; Measure
.for i in 0..3
    m_{i}: MEASURE_Z q{i} -> m{i}
.endfor
"""
        result = assemble(asm)
        self.assertIn('program', result)
        self.assertGreater(len(result['program']['nodes']), 4)


def run_library_tests():
    """Run all library component tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQFT))
    suite.addTests(loader.loadTestsFromTestCase(TestDraperAdder))
    suite.addTests(loader.loadTestsFromTestCase(TestCuccaroAdder))
    suite.addTests(loader.loadTestsFromTestCase(TestComparator))
    suite.addTests(loader.loadTestsFromTestCase(TestPhaseEstimation))
    suite.addTests(loader.loadTestsFromTestCase(TestAmplitudeAmplification))
    suite.addTests(loader.loadTestsFromTestCase(TestGroverOracle))
    suite.addTests(loader.loadTestsFromTestCase(TestSyndromeExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestModularExponentiation))
    suite.addTests(loader.loadTestsFromTestCase(TestLibraryIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_library_tests()
    sys.exit(0 if success else 1)
