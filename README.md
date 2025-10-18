# QMK — Quantum Microkernel (prototype repo)

This repository defines a **Quantum Microkernel (QMK)** architecture for a **logical-qubit** quantum system,
supporting **multi-tenant** execution of **Quantum Virtual Machine (QVM)** programs expressed in a minimal,
verifiable **QVM Bytecode (QVM)**.

> Design goals: microkernel minimalism, capability security, verifiability, reversibility-aware semantics,
> and adaptability via a user-mode JIT + resource manager.

## Contents
- **`docs/`** — Comprehensive specifications
  - `QVM-spec.md` — Complete QVM specification (JVM-style structure)
  - `QVM-instruction-reference.md` — Detailed opcode documentation
  - `design-architecture-spec.md` — Overall architecture and roadmap
  - `qsyscall-abi.md`, `security-model.md`, `reversibility.md`, etc.
- **`qvm/`** — QVM format and tools
  - `qvm_schema.json` — JSON Schema with validation rules
  - `examples/` — Example programs (Bell states, teleportation, GHZ, etc.)
  - `tools/qvm_validate.py` — Enhanced validator with linearity checks
- **`kernel/`** — Reference simulator (mapping, scheduling, capabilities)
- **`runtime/`** — User-mode client stubs
- **`scripts/demo_run.py`** — Runs validator and simulator on examples

## Quick start
```bash
python3 scripts/demo_run.py
```
This will:
1) validate the sample QVM graphs, and
2) execute them on the QMK kernel simulator (with synthetic measurement outcomes).

## Documentation

### Core Specifications
- **[QVM Specification](docs/QVM-spec.md)** — Comprehensive specification modeled after the JVM spec, covering:
  - Introduction and design principles
  - Resource handles and graph structure
  - Verification and execution semantics
  - Security model and conformance
- **[Instruction Reference](docs/QVM-instruction-reference.md)** — Detailed documentation for all QVM opcodes
- **[Design & Architecture](docs/design-architecture-spec.md)** — System architecture and roadmap

### Examples
See [`qvm/examples/`](qvm/examples/) for sample programs:
- `bell_teleport_cnot.qvm.json` — Bell state preparation
- `teleportation_demo.qvm.json` — Full quantum teleportation protocol
- `ghz_state.qvm.json` — 4-qubit GHZ state
- `conditional_correction.qvm.json` — Measurement-based control flow
- `reversible_segment.qvm.json` — REV segment demonstration

## Status
This is a pedagogical prototype to make the specification concrete. **Phase 1 complete:**
- ✅ Comprehensive QVM specification (100+ pages)
- ✅ JSON Schema with validation rules
- ✅ Enhanced validator (linearity, capabilities, DAG, REV segments)
- ✅ Example programs demonstrating key features
- ✅ Minimal kernel simulator

**Not yet implemented:** Real QEC decoding, fault injection, distributed teleportation channels, formal verification, multi-tenant isolation.
