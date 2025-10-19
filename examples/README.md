# QMK Examples

This directory contains examples demonstrating how to use the QMK client library.

## Prerequisites

Start the QMK server:

```bash
python -m kernel.qmk_server
```

The server will listen on `/tmp/qmk.sock` by default.

## Quick Start

Run all examples with the provided script:
```bash
./examples/run_all_examples.sh
```

Or run individual examples as shown below.

## Examples

### 1. Simple Bell State (`simple_bell_state.py`)

Demonstrates the complete workflow:
1. Capability negotiation
2. Job submission
3. Waiting for completion
4. Retrieving telemetry

**Run:**
```bash
python examples/simple_bell_state.py
```

**Expected Output:**
```
=== QMK Bell State Example ===

1. Negotiating capabilities...
   Session ID: sess_xxxxxxxx
   Granted: ['CAP_ALLOC', 'CAP_TELEPORT']
   Denied: []

2. Loading Bell state graph...
   Nodes: 6
   Edges: 7

3. Submitting job...
   Job ID: job_xxxxxxxx

4. Waiting for job completion...
   State: COMPLETED
   Progress: {...}
   Events: {'mA': 0, 'mB': 0}

5. Getting telemetry...
   Logical qubits: 2
   Physical qubits: 18
   Channels: 0

✅ Bell state preparation completed successfully!
```

### 2. VQE-Style Ansatz (`vqe_ansatz.py`)

Demonstrates variational quantum algorithms:
- Parameterized rotation gates (RZ)
- Entangling layers (CNOT)
- Parameter sweeps
- Energy estimation from measurements

**Run:**
```bash
python examples/vqe_ansatz.py
```

**Features:**
- Creates ansatz circuits with adjustable parameters
- Runs multiple iterations with different parameter values
- Simulates VQE optimization workflow
- Tracks energy as a function of parameters

### 3. Multi-Qubit Entanglement (`multi_qubit_entanglement.py`)

Creates various entangled states:
- **GHZ states**: (|00...0⟩ + |11...1⟩)/√2 for 4 and 6 qubits
- **W states**: (|100⟩ + |010⟩ + |001⟩)/√3 for 3 qubits
- Analysis of measurement outcomes

**Run:**
```bash
python examples/multi_qubit_entanglement.py
```

**Features:**
- Scalable entanglement generation
- Hamming weight analysis
- Verification of expected correlations
- Resource usage tracking

### 4. Adaptive Circuit (`adaptive_circuit.py`)

Demonstrates mid-circuit measurements with conditional operations:
- Syndrome measurements
- Guard-based conditional corrections
- Multi-round error detection
- 3-qubit repetition code implementation

**Run:**
```bash
python examples/adaptive_circuit.py
```

**Features:**
- Mid-circuit measurements
- Conditional gate application using guards
- Syndrome-based error detection
- Multiple measurement rounds

### 5. Performance Benchmark (`benchmark.py`)

Comprehensive performance benchmarking:
- Job submission latency
- End-to-end execution time
- Scaling with qubit count
- Concurrent job throughput

**Run:**
```bash
python examples/benchmark.py
```

**Metrics:**
- Mean/median/min/max latencies
- Throughput (jobs/second)
- Scaling factors
- Resource utilization

## Client Library API

### Basic Usage

```python
from runtime.client import QSyscallClient

# Create client
client = QSyscallClient(socket_path="/tmp/qmk.sock")

# Negotiate capabilities
result = client.negotiate_capabilities(["CAP_ALLOC", "CAP_TELEPORT"])
session_id = result["session_id"]

# Submit job
job_id = client.submit_job(graph, priority=10, seed=42)

# Wait for completion
result = client.wait_for_job(job_id, timeout_ms=10000)

# Or submit and wait in one call
result = client.submit_and_wait(graph, timeout_ms=10000)
```

### Available Methods

- `negotiate_capabilities(requested)` - Negotiate capabilities
- `submit_job(graph, priority, seed, debug)` - Submit a job
- `get_job_status(job_id)` - Get job status
- `wait_for_job(job_id, timeout_ms)` - Wait for completion
- `cancel_job(job_id)` - Cancel a job
- `open_channel(vq_a, vq_b, fidelity)` - Open entanglement channel
- `get_telemetry()` - Get system telemetry
- `submit_and_wait(graph, timeout_ms, **kwargs)` - Submit and wait

### Error Handling

```python
from runtime.client import QSyscallClient, QSyscallError

try:
    result = client.submit_job(graph)
except QSyscallError as e:
    print(f"Error [{e.code}]: {e.message}")
    if e.data:
        print(f"Details: {e.data}")
```

## QVM Graph Format

See `qvm/examples/` for example QVM graphs:
- `bell_teleport_cnot.qvm.json` - Bell state with teleportation
- `ghz_state.qvm.json` - GHZ state preparation
- `teleportation_demo.qvm.json` - Quantum teleportation
- `conditional_correction.qvm.json` - Conditional operations
- `reversible_segment.qvm.json` - Reversible computation

## Capabilities

Available capabilities:
- `CAP_ALLOC` - Allocate logical qubits
- `CAP_TELEPORT` - Teleportation operations
- `CAP_MAGIC` - Magic state distillation
- `CAP_LINK` - Entanglement channels
- `CAP_CHECKPOINT` - Checkpoint/restore
- `CAP_DEBUG` - Debug operations

## Session Management

Sessions track:
- Granted capabilities
- Resource quotas (max qubits, jobs, channels)
- Active resources (jobs, qubits, channels)
- Tenant isolation

## Job States

- `QUEUED` - Waiting for resources
- `VALIDATING` - Graph validation in progress
- `RUNNING` - Executing on quantum hardware
- `COMPLETED` - Successfully completed
- `FAILED` - Execution failed
- `CANCELLED` - Cancelled by user

## Further Reading

- [QVM Specification](../docs/QVM-spec.md)
- [qSyscall ABI](../docs/qsyscall-abi.md)
- [Implementation Plan](../docs/IMPLEMENTATION_PLAN.md)
