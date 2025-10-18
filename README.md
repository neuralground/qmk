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

## Documentation Index

### 📖 Getting Started (Read in Order)

1. **[Overview](docs/overview.md)** — High-level introduction to QMK
2. **[Design & Architecture](docs/design-architecture-spec.md)** — System architecture, goals, and roadmap
3. **[QVM Specification](docs/QVM-spec.md)** ⭐ — **Complete QVM specification** (primary reference)
   - Introduction and design principles
   - Resource handles (VQ, CH, EV, CAP, BND)
   - Graph structure and format
   - Verification rules (linearity, capabilities, DAG)
   - Execution semantics and reversibility
   - Security model and conformance
   - Future extensions
4. **[QVM Instruction Reference](docs/QVM-instruction-reference.md)** — Detailed opcode documentation
   - All 20 operations with examples
   - Capability requirements
   - Reversibility classification

### 🔧 Technical Deep Dives

- **[Architecture](docs/architecture.md)** — Layered architecture details
- **[qSyscall ABI](docs/qsyscall-abi.md)** — User ↔ Kernel interface
- **[Security Model](docs/security-model.md)** — Capability security and isolation
- **[Reversibility](docs/reversibility.md)** — REV segments and uncomputation
- **[Scheduling](docs/scheduling.md)** — Epoch-based scheduling model
- **[Testing](docs/testing.md)** — Testing strategy

### 💻 Examples & Tools

- **[Example Programs](qvm/examples/README.md)** — Comprehensive guide to all examples
  - `bell_teleport_cnot.qvm.json` — Bell state preparation
  - `teleportation_demo.qvm.json` — Full quantum teleportation protocol
  - `ghz_state.qvm.json` — 4-qubit GHZ state
  - `conditional_correction.qvm.json` — Measurement-based control flow
  - `reversible_segment.qvm.json` — REV segment demonstration
- **[JSON Schema](qvm/qvm_schema.json)** — Canonical QVM format schema
- **[Validator Tool](qvm/tools/qvm_validate.py)** — Graph validation with linearity checks

### 📚 Reference Materials

**Suggested Reading Order for New Contributors:**
1. Start with [Overview](docs/overview.md) for context
2. Read [Design & Architecture](docs/design-architecture-spec.md) for the big picture
3. Study [QVM Specification](docs/QVM-spec.md) for complete details
4. Explore [Example Programs](qvm/examples/README.md) to see QVM in action
5. Consult [Instruction Reference](docs/QVM-instruction-reference.md) as needed
6. Deep dive into specific topics (security, scheduling, etc.) as relevant

## Status
This is a pedagogical prototype to make the specification concrete. **Phase 1 complete:**
- ✅ Comprehensive QVM specification (100+ pages)
- ✅ JSON Schema with validation rules
- ✅ Enhanced validator (linearity, capabilities, DAG, REV segments)
- ✅ Example programs demonstrating key features
- ✅ Minimal kernel simulator

**Not yet implemented:** Real QEC decoding, fault injection, distributed teleportation channels, formal verification, multi-tenant isolation.
