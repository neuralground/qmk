#!/usr/bin/env python3
"""
Simple Bell State Example

Demonstrates using the QMK client library to submit and execute a Bell state
preparation circuit using QVM Assembly.
"""

import sys
from pathlib import Path

# Add parent directory to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient

# Import ASM runner
try:
    from asm_runner import assemble_file
except ImportError:
    from examples.asm_runner import assemble_file


def main():
    """Run Bell state example."""
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    print("=== QMK Bell State Example ===\n")
    
    # Step 1: Negotiate capabilities
    print("1. Negotiating capabilities...")
    caps_result = client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",  # Required for quantum operations
        "CAP_MEASURE"   # Required for measurements
    ])
    
    print(f"   Session ID: {caps_result['session_id']}")
    print(f"   Granted: {caps_result['granted']}")
    print(f"   Denied: {caps_result['denied']}")
    print()
    
    # Step 2: Load Bell state circuit from ASM
    print("2. Loading Bell state circuit from ASM...")
    graph = assemble_file("bell_state.qvm.asm")
    
    print(f"   Nodes: {len(graph['program']['nodes'])}")
    print(f"   Resources: {len(graph['resources']['vqs'])} qubits")
    print()
    
    # Step 3: Submit job
    print("3. Submitting job...")
    job_id = client.submit_job(
        graph=graph,
        priority=10,
        seed=42,
        debug=True
    )
    
    print(f"   Job ID: {job_id}")
    print()
    
    # Step 4: Wait for completion
    print("4. Waiting for job completion...")
    result = client.wait_for_job(job_id, timeout_ms=10000)
    
    print(f"   State: {result['state']}")
    print(f"   Progress: {result['progress']}")
    
    if result['state'] == 'COMPLETED':
        print(f"   Events: {result.get('events', {})}")
        print()
        
        # Step 5: Show execution context
        context = result.get('execution_context', {})
        if context:
            print("5. Execution context...")
            print(f"   Backend: {context.get('backend', 'Unknown')}")
            print(f"   Simulator: {context.get('simulator', 'Unknown')}")
            config = context.get('configuration', {})
            if config:
                print(f"   Configuration:")
                print(f"      Max physical qubits: {config.get('max_physical_qubits', 'N/A')}")
                print(f"      Deterministic: {config.get('deterministic', False)}")
                print(f"      Certification: {config.get('certification_required', False)}")
            print()
        
        # Step 6: Get telemetry
        print("6. Resource usage summary...")
        telemetry = client.get_telemetry()
        
        # Show peak usage during execution
        peak = result.get('peak_resources', {})
        if peak:
            print(f"   Peak usage (during execution):")
            print(f"      Logical qubits: {peak.get('logical_qubits', 0)}")
            print(f"      Physical qubits: {peak.get('physical_qubits', 0)}")
            print(f"      Channels: {peak.get('channels', 0)}")
        
        # Show current usage (after cleanup)
        current = telemetry['resource_usage']
        print(f"   Current usage (after cleanup):")
        print(f"      Logical qubits: {current['logical_qubits_allocated']} ✅")
        print(f"      Physical qubits: {current['physical_qubits_used']} ✅")
        print(f"      Channels: {current['channels_open']} ✅")
        print()
        
        print("✅ Bell state preparation completed successfully!")
        print("   (Resources automatically cleaned up)")
    
    elif result['state'] == 'FAILED':
        print(f"   Error: {result.get('error', {})}")
        print()
        print("❌ Job failed")
    
    else:
        print(f"   Unexpected state: {result['state']}")


if __name__ == "__main__":
    # Note: This requires the QMK server to be running
    # Start with: python -m kernel.qmk_server
    
    try:
        main()
    except ConnectionRefusedError:
        print("❌ Error: QMK server not running")
        print("   Start with: python -m kernel.qmk_server")
    except Exception as e:
        print(f"❌ Error: {e}")
