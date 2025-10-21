#!/usr/bin/env python3
"""
QMK Test Runner

Runs all unit and integration tests and reports results.

Test Suites:
- QVM library components (qvm/lib/)
- Example circuits (examples/asm/)
- Integration tests
- Unit tests
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
    
    all_success = True
    
    # Test directories to run
    test_dirs = [
        ("tests/qvm/lib", "Library component tests"),
        ("tests/examples", "Example circuit tests"),
        ("tests/qvm", "QVM tests"),
        ("tests/unit", "Unit tests"),
        ("tests/integration", "Integration tests"),
    ]
    
    for test_dir, description in test_dirs:
        full_path = os.path.join(ROOT, test_dir)
        if os.path.exists(full_path):
            # Check if there are any test files
            has_tests = False
            for root, dirs, files in os.walk(full_path):
                if any(f.startswith("test_") and f.endswith(".py") for f in files):
                    has_tests = True
                    break
            
            if has_tests:
                print(f"Running {description}...")
                print("-" * 70)
                success = run_tests(test_dir)
                all_success = all_success and success
                print()
    
    # Overall result
    if all_success:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
