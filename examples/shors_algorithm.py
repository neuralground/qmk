#!/usr/bin/env python3
"""
Shor's Algorithm (Simplified Demonstration)

This is a pedagogical implementation of Shor's factoring algorithm.
We demonstrate the quantum period-finding subroutine, which is the quantum
core of Shor's algorithm.

Full Shor's algorithm:
1. Classical: Pick random a < N
2. Classical: Check if gcd(a, N) > 1
3. Quantum: Find period r of f(x) = a^x mod N  ← Uses ASM
4. Classical: Use r to find factors

Architecture:
- Quantum part (period finding): shors_period_finding.qvm.asm
- Classical parts (GCD, factor extraction): Python

Example: Factor N=15 using a=7
- f(x) = 7^x mod 15 has period r=4
- 7^0 mod 15 = 1
- 7^1 mod 15 = 7
- 7^2 mod 15 = 4
- 7^3 mod 15 = 13
- 7^4 mod 15 = 1 (period!)
"""

import math
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


def gcd(a: int, b: int) -> int:
    """Compute greatest common divisor."""
    while b:
        a, b = b, a % b
    return a


def create_period_finding_circuit(N: int = 15, a: int = 7, n_count_qubits: int = 3) -> dict:
    """
    Create quantum period-finding circuit using ASM.
    
    This is the quantum core of Shor's algorithm.
    
    Args:
        N: Number to factor
        a: Base for modular exponentiation
        n_count_qubits: Number of counting qubits (determines precision)
    
    Returns:
        QVM graph dictionary
    """
    # Use ASM file for quantum circuit
    return assemble_file("shors_period_finding.qvm.asm", {
        "n_count_qubits": n_count_qubits,
        "N": N,
        "a": a
    })


def classical_period_finding(a: int, N: int) -> int:
    """
    Classical period finding (for verification).
    
    Find smallest r > 0 such that a^r ≡ 1 (mod N)
    """
    result = 1
    for r in range(1, N):
        result = (result * a) % N
        if result == 1:
            return r
    return None


def factor_from_period(N: int, a: int, r: int) -> tuple:
    """
    Given period r, attempt to find factors of N.
    
    If r is even and a^(r/2) ≠ -1 (mod N), then:
    gcd(a^(r/2) ± 1, N) gives non-trivial factors
    """
    if r % 2 != 0:
        return None, None
    
    x = pow(a, r // 2, N)
    
    if x == N - 1:  # x ≡ -1 (mod N)
        return None, None
    
    factor1 = gcd(x + 1, N)
    factor2 = gcd(x - 1, N)
    
    if factor1 > 1 and factor1 < N:
        return factor1, N // factor1
    if factor2 > 1 and factor2 < N:
        return factor2, N // factor2
    
    return None, None


def demonstrate_shors_algorithm(client: QSyscallClient, N: int = 15, a: int = 7):
    """
    Demonstrate Shor's algorithm for factoring N.
    
    Args:
        client: QSyscall client
        N: Number to factor
        a: Base for modular exponentiation
    """
    print(f"\n{'='*60}")
    print(f"Shor's Algorithm: Factoring N = {N}")
    print(f"{'='*60}\n")
    
    # Step 1: Check if a and N are coprime
    g = gcd(a, N)
    if g > 1:
        print(f"Lucky! gcd({a}, {N}) = {g}")
        print(f"Factors: {g} and {N//g}")
        return
    
    print(f"Step 1: Check gcd({a}, {N}) = {g} ✓")
    print(f"Step 2: Find period r of f(x) = {a}^x mod {N}\n")
    
    # Classical verification
    r_classical = classical_period_finding(a, N)
    print(f"Classical period finding: r = {r_classical}")
    print(f"Verification: {a}^{r_classical} mod {N} = {pow(a, r_classical, N)}\n")
    
    # Quantum period finding
    print("Step 3: Quantum period finding (simplified demonstration)")
    print("Note: This is a pedagogical version showing the circuit structure.\n")
    
    circuit = create_period_finding_circuit(N, a, n_count_qubits=3)
    
    print("Submitting quantum circuit...")
    result = client.submit_and_wait(circuit, timeout_ms=15000, seed=42)
    
    if result['state'] == 'COMPLETED':
        print("✓ Quantum circuit executed successfully\n")
        
        # Extract measurement
        events = result['events']
        measured_value = 0
        for i in range(3):
            measured_value += events[f"m{i}"] * (2 ** i)
        
        print(f"Measured value: {measured_value}")
        print(f"(In full Shor's, this would be processed to extract period)\n")
    else:
        print(f"✗ Circuit failed: {result.get('error')}\n")
    
    # Step 4: Use period to find factors
    print(f"Step 4: Use period r = {r_classical} to find factors")
    
    if r_classical % 2 != 0:
        print(f"Period {r_classical} is odd, need to try different 'a'")
        return
    
    x = pow(a, r_classical // 2, N)
    print(f"{a}^({r_classical}//2) mod {N} = {x}")
    
    if x == N - 1:
        print(f"Result is -1 mod {N}, need to try different 'a'")
        return
    
    factor1, factor2 = factor_from_period(N, a, r_classical)
    
    if factor1 and factor2:
        print(f"\n{'='*60}")
        print(f"✅ SUCCESS! Factors found:")
        print(f"   {N} = {factor1} × {factor2}")
        print(f"{'='*60}")
        
        # Verify
        if factor1 * factor2 == N:
            print(f"✓ Verification: {factor1} × {factor2} = {N}")
    else:
        print("Could not extract factors from this period")


def explain_shors_algorithm():
    """Explain Shor's algorithm."""
    print("="*60)
    print("Shor's Algorithm for Integer Factorization")
    print("="*60)
    print("""
Shor's algorithm factors an integer N in polynomial time using
a quantum computer, providing exponential speedup over classical algorithms.

Algorithm Overview:
1. Pick random a < N
2. If gcd(a, N) > 1, we found a factor (lucky!)
3. Use quantum period finding to find r where a^r ≡ 1 (mod N)
4. If r is even and a^(r/2) ≢ -1 (mod N):
   - Compute gcd(a^(r/2) ± 1, N) to get factors

The quantum speedup comes from step 3 (period finding), which uses:
- Quantum Fourier Transform (QFT)
- Quantum phase estimation
- Modular exponentiation in superposition

Complexity:
- Classical (best known): O(exp(n^(1/3)))
- Shor's algorithm: O(n^3)

where n is the number of bits in N.

Impact:
Shor's algorithm can break RSA encryption, which relies on the
difficulty of factoring large numbers. This is why post-quantum
cryptography is being developed.
""")


def main():
    """Run Shor's algorithm demonstration."""
    explain_shors_algorithm()
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("Negotiating capabilities...")
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}\n")
    
    # Demonstrate factoring 15
    demonstrate_shors_algorithm(client, N=15, a=7)
    
    # Show scaling
    print(f"\n{'='*60}")
    print("Shor's Algorithm Scaling")
    print(f"{'='*60}\n")
    
    print(f"{'N (bits)':<15} {'Classical':<20} {'Quantum':<20} {'Speedup'}")
    print(f"{'-'*75}")
    
    for n_bits in [10, 20, 50, 100, 200, 512, 1024, 2048]:
        classical = f"~2^{n_bits**(1/3):.0f}"
        quantum = f"~{n_bits**3:,}"
        print(f"{n_bits:<15} {classical:<20} {quantum:<20} Exponential")
    
    print(f"\n{'='*60}")
    print("Note: This implementation is simplified for demonstration.")
    print("Full Shor's requires:")
    print("- More qubits (2n for n-bit number)")
    print("- Modular exponentiation circuits")
    print("- Continued fractions for period extraction")
    print(f"{'='*60}")
    
    # Telemetry
    print(f"\n{'='*60}")
    print("Telemetry")
    print(f"{'='*60}")
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ Shor's algorithm demonstration completed!")


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
