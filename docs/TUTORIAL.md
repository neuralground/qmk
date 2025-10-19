# QMK Tutorial: Building Your First Quantum Application

This tutorial will guide you through building quantum applications on QMK, from basic concepts to advanced patterns.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Tutorial 1: Hello Quantum World](#tutorial-1-hello-quantum-world)
3. [Tutorial 2: Understanding Sessions and Capabilities](#tutorial-2-understanding-sessions-and-capabilities)
4. [Tutorial 3: Building a Simple Circuit](#tutorial-3-building-a-simple-circuit)
5. [Tutorial 4: Working with Measurements](#tutorial-4-working-with-measurements)
6. [Tutorial 5: Parameterized Circuits](#tutorial-5-parameterized-circuits)
7. [Tutorial 6: Adaptive Circuits with Guards](#tutorial-6-adaptive-circuits-with-guards)
8. [Tutorial 7: Multi-Qubit Entanglement](#tutorial-7-multi-qubit-entanglement)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)

---

## Prerequisites

- Python 3.8 or higher
- QMK installed and server running
- Basic understanding of quantum computing concepts

**Start the QMK server:**
```bash
python -m kernel.qmk_server
```

---

## Tutorial 1: Hello Quantum World

Let's create the simplest possible quantum program: preparing and measuring a single qubit.

### Step 1: Import the Client

```python
from runtime.client import QSyscallClient

# Create a client connection
client = QSyscallClient(socket_path="/tmp/qmk.sock")
```

### Step 2: Negotiate Capabilities

Before doing anything, you need to request capabilities:

```python
result = client.negotiate_capabilities(["CAP_ALLOC"])
print(f"Session ID: {result['session_id']}")
print(f"Granted capabilities: {result['granted']}")
```

**What's happening:**
- You're requesting the `CAP_ALLOC` capability (permission to allocate qubits)
- The kernel creates a session and grants capabilities
- You receive a session ID for tracking

### Step 3: Create Your First Circuit

```python
# Define a simple circuit: allocate, hadamard, measure
graph = {
    "version": "0.1",
    "metadata": {
        "name": "hello_quantum",
        "description": "My first quantum circuit"
    },
    "nodes": [
        # Allocate a qubit
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": ["q0"],
            "profile": "logical:surface_code(d=3)"
        },
        # Apply Hadamard gate (creates superposition)
        {
            "id": "hadamard",
            "op": "H",
            "qubits": ["q0"],
            "deps": ["alloc"]
        },
        # Measure in Z basis
        {
            "id": "measure",
            "op": "MEASURE_Z",
            "qubits": ["q0"],
            "outputs": ["result"],
            "deps": ["hadamard"]
        },
        # Free the qubit
        {
            "id": "free",
            "op": "FREE_LQ",
            "qubits": ["q0"],
            "deps": ["measure"]
        }
    ],
    "edges": []  # Dependencies are specified in "deps" field
}
```

### Step 4: Submit and Execute

```python
# Submit the job
job_id = client.submit_job(graph, seed=42)
print(f"Job submitted: {job_id}")

# Wait for completion
result = client.wait_for_job(job_id, timeout_ms=5000)

# Check the result
if result['state'] == 'COMPLETED':
    measurement = result['events']['result']
    print(f"Measurement result: {measurement}")
    print("Expected: 0 or 1 with ~50% probability each")
else:
    print(f"Job failed: {result.get('error')}")
```

### Complete Example

Save this as `hello_quantum.py`:

```python
from runtime.client import QSyscallClient

def main():
    # Connect to QMK
    client = QSyscallClient()
    
    # Get capabilities
    caps = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"✓ Session created: {caps['session_id']}")
    
    # Define circuit
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
    
    # Execute
    result = client.submit_and_wait(graph, seed=42)
    
    if result['state'] == 'COMPLETED':
        print(f"✓ Measurement: {result['events']['result']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

if __name__ == "__main__":
    main()
```

Run it:
```bash
python hello_quantum.py
```

---

## Tutorial 2: Understanding Sessions and Capabilities

### What are Sessions?

Sessions represent your connection to the QMK kernel. Each session:
- Has a unique ID
- Tracks granted capabilities
- Enforces resource quotas
- Isolates your resources from other tenants

### Available Capabilities

| Capability | Description |
|------------|-------------|
| `CAP_ALLOC` | Allocate and free logical qubits |
| `CAP_TELEPORT` | Perform quantum teleportation |
| `CAP_MAGIC` | Use magic state distillation |
| `CAP_LINK` | Create entanglement channels |
| `CAP_CHECKPOINT` | Save and restore job state |
| `CAP_DEBUG` | Access debug information |

### Requesting Multiple Capabilities

```python
result = client.negotiate_capabilities([
    "CAP_ALLOC",
    "CAP_TELEPORT",
    "CAP_LINK"
])

print(f"Granted: {result['granted']}")
print(f"Denied: {result['denied']}")
```

### Understanding Quotas

Each session has resource limits:

```python
quota = result['quota']
print(f"Max logical qubits: {quota['max_logical_qubits']}")
print(f"Max channels: {quota['max_channels']}")
print(f"Max concurrent jobs: {quota['max_jobs']}")
```

### Checking Session Info

```python
# Get telemetry to see current usage
telemetry = client.get_telemetry()
usage = telemetry['resource_usage']

print(f"Qubits allocated: {usage['logical_qubits_allocated']}")
print(f"Physical qubits used: {usage['physical_qubits_used']}")
print(f"Utilization: {usage['utilization']:.1%}")
```

---

## Tutorial 3: Building a Simple Circuit

### Circuit Structure

A QVM circuit consists of:
1. **Nodes**: Operations (gates, measurements, allocations)
2. **Edges**: Dependencies between operations (optional if using `deps`)
3. **Metadata**: Name, description, version

### Basic Template

```python
circuit = {
    "version": "0.1",
    "metadata": {
        "name": "my_circuit",
        "description": "What this circuit does"
    },
    "nodes": [
        # Your operations here
    ],
    "edges": []
}
```

### Node Types

#### 1. Allocation
```python
{
    "id": "alloc",
    "op": "ALLOC_LQ",
    "outputs": ["q0", "q1", "q2"],  # Qubit IDs
    "profile": "logical:surface_code(d=3)"
}
```

#### 2. Single-Qubit Gates
```python
# Hadamard
{"id": "h1", "op": "H", "qubits": ["q0"], "deps": ["alloc"]}

# Pauli X, Y, Z
{"id": "x1", "op": "X", "qubits": ["q0"], "deps": ["h1"]}
{"id": "y1", "op": "Y", "qubits": ["q0"], "deps": ["x1"]}
{"id": "z1", "op": "Z", "qubits": ["q0"], "deps": ["y1"]}

# S gate (phase)
{"id": "s1", "op": "S", "qubits": ["q0"], "deps": ["z1"]}
```

#### 3. Rotation Gates
```python
import math

# Rotation around Z axis
{
    "id": "rz1",
    "op": "RZ",
    "qubits": ["q0"],
    "params": {"theta": math.pi / 4},
    "deps": ["alloc"]
}

# Rotation around Y axis
{
    "id": "ry1",
    "op": "RY",
    "qubits": ["q0"],
    "params": {"theta": math.pi / 2},
    "deps": ["rz1"]
}
```

#### 4. Two-Qubit Gates
```python
# CNOT (controlled-NOT)
{
    "id": "cnot1",
    "op": "CNOT",
    "qubits": ["q0", "q1"],  # [control, target]
    "deps": ["alloc"]
}
```

#### 5. Measurements
```python
# Z-basis measurement
{
    "id": "measure",
    "op": "MEASURE_Z",
    "qubits": ["q0"],
    "outputs": ["m0"],  # Event name
    "deps": ["cnot1"]
}

# X-basis measurement
{
    "id": "measure_x",
    "op": "MEASURE_X",
    "qubits": ["q1"],
    "outputs": ["m1"],
    "deps": ["cnot1"]
}
```

#### 6. Deallocation
```python
{
    "id": "free",
    "op": "FREE_LQ",
    "qubits": ["q0", "q1"],
    "deps": ["measure", "measure_x"]
}
```

### Example: Bell State Circuit

```python
def create_bell_state():
    return {
        "version": "0.1",
        "metadata": {"name": "bell_state"},
        "nodes": [
            # Allocate two qubits
            {
                "id": "alloc",
                "op": "ALLOC_LQ",
                "outputs": ["q0", "q1"],
                "profile": "logical:surface_code(d=3)"
            },
            # Apply H to first qubit
            {
                "id": "h",
                "op": "H",
                "qubits": ["q0"],
                "deps": ["alloc"]
            },
            # CNOT to create entanglement
            {
                "id": "cnot",
                "op": "CNOT",
                "qubits": ["q0", "q1"],
                "deps": ["h"]
            },
            # Measure both qubits
            {
                "id": "m0",
                "op": "MEASURE_Z",
                "qubits": ["q0"],
                "outputs": ["m0"],
                "deps": ["cnot"]
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
        "edges": []
    }
```

---

## Tutorial 4: Working with Measurements

### Measurement Basics

Measurements collapse quantum states and produce classical bits:

```python
{
    "id": "measure",
    "op": "MEASURE_Z",  # or MEASURE_X
    "qubits": ["q0"],
    "outputs": ["result_bit"],  # Name for the measurement outcome
    "deps": ["previous_operation"]
}
```

### Accessing Measurement Results

```python
result = client.submit_and_wait(graph)

if result['state'] == 'COMPLETED':
    events = result['events']
    
    # Get individual measurements
    m0 = events['m0']  # 0 or 1
    m1 = events['m1']
    
    print(f"Qubit 0: {m0}")
    print(f"Qubit 1: {m1}")
```

### Running Multiple Shots

To get statistics, run the circuit multiple times:

```python
def run_circuit_multiple_times(client, graph, shots=100):
    results = {'00': 0, '01': 0, '10': 0, '11': 0}
    
    for i in range(shots):
        result = client.submit_and_wait(graph, seed=i)
        
        if result['state'] == 'COMPLETED':
            m0 = result['events']['m0']
            m1 = result['events']['m1']
            bitstring = f"{m0}{m1}"
            results[bitstring] += 1
    
    # Print statistics
    for bitstring, count in results.items():
        probability = count / shots
        print(f"|{bitstring}⟩: {count}/{shots} ({probability:.1%})")
    
    return results
```

### Example: Measuring Superposition

```python
# Create |+⟩ state and measure
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

# Run 100 times
results = run_circuit_multiple_times(client, graph, shots=100)
# Expected: ~50% |0⟩, ~50% |1⟩
```

---

## Tutorial 5: Parameterized Circuits

### Why Parameterize?

Parameterized circuits are essential for:
- Variational algorithms (VQE, QAOA)
- Machine learning
- Optimization problems

### Creating Parameterized Gates

```python
import math

def create_parameterized_circuit(theta1, theta2, theta3):
    return {
        "version": "0.1",
        "nodes": [
            {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"],
             "profile": "logical:surface_code(d=3)"},
            
            # Parameterized rotation
            {
                "id": "rz1",
                "op": "RZ",
                "qubits": ["q0"],
                "params": {"theta": theta1},  # Parameter!
                "deps": ["alloc"]
            },
            {
                "id": "ry",
                "op": "RY",
                "qubits": ["q0"],
                "params": {"theta": theta2},
                "deps": ["rz1"]
            },
            {
                "id": "rz2",
                "op": "RZ",
                "qubits": ["q0"],
                "params": {"theta": theta3},
                "deps": ["ry"]
            },
            
            {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"],
             "outputs": ["result"], "deps": ["rz2"]},
            {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
        ],
        "edges": []
    }
```

### Parameter Sweep

```python
# Test different parameter values
import numpy as np

angles = np.linspace(0, 2*np.pi, 8)
results = []

for theta in angles:
    circuit = create_parameterized_circuit(theta, 0, 0)
    result = client.submit_and_wait(circuit, seed=42)
    
    if result['state'] == 'COMPLETED':
        measurement = result['events']['result']
        results.append((theta, measurement))
        print(f"θ={theta:.2f}: {measurement}")
```

---

## Tutorial 6: Adaptive Circuits with Guards

### What are Guards?

Guards enable conditional execution based on measurement outcomes:

```python
{
    "id": "correction",
    "op": "X",
    "qubits": ["q0"],
    "deps": ["measurement"],
    "guard": {
        "type": "eq",
        "event": "syndrome_bit",
        "value": 1
    }
}
```

This X gate only executes if `syndrome_bit == 1`.

### Guard Types

#### Equality Check
```python
"guard": {
    "type": "eq",
    "event": "measurement_name",
    "value": 1
}
```

#### AND Condition
```python
"guard": {
    "type": "and",
    "conditions": [
        {"type": "eq", "event": "m0", "value": 1},
        {"type": "eq", "event": "m1", "value": 0}
    ]
}
```

### Example: Quantum Error Correction

```python
def create_qec_circuit():
    return {
        "version": "0.1",
        "nodes": [
            # Allocate data and ancilla qubits
            {"id": "alloc", "op": "ALLOC_LQ", 
             "outputs": ["data", "ancilla"],
             "profile": "logical:surface_code(d=3)"},
            
            # Prepare |+⟩ state
            {"id": "h_data", "op": "H", "qubits": ["data"], 
             "deps": ["alloc"]},
            {"id": "h_anc", "op": "H", "qubits": ["ancilla"], 
             "deps": ["alloc"]},
            
            # Syndrome extraction
            {"id": "cnot", "op": "CNOT", 
             "qubits": ["data", "ancilla"],
             "deps": ["h_data", "h_anc"]},
            
            # Measure syndrome
            {"id": "syndrome", "op": "MEASURE_Z", 
             "qubits": ["ancilla"],
             "outputs": ["syndrome_bit"], "deps": ["cnot"]},
            
            # Conditional correction
            {
                "id": "correction",
                "op": "X",
                "qubits": ["data"],
                "deps": ["syndrome"],
                "guard": {
                    "type": "eq",
                    "event": "syndrome_bit",
                    "value": 1
                }
            },
            
            # Final measurement
            {"id": "measure", "op": "MEASURE_Z", 
             "qubits": ["data"],
             "outputs": ["result"], "deps": ["correction"]},
            
            {"id": "free", "op": "FREE_LQ", 
             "qubits": ["data", "ancilla"],
             "deps": ["measure", "syndrome"]}
        ],
        "edges": []
    }
```

---

## Tutorial 7: Multi-Qubit Entanglement

### Creating Entangled States

#### Bell State (2 qubits)
```python
# |Φ+⟩ = (|00⟩ + |11⟩)/√2
nodes = [
    {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"], ...},
    {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
    {"id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h"]},
    # ... measurements ...
]
```

#### GHZ State (n qubits)
```python
def create_ghz_state(n_qubits):
    qubits = [f"q{i}" for i in range(n_qubits)]
    
    nodes = [
        {"id": "alloc", "op": "ALLOC_LQ", "outputs": qubits, ...},
        {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]}
    ]
    
    # Chain of CNOTs
    prev = "h"
    for i in range(1, n_qubits):
        cnot_id = f"cnot_{i}"
        nodes.append({
            "id": cnot_id,
            "op": "CNOT",
            "qubits": ["q0", f"q{i}"],
            "deps": [prev]
        })
        prev = cnot_id
    
    # Add measurements and free
    # ...
    
    return {"version": "0.1", "nodes": nodes, "edges": []}
```

---

## Best Practices

### 1. Always Handle Errors

```python
try:
    result = client.submit_and_wait(graph, timeout_ms=10000)
    
    if result['state'] == 'COMPLETED':
        # Process results
        pass
    elif result['state'] == 'FAILED':
        print(f"Job failed: {result.get('error')}")
    elif result['state'] == 'CANCELLED':
        print("Job was cancelled")
        
except TimeoutError:
    print("Job timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 2. Use Descriptive IDs

```python
# Good
{"id": "prepare_superposition", "op": "H", ...}
{"id": "entangle_qubits", "op": "CNOT", ...}
{"id": "measure_computational_basis", "op": "MEASURE_Z", ...}

# Bad
{"id": "n1", "op": "H", ...}
{"id": "n2", "op": "CNOT", ...}
```

### 3. Add Metadata

```python
graph = {
    "version": "0.1",
    "metadata": {
        "name": "vqe_h2_molecule",
        "description": "VQE ansatz for H2 molecule at 0.74Å",
        "author": "Your Name",
        "created": "2025-10-18"
    },
    "nodes": [...]
}
```

### 4. Reuse Circuit Builders

```python
def add_rotation_layer(nodes, qubits, angles, prev_id):
    """Add a layer of rotation gates."""
    for i, (qubit, angle) in enumerate(zip(qubits, angles)):
        node_id = f"rz_{qubit}"
        nodes.append({
            "id": node_id,
            "op": "RZ",
            "qubits": [qubit],
            "params": {"theta": angle},
            "deps": [prev_id]
        })
    return node_id  # Return last node for chaining
```

### 5. Use Seeds for Reproducibility

```python
# Deterministic execution
result1 = client.submit_and_wait(graph, seed=42)
result2 = client.submit_and_wait(graph, seed=42)
# result1 == result2 (same measurements)

# Different outcomes
result3 = client.submit_and_wait(graph, seed=43)
# result3 may differ from result1
```

---

## Common Patterns

### Pattern 1: State Preparation

```python
def prepare_state(state_vector):
    """Prepare arbitrary single-qubit state."""
    # Calculate rotation angles from state vector
    theta = 2 * math.acos(abs(state_vector[0]))
    phi = math.atan2(state_vector[1].imag, state_vector[1].real)
    
    return {
        "version": "0.1",
        "nodes": [
            {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"], ...},
            {"id": "ry", "op": "RY", "qubits": ["q0"],
             "params": {"theta": theta}, "deps": ["alloc"]},
            {"id": "rz", "op": "RZ", "qubits": ["q0"],
             "params": {"theta": phi}, "deps": ["ry"]},
            # ...
        ],
        "edges": []
    }
```

### Pattern 2: Expectation Value Estimation

```python
def estimate_expectation(client, circuit, shots=1000):
    """Estimate ⟨Z⟩ expectation value."""
    counts = {0: 0, 1: 0}
    
    for i in range(shots):
        result = client.submit_and_wait(circuit, seed=i)
        if result['state'] == 'COMPLETED':
            measurement = result['events']['result']
            counts[measurement] += 1
    
    # ⟨Z⟩ = P(0) - P(1)
    expectation = (counts[0] - counts[1]) / shots
    return expectation
```

### Pattern 3: Circuit Composition

```python
def compose_circuits(circuit1, circuit2):
    """Compose two circuits sequentially."""
    # Combine nodes
    all_nodes = circuit1['nodes'][:-1]  # Remove FREE from first
    
    # Adjust dependencies in second circuit
    first_last = circuit1['nodes'][-2]['id']  # Last op before FREE
    
    for node in circuit2['nodes'][1:]:  # Skip ALLOC in second
        if 'deps' in node and 'alloc' in node['deps']:
            node['deps'] = [first_last]
        all_nodes.append(node)
    
    return {
        "version": "0.1",
        "nodes": all_nodes,
        "edges": []
    }
```

---

## Next Steps

1. **Try the examples**: Run `examples/` to see these patterns in action
2. **Read the specification**: [QVM-spec.md](QVM-spec.md) for complete details
3. **Explore algorithms**: Check out Grover's and Shor's algorithm examples
4. **Build your own**: Start with a simple circuit and expand
5. **Optimize**: Use the benchmark tool to measure performance

## Additional Resources

- [Getting Started Guide](GETTING_STARTED.md)
- [QVM Specification](QVM-spec.md)
- [qSyscall ABI](qsyscall-abi.md)
- [Examples Directory](../examples/)

Happy quantum programming! 🚀
