# QMK Documentation Index

Complete documentation organized by domain.

## 📖 Getting Started (Read First!)

Start here if you're new to QMK:

1. **[Installation Guide](INSTALLATION.md)** ⭐ — Install QMK and dependencies
2. **[Getting Started](GETTING_STARTED.md)** — Quick start and first examples
3. **[Tutorial](TUTORIAL.md)** — Step-by-step guide to building quantum applications
4. **[Quick Reference](QUICK_REFERENCE.md)** — Fast reference for common operations

---

## 🔷 QIR Domain (Quantum Intermediate Representation)

Circuit optimization and compilation:

- **[QIR Domain Overview](qir/QIR_DOMAIN.md)** — QIR architecture and pipeline
- **[Optimization Passes](qir/QIR_OPTIMIZATION_PASSES.md)** ⭐ — Complete pass documentation (17 passes, 18+ papers)
- **[Optimizer Guide](qir/OPTIMIZER_GUIDE.md)** — How to use the optimizer
- **[Pipeline Guide](qir/PIPELINE_GUIDE.md)** — Full QIR pipeline documentation
- **[Optimization Plan](qir/OPTIMIZATION_PLAN.md)** — Optimization strategy and roadmap

**Key Features:**
- 17 optimization passes (12 standard + 5 experimental)
- 30-80% gate reduction typical
- Multi-framework support (Qiskit, Cirq, Q#)
- Research-backed techniques (18+ papers cited)

---

## 🔶 QVM Domain (Quantum Virtual Machine)

QVM graph format and execution:

- **[QVM Specification](qvm/SPECIFICATION.md)** ⭐ — Complete QVM specification
- **[Instruction Reference](qvm/INSTRUCTION_REFERENCE.md)** — All 20 operations documented
- **[Assembly Language](qvm/ASSEMBLY_LANGUAGE.md)** — Human-readable QVM assembly
- **[Measurement Bases](qvm/MEASUREMENT_BASES.md)** — Measurement basis documentation

**Key Features:**
- 20 quantum operations
- Resource handles (VQ, CH, EV, CAP, BND)
- Graph-based representation
- Linearity verification
- Reversibility support

---

## 🔷 QMK Domain (Quantum Microkernel)

Core system architecture:

- **[Architecture](qmk/ARCHITECTURE.md)** — Layered architecture details
- **[Design Specification](qmk/DESIGN_SPEC.md)** — System design and goals
- **[qSyscall ABI](qmk/QSYSCALL_ABI.md)** — User ↔ Kernel interface
- **[Reversibility](qmk/REVERSIBILITY.md)** — REV segments and uncomputation
- **[Scheduling](qmk/SCHEDULING.md)** — Epoch-based scheduling model
- **[Azure QRE Compatibility](qmk/AZURE_QRE_COMPATIBILITY.md)** — Azure Quantum integration

**Key Features:**
- Microkernel architecture
- Capability-based security
- Logical qubit simulation
- Multi-tenant support
- Fault-tolerant simulation

---

## 🛡️ Security Domain

Security model and implementation:

- **[Security Model](security/SECURITY_MODEL.md)** ⭐ — Complete security architecture
- **[Security Index](security/SECURITY_INDEX.md)** — Security documentation overview
- **[Capability System](security/CAPABILITY_SYSTEM.md)** — Cryptographic capability tokens
- **[Multi-Tenant Security](security/MULTI_TENANT_SECURITY.md)** — Tenant isolation
- **[Implementation Summary](security/IMPLEMENTATION_SUMMARY.md)** — Phase 1-3 completion summary

**Key Features:**
- 4-layer defense in depth
- Static verification (mandatory certification)
- Cryptographic capability tokens
- Entanglement firewall
- Linear type system
- 91 security tests (100% passing)
- 0% attack success rate

---

## 📚 Documentation by Use Case

### For Users:
1. [Installation Guide](INSTALLATION.md)
2. [Getting Started](GETTING_STARTED.md)
3. [Tutorial](TUTORIAL.md)
4. [Quick Reference](QUICK_REFERENCE.md)

### For Circuit Optimization:
1. [QIR Domain Overview](qir/QIR_DOMAIN.md)
2. [Optimization Passes](qir/QIR_OPTIMIZATION_PASSES.md)
3. [Optimizer Guide](qir/OPTIMIZER_GUIDE.md)
4. [Pipeline Guide](qir/PIPELINE_GUIDE.md)

### For QVM Development:
1. [QVM Specification](qvm/SPECIFICATION.md)
2. [Instruction Reference](qvm/INSTRUCTION_REFERENCE.md)
3. [Assembly Language](qvm/ASSEMBLY_LANGUAGE.md)

### For System Architecture:
1. [Architecture](qmk/ARCHITECTURE.md)
2. [Design Specification](qmk/DESIGN_SPEC.md)
3. [qSyscall ABI](qmk/QSYSCALL_ABI.md)

### For Security:
1. [Security Model](security/SECURITY_MODEL.md)
2. [Capability System](security/CAPABILITY_SYSTEM.md)
3. [Multi-Tenant Security](security/MULTI_TENANT_SECURITY.md)
4. [Implementation Summary](security/IMPLEMENTATION_SUMMARY.md)

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md                    # This file
├── INSTALLATION.md             # Installation guide
├── GETTING_STARTED.md          # Quick start
├── TUTORIAL.md                 # Step-by-step tutorial
├── QUICK_REFERENCE.md          # Fast reference
│
├── qir/                        # QIR Domain
│   ├── QIR_DOMAIN.md
│   ├── QIR_OPTIMIZATION_PASSES.md
│   ├── OPTIMIZER_GUIDE.md
│   ├── PIPELINE_GUIDE.md
│   └── OPTIMIZATION_PLAN.md
│
├── qvm/                        # QVM Domain
│   ├── SPECIFICATION.md
│   ├── INSTRUCTION_REFERENCE.md
│   ├── ASSEMBLY_LANGUAGE.md
│   └── MEASUREMENT_BASES.md
│
├── qmk/                        # QMK Domain
│   ├── ARCHITECTURE.md
│   ├── DESIGN_SPEC.md
│   ├── QSYSCALL_ABI.md
│   ├── REVERSIBILITY.md
│   ├── SCHEDULING.md
│   └── AZURE_QRE_COMPATIBILITY.md
│
├── security/                   # Security Domain
│   ├── SECURITY_MODEL.md
│   ├── SECURITY_INDEX.md
│   ├── CAPABILITY_SYSTEM.md
│   ├── MULTI_TENANT_SECURITY.md
│   └── IMPLEMENTATION_SUMMARY.md
│
└── archive/                    # Old/Planning Docs
    ├── IMPLEMENTATION_PLAN.md
    ├── IMPLEMENTATION_STATUS.md
    ├── REFACTORING_PLAN.md
    └── SESSION_SUMMARY.md
```

---

## 🔍 Quick Links

### Most Important Documents:
- ⭐ [Installation Guide](INSTALLATION.md)
- ⭐ [QVM Specification](qvm/SPECIFICATION.md)
- ⭐ [Optimization Passes](qir/QIR_OPTIMIZATION_PASSES.md)
- ⭐ [Security Model](security/SECURITY_MODEL.md)

### For New Contributors:
1. Start with [Getting Started](GETTING_STARTED.md)
2. Read [Tutorial](TUTORIAL.md)
3. Study [QVM Specification](qvm/SPECIFICATION.md)
4. Explore [Architecture](qmk/ARCHITECTURE.md)

### For Researchers:
1. [Optimization Passes](qir/QIR_OPTIMIZATION_PASSES.md) — 18+ papers cited
2. [Security Model](security/SECURITY_MODEL.md) — 25+ papers cited
3. [QVM Specification](qvm/SPECIFICATION.md) — Formal specification

---

## 📊 Statistics

**Documentation:**
- Total documents: 25+
- Lines of documentation: 50,000+
- Research papers cited: 40+

**Code:**
- Lines of code: 15,000+
- Test coverage: 91 tests (100% passing)
- Optimization passes: 17 (12 standard + 5 experimental)

**Performance:**
- Gate reduction: 30-80% typical
- T-count reduction: 70% typical
- Attack success rate: 0%

---

**Last Updated:** October 19, 2025
