#!/usr/bin/env python3
"""
Shor's Algorithm - Classical Helper Functions

This module provides the classical components of Shor's algorithm:
- GCD computation
- Continued fractions for period extraction
- Factor extraction from period
- Classical period verification

These functions work with the quantum circuit to complete Shor's algorithm.
"""

import math
from fractions import Fraction
from typing import Tuple, Optional, List


def gcd(a: int, b: int) -> int:
    """
    Compute greatest common divisor using Euclid's algorithm.
    
    Args:
        a, b: Integers
        
    Returns:
        GCD of a and b
    """
    while b:
        a, b = b, a % b
    return a


def continued_fraction(numerator: int, denominator: int, max_terms: int = 10) -> List[int]:
    """
    Compute continued fraction representation of numerator/denominator.
    
    A continued fraction represents a number as:
    a0 + 1/(a1 + 1/(a2 + 1/(a3 + ...)))
    
    Args:
        numerator: Numerator of fraction
        denominator: Denominator of fraction
        max_terms: Maximum number of terms to compute
        
    Returns:
        List of continued fraction coefficients [a0, a1, a2, ...]
    """
    cf = []
    for _ in range(max_terms):
        if denominator == 0:
            break
        a = numerator // denominator
        cf.append(a)
        numerator, denominator = denominator, numerator - a * denominator
    return cf


def convergents(cf: List[int]) -> List[Fraction]:
    """
    Compute convergents from continued fraction.
    
    Convergents are the rational approximations obtained by truncating
    the continued fraction at each term.
    
    Args:
        cf: Continued fraction coefficients
        
    Returns:
        List of convergents as Fraction objects
    """
    convergents_list = []
    
    for i in range(len(cf)):
        if i == 0:
            convergents_list.append(Fraction(cf[0], 1))
        elif i == 1:
            convergents_list.append(Fraction(cf[0] * cf[1] + 1, cf[1]))
        else:
            # Recursive formula for convergents
            p_prev2, q_prev2 = convergents_list[i-2].numerator, convergents_list[i-2].denominator
            p_prev1, q_prev1 = convergents_list[i-1].numerator, convergents_list[i-1].denominator
            
            p = cf[i] * p_prev1 + p_prev2
            q = cf[i] * q_prev1 + q_prev2
            
            convergents_list.append(Fraction(p, q))
    
    return convergents_list


def extract_period_from_measurement(measurement: int, n_qubits: int, N: int) -> Optional[int]:
    """
    Extract period from quantum measurement using continued fractions.
    
    The quantum circuit measures a value m such that m/2^n ≈ s/r
    where s is random and r is the period. We use continued fractions
    to find r.
    
    Args:
        measurement: Measured value from quantum circuit
        n_qubits: Number of counting qubits used
        N: The number being factored
        
    Returns:
        Candidate period r, or None if extraction fails
    """
    if measurement == 0:
        return None
    
    # Convert measurement to fraction
    denominator = 2 ** n_qubits
    
    # Use Python's Fraction to get best rational approximation
    frac = Fraction(measurement, denominator).limit_denominator(N)
    
    # The denominator is our period candidate
    r = frac.denominator
    
    # Period must be reasonable
    if r >= N or r == 0:
        return None
    
    return r


def classical_period_finding(a: int, N: int) -> int:
    """
    Classical period finding for verification.
    
    Find smallest r > 0 such that a^r ≡ 1 (mod N)
    
    Args:
        a: Base
        N: Modulus
        
    Returns:
        Period r
    """
    result = 1
    for r in range(1, N):
        result = (result * a) % N
        if result == 1:
            return r
    return N  # Should not reach here if a and N are coprime


def verify_period(a: int, N: int, r: int) -> bool:
    """
    Verify that r is the period of a mod N.
    
    Args:
        a: Base
        N: Modulus
        r: Candidate period
        
    Returns:
        True if a^r ≡ 1 (mod N), False otherwise
    """
    return pow(a, r, N) == 1


def factor_from_period(N: int, a: int, r: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract factors of N from period r.
    
    If r is even and a^(r/2) ≢ -1 (mod N), then:
    gcd(a^(r/2) ± 1, N) gives non-trivial factors
    
    Args:
        N: Number to factor
        a: Base used in period finding
        r: Period of a mod N
        
    Returns:
        Tuple of (factor1, factor2) or (None, None) if extraction fails
    """
    # Period must be even
    if r % 2 != 0:
        return None, None
    
    # Compute a^(r/2) mod N
    x = pow(a, r // 2, N)
    
    # Check if x ≡ -1 (mod N)
    if x == N - 1:
        return None, None
    
    # Try gcd(x + 1, N)
    factor1 = gcd(x + 1, N)
    if 1 < factor1 < N:
        factor2 = N // factor1
        return factor1, factor2
    
    # Try gcd(x - 1, N)
    factor2 = gcd(x - 1, N)
    if 1 < factor2 < N:
        factor1 = N // factor2
        return factor1, factor2
    
    return None, None


def shors_classical_postprocessing(measurement: int, n_qubits: int, N: int, a: int) -> dict:
    """
    Complete classical post-processing for Shor's algorithm.
    
    Takes the quantum measurement and extracts factors.
    
    Args:
        measurement: Value measured from quantum circuit
        n_qubits: Number of counting qubits
        N: Number to factor
        a: Base used in quantum circuit
        
    Returns:
        Dictionary with results:
        {
            'measurement': measured value,
            'period_candidate': extracted period,
            'period_verified': whether period is correct,
            'factors': (factor1, factor2) or (None, None),
            'success': whether factoring succeeded
        }
    """
    result = {
        'measurement': measurement,
        'period_candidate': None,
        'period_verified': False,
        'factors': (None, None),
        'success': False
    }
    
    # Extract period from measurement
    r = extract_period_from_measurement(measurement, n_qubits, N)
    result['period_candidate'] = r
    
    if r is None:
        return result
    
    # Verify period
    if verify_period(a, N, r):
        result['period_verified'] = True
        
        # Extract factors
        factor1, factor2 = factor_from_period(N, a, r)
        result['factors'] = (factor1, factor2)
        
        if factor1 is not None and factor2 is not None:
            result['success'] = True
    
    return result


# Example usage and testing
if __name__ == "__main__":
    print("=== Shor's Algorithm Classical Helper Functions ===\n")
    
    # Test case: Factor N=15 with a=7
    N = 15
    a = 7
    
    print(f"Factoring N={N} using a={a}\n")
    
    # Step 1: Check GCD
    g = gcd(a, N)
    print(f"1. GCD({a}, {N}) = {g}")
    if g > 1:
        print(f"   Lucky! Found factor: {g}")
    else:
        print(f"   No common factor, proceed to quantum step\n")
    
    # Step 2: Classical period finding (for verification)
    r_classical = classical_period_finding(a, N)
    print(f"2. Classical period finding: r = {r_classical}")
    print(f"   Verification: {a}^{r_classical} mod {N} = {pow(a, r_classical, N)}\n")
    
    # Step 3: Simulate quantum measurement
    # For a=7, N=15, period r=4
    # Quantum circuit with 4 counting qubits might measure:
    # m/16 ≈ s/4 where s ∈ {0, 1, 2, 3}
    # Possible measurements: 0, 4, 8, 12
    
    print("3. Simulating quantum measurements:\n")
    for m in [4, 8, 12]:
        print(f"   Measurement: {m}")
        
        # Extract period
        r = extract_period_from_measurement(m, 4, N)
        print(f"   Extracted period: {r}")
        
        if r and verify_period(a, N, r):
            print(f"   ✓ Period verified: {a}^{r} mod {N} = 1")
            
            # Extract factors
            f1, f2 = factor_from_period(N, a, r)
            if f1 and f2:
                print(f"   ✓ Factors found: {N} = {f1} × {f2}\n")
            else:
                print(f"   ✗ Could not extract factors from period\n")
        else:
            print(f"   ✗ Period verification failed\n")
    
    print("=== Complete Example ===\n")
    
    # Full post-processing
    measurement = 8
    result = shors_classical_postprocessing(measurement, 4, N, a)
    
    print(f"Measurement: {result['measurement']}")
    print(f"Period candidate: {result['period_candidate']}")
    print(f"Period verified: {result['period_verified']}")
    print(f"Factors: {result['factors']}")
    print(f"Success: {result['success']}")
