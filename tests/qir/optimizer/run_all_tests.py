#!/usr/bin/env python3
"""Run all QIR optimizer tests and generate report."""

import unittest
import sys
from pathlib import Path
from io import StringIO

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))


def run_test_suite():
    """Run all optimizer tests and generate report."""
    
    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "="*70)
    print("QIR OPTIMIZER TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_test_suite())
