#!/usr/bin/env python3
"""
Shor's Algorithm - Full Implementation

This demonstrates the complete Shor's factoring algorithm with:
- Full Quantum Fourier Transform
- Proper period extraction using continued fractions
- Classical post-processing

Architecture:
- Quantum circuit: shors_full.qvm.asm (with full QFT)
- Classical helpers: lib/shors_classical.py
- Reusable components: lib/qft.qvm.asm, lib/modular_exp.qvm.asm

This shows how to build complex quantum algorithms from library components.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient

# Import ASM runner
try:
    from asm_runner import assemble_file
except ImportError:
    from examples.asm_runner import assemble_file

# Import classical helpers
try:
    from lib.shors_classical import (
        gcd,
        shors_classical_postprocessing,
        classical_period_finding,
        verify_period,
        factor_from_period
    )
except ImportError:
    from examples.lib.shors_classical import (
        gcd,
        shors_classical_postprocessing,
        classical_period_finding,
        verify_period,
        factor_from_period
    )


def create_full_shors_circuit(N: int = 15, a: int = 7, n_count_qubits: int = 4) -> dict:
    """
    Create full Shor's period-finding circuit with complete QFT.
    
    Args:
        N: Number to factor
        a: Base for modular exponentiation (must be coprime to N)
        n_count_qubits: Number of counting qubits (precision)
    
    Returns:
        QVM graph dictionary
    """
    return assemble_file("shors_full.qvm.asm", {
        "N": N,
        "a": a,
        "n_count_qubits": n_count_qubits
    })


def run_shors_algorithm(client: QSyscallClient, N: int = 15, a: int = 7, n_shots: int = 10):
    """
    Run complete Shor's algorithm with multiple shots.
    
    Args:
        client: QSyscall client
        N: Number to factor
        a: Base (must be coprime to N)
        n_shots: Number of quantum measurements to try
    """
    print(f"\n{'='*70}")
    print(f"Shor's Algorithm: Factoring N = {N}")
    print(f"{'='*70}\n")
    
    # Step 1: Classical pre-check
    print("Step 1: Classical Pre-Processing")
    print("-" * 70)
    
    g = gcd(a, N)
    if g > 1:
        print(f"✓ Lucky! gcd({a}, {N}) = {g}")
        print(f"  Factors: {g} and {N//g}")
        return
    
    print(f"  gcd({a}, {N}) = {g} ✓")
    print(f"  Proceeding to quantum period finding...\n")
    
    # Step 2: Classical period finding (for verification)
    print("Step 2: Classical Verification")
    print("-" * 70)
    r_classical = classical_period_finding(a, N)
    print(f"  Classical period: r = {r_classical}")
    print(f"  Verification: {a}^{r_classical} mod {N} = {pow(a, r_classical, N)}\n")
    
    # Step 3: Quantum period finding
    print("Step 3: Quantum Period Finding")
    print("-" * 70)
    print(f"  Creating quantum circuit...")
    print(f"    Counting qubits: 4")
    print(f"    Work qubits: 5")
    print(f"    Total gates: ~100 (with full QFT)")
    
    circuit = create_full_shors_circuit(N, a, 4)
    print(f"  ✓ Circuit created ({len(circuit['program']['nodes'])} nodes)\n")
    
    # Step 4: Run quantum circuit multiple times
    print("Step 4: Quantum Measurements")
    print("-" * 70)
    
    successful_factors = []
    
    for shot in range(n_shots):
        print(f"\n  Shot {shot + 1}/{n_shots}:")
        
        # Execute quantum circuit
        result = client.submit_and_wait(circuit, timeout_ms=15000, seed=shot)
        
        if result['state'] != 'COMPLETED':
            print(f"    ✗ Quantum circuit failed: {result.get('error')}")
            continue
        
        # Extract measurement
        events = result['events']
        measurement = 0
        for i in range(4):
            measurement += events[f"m{i}"] * (2 ** i)
        
        print(f"    Measured value: {measurement}")
        
        # Classical post-processing
        post_result = shors_classical_postprocessing(measurement, 4, N, a)
        
        print(f"    Period candidate: {post_result['period_candidate']}")
        
        if post_result['period_verified']:
            print(f"    ✓ Period verified: r = {post_result['period_candidate']}")
            
            if post_result['success']:
                f1, f2 = post_result['factors']
                print(f"    ✓ Factors found: {N} = {f1} × {f2}")
                successful_factors.append((f1, f2))
            else:
                print(f"    ✗ Could not extract factors from period")
        else:
            print(f"    ✗ Period verification failed")
    
    # Step 5: Summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}\n")
    
    if successful_factors:
        # Get most common factorization
        f1, f2 = successful_factors[0]
        print(f"✓ SUCCESS! Factored {N}")
        print(f"  {N} = {f1} × {f2}")
        print(f"  Success rate: {len(successful_factors)}/{n_shots} shots")
        print(f"  Classical period: {r_classical}")
        print(f"\nVerification: {f1} × {f2} = {f1 * f2} ✓")
    else:
        print(f"✗ No successful factorizations in {n_shots} shots")
        print(f"  (This can happen due to measurement randomness)")
        print(f"  Try running again or increase n_shots")


def explain_full_implementation():
    """Explain the full implementation."""
    print("="*70)
    print("Shor's Algorithm - Full Implementation")
    print("="*70)
    print("""
This implementation includes:

1. Complete Quantum Fourier Transform (QFT)
   - Hadamard gates on all qubits
   - Controlled phase rotations: R_k = diag(1, exp(2πi/2^k))
   - Qubit swaps to reverse order
   - ~O(n²) gates for n qubits

2. Modular Exponentiation Structure
   - Controlled-U^(2^i) operations
   - Each control applies a^(2^i) mod N
   - Simplified for pedagogical purposes
   - Full version would use modular arithmetic circuits

3. Classical Post-Processing
   - Continued fractions to extract period
   - Period verification: a^r mod N = 1
   - Factor extraction: gcd(a^(r/2) ± 1, N)

4. Reusable Library Components
   - lib/qft.qvm.asm - Quantum Fourier Transform
   - lib/modular_exp.qvm.asm - Modular exponentiation
   - lib/shors_classical.py - Classical helpers

Key Differences from Simplified Version:
- Full QFT with all controlled rotations (not just Hadamards)
- Proper phase estimation precision
- Complete continued fractions algorithm
- Modular arithmetic circuit structure (framework for full implementation)

Complexity:
- Quantum gates: O(n²) for QFT + O(n³) for modular exp
- Classical post-processing: O(n³) for continued fractions
- Total: Polynomial time (vs exponential classical)

For N=15 (4 bits):
- 4 counting qubits (precision)
- 5 work qubits (value + ancilla)
- ~100 quantum gates total
- Period r=4 for a=7

Success Probability:
- Each measurement has ~φ(r)/r chance of success
- For r=4: φ(4)/4 = 2/4 = 50% per shot
- Multiple shots increase overall success rate
""")


def main():
    """Run full Shor's algorithm demonstration."""
    explain_full_implementation()
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("\nNegotiating capabilities...")
    caps_result = client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",
        "CAP_MEASURE"
    ])
    print(f"Session ID: {caps_result['session_id']}\n")
    
    # Run Shor's algorithm
    run_shors_algorithm(client, N=15, a=7, n_shots=10)
    
    # Telemetry
    print(f"\n{'='*70}")
    print("Telemetry")
    print(f"{'='*70}")
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ Full Shor's algorithm demonstration completed!")


if __name__ == "__main__":
    try:
        main()
    except ConnectionRefusedError:
        print("❌ Error: QMK server not running")
        print("   Start with: python -m kernel.qmk_server")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
