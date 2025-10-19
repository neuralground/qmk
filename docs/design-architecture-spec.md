# QMK — Design & Architecture Specification

**Scope:** Logical-qubit microkernel for multi-tenant quantum systems. The QMK supervisor manages all physical resources and executes user-submitted **QVM graphs** (verifiable bytecode).

## 1. Goals & Non-goals
### Goals
- Minimal, auditable **microkernel** with strict privilege separation.
- **Capability security**, **linear resources**, and **isolation** (entanglement firewall).
- **Deterministic epochs** aligned with stabilizer cycles.
- **Reversibility-aware** semantics to enable rollback, migration, and energy efficiency.
- Adaptivity via **user-mode JIT** and **resource manager**.
- Portable pipeline: Front-end → QIR/MLIR (static) → **QVM** (runtime).

### Non-goals
- No vendor pulse compilation in kernel.
- No heavy compiler heuristics in kernel.
- No NISQ-specific features (assume logical qubits).

## 2. Layered Architecture
1. **Front-ends & static compilers** (Q#, Qiskit via bridges) → QIR/MLIR.
2. **Middle-end**: QIR-to-QIR optimizations.
3. **Lowering**: QIR → **QVM** (graphs with handles, caps, guards).
4. **User-mode Runtime**: JIT planner, resource manager, submission client.
5. **QMK Microkernel** (supervisor): mapping, decoding, scheduling, capability enforcement.
6. **Physical Control Layer**: device drivers, calibration (out of scope).

## 3. QVM (Bytecode) Model
- **Graph**: finite DAG of nodes (ops) with typed resources and event guards.
- **Handles**: VQ (virtual qubit), CH (channel), EV (event), CAP (capability), BND (policy binding). VQ/CH are **linear**.
- **Ops**: lifecycle, logical, composite (cap-gated), admin (metadata). See `docs/QVM-spec.md` and `qvm/qvm_schema.json`.
- **Guards**: event-driven branching; no unbounded loops in supervisor.
- **Reversibility**: Unitary-only segments between irreversible ops are **REV**; kernel may uncompute.

## 4. Security Model
- **Capabilities** gate privileged ops (ALLOC, LINK, TELEPORT, MAGIC).
- **Tenant isolation** via handle namespaces and channel brokering.
- **Verifier** enforces linearity, caps, DAG acyclicity, bounded guards.

## 5. Scheduling Model
- **Epochs**: all scheduling decisions occur at epoch boundaries.
- **Preemption**: at `FENCE_EPOCH`; REV segments allow cheap rollback.
- **QoS**: priorities, deadlines (hints via BND). Kernel aims for fairness + stability.

## 6. Mapping & Decoding
- Supervisor owns virtual→physical mapping; can migrate at fences.
- Continuous decoding loop; code-distance adjustments are internal policy.
- Entanglement service for channels with purification and accounting.

## 7. User-mode JIT & Resource Manager
- **JIT**: profile-guided selection (SHYPS vs surface), teleport planning, caching, variant generation.
- **Resource Manager**: inventory of logical blocks, T-state throughput, link capacity, admission control.
- **Adaptivity**: degraded modes (serialize teleports, raise distances, add fences).

## 8. Failure & Exceptional Conditions
- Calibration drift → tighter fences, adjusted distances.
- Link degradation → switch to local decompositions or batched links.
- Hot module failure → migrate logical blocks; rollback REV segments.
- Decoder overload → throttle measurement-heavy regions.

## 9. Auditability & Telemetry
- Per-epoch attestation: mapping summaries, capability decisions, resource usage.
- Deterministic replay via seed logs and event timelines.

## 10. Conformance & Interop
- Canonical **QVM JSON Schema** and reference **validator**.
- qSyscall ABI (JSON/proto) for kernel interface.
- Reference kernel simulator for semantics.

## 11. Threat Model (excerpt)
- Tenant attempts to forge cross-tenant entanglement → blocked by capability + linear handles.
- Handle forgery → unforgeable handles + namespace binding.
- Resource exhaustion → quotas & admission control.

## 12. Evolution & Versioning
- Versioned op families; capability negotiation.
- Backwards-compatible schema evolution; deprecation windows.

## 13. Performance Considerations
- Short REV segments to enable frequent fences and migration.
- Batch measurements to reduce decoder peaks.
- Cache composite operations (teleportation macros) in JIT.

## 14. Evolution & Future Directions

The architecture is designed to support incremental enhancement in several key areas:

- **Advanced Reversibility**: Formal REV segment analysis, rollback/migration capabilities
- **JIT & Adaptivity**: Profile-guided optimization, variant generation, policy engines
- **Multi-tenant Hardening**: Enhanced isolation, quotas, attestation, replay tools
- **Hardware Integration**: HAL abstractions, device drivers, entanglement service backends
- **Compiler Integration**: QIR/MLIR bridges, teleportation planning passes
- **Verification**: Formal methods, fuzzing, SMT-backed proofs, conformance suites

For detailed implementation roadmap and milestones, see [Implementation Plan](IMPLEMENTATION_PLAN.md).
