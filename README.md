# QMK - Quantum Microkernel

A capability-based quantum operating system with logical qubit simulation and qSyscall ABI.

[![Tests](https://img.shields.io/badge/tests-146%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Quantum Microkernel (QMK)** architecture for a **logical-qubit** quantum system,
supporting **multi-tenant** execution of **Quantum Virtual Machine (QVM)** programs expressed in a minimal,
verifiable **QVM Bytecode**.

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

## Quick Start

### Start the Server
```bash
python -m kernel.qmk_server
```

### Run Examples
```bash
# Simple Bell state
python examples/simple_bell_state.py

# Run all examples
./examples/run_all_examples.sh

# Performance benchmark
python examples/benchmark.py
```

See **[Getting Started Guide](docs/GETTING_STARTED.md)** for detailed instructions.

## Documentation Index

### 📖 Getting Started (Read in Order)

1. **[Overview](docs/overview.md)** — High-level introduction to QMK
2. **[Getting Started Guide](docs/GETTING_STARTED.md)** — Installation, quick start, and basic usage
3. **[Tutorial](docs/TUTORIAL.md)** — Step-by-step guide to building quantum applications
4. **[Quick Reference](docs/QUICK_REFERENCE.md)** — Fast reference for common operations
5. **[Design & Architecture](docs/design-architecture-spec.md)** — System architecture and goals
6. **[QVM Specification](docs/QVM-spec.md)** ⭐ — **Complete QVM specification** (primary reference)
   - Introduction and design principles
   - Resource handles (VQ, CH, EV, CAP, BND)
   - Graph structure and format
   - Verification rules (linearity, capabilities, DAG)
   - Execution semantics and reversibility
   - Security model and conformance
   - Future extensions
7. **[QVM Instruction Reference](docs/QVM-instruction-reference.md)** — Detailed opcode documentation
   - All 20 operations with examples
   - Capability requirements
   - Reversibility classification
8. **[QVM Assembly Language](docs/QVM-ASSEMBLY.md)** — Human-readable assembly format
   - Simpler syntax than JSON
   - Full round-trip conversion
   - Assembler and disassembler tools

### 🔧 Technical Deep Dives

- **[Architecture](docs/architecture.md)** — Layered architecture details
- **[qSyscall ABI](docs/qsyscall-abi.md)** — User ↔ Kernel interface
- **[Security Model](docs/security-model.md)** — Capability security and isolation
- **[Reversibility](docs/reversibility.md)** — REV segments and uncomputation
- **[Scheduling](docs/scheduling.md)** — Epoch-based scheduling model
- **[Azure QRE Compatibility](docs/AZURE_QRE_COMPATIBILITY.md)** — Integration with Azure Quantum Resource Estimator
- **[Testing](docs/testing.md)** — Testing strategy

### 💻 Examples & Tools

- **[Python Examples](examples/README.md)** — Working examples using the client library
  - Bell states, VQE ansatz, multi-qubit entanglement
  - Adaptive circuits with guards
  - Classic algorithms (Grover's, Shor's, Deutsch-Jozsa)
  - Performance benchmarking
- **[QIR Examples](qir_examples/README.md)** — External front-end integration
  - Q# programs compiled to QIR
  - Qiskit circuits exported to QIR
  - Cirq circuits exported to QIR
  - End-to-end QIR → QVM → Execution workflow
- **[QVM Example Programs](qvm/examples/README.md)** — QVM graph format examples
  - `bell_teleport_cnot.qvm.json` — Bell state preparation
  - `teleportation_demo.qvm.json` — Full quantum teleportation protocol
  - `ghz_state.qvm.json` — 4-qubit GHZ state
  - `conditional_correction.qvm.json` — Measurement-based control flow
  - `reversible_segment.qvm.json` — REV segment demonstration
- **[JSON Schema](qvm/qvm_schema.json)** — Canonical QVM format schema
- **[Validator Tool](qvm/tools/qvm_validate.py)** — Graph validation with linearity checks
- **[Assembler](qvm/tools/qvm_asm.py)** — Convert assembly to JSON
- **[Disassembler](qvm/tools/qvm_disasm.py)** — Convert JSON to assembly

### 📚 Reference Materials

**Suggested Reading Order for New Contributors:**
1. Start with [Overview](docs/overview.md) for high-level context
2. Follow the [Getting Started Guide](docs/GETTING_STARTED.md) to run your first example
3. Work through the [Tutorial](docs/TUTORIAL.md) to build quantum applications
4. Read [Design & Architecture](docs/design-architecture-spec.md) for system architecture
5. Study [QVM Specification](docs/QVM-spec.md) for complete technical details
6. Explore [Python Examples](examples/README.md) and [QVM Examples](qvm/examples/README.md)
7. Consult [Instruction Reference](docs/QVM-instruction-reference.md) and [Quick Reference](docs/QUICK_REFERENCE.md) as needed
8. Deep dive into specific topics ([Security](docs/security-model.md), [Scheduling](docs/scheduling.md), [qSyscall ABI](docs/qsyscall-abi.md), etc.) as relevant

## Current Status

**Implemented Features:**
- Comprehensive QVM specification with 20 documented operations
- JSON Schema with validation rules and enhanced validator
- qSyscall ABI specification (600+ lines)
- Azure QRE compatibility layer
- Logical qubit simulator with configurable error models
- QEC profiles (Surface, SHYPS, Bacon-Shor)
- Enhanced kernel executor supporting all QVM operations
- Resource manager with telemetry
- Session manager with capability negotiation
- Job manager with async execution
- RPC server (JSON-RPC 2.0 over Unix sockets)
- Python client library
- Comprehensive example programs (Bell states, VQE, GHZ/W states, adaptive circuits)
- Performance benchmarking suite

**Test Coverage:**
```
Total Tests: 146 (100% passing)
  Session Manager: 19 tests
  Job Manager: 19 tests
  Integration: 9 tests
  Simulator: 67 tests
  Executor: 10 tests
  Other: 22 tests
```

For future development roadmap, see [Implementation Plan](docs/IMPLEMENTATION_PLAN.md).
