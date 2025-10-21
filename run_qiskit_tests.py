#!/usr/bin/env python3
"""
Qiskit Path Equivalence Test Runner

Runs automated tests comparing Qiskit execution through:
1. Native Qiskit Aer simulator
2. Qiskit → QIR → Optimizer → QVM → QMK path

Requirements:
- pip install qiskit qiskit-aer
- QMK server running: python -m kernel.qmk_server
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


def main():
    """Run Qiskit path equivalence tests."""
    print("=" * 70)
    print("Qiskit Path Equivalence Tests")
    print("=" * 70)
    print()
    
    if not QISKIT_AVAILABLE:
        print("❌ Qiskit not available")
        print("   Install with: pip install qiskit qiskit-aer")
        print()
        print("⚠️  Skipping Qiskit tests (not a failure)")
        return 0
    
    print("✅ Qiskit available")
    print()
    print("These tests verify that Qiskit circuits produce equivalent")
    print("results through both execution paths:")
    print("  1. Native Qiskit Aer simulator")
    print("  2. Qiskit → QIR → Optimizer → QVM → QMK")
    print()
    print("Note: QMK server must be running")
    print("      Start with: python -m kernel.qmk_server")
    print()
    print("-" * 70)
    print()
    
    # Import and run tests
    from tests.integration.test_qiskit_path_equivalence import run_qiskit_equivalence_tests
    
    success = run_qiskit_equivalence_tests()
    
    print()
    print("=" * 70)
    if success:
        print("✅ ALL QISKIT EQUIVALENCE TESTS PASSED")
        print()
        print("Both execution paths produce equivalent results!")
        return 0
    else:
        print("❌ SOME QISKIT TESTS FAILED")
        print()
        print("Check if:")
        print("  - QMK server is running")
        print("  - Qiskit is properly installed")
        print("  - Both paths are configured correctly")
        return 1


if __name__ == "__main__":
    sys.exit(main())
