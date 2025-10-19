# Getting Started with QMK

This guide will help you get started with the Quantum Microkernel (QMK).

## Overview

QMK is a capability-based quantum operating system that provides:
- **Logical qubit simulation** with configurable QEC codes
- **qSyscall ABI** for quantum operations via RPC
- **Session management** with capability-based security
- **Asynchronous job execution** with state tracking
- **Resource management** with quota enforcement

## Installation

### Prerequisites

- Python 3.8+
- pytest (for running tests)

### Setup

Clone the repository:
```bash
git clone https://github.com/neuralground/qmk.git
cd qmk
```

Install dependencies (if any):
```bash
pip install -r requirements.txt  # If requirements file exists
```

## Quick Start

### 1. Start the QMK Server

```bash
python -m kernel.qmk_server
```

The server will start and listen on `/tmp/qmk.sock` by default.

Output:
```
Starting QMK server on /tmp/qmk.sock
QMK server started
```

### 2. Run an Example

In a new terminal, run the Bell state example:

```bash
python examples/simple_bell_state.py
```

You should see output showing:
- Capability negotiation
- Job submission
- Execution progress
- Measurement results
- Resource telemetry

### 3. Run All Examples

```bash
./examples/run_all_examples.sh
```

This will run all examples in sequence with the server.

## Basic Usage

### Python Client

```python
from runtime.client import QSyscallClient

# Create client
client = QSyscallClient(socket_path="/tmp/qmk.sock")

# Negotiate capabilities
result = client.negotiate_capabilities(["CAP_ALLOC", "CAP_TELEPORT"])
print(f"Session ID: {result['session_id']}")

# Submit a job
graph = {
    "version": "0.1",
    "nodes": [
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": ["q0"],
            "profile": "logical:surface_code(d=3)"
        },
        {
            "id": "h",
            "op": "H",
            "qubits": ["q0"],
            "deps": ["alloc"]
        },
        {
            "id": "m",
            "op": "MEASURE_Z",
            "qubits": ["q0"],
            "outputs": ["m0"],
            "deps": ["h"]
        },
        {
            "id": "free",
            "op": "FREE_LQ",
            "qubits": ["q0"],
            "deps": ["m"]
        }
    ],
    "edges": []
}

# Submit and wait for completion
result = client.submit_and_wait(graph, timeout_ms=5000)

if result['state'] == 'COMPLETED':
    print(f"Measurement: {result['events']['m0']}")
```

## Core Concepts

### Sessions

Sessions represent a tenant's connection to the kernel:
- Each session has a unique ID
- Sessions have granted capabilities
- Sessions track resource usage
- Sessions enforce quotas

### Capabilities

Capabilities control access to privileged operations:
- `CAP_ALLOC` - Allocate logical qubits
- `CAP_TELEPORT` - Teleportation operations
- `CAP_MAGIC` - Magic state distillation
- `CAP_LINK` - Entanglement channels
- `CAP_CHECKPOINT` - Checkpoint/restore
- `CAP_DEBUG` - Debug operations

### Jobs

Jobs represent quantum computations:
- Jobs are submitted asynchronously
- Jobs progress through states: QUEUED → VALIDATING → RUNNING → COMPLETED/FAILED
- Jobs can be cancelled
- Jobs produce measurement events and telemetry

### QVM Graphs

QVM graphs define quantum computations:
- **Nodes** represent operations (gates, measurements, allocations)
- **Edges** define dependencies between operations
- **Guards** enable conditional execution based on measurements
- **Profiles** specify QEC code parameters

## QEC Profiles

QMK supports multiple QEC codes:

```python
# Surface code with distance 3
"logical:surface_code(d=3)"

# SHYPS code with distance 7
"logical:SHYPS(d=7)"

# Bacon-Shor code with distance 5
"logical:bacon_shor(d=5)"
```

Each profile determines:
- Physical qubit count per logical qubit
- Logical error rate
- Cycle time
- Resource requirements

## Examples

### Bell State Preparation

See `examples/simple_bell_state.py` for a complete example.

### VQE-Style Circuit

See `examples/vqe_ansatz.py` for parameterized circuits.

### Multi-Qubit Entanglement

See `examples/multi_qubit_entanglement.py` for GHZ and W states.

### Adaptive Circuits

See `examples/adaptive_circuit.py` for mid-circuit measurements with guards.

### Performance Benchmarking

See `examples/benchmark.py` for performance metrics.

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_session_manager.py -v

# Run with coverage
python -m pytest tests/ --cov=kernel --cov=runtime
```

Current test coverage: **146 tests, 100% passing**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Application                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ QSyscallClient
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   RPC Server (JSON-RPC 2.0)             │
│                   Unix Domain Socket                     │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼────┐  ┌────▼─────┐  ┌───▼──────┐
│  Session   │  │   Job    │  │ Resource │
│  Manager   │  │ Manager  │  │ Manager  │
└────────────┘  └──────────┘  └──────────┘
                      │
                ┌─────▼──────┐
                │  Enhanced  │
                │  Executor  │
                └────────────┘
                      │
                ┌─────▼──────┐
                │  Logical   │
                │   Qubit    │
                │ Simulator  │
                └────────────┘
```

## Next Steps

1. **Work Through the Tutorial**: Follow the [Tutorial](TUTORIAL.md) for step-by-step guidance
2. **Explore Examples**: Run all examples to see QMK capabilities
3. **Read Core Specifications**: 
   - [QVM Specification](QVM-spec.md) — Complete technical reference
   - [qSyscall ABI](qsyscall-abi.md) — Kernel interface details
   - [Quick Reference](QUICK_REFERENCE.md) — Fast lookup for common patterns
4. **Create Your Own Circuits**: Use the client library to build custom quantum programs
5. **Run Benchmarks**: Measure performance for your use case
6. **Dive Deeper**: Explore [Architecture](architecture.md), [Security Model](security-model.md), and other technical deep dives

## Troubleshooting

### Server won't start

- Check if socket file exists: `ls -la /tmp/qmk.sock`
- Remove stale socket: `rm /tmp/qmk.sock`
- Check for port conflicts

### Connection refused

- Ensure server is running: `ps aux | grep qmk_server`
- Check socket path matches in client and server
- Verify file permissions on socket

### Job fails

- Check error message in job status
- Verify capabilities are granted
- Check graph validation errors
- Review QVM specification for correct format

### Tests fail

- Ensure no server is running during tests
- Check Python version (3.8+ required)
- Install test dependencies: `pip install pytest`

## Support

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Tests**: See `tests/` directory
- **Issues**: GitHub Issues

## License

See LICENSE file for details.
