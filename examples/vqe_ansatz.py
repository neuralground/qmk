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


def create_vqe_ansatz(theta1: float, theta2: float, theta3: float) -> dict:
    """
    Create a simple VQE ansatz circuit.
    
    Circuit structure:
    q0: ─H─Rz(θ1)─●─Rz(θ3)─M
                   │
    q1: ─H─Rz(θ2)─X────────M
    
    Args:
        theta1, theta2, theta3: Rotation angles in radians
    
    Returns:
        QVM graph dictionary
    """
    return {
        "version": "0.1",
        "metadata": {
            "name": "vqe_ansatz",
            "description": f"VQE ansatz with θ=({theta1:.3f}, {theta2:.3f}, {theta3:.3f})"
        },
        "nodes": [
            # Allocate qubits
            {
                "id": "alloc",
                "op": "ALLOC_LQ",
                "outputs": ["q0", "q1"],
                "profile": "logical:surface_code(d=3)"
            },
            # Initial Hadamards
            {
                "id": "h0",
                "op": "H",
                "qubits": ["q0"],
                "deps": ["alloc"]
            },
            {
                "id": "h1",
                "op": "H",
                "qubits": ["q1"],
                "deps": ["alloc"]
            },
            # First rotation layer
            {
                "id": "rz0",
                "op": "RZ",
                "qubits": ["q0"],
                "params": {"theta": theta1},
                "deps": ["h0"]
            },
            {
                "id": "rz1",
                "op": "RZ",
                "qubits": ["q1"],
                "params": {"theta": theta2},
                "deps": ["h1"]
            },
            # Entangling layer (CNOT)
            {
                "id": "cnot",
                "op": "CNOT",
                "qubits": ["q0", "q1"],
                "deps": ["rz0", "rz1"]
            },
            # Final rotation
            {
                "id": "rz2",
                "op": "RZ",
                "qubits": ["q0"],
                "params": {"theta": theta3},
                "deps": ["cnot"]
            },
            # Measurements
            {
                "id": "m0",
                "op": "MEASURE_Z",
                "qubits": ["q0"],
                "outputs": ["m0"],
                "deps": ["rz2"]
            },
            {
                "id": "m1",
                "op": "MEASURE_Z",
                "qubits": ["q1"],
                "outputs": ["m1"],
                "deps": ["cnot"]
            },
            # Free qubits
            {
                "id": "free",
                "op": "FREE_LQ",
                "qubits": ["q0", "q1"],
                "deps": ["m0", "m1"]
            }
        ],
        "edges": [
            {"from": "alloc", "to": "h0"},
            {"from": "alloc", "to": "h1"},
            {"from": "h0", "to": "rz0"},
            {"from": "h1", "to": "rz1"},
            {"from": "rz0", "to": "cnot"},
            {"from": "rz1", "to": "cnot"},
            {"from": "cnot", "to": "rz2"},
            {"from": "rz2", "to": "m0"},
            {"from": "cnot", "to": "m1"},
            {"from": "m0", "to": "free"},
            {"from": "m1", "to": "free"}
        ]
    }


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
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}\n")
    
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
    print(f"Total jobs run: {len(parameter_sets)}")
    print(f"Physical qubits used: {telemetry['resource_usage']['physical_qubits_used']}")


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
