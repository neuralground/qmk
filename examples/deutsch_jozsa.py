#!/usr/bin/env python3
"""
Deutsch-Jozsa Algorithm

Demonstrates the Deutsch-Jozsa algorithm, one of the first quantum algorithms
showing exponential speedup over classical computation.

Problem: Given a black-box function f: {0,1}^n → {0,1}, determine if f is:
- Constant: f(x) = 0 for all x, or f(x) = 1 for all x
- Balanced: f(x) = 0 for exactly half the inputs, f(x) = 1 for the other half

Classical: Requires 2^(n-1) + 1 queries in the worst case
Quantum: Requires only 1 query!

This implementation uses 2 input qubits (4 possible inputs).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient


def create_deutsch_jozsa_circuit(oracle_type: str = "constant_0") -> dict:
    """
    Create Deutsch-Jozsa circuit for 2-qubit input.
    
    Args:
        oracle_type: Type of oracle function
            - "constant_0": f(x) = 0 for all x
            - "constant_1": f(x) = 1 for all x
            - "balanced_x0": f(x) = x0 (first bit)
            - "balanced_x1": f(x) = x1 (second bit)
            - "balanced_xor": f(x) = x0 ⊕ x1
    
    Returns:
        QVM graph dictionary
    """
    nodes = [
        # Allocate 2 input qubits + 1 output qubit
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": ["x0", "x1", "y"],
            "profile": "logical:surface_code(d=3)"
        },
        
        # Initialize output qubit to |1⟩
        {
            "id": "x_y",
            "op": "X",
            "qubits": ["y"],
            "deps": ["alloc"]
        },
        
        # Apply Hadamard to all qubits
        {
            "id": "h_x0",
            "op": "H",
            "qubits": ["x0"],
            "deps": ["alloc"]
        },
        {
            "id": "h_x1",
            "op": "H",
            "qubits": ["x1"],
            "deps": ["alloc"]
        },
        {
            "id": "h_y",
            "op": "H",
            "qubits": ["y"],
            "deps": ["x_y"]
        }
    ]
    
    # Oracle implementation
    oracle_deps = ["h_x0", "h_x1", "h_y"]
    
    if oracle_type == "constant_0":
        # Do nothing (identity)
        oracle_last = oracle_deps
        
    elif oracle_type == "constant_1":
        # Flip output qubit
        nodes.append({
            "id": "oracle_x",
            "op": "X",
            "qubits": ["y"],
            "deps": oracle_deps
        })
        oracle_last = ["oracle_x"]
        
    elif oracle_type == "balanced_x0":
        # CNOT from x0 to y
        nodes.append({
            "id": "oracle_cnot",
            "op": "CNOT",
            "qubits": ["x0", "y"],
            "deps": oracle_deps
        })
        oracle_last = ["oracle_cnot"]
        
    elif oracle_type == "balanced_x1":
        # CNOT from x1 to y
        nodes.append({
            "id": "oracle_cnot",
            "op": "CNOT",
            "qubits": ["x1", "y"],
            "deps": oracle_deps
        })
        oracle_last = ["oracle_cnot"]
        
    elif oracle_type == "balanced_xor":
        # CNOT from x0 to y, then CNOT from x1 to y
        nodes.append({
            "id": "oracle_cnot0",
            "op": "CNOT",
            "qubits": ["x0", "y"],
            "deps": oracle_deps
        })
        nodes.append({
            "id": "oracle_cnot1",
            "op": "CNOT",
            "qubits": ["x1", "y"],
            "deps": ["oracle_cnot0"]
        })
        oracle_last = ["oracle_cnot1"]
    
    else:
        raise ValueError(f"Unknown oracle type: {oracle_type}")
    
    # Apply Hadamard to input qubits
    nodes.append({
        "id": "h_x0_final",
        "op": "H",
        "qubits": ["x0"],
        "deps": oracle_last
    })
    nodes.append({
        "id": "h_x1_final",
        "op": "H",
        "qubits": ["x1"],
        "deps": oracle_last
    })
    
    # Measure input qubits
    nodes.append({
        "id": "measure_x0",
        "op": "MEASURE_Z",
        "qubits": ["x0"],
        "outputs": ["m0"],
        "deps": ["h_x0_final"]
    })
    nodes.append({
        "id": "measure_x1",
        "op": "MEASURE_Z",
        "qubits": ["x1"],
        "outputs": ["m1"],
        "deps": ["h_x1_final"]
    })
    
    # Free qubits
    nodes.append({
        "id": "free",
        "op": "FREE_LQ",
        "qubits": ["x0", "x1", "y"],
        "deps": ["measure_x0", "measure_x1"]
    })
    
    return {
        "version": "0.1",
        "metadata": {
            "name": f"deutsch_jozsa_{oracle_type}",
            "description": f"Deutsch-Jozsa algorithm with {oracle_type} oracle"
        },
        "nodes": nodes,
        "edges": []
    }


def run_deutsch_jozsa(client: QSyscallClient, oracle_type: str, shots: int = 10):
    """
    Run Deutsch-Jozsa algorithm and analyze results.
    
    Args:
        client: QSyscall client
        oracle_type: Type of oracle
        shots: Number of measurements
    """
    is_constant = oracle_type.startswith("constant")
    
    print(f"\n{'='*60}")
    print(f"Oracle: {oracle_type}")
    print(f"Expected: {'Constant' if is_constant else 'Balanced'}")
    print(f"{'='*60}")
    
    circuit = create_deutsch_jozsa_circuit(oracle_type)
    
    # Run multiple times
    results = []
    for i in range(shots):
        result = client.submit_and_wait(circuit, timeout_ms=10000, seed=i)
        
        if result['state'] == 'COMPLETED':
            m0 = result['events']['m0']
            m1 = result['events']['m1']
            results.append((m0, m1))
    
    # Analyze results
    all_zero = all(m0 == 0 and m1 == 0 for m0, m1 in results)
    
    print(f"\nMeasurements ({shots} shots):")
    for i, (m0, m1) in enumerate(results[:5]):  # Show first 5
        print(f"  Shot {i+1}: |{m0}{m1}⟩")
    if shots > 5:
        print(f"  ... ({shots-5} more)")
    
    print(f"\nResult: All measurements = |00⟩? {all_zero}")
    
    if all_zero:
        print("✅ Conclusion: Function is CONSTANT")
        if is_constant:
            print("   ✓ Correct!")
        else:
            print("   ✗ Incorrect (should be balanced)")
    else:
        print("✅ Conclusion: Function is BALANCED")
        if not is_constant:
            print("   ✓ Correct!")
        else:
            print("   ✗ Incorrect (should be constant)")
    
    return all_zero == is_constant


def explain_deutsch_jozsa():
    """Explain the Deutsch-Jozsa algorithm."""
    print("="*60)
    print("Deutsch-Jozsa Algorithm")
    print("="*60)
    print("""
The Deutsch-Jozsa algorithm solves the following problem:

Given: A black-box function f: {0,1}^n → {0,1}
Promise: f is either constant or balanced
Goal: Determine which

Definitions:
- Constant: f(x) = 0 for all x, OR f(x) = 1 for all x
- Balanced: f(x) = 0 for exactly half the inputs

Classical Solution:
- Worst case: Need to evaluate f(x) for 2^(n-1) + 1 inputs
- For n=2: Need up to 3 evaluations

Quantum Solution:
- Only 1 evaluation of f (in quantum superposition)!
- Exponential speedup

How it works:
1. Prepare input qubits in equal superposition: |+⟩^⊗n
2. Prepare output qubit in |−⟩ state
3. Apply oracle Uf in superposition
4. Apply Hadamard to input qubits
5. Measure input qubits:
   - All |0⟩ → function is constant
   - Any |1⟩ → function is balanced

This was one of the first algorithms demonstrating quantum advantage!
""")


def demonstrate_all_oracles(client: QSyscallClient):
    """Test all oracle types."""
    print(f"\n{'='*60}")
    print("Testing All Oracle Types")
    print(f"{'='*60}")
    
    oracles = [
        ("constant_0", "Constant (always 0)"),
        ("constant_1", "Constant (always 1)"),
        ("balanced_x0", "Balanced (f = x₀)"),
        ("balanced_x1", "Balanced (f = x₁)"),
        ("balanced_xor", "Balanced (f = x₀ ⊕ x₁)")
    ]
    
    results = []
    for oracle_type, description in oracles:
        print(f"\n{'-'*60}")
        print(f"Testing: {description}")
        print(f"{'-'*60}")
        
        success = run_deutsch_jozsa(client, oracle_type, shots=10)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{description:<30} {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print(f"\n✅ All tests passed!")
    else:
        print(f"\n⚠️  Some tests failed")


def show_classical_vs_quantum():
    """Compare classical and quantum approaches."""
    print(f"\n{'='*60}")
    print("Classical vs Quantum Comparison")
    print(f"{'='*60}\n")
    
    print(f"{'n (qubits)':<15} {'Inputs':<15} {'Classical':<20} {'Quantum':<15}")
    print(f"{'-'*65}")
    
    for n in [1, 2, 4, 8, 16, 32, 64]:
        inputs = 2 ** n
        classical_worst = 2 ** (n - 1) + 1
        quantum = 1
        
        print(f"{n:<15} {inputs:<15} {classical_worst:<20} {quantum:<15}")
    
    print(f"\n{'='*60}")
    print("Key Insight: Quantum algorithm uses only 1 query regardless of n!")
    print(f"{'='*60}")


def main():
    """Run Deutsch-Jozsa algorithm demonstrations."""
    explain_deutsch_jozsa()
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("\nNegotiating capabilities...")
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}")
    
    # Test all oracles
    demonstrate_all_oracles(client)
    
    # Show scaling
    show_classical_vs_quantum()
    
    # Telemetry
    print(f"\n{'='*60}")
    print("Telemetry")
    print(f"{'='*60}")
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ Deutsch-Jozsa algorithm demonstrations completed!")


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
