#!/usr/bin/env python3
"""
QMK Test Runner

Runs all unit and integration tests and reports results.
"""

import sys
import os
import unittest

# Add root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def run_tests(test_dir="tests", pattern="test_*.py", verbosity=2):
    """
    Run all tests in the specified directory.
    
    Args:
        test_dir: Directory containing tests
        pattern: Pattern to match test files
        verbosity: Test output verbosity (0-2)
    
    Returns:
        True if all tests passed, False otherwise
    """
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(ROOT, test_dir)
    suite = loader.discover(start_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)
    
    return result.wasSuccessful()


def main():
    """Main entry point."""
    print("=" * 70)
    print("QMK Test Suite")
    print("=" * 70)
    print()
    
    # Run unit tests
    print("Running unit tests...")
    print("-" * 70)
    unit_success = run_tests("tests/unit")
    
    print()
    
    # Run integration tests (if any exist)
    integration_dir = os.path.join(ROOT, "tests/integration")
    if os.path.exists(integration_dir) and any(f.startswith("test_") for f in os.listdir(integration_dir)):
        print("Running integration tests...")
        print("-" * 70)
        integration_success = run_tests("tests/integration")
    else:
        print("No integration tests found.")
        integration_success = True
    
    # Overall result
    print()
    if unit_success and integration_success:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
