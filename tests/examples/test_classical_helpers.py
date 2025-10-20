#!/usr/bin/env python3
"""
Tests for Classical Helper Functions

Tests the classical post-processing functions used in quantum algorithms,
particularly for Shor's algorithm.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples" / "lib"))

from shors_classical import (
    gcd,
    continued_fraction,
    convergents,
    extract_period_from_measurement,
    classical_period_finding,
    verify_period,
    factor_from_period,
    shors_classical_postprocessing
)


class TestGCD(unittest.TestCase):
    """Test greatest common divisor function."""
    
    def test_gcd_coprime(self):
        """Test GCD of coprime numbers."""
        self.assertEqual(gcd(7, 15), 1)
        self.assertEqual(gcd(11, 13), 1)
    
    def test_gcd_common_factor(self):
        """Test GCD with common factors."""
        self.assertEqual(gcd(12, 18), 6)
        self.assertEqual(gcd(15, 25), 5)
    
    def test_gcd_same_number(self):
        """Test GCD of same number."""
        self.assertEqual(gcd(7, 7), 7)


class TestPeriodExtraction(unittest.TestCase):
    """Test period extraction from quantum measurements."""
    
    def test_extract_period_shor_example(self):
        """Test period extraction for Shor's N=15, a=7."""
        r = extract_period_from_measurement(4, 4, 15)
        self.assertEqual(r, 4)
        
        r = extract_period_from_measurement(12, 4, 15)
        self.assertEqual(r, 4)
    
    def test_extract_period_zero_measurement(self):
        """Test period extraction with zero measurement."""
        r = extract_period_from_measurement(0, 4, 15)
        self.assertIsNone(r)


class TestClassicalPeriodFinding(unittest.TestCase):
    """Test classical period finding."""
    
    def test_period_finding_shor_example(self):
        """Test classical period finding for N=15, a=7."""
        r = classical_period_finding(7, 15)
        self.assertEqual(r, 4)
        self.assertEqual(pow(7, 4, 15), 1)


class TestVerifyPeriod(unittest.TestCase):
    """Test period verification."""
    
    def test_verify_correct_period(self):
        """Test verification of correct period."""
        self.assertTrue(verify_period(7, 15, 4))
        self.assertTrue(verify_period(2, 15, 4))
    
    def test_verify_incorrect_period(self):
        """Test verification of incorrect period."""
        self.assertFalse(verify_period(7, 15, 3))


class TestFactorExtraction(unittest.TestCase):
    """Test factor extraction from period."""
    
    def test_factor_from_period_success(self):
        """Test successful factor extraction."""
        f1, f2 = factor_from_period(15, 7, 4)
        self.assertIsNotNone(f1)
        self.assertIsNotNone(f2)
        self.assertEqual(f1 * f2, 15)


class TestShorsPostprocessing(unittest.TestCase):
    """Test complete Shor's algorithm post-processing."""
    
    def test_postprocessing_success(self):
        """Test successful post-processing."""
        result = shors_classical_postprocessing(4, 4, 15, 7)
        
        self.assertEqual(result['measurement'], 4)
        self.assertIsNotNone(result['period_candidate'])
        self.assertTrue(result['period_verified'])
        self.assertTrue(result['success'])
        
        f1, f2 = result['factors']
        self.assertIsNotNone(f1)
        self.assertIsNotNone(f2)
        self.assertEqual(f1 * f2, 15)


def run_classical_tests():
    """Run all classical helper tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestGCD))
    suite.addTests(loader.loadTestsFromTestCase(TestPeriodExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestClassicalPeriodFinding))
    suite.addTests(loader.loadTestsFromTestCase(TestVerifyPeriod))
    suite.addTests(loader.loadTestsFromTestCase(TestFactorExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestShorsPostprocessing))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_classical_tests()
    sys.exit(0 if success else 1)
