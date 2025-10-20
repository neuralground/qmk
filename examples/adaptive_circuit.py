#!/usr/bin/env python3
"""
Adaptive Circuit Example

Demonstrates mid-circuit measurements with conditional operations using guards.
This example implements a simple quantum error correction scenario where
measurements guide subsequent corrections.
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


def create_adaptive_circuit() -> dict:
    """
    Create an adaptive circuit with mid-circuit measurements and guards.
    
    Circuit flow:
    1. Prepare |+⟩ state on q0
    2. Create entanglement with q1
    3. Measure q1 (syndrome measurement)
    4. Conditionally apply correction to q0 based on measurement
    5. Final measurement of q0
    
    Returns:
        QVM graph dictionary
    """
    return {
        "version": "0.1",
        "program": {
            "nodes": [
                # Allocate qubits
                {
                    "id": "alloc",
                    "op": "ALLOC_LQ",
                    "args": {
                        "n": 2,
                        "profile": "logical:Surface(d=3)"
                    },
                    "vqs": ["q0", "q1"]
                },
                
                # Prepare |+⟩ state on q0
                {
                    "id": "h0",
                    "op": "APPLY_H",
                    "vqs": ["q0"]
                },
                
                # Prepare |+⟩ state on q1 (ancilla)
                {
                    "id": "h1",
                    "op": "APPLY_H",
                    "vqs": ["q1"]
                },
                
                # Entangle for syndrome extraction
                {
                    "id": "cnot1",
                    "op": "APPLY_CNOT",
                    "vqs": ["q0", "q1"]
                },
                
                # Syndrome measurement (mid-circuit)
                {
                    "id": "syndrome",
                    "op": "MEASURE_Z",
                    "vqs": ["q1"],
                    "produces": ["syndrome_bit"]
                },
                
                # Conditional correction: Apply X to q0 if syndrome_bit == 1
                {
                    "id": "correction",
                    "op": "APPLY_X",
                    "vqs": ["q0"],
                    "guard": {
                        "event": "syndrome_bit",
                        "equals": 1
                    }
                },
                
                # Additional operations on q0
                {
                    "id": "h2",
                    "op": "APPLY_H",
                    "vqs": ["q0"]
                },
                
                # Final measurement
                {
                    "id": "final_measure",
                    "op": "MEASURE_Z",
                    "vqs": ["q0"],
                    "produces": ["result"]
                }
            ]
        },
        "resources": {
            "vqs": ["q0", "q1"],
            "chs": [],
            "events": ["syndrome_bit", "result"]
        }
    }


def create_multi_round_adaptive() -> dict:
    """
    Create a more complex adaptive circuit with multiple measurement rounds.
    
    Implements a 3-qubit repetition code with syndrome measurements using ASM.
    
    Returns:
        QVM graph dictionary
    """
    return assemble_file("adaptive_multi_round.qvm.asm")


def main():
    """Run adaptive circuit examples."""
    
    print("=== Adaptive Circuit Examples ===\n")
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("Negotiating capabilities...")
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}\n")
    
    # Example 1: Simple adaptive circuit
    print("=" * 60)
    print("Example 1: Simple Adaptive Circuit with Conditional Correction")
    print("=" * 60)
    print("\nThis circuit:")
    print("1. Prepares |+⟩ state")
    print("2. Performs syndrome measurement")
    print("3. Conditionally applies correction based on measurement")
    print("4. Measures final result\n")
    
    simple_circuit = create_adaptive_circuit()
    
    # Run multiple times to see different outcomes
    print("Running 3 iterations with different seeds:\n")
    
    for i in range(3):
        print(f"--- Iteration {i+1} ---")
        result = client.submit_and_wait(
            simple_circuit,
            timeout_ms=10000,
            seed=100 + i
        )
        
        if result['state'] == 'COMPLETED':
            events = result['events']
            syndrome = events.get('syndrome_bit', 0)
            final = events.get('result', 0)
            
            print(f"  Syndrome measurement: {syndrome}")
            print(f"  Correction applied: {'Yes' if syndrome == 1 else 'No'}")
            print(f"  Final result: {final}")
            print()
        else:
            print(f"  ❌ Job failed: {result.get('error', 'Unknown')}\n")
    
    # Example 2: Multi-round adaptive circuit
    print("=" * 60)
    print("Example 2: Multi-Round Syndrome Measurement (3-Qubit Code)")
    print("=" * 60)
    print("\nThis implements a 3-qubit repetition code with:")
    print("- 2 syndrome measurements (parity checks)")
    print("- Conditional corrections based on syndrome pattern")
    print("- Final readout of all data qubits\n")
    
    multi_round = create_multi_round_adaptive()
    
    print("Submitting multi-round adaptive circuit...")
    result = client.submit_and_wait(multi_round, timeout_ms=15000, seed=200)
    
    if result['state'] == 'COMPLETED':
        print("✅ Job completed\n")
        events = result['events']
        
        # Syndrome measurements
        s01 = events.get('s01_r1', 0)
        s12 = events.get('s12_r1', 0)
        
        print(f"Syndrome measurements:")
        print(f"  s01 (d0⊕d1): {s01}")
        print(f"  s12 (d1⊕d2): {s12}")
        
        # Determine which qubit had error
        if s01 == 1 and s12 == 0:
            error_qubit = "d0"
        elif s01 == 1 and s12 == 1:
            error_qubit = "d1"
        elif s01 == 0 and s12 == 1:
            error_qubit = "d2"
        else:
            error_qubit = "none"
        
        print(f"  Detected error on: {error_qubit}")
        
        # Final measurements
        m_d0 = events.get('m_d0', 0)
        m_d1 = events.get('m_d1', 0)
        m_d2 = events.get('m_d2', 0)
        
        print(f"\nFinal measurements:")
        print(f"  d0: {m_d0}")
        print(f"  d1: {m_d1}")
        print(f"  d2: {m_d2}")
        
        # Check if all agree (successful correction)
        if m_d0 == m_d1 == m_d2:
            print(f"  ✓ All qubits agree → decoded value: {m_d0}")
        else:
            print(f"  ⚠ Qubits don't agree (uncorrectable error)")
    else:
        print(f"❌ Job failed: {result.get('error', 'Unknown')}")
    
    # Telemetry
    print("\n" + "=" * 60)
    print("Telemetry")
    print("=" * 60)
    telemetry = client.get_telemetry()
    usage = telemetry['resource_usage']
    print(f"Physical qubits used: {usage['physical_qubits_used']}")
    print(f"Utilization: {usage['utilization']:.1%}")
    
    print("\n✅ Adaptive circuit examples completed!")


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
