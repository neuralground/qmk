"""
Hardware Adapters Demonstration

Shows how to use hardware adapters to connect to quantum backends.
"""

import time
from kernel.hardware import (
    SimulatedBackend, AzureQuantumBackend, BackendManager,
    HardwareStatus
)


# Sample circuit
BELL_STATE_CIRCUIT = {
    "name": "bell_state",
    "nodes": [
        {"node_id": "n0", "op": "ALLOC_LQ", "qubits": ["q0"]},
        {"node_id": "n1", "op": "ALLOC_LQ", "qubits": ["q1"]},
        {"node_id": "n2", "op": "H", "qubits": ["q0"]},
        {"node_id": "n3", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n4", "op": "MEASURE_Z", "qubits": ["q0"], "params": {"result": "r0"}},
        {"node_id": "n5", "op": "MEASURE_Z", "qubits": ["q1"], "params": {"result": "r1"}},
    ]
}


def demo_simulated_backend():
    """Demonstrate simulated backend."""
    print("=" * 70)
    print("1. SIMULATED BACKEND")
    print("=" * 70)
    
    # Create and connect to simulated backend
    backend = SimulatedBackend(
        backend_name="Simulated QPU",
        backend_id="sim_qpu_001",
        num_qubits=20,
        error_rate=0.001
    )
    
    print("\nConnecting to simulated backend...")
    backend.connect()
    print(f"  Status: {backend.get_status().value}")
    
    # Get capabilities
    caps = backend.get_capabilities()
    print(f"\n📊 Capabilities:")
    print(f"  Max qubits: {caps.max_qubits}")
    print(f"  Supported gates: {', '.join(caps.supported_gates[:8])}...")
    print(f"  Native gates: {', '.join(caps.native_gates)}")
    print(f"  Mid-circuit measurement: {caps.has_mid_circuit_measurement}")
    print(f"  QEC capable: {caps.qec_capable}")
    
    # Get calibration data
    calib = backend.get_calibration_data()
    print(f"\n🔧 Calibration Data:")
    print(f"  Timestamp: {calib.timestamp:.2f}")
    print(f"  Average T1: {sum(calib.qubit_t1.values())/len(calib.qubit_t1):.2f} μs")
    print(f"  Average T2: {sum(calib.qubit_t2.values())/len(calib.qubit_t2):.2f} μs")
    print(f"  Single-qubit fidelity: {calib.gate_fidelities['single_qubit']:.4f}")
    print(f"  Two-qubit fidelity: {calib.gate_fidelities['two_qubit']:.4f}")
    
    # Submit job
    print(f"\n🚀 Submitting Bell state circuit...")
    backend_job_id = backend.submit_job("job_001", BELL_STATE_CIRCUIT, shots=1000)
    print(f"  Backend job ID: {backend_job_id}")
    
    # Wait for completion
    print(f"  Waiting for execution...")
    time.sleep(0.3)
    
    # Get result
    result = backend.get_job_result(backend_job_id)
    print(f"\n✅ Job completed!")
    print(f"  Status: {result.status.value}")
    print(f"  Execution time: {result.execution_time:.4f}s")
    print(f"  Measurements: {len(result.measurements)} qubits")
    
    # Show measurement statistics
    for qubit, measurements in result.measurements.items():
        zeros = measurements.count(0)
        ones = measurements.count(1)
        print(f"    {qubit}: |0⟩={zeros}, |1⟩={ones} ({zeros/len(measurements)*100:.1f}% / {ones/len(measurements)*100:.1f}%)")
    
    backend.disconnect()


def demo_backend_manager():
    """Demonstrate backend manager."""
    print("\n" + "=" * 70)
    print("2. BACKEND MANAGER")
    print("=" * 70)
    
    # Create manager
    manager = BackendManager()
    
    # Register multiple backends
    print("\nRegistering backends...")
    
    sim1 = SimulatedBackend(backend_id="sim_small", num_qubits=10)
    sim1.connect()
    manager.register_backend(sim1, set_as_default=True)
    print(f"  ✓ Registered: {sim1.backend_name} (10 qubits)")
    
    sim2 = SimulatedBackend(backend_id="sim_large", num_qubits=50)
    sim2.connect()
    manager.register_backend(sim2)
    print(f"  ✓ Registered: {sim2.backend_name} (50 qubits)")
    
    azure = AzureQuantumBackend(backend_id="azure_qpu")
    azure.connect()
    manager.register_backend(azure)
    print(f"  ✓ Registered: {azure.backend_name}")
    
    # List backends
    print(f"\n📋 Available Backends:")
    backends = manager.list_backends()
    for backend_info in backends:
        default_marker = " (default)" if backend_info["is_default"] else ""
        print(f"  • {backend_info['backend_name']}: {backend_info['status']}{default_marker}")
    
    # Get health status
    health = manager.get_health_status()
    print(f"\n💚 Health Status:")
    print(f"  Total backends: {health['total_backends']}")
    print(f"  Online: {health['online_backends']}")
    print(f"  Offline: {health['offline_backends']}")
    print(f"  Default: {health['default_backend']}")
    
    # Select best backend
    print(f"\n🎯 Backend Selection:")
    
    # Small job
    best = manager.select_best_backend({"qubits": 5})
    print(f"  For 5 qubits: {best}")
    
    # Large job
    best = manager.select_best_backend({"qubits": 30})
    print(f"  For 30 qubits: {best}")
    
    # Submit job through manager
    print(f"\n🚀 Submitting job through manager...")
    backend_id, backend_job_id = manager.submit_job(
        "managed_job_001",
        BELL_STATE_CIRCUIT,
        shots=500
    )
    print(f"  Routed to: {backend_id}")
    print(f"  Backend job ID: {backend_job_id}")
    
    # Wait and get result
    time.sleep(0.3)
    result = manager.get_job_result(backend_id, backend_job_id)
    print(f"  Status: {result.status.value}")


def demo_azure_backend():
    """Demonstrate Azure Quantum backend (stub)."""
    print("\n" + "=" * 70)
    print("3. AZURE QUANTUM BACKEND")
    print("=" * 70)
    
    print("\nNote: This is a stub implementation for demonstration.")
    print("Real Azure Quantum integration requires azure-quantum SDK.\n")
    
    # Create Azure backend
    backend = AzureQuantumBackend(
        backend_name="Azure Quantum IonQ",
        backend_id="azure_ionq",
        workspace_id="my-workspace",
        target_id="ionq.simulator"
    )
    
    print(f"Backend: {backend.backend_name}")
    print(f"Workspace: {backend.workspace_id}")
    print(f"Target: {backend.target_id}")
    
    # Connect
    print(f"\nConnecting to Azure Quantum...")
    backend.connect()
    print(f"  Status: {backend.get_status().value}")
    
    # Get capabilities
    caps = backend.get_capabilities()
    print(f"\n📊 Capabilities:")
    print(f"  Max qubits: {caps.max_qubits}")
    print(f"  QEC capable: {caps.qec_capable}")
    
    # Submit job (stub)
    print(f"\n🚀 Submitting job (stub)...")
    backend_job_id = backend.submit_job("azure_job_001", BELL_STATE_CIRCUIT, shots=1000)
    print(f"  Azure job ID: {backend_job_id}")
    print(f"  Note: Job submission is simulated")


def main():
    """Run all hardware adapter demonstrations."""
    print("\n" + "=" * 70)
    print("QMK HARDWARE ADAPTERS DEMONSTRATION")
    print("=" * 70)
    print("\nDemonstrating:")
    print("  • Simulated backend")
    print("  • Backend manager")
    print("  • Azure Quantum integration (stub)")
    print()
    
    demo_simulated_backend()
    demo_backend_manager()
    demo_azure_backend()
    
    print("\n" + "=" * 70)
    print("HARDWARE ADAPTERS COMPLETE")
    print("=" * 70)
    print("\n✅ QMK provides a complete HAL for quantum hardware!")
    print("\nKey capabilities:")
    print("  • Unified interface for multiple backends")
    print("  • Automatic backend selection")
    print("  • Health monitoring")
    print("  • Calibration data access")
    print("  • Job management and routing")


if __name__ == "__main__":
    main()
