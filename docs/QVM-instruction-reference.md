# QVM Instruction Reference

**Version 0.1**

This document provides detailed specifications for all QVM operations.

## Table of Contents

1. [Lifecycle Operations](#lifecycle-operations)
2. [Logical Gate Operations](#logical-gate-operations)
3. [Measurement Operations](#measurement-operations)
4. [Composite Operations](#composite-operations)
5. [Control Flow](#control-flow)
6. [Administrative Operations](#administrative-operations)

---

## Lifecycle Operations

### ALLOC_LQ

**Opcode**: `ALLOC_LQ`

**Description**: Allocates logical qubits with specified error correction profile.

**Required Capability**: `CAP_ALLOC`

**Arguments**:
- `n` (integer): Number of logical qubits to allocate
- `profile` (string): Error correction profile specification
  - Format: `"logical:SCHEME(d=distance,...)"`
  - Examples: `"logical:SHYPS(d=9)"`, `"logical:Surface(d=7)"`

**Produces**: Array of `n` virtual qubit handles (VQ)

**Semantics**:
- Allocates `n` logical qubits in the |0⟩ state
- Kernel selects physical qubits and initializes error correction
- Profile specifies code type and distance (higher distance = more physical qubits, better error suppression)

**Example**:
```json
{
  "id": "alloc1",
  "op": "ALLOC_LQ",
  "args": {
    "n": 3,
    "profile": "logical:SHYPS(d=9)"
  },
  "vqs": ["q0", "q1", "q2"],
  "caps": ["CAP_ALLOC"]
}
```

**Errors**:
- Insufficient physical qubits available
- Invalid profile specification
- Missing `CAP_ALLOC` capability

---

### FREE_LQ

**Opcode**: `FREE_LQ`

**Description**: Deallocates logical qubits, releasing physical resources.

**Required Capability**: None

**Arguments**: None

**Consumes**: Array of virtual qubit handles (VQ)

**Produces**: Nothing

**Semantics**:
- Releases physical qubits back to the kernel's resource pool
- Quantum state is discarded (irreversible operation)
- All qubits must be in a computational basis state or measured

**Example**:
```json
{
  "id": "free1",
  "op": "FREE_LQ",
  "vqs": ["q0", "q1"]
}
```

**Errors**:
- Attempting to free qubits still in use
- Freeing qubits in superposition (implementation-dependent)

---

### FENCE_EPOCH

**Opcode**: `FENCE_EPOCH`

**Description**: Marks an epoch boundary for scheduling and preemption.

**Required Capability**: None

**Arguments**: None

**Consumes**: Nothing

**Produces**: Nothing

**Semantics**:
- Synchronization point aligned with stabilizer measurement cycles
- Kernel may preempt, migrate, or reschedule at fences
- All operations before the fence complete before any after
- Enables deterministic checkpointing

**Example**:
```json
{
  "id": "fence1",
  "op": "FENCE_EPOCH"
}
```

**Usage**: Insert fences to enable:
- Preemption in long-running computations
- Migration of logical qubits between physical modules
- Checkpoint/restore functionality

---

### BAR_REGION

**Opcode**: `BAR_REGION`

**Description**: Hint to kernel about barrier/synchronization region.

**Required Capability**: None

**Arguments**:
- `tag` (string): Region identifier for telemetry

**Consumes**: Nothing

**Produces**: Nothing

**Semantics**:
- Non-binding hint for kernel optimization
- May influence scheduling or batching decisions
- Does not affect program semantics

**Example**:
```json
{
  "id": "bar1",
  "op": "BAR_REGION",
  "args": { "tag": "measurement_batch_1" }
}
```

---

## Logical Gate Operations

All logical gate operations are **reversible** (unitary) and can be uncomputed.

### APPLY_H

**Opcode**: `APPLY_H`

**Description**: Applies Hadamard gate to a logical qubit.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- Unitary operation: H = (1/√2) [[1, 1], [1, -1]]
- Maps |0⟩ → |+⟩ = (|0⟩ + |1⟩)/√2
- Maps |1⟩ → |-⟩ = (|0⟩ - |1⟩)/√2
- Self-inverse: H² = I

**Example**:
```json
{
  "id": "h1",
  "op": "APPLY_H",
  "vqs": ["q0"]
}
```

**Reversibility**: Self-inverse (apply H again to undo)

---

### APPLY_S

**Opcode**: `APPLY_S`

**Description**: Applies S (phase) gate to a logical qubit.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- Unitary operation: S = [[1, 0], [0, i]]
- Adds π/2 phase to |1⟩ state
- S² = Z (Pauli-Z)
- S⁴ = I

**Example**:
```json
{
  "id": "s1",
  "op": "APPLY_S",
  "vqs": ["q0"]
}
```

**Reversibility**: Inverse is S† (apply S three times)

---

### APPLY_X

**Opcode**: `APPLY_X`

**Description**: Applies Pauli-X (bit flip) gate.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- Unitary operation: X = [[0, 1], [1, 0]]
- Bit flip: |0⟩ ↔ |1⟩
- Self-inverse: X² = I

**Example**:
```json
{
  "id": "x1",
  "op": "APPLY_X",
  "vqs": ["q0"]
}
```

**Reversibility**: Self-inverse

---

### APPLY_Y

**Opcode**: `APPLY_Y`

**Description**: Applies Pauli-Y gate.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- Unitary operation: Y = [[0, -i], [i, 0]]
- Y = iXZ
- Self-inverse: Y² = I

**Example**:
```json
{
  "id": "y1",
  "op": "APPLY_Y",
  "vqs": ["q0"]
}
```

**Reversibility**: Self-inverse

---

### APPLY_Z

**Opcode**: `APPLY_Z`

**Description**: Applies Pauli-Z (phase flip) gate.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- Unitary operation: Z = [[1, 0], [0, -1]]
- Phase flip: |1⟩ → -|1⟩
- Self-inverse: Z² = I

**Example**:
```json
{
  "id": "z1",
  "op": "APPLY_Z",
  "vqs": ["q0"]
}
```

**Reversibility**: Self-inverse

---

### APPLY_CNOT

**Opcode**: `APPLY_CNOT`

**Description**: Applies controlled-NOT (CNOT) gate.

**Required Capability**: None

**Arguments**: None

**Consumes**: 2 virtual qubits (VQ) - control, target

**Produces**: 2 virtual qubits (VQ, same handles)

**Semantics**:
- Two-qubit unitary: CNOT = [[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]]
- If control is |1⟩, flip target; otherwise do nothing
- Creates entanglement: |00⟩ → |00⟩, |10⟩ → |11⟩
- Self-inverse: CNOT² = I

**Example**:
```json
{
  "id": "cnot1",
  "op": "APPLY_CNOT",
  "vqs": ["qControl", "qTarget"]
}
```

**Note**: First VQ in array is control, second is target.

**Reversibility**: Self-inverse

---

### RESET

**Opcode**: `RESET`

**Description**: Resets a qubit to |0⟩ state.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- **Irreversible operation** (discards quantum information)
- Measures qubit in Z basis, applies X if result is 1
- Guarantees qubit is in |0⟩ state afterward
- Ends any REV segment

**Example**:
```json
{
  "id": "reset1",
  "op": "RESET",
  "vqs": ["q0"]
}
```

**Reversibility**: Not reversible (irreversible boundary)

---

## Measurement Operations

All measurement operations are **irreversible** and produce classical events.

### MEASURE_Z

**Opcode**: `MEASURE_Z`

**Description**: Measures qubit in computational (Z) basis.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 
- 1 virtual qubit (VQ, same handle, collapsed to |0⟩ or |1⟩)
- 1 event (EV) with measurement outcome

**Semantics**:
- **Irreversible operation** (collapses superposition)
- Projects onto Z eigenstates: {|0⟩, |1⟩}
- Outcome probabilities: P(0) = |⟨0|ψ⟩|², P(1) = |⟨1|ψ⟩|²
- Event value: 0 or 1
- Ends any REV segment

**Example**:
```json
{
  "id": "mz1",
  "op": "MEASURE_Z",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

**Reversibility**: Not reversible (irreversible boundary)

---

### MEASURE_X

**Opcode**: `MEASURE_X`

**Description**: Measures qubit in X (Hadamard) basis.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 
- 1 virtual qubit (VQ, same handle, collapsed to |+⟩ or |-⟩)
- 1 event (EV) with measurement outcome

**Semantics**:
- **Irreversible operation**
- Projects onto X eigenstates: {|+⟩, |-⟩}
- Equivalent to H, MEASURE_Z, H
- Event value: 0 (for |+⟩) or 1 (for |-⟩)

**Example**:
```json
{
  "id": "mx1",
  "op": "MEASURE_X",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

**Reversibility**: Not reversible

---

### MEASURE_Y

**Opcode**: `MEASURE_Y`

**Description**: Measures qubit in Y basis.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 
- 1 virtual qubit (VQ, same handle, collapsed to computational basis)
- 1 event (EV) with measurement outcome

**Semantics**:
- **Irreversible operation**
- Projects onto Y eigenstates: {|+i⟩, |-i⟩} where |±i⟩ = (|0⟩ ± i|1⟩)/√2
- Equivalent to S†, H, MEASURE_Z, H, S
- Event value: 0 (for |+i⟩) or 1 (for |-i⟩)
- Ends any REV segment

**Example**:
```json
{
  "id": "my1",
  "op": "MEASURE_Y",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

**Reversibility**: Not reversible

**Use Cases**:
- Y-error detection in quantum error correction
- State tomography
- Measurement-based quantum computing

---

### MEASURE_ANGLE

**Opcode**: `MEASURE_ANGLE`

**Description**: Measures qubit in arbitrary basis at angle θ from Z-axis.

**Required Capability**: None

**Arguments**:
- `angle` (float): Rotation angle in radians from Z-axis

**Consumes**: 1 virtual qubit (VQ)

**Produces**: 
- 1 virtual qubit (VQ, same handle, collapsed to computational basis)
- 1 event (EV) with measurement outcome

**Semantics**:
- **Irreversible operation**
- Projects onto basis rotated by angle θ from Z-axis
- Measurement eigenstates: |θ+⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩, |θ-⟩ = sin(θ/2)|0⟩ - cos(θ/2)|1⟩
- Event value: 0 (for |θ+⟩) or 1 (for |θ-⟩)
- Special cases: θ=0 (Z-basis), θ=π/2 (X-basis), θ=π (-Z-basis)

**Example**:
```json
{
  "id": "mangle1",
  "op": "MEASURE_ANGLE",
  "args": {
    "angle": 0.7853981633974483
  },
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

**Reversibility**: Not reversible

**Use Cases**:
- Generalized measurements
- Quantum state tomography
- Adaptive measurement protocols
- Weak measurements

---

### MEASURE_BELL

**Opcode**: `MEASURE_BELL`

**Description**: Performs Bell basis measurement on two qubits jointly.

**Required Capability**: None

**Arguments**: None

**Consumes**: 2 virtual qubits (VQ)

**Produces**: 
- 2 virtual qubits (VQ, same handles, both collapsed to computational basis)
- 2 events (EV) with measurement outcomes, or 1 event with Bell state index

**Semantics**:
- **Irreversible operation** (collapses both qubits)
- Projects onto Bell basis: {|Φ+⟩, |Ψ+⟩, |Φ-⟩, |Ψ-⟩}
  - |Φ+⟩ = (|00⟩ + |11⟩)/√2  → outcomes (0,0) → index 0
  - |Ψ+⟩ = (|01⟩ + |10⟩)/√2  → outcomes (0,1) → index 1
  - |Φ-⟩ = (|00⟩ - |11⟩)/√2  → outcomes (1,0) → index 2
  - |Ψ-⟩ = (|01⟩ - |10⟩)/√2  → outcomes (1,1) → index 3
- Implemented as: CNOT(q0,q1), H(q0), MEASURE_Z(q0), MEASURE_Z(q1)
- Ends any REV segment

**Example (two outcomes)**:
```json
{
  "id": "bell_meas",
  "op": "MEASURE_BELL",
  "vqs": ["q0", "q1"],
  "produces": ["m0", "m1"]
}
```

**Example (Bell state index)**:
```json
{
  "id": "bell_meas",
  "op": "MEASURE_BELL",
  "vqs": ["q0", "q1"],
  "produces": ["bell_index"]
}
```

**Reversibility**: Not reversible

**Use Cases**:
- Quantum teleportation
- Entanglement swapping
- Superdense coding verification
- Quantum repeaters
- Bell inequality tests

---

## Composite Operations

Composite operations require capabilities and may involve multiple logical qubits or distributed resources.

### TELEPORT_CNOT

**Opcode**: `TELEPORT_CNOT`

**Description**: Performs CNOT via gate teleportation using pre-shared entanglement.

**Required Capability**: `CAP_TELEPORT`

**Arguments**: None

**Consumes**: 2 virtual qubits (VQ) - control, target

**Produces**: 2 virtual qubits (VQ, same handles)

**Semantics**:
- Logically equivalent to CNOT but uses teleportation protocol
- Useful when qubits are on different physical modules
- Consumes pre-shared Bell pairs (managed by kernel)
- May involve classical communication and Pauli corrections

**Example**:
```json
{
  "id": "tcnot1",
  "op": "TELEPORT_CNOT",
  "vqs": ["qA", "qB"],
  "caps": ["CAP_TELEPORT"]
}
```

**Reversibility**: Reversible (unitary overall, but may involve internal measurements)

**Performance**: Higher latency than local CNOT; use when qubits are distributed.

---

### INJECT_T_STATE

**Opcode**: `INJECT_T_STATE`

**Description**: Injects a magic |T⟩ state into a qubit for T-gate synthesis.

**Required Capability**: `CAP_MAGIC`

**Arguments**: None

**Consumes**: 1 virtual qubit (VQ, must be in |0⟩)

**Produces**: 1 virtual qubit (VQ, now in |T⟩ state)

**Semantics**:
- Prepares qubit in |T⟩ = (|0⟩ + e^(iπ/4)|1⟩)/√2
- Used for T-gate synthesis via gate teleportation
- Kernel manages magic state distillation factory
- Expensive operation (requires many physical qubits)

**Example**:
```json
{
  "id": "inject1",
  "op": "INJECT_T_STATE",
  "vqs": ["q0"],
  "caps": ["CAP_MAGIC"]
}
```

**Usage**: For non-Clifford gates in fault-tolerant quantum computing.

---

### OPEN_CHAN

**Opcode**: `OPEN_CHAN`

**Description**: Opens an entanglement channel between two qubits.

**Required Capability**: `CAP_LINK`

**Arguments**:
- `opts` (object): Channel options
  - `fidelity` (number): Minimum required fidelity (0-1)
  - `type` (string): Channel type (e.g., "bell_pair", "ghz")

**Consumes**: 2 virtual qubits (VQ)

**Produces**: 
- 2 virtual qubits (VQ, now entangled)
- 1 channel handle (CH)

**Semantics**:
- Establishes entanglement between qubits (e.g., Bell pair)
- Channel handle tracks entanglement resource
- Kernel may perform entanglement purification
- Cross-tenant channels require brokering

**Example**:
```json
{
  "id": "open1",
  "op": "OPEN_CHAN",
  "args": {
    "opts": {
      "fidelity": 0.99,
      "type": "bell_pair"
    }
  },
  "vqs": ["qA", "qB"],
  "chs": ["ch0"],
  "caps": ["CAP_LINK"]
}
```

---

### USE_CHAN

**Opcode**: `USE_CHAN`

**Description**: Performs an operation using an established channel.

**Required Capability**: None (channel already opened with `CAP_LINK`)

**Arguments**:
- `semantic` (string): Operation to perform (e.g., "teleport", "swap")

**Consumes**: 1 channel handle (CH)

**Produces**: 1 channel handle (CH, potentially degraded)

**Semantics**:
- Uses entanglement resource for distributed operation
- Channel fidelity may degrade with use
- Kernel tracks entanglement consumption

**Example**:
```json
{
  "id": "use1",
  "op": "USE_CHAN",
  "args": { "semantic": "teleport" },
  "chs": ["ch0"]
}
```

---

### CLOSE_CHAN

**Opcode**: `CLOSE_CHAN`

**Description**: Closes an entanglement channel, releasing resources.

**Required Capability**: None

**Arguments**: None

**Consumes**: 1 channel handle (CH)

**Produces**: Nothing

**Semantics**:
- **Irreversible operation** (destroys entanglement)
- Releases channel resources back to kernel
- Ends any REV segment involving the channel

**Example**:
```json
{
  "id": "close1",
  "op": "CLOSE_CHAN",
  "chs": ["ch0"]
}
```

**Reversibility**: Not reversible (irreversible boundary)

---

## Control Flow

### COND_PAULI

**Opcode**: `COND_PAULI`

**Description**: Conditionally applies Pauli corrections based on measurement outcome.

**Required Capability**: None

**Arguments**:
- `mask` (string): Pauli operator to apply ("X", "Y", "Z", "I")

**Consumes**: 
- 1 virtual qubit (VQ)
- 1 or more events (EV) as inputs

**Produces**: 1 virtual qubit (VQ, same handle)

**Semantics**:
- If event value is 1, apply Pauli; otherwise do nothing
- Used for measurement-based quantum computing
- Can combine multiple events with XOR logic

**Example**:
```json
{
  "id": "cond1",
  "op": "COND_PAULI",
  "args": { "mask": "X" },
  "vqs": ["q0"],
  "inputs": ["m0"]
}
```

**Reversibility**: Reversible if Pauli is self-inverse (X, Y, Z)

---

### Guards (Conditional Execution)

Guards are not operations but node attributes that enable conditional execution.

**Syntax**:
```json
{
  "id": "node1",
  "op": "APPLY_H",
  "vqs": ["q0"],
  "guard": {
    "event": "m0",
    "equals": 1
  }
}
```

**Semantics**:
- Node executes only if `event == equals`
- All branches must be pre-materialized in the DAG
- No unbounded loops (DAG structure enforced)

**Usage**: Implement measurement-based feedback and error correction.

---

## Administrative Operations

### SET_POLICY

**Opcode**: `SET_POLICY`

**Description**: Sets policy hints for kernel scheduling and resource management.

**Required Capability**: None

**Arguments**: Key-value pairs for policy settings
- `priority` (integer): Scheduling priority (higher = more urgent)
- `deadline` (integer): Deadline in epochs
- `code_distance` (integer): Preferred error correction distance

**Consumes**: Nothing

**Produces**: 1 policy binding handle (BND)

**Semantics**:
- **Non-binding hints** to kernel
- Does not affect program semantics
- Kernel makes best-effort attempt to honor policies
- Used for QoS and resource optimization

**Example**:
```json
{
  "id": "policy1",
  "op": "SET_POLICY",
  "args": {
    "priority": 10,
    "deadline": 100,
    "code_distance": 9
  }
}
```

**Note**: Policies are advisory; kernel may ignore them under resource pressure.

---

## Instruction Summary Table

| Opcode | Category | Reversible | Required CAP | Produces |
|--------|----------|------------|--------------|----------|
| ALLOC_LQ | Lifecycle | No | CAP_ALLOC | VQ handles |
| FREE_LQ | Lifecycle | No | None | - |
| FENCE_EPOCH | Lifecycle | Yes | None | - |
| BAR_REGION | Lifecycle | Yes | None | - |
| APPLY_H | Logical | Yes | None | VQ |
| APPLY_S | Logical | Yes | None | VQ |
| APPLY_X | Logical | Yes | None | VQ |
| APPLY_Y | Logical | Yes | None | VQ |
| APPLY_Z | Logical | Yes | None | VQ |
| APPLY_CNOT | Logical | Yes | None | VQ |
| RESET | Logical | No | None | VQ |
| MEASURE_Z | Measurement | No | None | VQ, EV |
| MEASURE_X | Measurement | No | None | VQ, EV |
| TELEPORT_CNOT | Composite | Yes* | CAP_TELEPORT | VQ |
| INJECT_T_STATE | Composite | No | CAP_MAGIC | VQ |
| OPEN_CHAN | Composite | No | CAP_LINK | VQ, CH |
| USE_CHAN | Composite | Depends | None | CH |
| CLOSE_CHAN | Composite | No | None | - |
| COND_PAULI | Control | Yes | None | VQ |
| SET_POLICY | Admin | Yes | None | BND |

*Reversible overall but may involve internal measurements

---

## Version History

- **v0.1** (2024): Initial specification with core instruction set
