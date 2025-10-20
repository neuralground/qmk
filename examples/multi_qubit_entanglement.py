#!/usr/bin/env python3
"""
Multi-Qubit Entanglement Examples

Demonstrates creating various entangled states:
- GHZ state (Greenberger-Horne-Zeilinger)
- W state
- Cluster state
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient


def create_ghz_state(n_qubits: int = 4) -> dict:
    """
    Create an n-qubit GHZ state: |GHZ⟩ = (|00...0⟩ + |11...1⟩)/√2
    
    Circuit:
    q0: ─H─●─────●─────●─────M
           │     │     │
    q1: ───X─────┼─────┼─────M
                 │     │
    q2: ─────────X─────┼─────M
                       │
    q3: ───────────────X─────M
    
    Args:
        n_qubits: Number of qubits (default 4)
    
    Returns:
        QVM graph dictionary
    """
    qubit_ids = [f"q{i}" for i in range(n_qubits)]
    
    nodes = [
        # Allocate qubits
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": qubit_ids,
            "profile": "logical:surface_code(d=3)"
        },
        # Hadamard on first qubit
        {
            "id": "h0",
            "op": "H",
            "qubits": ["q0"],
            "deps": ["alloc"]
        }
    ]
    
    edges = [{"from": "alloc", "to": "h0"}]
    
    # CNOTs to create entanglement
    prev_node = "h0"
    for i in range(1, n_qubits):
        cnot_id = f"cnot_{i}"
        nodes.append({
            "id": cnot_id,
            "op": "CNOT",
            "qubits": ["q0", f"q{i}"],
            "deps": [prev_node]
        })
        edges.append({"from": prev_node, "to": cnot_id})
        prev_node = cnot_id
    
    # Measurements
    measure_deps = []
    for i in range(n_qubits):
        measure_id = f"m{i}"
        nodes.append({
            "id": measure_id,
            "op": "MEASURE_Z",
            "qubits": [f"q{i}"],
            "outputs": [measure_id],
            "deps": [prev_node]
        })
        edges.append({"from": prev_node, "to": measure_id})
        measure_deps.append(measure_id)
    
    # Free qubits
    nodes.append({
        "id": "free",
        "op": "FREE_LQ",
        "qubits": qubit_ids,
        "deps": measure_deps
    })
    
    for dep in measure_deps:
        edges.append({"from": dep, "to": "free"})
    
    return {
        "version": "0.1",
        "metadata": {
            "name": f"ghz_{n_qubits}",
            "description": f"{n_qubits}-qubit GHZ state"
        },
        "nodes": nodes,
        "edges": edges
    }


def create_w_state(n_qubits: int = 3) -> dict:
    """
    Create an n-qubit W state: |W⟩ = (|100...0⟩ + |010...0⟩ + ... + |00...01⟩)/√n
    
    This is a simplified construction using rotations and CNOTs.
    
    Args:
        n_qubits: Number of qubits (default 3)
    
    Returns:
        QVM graph dictionary
    """
    import math
    
    qubit_ids = [f"q{i}" for i in range(n_qubits)]
    
    nodes = [
        # Allocate qubits
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": qubit_ids,
            "profile": "logical:surface_code(d=3)"
        },
        # X on first qubit to start with |1⟩
        {
            "id": "x0",
            "op": "X",
            "qubits": ["q0"],
            "deps": ["alloc"]
        }
    ]
    
    edges = [{"from": "alloc", "to": "x0"}]
    
    # Create W state using controlled rotations
    prev_node = "x0"
    for i in range(n_qubits - 1):
        # Rotation to distribute amplitude
        ry_id = f"ry_{i}"
        angle = math.acos(math.sqrt(1.0 / (n_qubits - i)))
        nodes.append({
            "id": ry_id,
            "op": "RY",
            "qubits": [f"q{i}"],
            "params": {"theta": angle},
            "deps": [prev_node]
        })
        edges.append({"from": prev_node, "to": ry_id})
        
        # CNOT to next qubit
        cnot_id = f"cnot_{i}"
        nodes.append({
            "id": cnot_id,
            "op": "CNOT",
            "qubits": [f"q{i}", f"q{i+1}"],
            "deps": [ry_id]
        })
        edges.append({"from": ry_id, "to": cnot_id})
        prev_node = cnot_id
    
    # Measurements
    measure_deps = []
    for i in range(n_qubits):
        measure_id = f"m{i}"
        nodes.append({
            "id": measure_id,
            "op": "MEASURE_Z",
            "qubits": [f"q{i}"],
            "outputs": [measure_id],
            "deps": [prev_node]
        })
        edges.append({"from": prev_node, "to": measure_id})
        measure_deps.append(measure_id)
    
    # Free qubits
    nodes.append({
        "id": "free",
        "op": "FREE_LQ",
        "qubits": qubit_ids,
        "deps": measure_deps
    })
    
    for dep in measure_deps:
        edges.append({"from": dep, "to": "free"})
    
    return {
        "version": "0.1",
        "metadata": {
            "name": f"w_{n_qubits}",
            "description": f"{n_qubits}-qubit W state"
        },
        "nodes": nodes,
        "edges": edges
    }


def analyze_measurements(events: dict, n_qubits: int, state_type: str):
    """Analyze measurement outcomes."""
    measurements = [events.get(f"m{i}", 0) for i in range(n_qubits)]
    bitstring = ''.join(str(m) for m in measurements)
    hamming_weight = sum(measurements)
    
    print(f"  Measurements: {bitstring}")
    print(f"  Hamming weight: {hamming_weight}")
    
    if state_type == "GHZ":
        # GHZ state should give all 0s or all 1s
        if hamming_weight == 0 or hamming_weight == n_qubits:
            print(f"  ✓ Expected outcome for GHZ state")
        else:
            print(f"  ⚠ Unexpected outcome (may be due to errors)")
    
    elif state_type == "W":
        # W state should give exactly one 1
        if hamming_weight == 1:
            print(f"  ✓ Expected outcome for W state")
        else:
            print(f"  ⚠ Unexpected outcome (may be due to errors)")


def main():
    """Run multi-qubit entanglement examples."""
    
    print("=== Multi-Qubit Entanglement Examples ===\n")
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("Negotiating capabilities...")
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}\n")
    
    # Example 1: 4-qubit GHZ state
    print("=" * 50)
    print("Example 1: 4-Qubit GHZ State")
    print("=" * 50)
    print("\nGHZ state: |GHZ⟩ = (|0000⟩ + |1111⟩)/√2")
    print("Expected measurements: 0000 or 1111\n")
    
    ghz_graph = create_ghz_state(n_qubits=4)
    print("Submitting GHZ circuit...")
    result = client.submit_and_wait(ghz_graph, timeout_ms=10000, seed=42)
    
    if result['state'] == 'COMPLETED':
        print("✅ Job completed")
        analyze_measurements(result['events'], 4, "GHZ")
    else:
        print(f"❌ Job failed: {result.get('error', 'Unknown')}")
    
    # Example 2: 3-qubit W state
    print("\n" + "=" * 50)
    print("Example 2: 3-Qubit W State")
    print("=" * 50)
    print("\nW state: |W⟩ = (|100⟩ + |010⟩ + |001⟩)/√3")
    print("Expected measurements: exactly one 1\n")
    
    w_graph = create_w_state(n_qubits=3)
    print("Submitting W state circuit...")
    result = client.submit_and_wait(w_graph, timeout_ms=10000, seed=43)
    
    if result['state'] == 'COMPLETED':
        print("✅ Job completed")
        analyze_measurements(result['events'], 3, "W")
    else:
        print(f"❌ Job failed: {result.get('error', 'Unknown')}")
    
    # Example 3: Larger GHZ state
    print("\n" + "=" * 50)
    print("Example 3: 6-Qubit GHZ State")
    print("=" * 50)
    print("\nScaling to 6 qubits...\n")
    
    ghz6_graph = create_ghz_state(n_qubits=6)
    print("Submitting 6-qubit GHZ circuit...")
    result = client.submit_and_wait(ghz6_graph, timeout_ms=10000, seed=44)
    
    if result['state'] == 'COMPLETED':
        print("✅ Job completed")
        analyze_measurements(result['events'], 6, "GHZ")
    else:
        print(f"❌ Job failed: {result.get('error', 'Unknown')}")
    
    # Final telemetry
    print("\n" + "=" * 50)
    print("Telemetry")
    print("=" * 50)
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Logical qubits allocated: {usage['logical_qubits_allocated']}")
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ All entanglement examples completed!")


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
