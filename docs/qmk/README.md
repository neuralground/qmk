# QMK Domain Documentation

Quantum Microkernel (QMK) - Core system architecture.

## Overview

The QMK domain defines the core microkernel architecture, including the qSyscall ABI, scheduling model, reversibility support, and system design.

## Key Documents

1. **[Architecture](ARCHITECTURE.md)**
   - Layered architecture details
   - Component interactions
   - System design

2. **[Design Specification](DESIGN_SPEC.md)**
   - System design and goals
   - Microkernel principles
   - Design philosophy

3. **[qSyscall ABI](QSYSCALL_ABI.md)**
   - User ↔ Kernel interface
   - System call specification
   - 600+ lines of specification

4. **[Reversibility](REVERSIBILITY.md)**
   - REV segments
   - Uncomputation support
   - Reversible operations

5. **[Scheduling](SCHEDULING.md)**
   - Epoch-based scheduling model
   - Resource allocation
   - Priority handling

6. **[Azure QRE Compatibility](AZURE_QRE_COMPATIBILITY.md)**
   - Azure Quantum Resource Estimator integration
   - Compatibility layer

## Architecture

### Microkernel Design
- Minimal trusted computing base
- Capability-based security
- User-mode services
- Verifiable execution

### Layers
1. **Hardware Abstraction Layer**
2. **Kernel Layer** (minimal)
3. **System Services** (user-mode)
4. **Application Layer**

### Key Components
- **Session Manager**: Capability negotiation
- **Job Manager**: Async execution
- **Resource Manager**: Qubit allocation
- **Executor**: QVM graph execution
- **RPC Server**: JSON-RPC 2.0

## Features

### Logical Qubit Simulation
- Surface code
- SHYPS (Hastings-Haah)
- Bacon-Shor
- Configurable error models

### Multi-Tenant Support
- Tenant isolation
- Resource quotas
- Entanglement firewall
- Capability-based access

### Fault-Tolerant Simulation
- QEC profiles
- Magic state distillation
- Lattice surgery
- Error tracking

## Quick Start

```python
from kernel.qmk_server import QMKServer

# Start server
server = QMKServer()
server.start()

# Server listens on Unix socket
# Clients connect via JSON-RPC 2.0
```

## qSyscall ABI

Key system calls:
- `qmk_session_create`: Create session
- `qmk_job_submit`: Submit QVM graph
- `qmk_job_wait`: Wait for completion
- `qmk_job_result`: Get results
- `qmk_resource_query`: Query resources

## Design Principles

1. **Microkernel Minimalism**: Small trusted base
2. **Capability Security**: No ambient authority
3. **Verifiability**: Formal verification possible
4. **Reversibility-Aware**: Support uncomputation
5. **Multi-Tenant**: Isolation by design

## Performance

- **Logical Qubit Simulation**: 1000+ qubits
- **Session Overhead**: <1ms
- **Job Submission**: <5ms
- **RPC Latency**: <1ms

## See Also

- [Main Documentation Index](../INDEX.md)
- [QIR Domain](../qir/)
- [QVM Domain](../qvm/)
- [Security Domain](../security/)
