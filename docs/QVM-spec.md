# The Quantum Virtual Machine Specification

**Version 0.1**

## Table of Contents

1. [Introduction](#1-introduction)
2. [The Structure of the QVM](#2-the-structure-of-the-qvm)
3. [QVM Graph Format](#3-qvm-graph-format)
4. [Instruction Set](#4-instruction-set)
5. [Verification](#5-verification)
6. [Execution Semantics](#6-execution-semantics)
7. [Instruction Reference](#7-instruction-reference)

---

## 1. Introduction

### 1.1 Purpose and Scope

The Quantum Virtual Machine (QVM) is an abstract execution model for quantum computations on logical qubits. By analogy to the Java Virtual Machine (JVM), which provides a platform-independent bytecode for classical computation, the QVM provides a **quantum bytecode** that abstracts hardware architecture, quantum error correction codes, and physical resource management.

The QVM is designed for:
- **Multi-tenant quantum systems** where multiple applications share physical quantum resources
- **Logical-qubit architectures** with quantum error correction
- **Supervisor-mode execution** where a certified kernel manages all physical resources
- **User-mode compilation** where applications are lowered to QVM graphs by trusted compilers

### 1.2 Design Principles

**Declarative DAG Model**: QVM programs are finite directed acyclic graphs (DAGs) of quantum operations, not imperative instruction sequences. This enables:
- Static verification of resource usage
- Parallel execution analysis
- Reversibility detection
- Migration and checkpointing

**Linear Resource Semantics**: Quantum resources (qubits, channels) are **linear types** with single ownership, preventing:
- Accidental cloning
- Cross-tenant entanglement leaks
- Resource aliasing bugs

**Capability Security**: Privileged operations require explicit capability tokens, enabling:
- Fine-grained access control
- Multi-tenant isolation
- Auditable resource usage

**Reversibility-Aware**: The QVM distinguishes reversible (unitary) and irreversible operations, enabling:
- Efficient rollback and migration
- Uncomputation for resource efficiency
- Checkpoint/restore semantics

### 1.3 Relationship to Other Quantum IRs

- **QIR (Quantum Intermediate Representation)**: QVM is a lower-level runtime format. QIR programs are compiled to QVM graphs.
- **OpenQASM**: QVM operates at the logical-qubit level, abstracting physical gates and error correction.
- **Quil**: Similar abstraction level but QVM emphasizes DAG structure and capability security.

### 1.4 Overview

QVM is a **declarative DAG** of operations over **linear, capability-guarded handles**.

---

## 2. The Structure of the QVM

### 2.1 Resource Handles

The QVM operates on typed **handles** that represent quantum and classical resources:

#### 2.1.1 Virtual Qubit (VQ)
- **Type**: Linear (single owner, no aliasing)
- **Semantics**: Represents a logical qubit with quantum error correction
- **Lifecycle**: Created by `ALLOC_LQ`, destroyed by `FREE_LQ`
- **Operations**: Can be operated on by gates, measured, or used in channels
- **Ownership**: Exactly one operation consumes and produces each VQ at each point in the DAG

#### 2.1.2 Channel (CH)
- **Type**: Linear (single owner)
- **Semantics**: Represents an entanglement resource between two qubits
- **Lifecycle**: Created by `OPEN_CHAN`, destroyed by `CLOSE_CHAN`
- **Purpose**: Enables distributed quantum operations (teleportation, entanglement swapping)
- **Brokering**: Cross-tenant channels require capability mediation

#### 2.1.3 Event (EV)
- **Type**: Non-linear (can be read multiple times)
- **Semantics**: Classical measurement outcome (0 or 1)
- **Production**: Created by `MEASURE_Z`, `MEASURE_X`, etc.
- **Consumption**: Used in guards and conditional operations
- **Determinism**: Events are deterministic within a QVM execution (seeded randomness)

#### 2.1.4 Capability (CAP)
- **Type**: Non-linear token
- **Semantics**: Authorization to perform privileged operations
- **Examples**: `CAP_ALLOC`, `CAP_TELEPORT`, `CAP_MAGIC`, `CAP_LINK`
- **Binding**: Capabilities are bound to the submitting tenant/principal
- **Verification**: Kernel verifies capability possession before executing gated operations

#### 2.1.5 Policy Binding (BND)
- **Type**: Metadata context
- **Semantics**: Hints and constraints for kernel scheduling/mapping
- **Examples**: QoS priorities, deadlines, code distance preferences
- **Enforcement**: Best-effort by kernel; not security-critical

### 2.2 Graph Structure

A QVM program is a **finite directed acyclic graph (DAG)** where:
- **Nodes** represent operations (instructions)
- **Edges** represent data dependencies (handle flow)
- **Guards** enable conditional execution based on measurement events

#### 2.2.1 Nodes
Each node has:
- **Unique ID**: String identifier within the graph
- **Opcode**: Operation type (e.g., `APPLY_H`, `MEASURE_Z`)
- **Arguments**: Operation-specific parameters (e.g., rotation angles, profiles)
- **Input Handles**: Resources consumed (VQs, CHs, EVs)
- **Output Handles**: Resources produced (VQs, EVs, CHs)
- **Required Capabilities**: CAPs needed to execute this operation
- **Guard**: Optional predicate on an event (enables conditional execution)

#### 2.2.2 Edges
Edges are implicit in the handle flow:
- A node that produces handle `h` must execute before any node that consumes `h`
- Linear handles (VQ, CH) enforce single-consumer semantics
- Non-linear handles (EV) can be consumed by multiple nodes

#### 2.2.3 Guards
Guards enable branching without unbounded loops:
- Form: `if event == value then execute_node`
- Values: 0 or 1 (binary measurement outcomes)
- Pre-materialization: All branches are present in the graph; guards select which execute
- No loops: DAG structure prevents unbounded iteration

### 2.3 Reversibility

The QVM distinguishes **reversible** and **irreversible** operations:

**Reversible Operations** (unitary gates):
- `APPLY_H`, `APPLY_S`, `APPLY_X`, `APPLY_Y`, `APPLY_Z`, `APPLY_CNOT`
- Carry inverse descriptors for uncomputation
- Can be rolled back without measurement

**Irreversible Operations**:
- `MEASURE_Z`, `MEASURE_X` (collapse quantum state)
- `RESET` (discards quantum information)
- `CLOSE_CHAN` (destroys entanglement resource)

**REV Segments**:
- Maximal sequences of reversible operations between irreversible boundaries
- Kernel may uncompute REV segments for:
  - Rollback after errors
  - Migration between physical resources
  - Energy efficiency (uncompute ancilla)

### 2.4 Execution Model

**Supervisor Mode**: The QMK kernel executes QVM graphs with exclusive control over:
- Physical qubit allocation and mapping
- Quantum error correction decoding
- Scheduling and preemption
- Capability enforcement

**Epochs**: Execution proceeds in discrete epochs aligned with stabilizer measurement cycles:
- `FENCE_EPOCH` operations mark epoch boundaries
- Scheduling decisions occur at fences
- Preemption and migration happen at fences

**Determinism**: QVM execution is deterministic given:
- The input graph
- Initial quantum state
- Random seed for measurements
- This enables replay and debugging

---

## 3. QVM Graph Format

### 3.1 JSON Representation

QVM graphs are represented in JSON format with the following top-level structure:

```json
{
  "version": "0.1",
  "program": { ... },
  "resources": { ... },
  "caps": [ ... ]
}
```

### 3.2 Version Field

- **Type**: String
- **Value**: `"0.1"` (current version)
- **Purpose**: Enables versioned evolution of the QVM format

### 3.3 Program Field

Contains the DAG of operations:

```json
"program": {
  "nodes": [
    {
      "id": "n1",
      "op": "APPLY_H",
      "vqs": ["q0"],
      "guard": { "event": "m0", "equals": 1 }
    },
    ...
  ]
}
```

Each node specifies:
- `id`: Unique string identifier
- `op`: Operation name
- `args`: Optional operation-specific arguments (object)
- `vqs`: Virtual qubits consumed/produced (array of strings)
- `chs`: Channels consumed/produced (array of strings)
- `inputs`: Input events (array of strings)
- `produces`: Output events (array of strings)
- `caps`: Required capabilities (array of strings)
- `guard`: Optional conditional execution (object with `event` and `equals` fields)

### 3.4 Resources Field

Declares all handles used in the graph:

```json
"resources": {
  "vqs": ["q0", "q1", "q2"],
  "chs": ["ch0"],
  "events": ["m0", "m1"]
}
```

### 3.5 Capabilities Field

Lists all capabilities required by the graph:

```json
"caps": ["CAP_ALLOC", "CAP_TELEPORT"]
```

The kernel verifies the submitting tenant possesses these capabilities before execution.

### 3.6 Formal Schema

See `qvm/qvm_schema.json` for the canonical JSON Schema definition.

---

## 4. Instruction Set

### 4.1 Opcode Families (v0)
### Lifecycle
- `ALLOC_LQ(n, profile) -> {VQ...}` (CAP:ALLOC)
- `FREE_LQ({VQ...})`
- `FENCE_EPOCH()`
- `BAR_REGION(tag)` (hint)

### Logical (portable)
- `APPLY_H(VQ)`
- `APPLY_S(VQ)`
- `APPLY_X/Z/Y(VQ)`
- `APPLY_CNOT(VQc,VQt)`
- `RESET(VQ)`
- `MEASURE_Z/X(VQ) -> EV`
- `COND_PAULI(EV, mask, actions)`

### Composite (negotiated via capability)
- `TELEPORT_CNOT(VQa,VQb)` (CAP:TELEPORT)
- `INJECT_T_STATE(VQdst)` (CAP:MAGIC)
- `OPEN_CHAN(VQa,VQb,opts) -> CH` (CAP:LINK)
- `USE_CHAN(CH, semantic)`
- `CLOSE_CHAN(CH)`

### Admin (metadata only)
- `SET_POLICY(BND, k=v,...)`

---

## 5. Verification

The QVM verifier performs static analysis to ensure graph validity before execution.

### 5.1 Structural Checks

**DAG Acyclicity**:
- The graph must be a directed acyclic graph (no cycles)
- Detected via topological sort or depth-first search
- Prevents unbounded loops in supervisor mode

**Node Uniqueness**:
- All node IDs must be unique within the graph
- Prevents ambiguous references

**Handle Declaration**:
- All handles used in nodes must be declared in `resources`
- Prevents undefined handle references

### 5.2 Linearity Checks

**Single Producer**:
- Each VQ and CH handle must be produced by exactly one node
- Exception: Handles created by `ALLOC_LQ` or `OPEN_CHAN`

**Single Consumer**:
- Each VQ and CH handle must be consumed by at most one subsequent node
- Linear resources cannot be aliased or duplicated

**Lifetime Tracking**:
- Every allocated VQ must eventually be freed or measured
- Channels must be closed before graph termination
- Prevents resource leaks

**Example Violation**:
```json
// INVALID: q0 consumed by two nodes
{"id": "n1", "op": "APPLY_H", "vqs": ["q0"]},
{"id": "n2", "op": "APPLY_X", "vqs": ["q0"]},  // ERROR: q0 already consumed by n1
{"id": "n3", "op": "APPLY_Z", "vqs": ["q0"]}   // ERROR: q0 already consumed
```

### 5.3 Capability Checks

**Capability Coverage**:
- For each node requiring a capability, verify the capability is in the graph's `caps` list
- Kernel verifies tenant possesses these capabilities at submission time

**Example**:
```json
// Node requires CAP_ALLOC
{"id": "n1", "op": "ALLOC_LQ", "caps": ["CAP_ALLOC"], ...}

// Graph must declare this capability
{"caps": ["CAP_ALLOC"], ...}
```

### 5.4 Guard Checks

**Event Existence**:
- All events referenced in guards must be declared in `resources.events`
- Events must be produced before they are used in guards

**Binary Values**:
- Guard `equals` field must be 0 or 1
- Matches binary measurement outcomes

**No Unbounded Loops**:
- Guards cannot create cycles (enforced by DAG structure)
- All branches must be pre-materialized

### 5.5 Type Checks

**Operation Signatures**:
- Each operation must receive the correct number and type of handles
- Example: `APPLY_CNOT` requires exactly 2 VQ handles
- Example: `MEASURE_Z` requires 1 VQ, produces 1 VQ and 1 EV

**Argument Validation**:
- Operation arguments must match expected types and formats
- Example: `ALLOC_LQ` requires integer `n` and string `profile`

### 5.6 Verification Algorithm

```
function verify_qvm_graph(graph):
    # Structural checks
    check_dag_acyclic(graph.program.nodes)
    check_node_ids_unique(graph.program.nodes)
    check_handles_declared(graph.program.nodes, graph.resources)
    
    # Linearity checks
    check_linear_handles(graph.program.nodes, graph.resources)
    check_resource_lifetimes(graph.program.nodes)
    
    # Capability checks
    check_capability_coverage(graph.program.nodes, graph.caps)
    
    # Guard checks
    check_guard_events(graph.program.nodes, graph.resources.events)
    
    # Type checks
    check_operation_signatures(graph.program.nodes)
    check_argument_types(graph.program.nodes)
    
    return VALID or list_of_errors
```

---

## 6. Execution Semantics

### 6.1 Execution Model

**Kernel-Managed Execution**:
- QVM graphs are executed by the QMK supervisor kernel
- User mode cannot directly access physical qubits
- All operations go through capability-checked syscalls

**Deterministic Execution**:
- Given the same graph, initial state, and random seed, execution is deterministic
- Measurement outcomes are pseudorandom (seeded)
- Enables replay and debugging

**Epoch-Based Scheduling**:
- Execution proceeds in discrete epochs
- `FENCE_EPOCH` operations mark epoch boundaries
- Kernel makes scheduling decisions at fences

### 6.2 Execution Order

**Topological Order**:
- Nodes execute in topological order respecting data dependencies
- Nodes with no dependencies may execute in parallel (kernel decision)

**Guard Evaluation**:
- Guarded nodes execute only if their guard predicate is true
- Guards are evaluated after the event is produced

**Example Execution**:
```
Graph:
  n1: ALLOC_LQ -> q0
  n2: APPLY_H(q0)
  n3: MEASURE_Z(q0) -> m0
  n4: APPLY_X(q0) [guard: m0 == 1]
  n5: FREE_LQ(q0)

Execution order:
  1. n1 (allocate q0)
  2. n2 (apply H to q0)
  3. n3 (measure q0, produce m0)
  4. if m0 == 1: n4 (apply X to q0)
  5. n5 (free q0)
```

### 6.3 Handle Semantics

**Virtual Qubits (VQ)**:
- Represent logical qubits with quantum state
- Mapped to physical qubits by kernel (mapping is opaque to user)
- State evolves according to quantum mechanics

**Channels (CH)**:
- Represent entanglement resources
- Kernel manages entanglement generation, purification, and tracking
- Fidelity may degrade with use

**Events (EV)**:
- Represent classical bits (0 or 1)
- Immutable once produced
- Can be read multiple times

### 6.4 Reversibility and Uncomputation

**REV Segments**:
- Maximal sequences of reversible operations between irreversible boundaries
- Kernel may uncompute REV segments for:
  - **Rollback**: Undo computation after detecting errors
  - **Migration**: Move logical qubits between physical modules
  - **Efficiency**: Uncompute ancilla qubits to free resources

**Irreversible Boundaries**:
- `MEASURE_Z`, `MEASURE_X`: Collapse quantum state
- `RESET`: Discard quantum information
- `CLOSE_CHAN`: Destroy entanglement
- `FREE_LQ`: Deallocate qubit

**Example**:
```
REV segment: [APPLY_H, APPLY_S, APPLY_CNOT]
Irreversible: MEASURE_Z
REV segment: [APPLY_X, APPLY_Z]
Irreversible: FREE_LQ
```

Kernel can uncompute the first REV segment by applying inverses in reverse order: CNOT†, S†, H†.

### 6.5 Error Handling

**Verification Errors**:
- Detected before execution
- Graph is rejected; no execution occurs
- Examples: Linearity violations, missing capabilities, cycles

**Runtime Errors**:
- Detected during execution
- Examples: Resource exhaustion, calibration failures, decoder overload
- Kernel may:
  - Rollback to last fence
  - Migrate to different physical resources
  - Abort and return error to user

**Degraded Mode**:
- Kernel may adapt to resource constraints:
  - Serialize parallel operations
  - Increase code distance (use more physical qubits)
  - Substitute composite operations with local decompositions

### 6.6 Measurement and Randomness

**Measurement Outcomes**:
- Determined by quantum state and Born rule: P(outcome) = |amplitude|²
- Pseudorandom using kernel-managed seed
- Seed can be specified for deterministic replay

**Event Production**:
- Measurement produces an event with value 0 or 1
- Event is immediately available for guards and conditional operations
- Multiple measurements produce independent events

### 6.7 Capability Enforcement

**Submission Time**:
- Kernel checks tenant possesses all capabilities in `graph.caps`
- Rejects graph if any capability is missing

**Execution Time**:
- Each capability-gated operation re-checks capability
- Prevents privilege escalation via graph manipulation

**Capability Delegation** (future):
- Tenants may delegate subsets of capabilities to sub-principals
- Enables fine-grained access control

---

## 7. Instruction Reference

For detailed specifications of all QVM operations, see:
- **[QVM Instruction Reference](QVM-instruction-reference.md)**: Complete reference for all opcodes

### 7.1 Quick Reference

**Lifecycle**: `ALLOC_LQ`, `FREE_LQ`, `FENCE_EPOCH`, `BAR_REGION`

**Logical Gates**: `APPLY_H`, `APPLY_S`, `APPLY_X`, `APPLY_Y`, `APPLY_Z`, `APPLY_CNOT`, `RESET`

**Measurements**: `MEASURE_Z`, `MEASURE_X`

**Composite**: `TELEPORT_CNOT`, `INJECT_T_STATE`, `OPEN_CHAN`, `USE_CHAN`, `CLOSE_CHAN`

**Control Flow**: `COND_PAULI`, guards

**Administrative**: `SET_POLICY`

---

## 8. Conformance and Interoperability

### 8.1 Conformance Requirements

A conforming QVM implementation must:
1. Accept all valid graphs per the JSON schema
2. Reject invalid graphs with appropriate error messages
3. Execute graphs according to the semantics in Section 6
4. Enforce linearity and capability constraints
5. Produce deterministic results given the same seed

### 8.2 JSON Schema

The canonical schema is defined in `qvm/qvm_schema.json`.

Implementations must validate graphs against this schema before execution.

### 8.3 Validator Tool

The reference validator is provided in `qvm/tools/qvm_validate.py`.

Usage:
```bash
python qvm/tools/qvm_validate.py <graph.qvm.json>
```

### 8.4 Interoperability

**QIR to QVM**:
- QIR programs can be lowered to QVM graphs
- Lowering pass maps QIR operations to QVM opcodes
- See Phase 6 roadmap in `docs/design-architecture-spec.md`

**OpenQASM to QVM**:
- OpenQASM can be compiled to QVM via intermediate QIR
- Direct lowering is also possible for simple programs

---

## 9. Security Considerations

### 9.1 Capability Security

- All privileged operations require explicit capabilities
- Capabilities are unforgeable and bound to tenants
- Prevents unauthorized resource allocation, teleportation, and cross-tenant entanglement

### 9.2 Linearity Enforcement

- Linear handles prevent accidental cloning and aliasing
- Enforced statically by verifier
- Prevents cross-tenant entanglement leaks

### 9.3 Entanglement Firewall

- Channels cannot connect tenants without brokered capability
- Kernel mediates all cross-tenant entanglement
- Prevents covert channels via entanglement

### 9.4 Resource Quotas

- Kernel enforces per-tenant resource quotas
- Prevents denial-of-service via resource exhaustion
- Quotas cover: logical qubits, channels, magic states, execution time

### 9.5 Audit and Attestation

- Kernel logs all capability decisions and resource allocations
- Per-epoch attestation enables auditing
- Deterministic replay enables forensic analysis

---

## 10. Future Extensions

### 10.1 Planned Features

**Parametric Gates**:
- Rotation gates with arbitrary angles: `RX(θ)`, `RY(θ)`, `RZ(θ)`
- Requires extended argument encoding

**Multi-Qubit Gates**:
- Toffoli, Fredkin, arbitrary controlled-U
- May require capability negotiation

**Advanced Channels**:
- GHZ states, cluster states
- Multipartite entanglement

**Dynamic Allocation**:
- Allocate qubits conditionally based on measurement outcomes
- Requires careful linearity tracking

**Capability Delegation**:
- Tenants can delegate subsets of capabilities
- Enables hierarchical access control

### 10.2 Versioning

- QVM version is specified in `version` field
- Future versions may add opcodes or extend schemas
- Backward compatibility via version negotiation

---

## Appendix A: Example Programs

See `qvm/examples/` for complete example programs:
- `bell_teleport_cnot.qvm.json`: Bell state preparation and measurement
- `reversible_segment.qvm.json`: Demonstrates REV segments and fences

---

## Appendix B: References

- **QIR Specification**: [https://github.com/qir-alliance/qir-spec](https://github.com/qir-alliance/qir-spec)
- **OpenQASM**: [https://github.com/openqasm/openqasm](https://github.com/openqasm/openqasm)
- **JVM Specification**: [https://docs.oracle.com/javase/specs/](https://docs.oracle.com/javase/specs/)
- **Linear Types**: Pierce, B. C. (2002). *Types and Programming Languages*
- **Capability Security**: Miller, M. S. (2006). *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control*

---

## Appendix C: Glossary

- **CAP**: Capability token authorizing privileged operations
- **CH**: Channel handle representing entanglement resource
- **DAG**: Directed Acyclic Graph
- **EV**: Event handle representing classical measurement outcome
- **QEC**: Quantum Error Correction
- **QIR**: Quantum Intermediate Representation
- **QMK**: Quantum Microkernel
- **QVM**: Quantum Virtual Machine
- **REV**: Reversible segment of unitary operations
- **VQ**: Virtual Qubit handle representing a logical qubit

---

**End of Specification**
