# QVM Specification (QVM Bytecode)

QVM is a **declarative DAG** of operations over **linear, capability-guarded handles**.

## Core Handles
- **VQ**: Virtual Qubit (linear, single owner)
- **CH**: Channel (linear)
- **EV**: Event/Future (produced by measurements)
- **CAP**: Capability token (non-linear)
- **BND**: Policy/binding context

## Opcode Families (v0)
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

## Reversibility
- Unitary ops carry inverse descriptors; segments between irreversible ops (MEASURE/RESET/CLOSE_CHAN) are **REV** and may be uncomputed by the kernel for rollback or efficiency.

## Guards & Events
- Branches are pre-materialized; edges guarded by EV predicates (`ev == 0/1`). No unbounded loops in-kernel.

See `qvm/eir_schema.json` for the canonical JSON Schema.
