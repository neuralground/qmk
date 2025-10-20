#!/usr/bin/env python3
"""
Grover's Search Algorithm

Demonstrates Grover's algorithm for searching an unsorted database.
This implementation searches for a marked item in a 4-element database (2 qubits).

Algorithm Overview:
1. Initialize qubits in equal superposition
2. Apply Grover iterations:
   - Oracle: Mark the target state
   - Diffusion: Amplify the marked state
3. Measure to find the target

For n qubits (N=2^n items), optimal iterations ≈ π/4 * √N
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


def create_grovers_circuit(target_state: str = "11", n_iterations: int = 1) -> dict:
    """
    Create Grover's search circuit for 2 qubits using QVM assembly.
    
    Args:
        target_state: Binary string of target state (e.g., "11" for |11⟩)
        n_iterations: Number of Grover iterations (default 1 for 2 qubits)
    
    Returns:
        QVM graph dictionary
    """
    if len(target_state) != 2 or not all(c in '01' for c in target_state):
        raise ValueError("target_state must be 2-bit binary string")
    
    # Use ASM file with .param override
    return assemble_file("grovers_search.qasm", {
        "target_state": target_state,
        "n_iterations": n_iterations
    })




def run_grovers_search(client: QSyscallClient, target: str, shots: int = 100):
    """
    Run Grover's algorithm multiple times and analyze results.
    
    Args:
        client: QSyscall client
        target: Target state to search for
        shots: Number of measurements
    """
    print(f"\n{'='*60}")
    print(f"Searching for target state: |{target}⟩")
    print(f"{'='*60}")
    
    # For 2 qubits (4 states), optimal iterations = 1
    n_iterations = 1
    print(f"Database size: 4 states (2 qubits)")
    print(f"Grover iterations: {n_iterations}")
    print(f"Classical search: ~2 queries on average")
    print(f"Quantum search: 1 iteration\n")
    
    # Create circuit
    circuit = create_grovers_circuit(target, n_iterations)
    
    # Run multiple times to get statistics
    results = {'00': 0, '01': 0, '10': 0, '11': 0}
    
    print(f"Running {shots} measurements...")
    for i in range(shots):
        result = client.submit_and_wait(circuit, timeout_ms=10000, seed=i)
        
        if result['state'] == 'COMPLETED':
            m0 = result['events']['m0']
            m1 = result['events']['m1']
            bitstring = f"{m0}{m1}"
            results[bitstring] += 1
        else:
            print(f"  ⚠ Shot {i} failed: {result.get('error')}")
    
    # Analyze results
    print(f"\n{'='*60}")
    print("Results:")
    print(f"{'='*60}")
    print(f"{'State':<10} {'Count':<10} {'Probability':<15} {'Bar'}")
    print(f"{'-'*60}")
    
    for state in ['00', '01', '10', '11']:
        count = results[state]
        prob = count / shots
        bar = '█' * int(prob * 50)
        marker = ' ← TARGET' if state == target else ''
        print(f"|{state}⟩{' '*5} {count:<10} {prob:<15.1%} {bar}{marker}")
    
    # Success rate
    success_rate = results[target] / shots
    print(f"\n{'='*60}")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Expected: ~100% (with 1 iteration)")
    
    if success_rate > 0.8:
        print("✅ Grover's algorithm successfully found the target!")
    else:
        print("⚠️  Lower than expected success rate (may be due to errors)")
    
    return results


def demonstrate_scaling(client: QSyscallClient):
    """Demonstrate how Grover's algorithm scales."""
    print(f"\n{'='*60}")
    print("Grover's Algorithm Scaling")
    print(f"{'='*60}\n")
    
    print("For larger databases:")
    print(f"{'Qubits':<10} {'States':<10} {'Classical':<15} {'Quantum':<15} {'Speedup'}")
    print(f"{'-'*70}")
    
    for n_qubits in [2, 4, 8, 16, 32]:
        n_states = 2 ** n_qubits
        classical_queries = n_states / 2  # Average
        quantum_iterations = math.pi / 4 * math.sqrt(n_states)
        speedup = classical_queries / quantum_iterations
        
        print(f"{n_qubits:<10} {n_states:<10} {classical_queries:<15.0f} "
              f"{quantum_iterations:<15.1f} {speedup:<15.1f}x")
    
    print(f"\n{'='*60}")
    print("Note: This implementation uses 2 qubits for demonstration.")
    print("Larger implementations would require more qubits and gates.")
    print(f"{'='*60}")


def main():
    """Run Grover's algorithm demonstrations."""
    print("="*60)
    print("Grover's Search Algorithm")
    print("="*60)
    print("\nGrover's algorithm provides quadratic speedup for unstructured search.")
    print("It can find a marked item in an unsorted database of N items")
    print("in O(√N) time, compared to O(N) classically.\n")
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("Negotiating capabilities...")
    caps_result = client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",
        "CAP_MEASURE"
    ])
    print(f"Session ID: {caps_result['session_id']}")
    print(f"Granted: {caps_result.get('granted', [])}\n")
    
    # Search for each possible state
    targets = ["00", "01", "10", "11"]
    
    for target in targets:
        run_grovers_search(client, target, shots=50)
        print()
    
    # Demonstrate scaling
    demonstrate_scaling(client)
    
    # Final telemetry
    print(f"\n{'='*60}")
    print("Telemetry")
    print(f"{'='*60}")
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ Grover's algorithm demonstrations completed!")


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
