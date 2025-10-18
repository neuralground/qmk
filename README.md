# QMK — Quantum Microkernel (prototype repo)

This repository defines a **Quantum Microkernel (QMK)** architecture for a **logical-qubit** quantum system,
supporting **multi-tenant** execution of **Quantum Virtual Machine (QVM)** programs expressed in a minimal,
verifiable **QVM Bytecode (QVM)**.

> Design goals: microkernel minimalism, capability security, verifiability, reversibility-aware semantics,
> and adaptability via a user-mode JIT + resource manager.

## Contents
- `docs/` — specifications (QVM, qSyscall ABI, security model, scheduling, reversibility, testing)
- `qvm/` — QVM JSON Schema, examples, and tools (validator, pretty-printer)
- `kernel/` — reference **simulator** of the microkernel (mapping, scheduling, capability checks)
- `runtime/` — stubs for user-mode JIT/lowering and a client that submits jobs
- `scripts/demo_run.py` — runs the validator and kernel simulator on the sample QVM graphs

## Quick start
```bash
python3 scripts/demo_run.py
```
This will:
1) validate the sample QVM graphs, and
2) execute them on the QMK kernel simulator (with synthetic measurement outcomes).

## Status
This is a pedagogical prototype to make the specification concrete. It demonstrates:
- QVM JSON Schema + validator (linear handles, capabilities, DAG, guards)
- qSyscall ABI (JSON/proto schemas)
- Minimal kernel loop with virtual→physical mapping, fences, measurement events, and capability gating

**Not implemented:** real decoding, fault models, real teleportation channels, full security hardening.
