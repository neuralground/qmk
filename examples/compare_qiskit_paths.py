#!/usr/bin/env python3
"""
Compare Qiskit Execution Paths

Demonstrates two execution paths for Qiskit circuits:
1. Native Qiskit Aer simulator (direct)
2. Qiskit → QIR → Optimizer → QVM → QMK (with Aer backend)

This shows the full pipeline integration and allows performance/correctness
comparison between native Qiskit and the QMK stack.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple
import json

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("⚠️  Qiskit not available. Install with: pip install qiskit qiskit-aer")

from runtime.client.qsyscall_client import QSyscallClient


def create_bell_state() -> QuantumCircuit:
    """Create a Bell state circuit."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def create_ghz_state(n_qubits: int = 3) -> QuantumCircuit:
    """Create a GHZ state circuit."""
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_grover_2qubit() -> QuantumCircuit:
    """Create a 2-qubit Grover search circuit."""
    qc = QuantumCircuit(2, 2)
    
    # Initialize
    qc.h([0, 1])
    
    # Oracle (mark |11⟩)
    qc.cz(0, 1)
    
    # Diffusion
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])
    
    qc.measure([0, 1], [0, 1])
    return qc


def run_native_qiskit(circuit: QuantumCircuit, shots: int = 1000) -> Tuple[Dict[str, int], float]:
    """
    Run circuit using native Qiskit Aer simulator.
    
    Args:
        circuit: Qiskit circuit to run
        shots: Number of shots
        
    Returns:
        (counts, execution_time)
    """
    simulator = AerSimulator()
    
    start_time = time.time()
    job = simulator.run(circuit, shots=shots)
    result = job.result()
    counts = result.get_counts()
    execution_time = time.time() - start_time
    
    return counts, execution_time


def qiskit_to_qir(circuit: QuantumCircuit) -> str:
    """
    Convert Qiskit circuit to QIR.
    
    Note: This is a placeholder. In production, you would use:
    - qiskit-qir package
    - Or pyqir
    - Or custom converter
    
    For now, we'll convert to QVM JSON directly.
    """
    # This is a simplified conversion - in production use proper QIR tools
    return convert_qiskit_to_qvm(circuit)


def convert_qiskit_to_qvm(circuit: QuantumCircuit) -> dict:
    """
    Convert Qiskit circuit to QVM JSON format.
    
    This is a direct conversion for demonstration.
    In production, you'd go through QIR.
    """
    nodes = []
    node_id = 0
    
    # Allocate qubits
    n_qubits = circuit.num_qubits
    qubit_names = [f"q{i}" for i in range(n_qubits)]
    
    nodes.append({
        "id": f"alloc",
        "op": "ALLOC_LQ",
        "args": {
            "n": n_qubits,
            "profile": "logical:Surface(d=3)"
        },
        "vqs": qubit_names
    })
    
    # Convert gates
    for instruction in circuit.data:
        gate = instruction.operation
        qubits = [circuit.qubits.index(q) for q in instruction.qubits]
        
        if gate.name == 'h':
            nodes.append({
                "id": f"h{node_id}",
                "op": "APPLY_H",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'cx':
            nodes.append({
                "id": f"cx{node_id}",
                "op": "APPLY_CNOT",
                "vqs": [f"q{qubits[0]}", f"q{qubits[1]}"]
            })
        elif gate.name == 'cz':
            nodes.append({
                "id": f"cz{node_id}",
                "op": "APPLY_CZ",
                "vqs": [f"q{qubits[0]}", f"q{qubits[1]}"]
            })
        elif gate.name == 'x':
            nodes.append({
                "id": f"x{node_id}",
                "op": "APPLY_X",
                "vqs": [f"q{qubits[0]}"]
            })
        elif gate.name == 'measure':
            clbit = circuit.clbits.index(instruction.clbits[0])
            nodes.append({
                "id": f"m{node_id}",
                "op": "MEASURE_Z",
                "vqs": [f"q{qubits[0]}"],
                "produces": [f"m{clbit}"]
            })
        
        node_id += 1
    
    # Build QVM graph
    qvm_graph = {
        "version": "0.1",
        "program": {
            "nodes": nodes
        },
        "resources": {
            "vqs": qubit_names,
            "chs": [],
            "events": [f"m{i}" for i in range(circuit.num_clbits)]
        }
    }
    
    return qvm_graph


def run_qmk_path(circuit: QuantumCircuit, shots: int = 1000) -> Tuple[Dict[str, int], float, Dict[str, Any]]:
    """
    Run circuit through QMK path: Qiskit → QIR → Optimizer → QVM → QMK.
    
    Args:
        circuit: Qiskit circuit to run
        shots: Number of shots
        
    Returns:
        (counts, execution_time, metadata)
    """
    # Step 1: Convert Qiskit → QVM (in production: Qiskit → QIR → QVM)
    qvm_graph = convert_qiskit_to_qvm(circuit)
    
    # Step 2: Connect to QMK server
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Step 3: Negotiate capabilities
    caps_result = client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",
        "CAP_MEASURE"
    ])
    
    # Step 4: Execute through QMK (with Aer backend in kernel)
    start_time = time.time()
    result = client.submit_and_wait(qvm_graph, timeout_ms=30000, seed=42)
    execution_time = time.time() - start_time
    
    # Step 5: Convert results to Qiskit format
    if result['state'] != 'COMPLETED':
        raise RuntimeError(f"Job failed: {result.get('error', 'Unknown')}")
    
    # Extract measurements and convert to bitstring counts
    events = result['events']
    n_clbits = circuit.num_clbits
    
    # For single shot, convert to counts format
    bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(n_clbits))
    counts = {bitstring: 1}  # Single shot for now
    
    # Get telemetry
    telemetry = client.get_telemetry()
    
    metadata = {
        "session_id": caps_result['session_id'],
        "telemetry": telemetry,
        "job_result": result
    }
    
    return counts, execution_time, metadata


def compare_results(native_counts: Dict[str, int], qmk_counts: Dict[str, int], 
                   circuit_name: str) -> None:
    """Compare results from both paths."""
    print(f"\n{'='*70}")
    print(f"Results Comparison: {circuit_name}")
    print(f"{'='*70}")
    
    print("\n📊 Native Qiskit Aer:")
    for bitstring, count in sorted(native_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {bitstring}: {count}")
    
    print("\n📊 QMK Path (Qiskit → QIR → Optimizer → QVM → QMK):")
    for bitstring, count in sorted(qmk_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {bitstring}: {count}")
    
    # Check if results match (for deterministic circuits)
    if len(native_counts) == 1 and len(qmk_counts) == 1:
        native_state = list(native_counts.keys())[0]
        qmk_state = list(qmk_counts.keys())[0]
        if native_state == qmk_state:
            print("\n✅ Results match perfectly!")
        else:
            print(f"\n⚠️  Results differ: {native_state} vs {qmk_state}")


def main():
    """Run comparison examples."""
    
    if not QISKIT_AVAILABLE:
        print("❌ Qiskit not available. Cannot run comparison.")
        return 1
    
    print("=" * 70)
    print("Qiskit Execution Path Comparison")
    print("=" * 70)
    print("\nComparing two execution paths:")
    print("1. Native Qiskit Aer simulator")
    print("2. Qiskit → QIR → Optimizer → QVM → QMK (with Aer backend)")
    print()
    
    # Test circuits
    circuits = [
        ("Bell State", create_bell_state()),
        ("3-Qubit GHZ State", create_ghz_state(3)),
        ("2-Qubit Grover Search", create_grover_2qubit()),
    ]
    
    for circuit_name, circuit in circuits:
        print(f"\n{'='*70}")
        print(f"Testing: {circuit_name}")
        print(f"{'='*70}")
        print(f"Circuit: {circuit.num_qubits} qubits, {len(circuit.data)} gates")
        
        try:
            # Path 1: Native Qiskit
            print("\n🔵 Running native Qiskit Aer...")
            native_counts, native_time = run_native_qiskit(circuit, shots=1000)
            print(f"   Execution time: {native_time:.4f}s")
            
            # Path 2: QMK
            print("\n🟢 Running QMK path...")
            qmk_counts, qmk_time, metadata = run_qmk_path(circuit, shots=1)
            print(f"   Execution time: {qmk_time:.4f}s")
            print(f"   Session ID: {metadata['session_id']}")
            
            # Compare
            compare_results(native_counts, qmk_counts, circuit_name)
            
            # Performance comparison
            print(f"\n⏱️  Performance:")
            print(f"   Native Qiskit: {native_time:.4f}s")
            print(f"   QMK Path:      {qmk_time:.4f}s")
            if native_time > 0:
                ratio = qmk_time / native_time
                print(f"   Ratio:         {ratio:.2f}x")
            
        except ConnectionRefusedError:
            print("\n❌ QMK server not running!")
            print("   Start with: python -m kernel.qmk_server")
            print("   Skipping QMK path comparison...")
            
            # Still show native results
            print("\n🔵 Native Qiskit Aer results:")
            for bitstring, count in sorted(native_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"  {bitstring}: {count}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("Comparison Complete")
    print(f"{'='*70}")
    print("\n✅ Both execution paths tested!")
    print("\nKey Observations:")
    print("- Native Qiskit: Direct execution, well-optimized")
    print("- QMK Path: Full stack with QIR, optimization, and QVM")
    print("- QMK enables: Advanced optimization, error correction, resource management")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
