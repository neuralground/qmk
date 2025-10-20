#!/usr/bin/env python3
"""
VQE-Style Ansatz Example

Demonstrates a variational quantum eigensolver (VQE) style circuit with:
- Parameterized rotation gates
- Entangling layers
- Measurement in computational basis
- Multiple iterations with different parameters
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient

# Import ASM runner from same directory
try:
    from asm_runner import assemble_file
except ImportError:
    from examples.asm_runner import assemble_file


def create_vqe_ansatz(theta1: float, theta2: float, theta3: float) -> dict:
    """
    Create a simple VQE ansatz circuit using QVM assembly.
    
    Circuit structure:
    q0: ─H─Rz(θ1)─●─Rz(θ3)─M
                   │
    q1: ─H─Rz(θ2)─X────────M
    
    Args:
        theta1, theta2, theta3: Rotation angles in radians
    
    Returns:
        QVM graph dictionary
    """
    return assemble_file("vqe_ansatz.qasm", {
        "theta1": theta1,
        "theta2": theta2,
        "theta3": theta3
    })


def run_vqe_iteration(client: QSyscallClient, params: tuple, iteration: int):
    """
    Run a single VQE iteration.
    
    Args:
        client: QSyscall client
        params: Tuple of (theta1, theta2, theta3)
        iteration: Iteration number
    """
    theta1, theta2, theta3 = params
    
    print(f"\n--- Iteration {iteration} ---")
    print(f"Parameters: θ1={theta1:.3f}, θ2={theta2:.3f}, θ3={theta3:.3f}")
    
    # Create ansatz
    graph = create_vqe_ansatz(theta1, theta2, theta3)
    
    # Submit and wait
    result = client.submit_and_wait(graph, timeout_ms=5000, seed=42)
    
    if result['state'] == 'COMPLETED':
        events = result.get('events', {})
        m0 = events.get('m0', 0)
        m1 = events.get('m1', 0)
        
        # Calculate "energy" (simplified - just based on measurement outcomes)
        # In real VQE, this would be expectation value of Hamiltonian
        energy = m0 + m1 * 0.5
        
        print(f"Measurements: m0={m0}, m1={m1}")
        print(f"Energy: {energy:.3f}")
        
        return energy
    else:
        print(f"Job failed: {result.get('error', 'Unknown error')}")
        return None


def main():
    """Run VQE example with parameter sweep."""
    
    print("=== VQE-Style Ansatz Example ===\n")
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("Negotiating capabilities...")
    caps_result = client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",  # Required for quantum operations
        "CAP_MEASURE"   # Required for measurements
    ])
    print(f"Session ID: {caps_result['session_id']}")
    print(f"Granted: {caps_result.get('granted', [])}\n")
    
    # Parameter sweep (simplified VQE optimization)
    import math
    
    parameter_sets = [
        (0.0, 0.0, 0.0),           # Initial guess
        (math.pi/4, 0.0, 0.0),     # Vary theta1
        (math.pi/4, math.pi/4, 0.0),  # Vary theta2
        (math.pi/4, math.pi/4, math.pi/4),  # Vary theta3
        (math.pi/2, math.pi/2, math.pi/2),  # Another point
    ]
    
    energies = []
    
    for i, params in enumerate(parameter_sets, 1):
        energy = run_vqe_iteration(client, params, i)
        if energy is not None:
            energies.append((params, energy))
    
    # Find best parameters
    if energies:
        print("\n=== Results ===")
        print("\nAll energies:")
        for params, energy in energies:
            print(f"  θ=({params[0]:.3f}, {params[1]:.3f}, {params[2]:.3f}) → E={energy:.3f}")
        
        best_params, best_energy = min(energies, key=lambda x: x[1])
        print(f"\n✅ Best parameters: θ=({best_params[0]:.3f}, {best_params[1]:.3f}, {best_params[2]:.3f})")
        print(f"   Best energy: {best_energy:.3f}")
        
        # Get final telemetry
        print("\n=== Telemetry ===")
        telemetry = client.get_telemetry()
        print(f"Successful jobs: {len(energies)}/{len(parameter_sets)}")
        print(f"Physical qubits used: {telemetry['resource_usage']['physical_qubits_used']}")
    else:
        print("\n❌ All jobs failed - no results to show")
        print("   Check the error messages above for details")


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
