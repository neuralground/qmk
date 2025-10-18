# QVM Example Programs

This directory contains example QVM graphs demonstrating various features of the Quantum Virtual Machine specification.

## Examples

### bell_teleport_cnot.qvm.json
**Description**: Creates a Bell state (maximally entangled pair) using Hadamard and CNOT gates, then measures both qubits.

**Features demonstrated**:
- Qubit allocation with `ALLOC_LQ`
- Single-qubit gates (`APPLY_H`)
- Two-qubit gates (`APPLY_CNOT`)
- Measurements (`MEASURE_Z`)
- Resource cleanup (`FREE_LQ`)
- Reversible (REV) segments

**Expected output**: Correlated measurement outcomes (both 0 or both 1)

---

### reversible_segment.qvm.json
**Description**: Demonstrates reversible computation segments with epoch fences and conditional Pauli corrections.

**Features demonstrated**:
- Epoch boundaries (`FENCE_EPOCH`)
- Reversible gate sequences (H, S)
- Measurement and conditional operations (`COND_PAULI`)
- REV segment identification

**Use case**: Shows how the kernel can identify and potentially uncompute reversible segments for rollback or migration.

---

### conditional_correction.qvm.json
**Description**: Bell state preparation with measurement-based conditional correction using guards.

**Features demonstrated**:
- Conditional execution with guards
- Measurement-dependent branching
- Multiple execution paths in the DAG
- Event-driven control flow

**Pattern**: Common in quantum error correction and measurement-based quantum computing.

---

### teleportation_demo.qvm.json
**Description**: Full quantum teleportation protocol - transfers quantum state from one qubit to another using entanglement and classical communication.

**Features demonstrated**:
- Multi-qubit entanglement preparation
- Bell measurement
- Conditional Pauli corrections (`COND_PAULI`)
- Classical communication via events
- Complex DAG with multiple dependencies

**Quantum protocol**: Standard teleportation circuit demonstrating how quantum information can be transmitted using pre-shared entanglement and classical bits.

---

### ghz_state.qvm.json
**Description**: Prepares a 4-qubit GHZ (Greenberger-Horne-Zeilinger) state - a maximally entangled state of multiple qubits.

**Features demonstrated**:
- Multi-qubit operations
- Barrier regions (`BAR_REGION`) for measurement batching hints
- Different error correction profile (`Surface(d=7)` vs `SHYPS(d=9)`)
- Parallel measurement operations

**Use case**: GHZ states are used in quantum metrology, quantum communication, and tests of quantum mechanics.

---

## Running the Examples

### Validation
Validate any example using the QVM validator:

```bash
python qvm/tools/qvm_validate.py qvm/examples/<example_name>.qvm.json
```

Example output:
```
ℹ️  [QVM-INFO] Validating QVM graph: qvm/examples/ghz_state.qvm.json
ℹ️  [QVM-INFO] JSON schema validation passed
ℹ️  [QVM-INFO] Graph contains 12 nodes
ℹ️  [QVM-INFO] Declared resources: 4 VQs, 0 CHs, 4 events
ℹ️  [QVM-INFO] Topological order: free1 → m3 → m2 → m1 → m0 → bar1 → fence1 → cnot3 → cnot2 → cnot1 → h1 → alloc1
ℹ️  [QVM-INFO] Found 2 reversible (REV) segments:
ℹ️  [QVM-INFO]   REV-1: alloc1 -> h1 -> cnot1 -> cnot2 -> cnot3 -> fence1 -> bar1
ℹ️  [QVM-INFO]   REV-2: free1
✅ [QVM-OK] Validation passed successfully!
```

### Execution
Run examples on the QMK kernel simulator:

```bash
python scripts/demo_run.py
```

This will validate and execute multiple examples, showing simulated measurement outcomes.

---

## Creating Your Own Examples

To create a new QVM program:

1. **Start with the template**:
   ```json
   {
     "version": "0.1",
     "program": { "nodes": [ ... ] },
     "resources": { "vqs": [], "chs": [], "events": [] },
     "caps": []
   }
   ```

2. **Add operations** in the `nodes` array. Each node needs:
   - `id`: Unique identifier
   - `op`: Operation name (see [QVM Instruction Reference](../../docs/QVM-instruction-reference.md))
   - `vqs`, `chs`, `inputs`, `produces`: Resource handles
   - `caps`: Required capabilities (if any)
   - `guard`: Optional conditional execution

3. **Declare all resources** in the `resources` section

4. **List required capabilities** in the `caps` array

5. **Validate** using `qvm_validate.py`

---

## Common Patterns

### Bell Pair Creation
```json
{"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
{"id": "cnot1", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]}
```

### Measurement with Conditional Correction
```json
{"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
{"id": "corr", "op": "APPLY_X", "vqs": ["q1"], "guard": {"event": "m0", "equals": 1}}
```

### Epoch Fence for Preemption
```json
{"id": "fence1", "op": "FENCE_EPOCH"}
```

---

## Reference Documentation

- **[QVM Specification](../../docs/QVM-spec.md)**: Complete specification
- **[Instruction Reference](../../docs/QVM-instruction-reference.md)**: Detailed opcode documentation
- **[JSON Schema](../qvm_schema.json)**: Canonical schema definition

---

## Notes

- All examples use `CAP_ALLOC` capability for qubit allocation
- Measurement outcomes are deterministic (seeded) in the simulator
- REV segments are automatically identified by the validator
- Topological order shows execution dependencies (reverse order in output)
