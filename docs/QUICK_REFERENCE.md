# QMK Quick Reference

Fast reference for common operations and patterns.

## Starting the Server

```bash
python -m kernel.qmk_server
```

## Basic Client Usage

```python
from runtime.client import QSyscallClient

# Connect
client = QSyscallClient()

# Get capabilities
caps = client.negotiate_capabilities(["CAP_ALLOC", "CAP_TELEPORT"])

# Submit job
result = client.submit_and_wait(graph, seed=42)

# Check result
if result['state'] == 'COMPLETED':
    print(result['events'])
```

## Common Operations

### Single Qubit Gates

```python
# Hadamard
{"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]}

# Pauli gates
{"id": "x", "op": "X", "qubits": ["q0"], "deps": ["h"]}
{"id": "y", "op": "Y", "qubits": ["q0"], "deps": ["x"]}
{"id": "z", "op": "Z", "qubits": ["q0"], "deps": ["y"]}

# Phase gate
{"id": "s", "op": "S", "qubits": ["q0"], "deps": ["z"]}

# Rotations
{"id": "rz", "op": "RZ", "qubits": ["q0"], 
 "params": {"theta": 1.57}, "deps": ["s"]}
{"id": "ry", "op": "RY", "qubits": ["q0"], 
 "params": {"theta": 3.14}, "deps": ["rz"]}
```

### Two-Qubit Gates

```python
# CNOT
{"id": "cnot", "op": "CNOT", "qubits": ["control", "target"], 
 "deps": ["alloc"]}
```

### Measurements

```python
# Z-basis
{"id": "mz", "op": "MEASURE_Z", "qubits": ["q0"], 
 "outputs": ["result"], "deps": ["gate"]}

# X-basis
{"id": "mx", "op": "MEASURE_X", "qubits": ["q0"], 
 "outputs": ["result"], "deps": ["gate"]}
```

### Allocation/Deallocation

```python
# Allocate
{"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"], 
 "profile": "logical:surface_code(d=3)"}

# Free
{"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], 
 "deps": ["measure"]}
```

## QEC Profiles

```python
# Surface code
"logical:surface_code(d=3)"   # Distance 3
"logical:surface_code(d=5)"   # Distance 5
"logical:surface_code(d=9)"   # Distance 9

# SHYPS code
"logical:SHYPS(d=7)"

# Bacon-Shor
"logical:bacon_shor(d=5)"
```

## Capabilities

| Capability | Description |
|------------|-------------|
| `CAP_ALLOC` | Allocate/free qubits |
| `CAP_TELEPORT` | Teleportation |
| `CAP_MAGIC` | Magic states |
| `CAP_LINK` | Entanglement channels |
| `CAP_CHECKPOINT` | Checkpointing |
| `CAP_DEBUG` | Debug info |

## Guards (Conditional Execution)

```python
# Simple condition
"guard": {
    "type": "eq",
    "event": "measurement",
    "value": 1
}

# AND condition
"guard": {
    "type": "and",
    "conditions": [
        {"type": "eq", "event": "m0", "value": 1},
        {"type": "eq", "event": "m1", "value": 0}
    ]
}
```

## Common Patterns

### Bell State

```python
graph = {
    "version": "0.1",
    "nodes": [
        {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"], 
         "profile": "logical:surface_code(d=3)"},
        {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
        {"id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h"]},
        {"id": "m0", "op": "MEASURE_Z", "qubits": ["q0"], 
         "outputs": ["m0"], "deps": ["cnot"]},
        {"id": "m1", "op": "MEASURE_Z", "qubits": ["q1"], 
         "outputs": ["m1"], "deps": ["cnot"]},
        {"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], 
         "deps": ["m0", "m1"]}
    ],
    "edges": []
}
```

### Superposition + Measurement

```python
graph = {
    "version": "0.1",
    "nodes": [
        {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"], 
         "profile": "logical:surface_code(d=3)"},
        {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
        {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
         "outputs": ["result"], "deps": ["h"]},
        {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
    ],
    "edges": []
}
```

### Parameterized Circuit

```python
def create_circuit(theta):
    return {
        "version": "0.1",
        "nodes": [
            {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"], 
             "profile": "logical:surface_code(d=3)"},
            {"id": "rz", "op": "RZ", "qubits": ["q0"], 
             "params": {"theta": theta}, "deps": ["alloc"]},
            {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
             "outputs": ["result"], "deps": ["rz"]},
            {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
        ],
        "edges": []
    }
```

## Error Handling

```python
try:
    result = client.submit_and_wait(graph, timeout_ms=10000)
    
    if result['state'] == 'COMPLETED':
        # Success
        events = result['events']
    elif result['state'] == 'FAILED':
        # Failed
        error = result.get('error')
    elif result['state'] == 'CANCELLED':
        # Cancelled
        pass
        
except TimeoutError:
    print("Job timed out")
except QSyscallError as e:
    print(f"Error [{e.code}]: {e.message}")
```

## Job Management

```python
# Submit without waiting
job_id = client.submit_job(graph, priority=10, seed=42)

# Check status
status = client.get_job_status(job_id)

# Wait for completion
result = client.wait_for_job(job_id, timeout_ms=5000)

# Cancel job
client.cancel_job(job_id)
```

## Telemetry

```python
telemetry = client.get_telemetry()

# Resource usage
usage = telemetry['resource_usage']
print(f"Logical qubits: {usage['logical_qubits_allocated']}")
print(f"Physical qubits: {usage['physical_qubits_used']}")
print(f"Utilization: {usage['utilization']:.1%}")

# Per-qubit telemetry
for vq_id, data in telemetry['qubits'].items():
    print(f"{vq_id}: {data['gate_count']} gates")
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_session_manager.py -v

# With coverage
python -m pytest tests/ --cov=kernel --cov=runtime
```

## Examples

```bash
# Simple examples
python examples/simple_bell_state.py
python examples/vqe_ansatz.py
python examples/multi_qubit_entanglement.py
python examples/adaptive_circuit.py

# Classic algorithms
python examples/grovers_algorithm.py
python examples/shors_algorithm.py
python examples/deutsch_jozsa.py

# Benchmarking
python examples/benchmark.py

# Run all
./examples/run_all_examples.sh
```

## Common Issues

### Connection Refused
```bash
# Start server
python -m kernel.qmk_server
```

### Capability Denied
```python
# Request the capability
client.negotiate_capabilities(["CAP_ALLOC", "CAP_LINK"])
```

### Quota Exceeded
```python
# Check usage
telemetry = client.get_telemetry()
print(telemetry['resource_usage'])
```

### Job Failed
```python
# Check error
if result['state'] == 'FAILED':
    print(result.get('error'))
```

## Performance Tips

1. **Use seeds for reproducibility**
   ```python
   result = client.submit_and_wait(graph, seed=42)
   ```

2. **Batch jobs for throughput**
   ```python
   job_ids = [client.submit_job(graph, seed=i) for i in range(10)]
   results = [client.wait_for_job(jid) for jid in job_ids]
   ```

3. **Choose appropriate QEC code**
   ```python
   # Lower distance = faster, less reliable
   "logical:surface_code(d=3)"
   
   # Higher distance = slower, more reliable
   "logical:surface_code(d=9)"
   ```

4. **Minimize qubit count**
   - Use fewer qubits when possible
   - Free qubits as soon as done

## Documentation

- [Getting Started](GETTING_STARTED.md)
- [Tutorial](TUTORIAL.md)
- [QVM Specification](QVM-spec.md)
- [qSyscall ABI](qsyscall-abi.md)
- [Examples README](../examples/README.md)
