# QMK Platform Architecture

## Overview

The QMK platform is organized into **three distinct architectural domains**, each with clear separation of concerns and well-defined interfaces:

```
┌─────────────────────────────────────────────────────────────────┐
│                      QIR DOMAIN                                 │
│  (Hardware-agnostic quantum circuit representation)             │
│                                                                 │
│  • Front-end translators (Qiskit, Cirq, PyQuil)                │
│  • QIR optimizer (14 optimization passes)                       │
│  • Static analysis and transformation                           │
│  • Intermediate Representation (IR)                             │
│                                                                 │
│  Output: Optimized QIR                                          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QVM DOMAIN                                 │
│  (User-mode quantum virtual machine)                            │
│                                                                 │
│  • QVM graph representation                                     │
│  • Capability-based resource model                              │
│  • Virtual qubit handles (VQ)                                   │
│  • Event system                                                 │
│  • User-mode runtime (JIT, planner)                             │
│  • Hardware-independent execution model                         │
│                                                                 │
│  Input: QIR → Output: QVM Graph                                 │
└─────────────────────────────────────────────────────────────────┘
                            ▼ qSyscalls
════════════════════════════════════════════════════════════════════
                    PRIVILEGE BOUNDARY
════════════════════════════════════════════════════════════════════
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QMK DOMAIN                                 │
│  (Supervisor-mode microkernel)                                  │
│                                                                 │
│  • Physical resource management                                 │
│  • Error correction implementation                              │
│  • Hardware abstraction layer (HAL)                             │
│  • Logical qubit simulation                                     │
│  • Scheduling and mapping                                       │
│  • Telemetry and monitoring                                     │
│  • Security and isolation                                       │
│                                                                 │
│  Input: QVM Graph → Output: Physical execution                  │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HARDWARE LAYER                                │
│  (Physical quantum processors or simulators)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Domain 1: QIR Domain

**Purpose**: Hardware-agnostic quantum circuit representation and optimization

**Scope**: Everything related to QIR format, independent of QVM or QMK

### Components

- **Front-end Translators**
  - `qir_bridge/qiskit_to_qir.py`
  - `qir_bridge/cirq_to_qir.py`
  - `qir_bridge/pyquil_to_qir.py`

- **QIR Optimizer**
  - `qir_bridge/optimizer/` - 14 optimization passes
  - `qir_bridge/optimizer/ir.py` - Intermediate representation
  - `qir_bridge/optimizer/passes/` - All optimization passes
  - `qir_bridge/optimizer/pass_manager.py` - Pass orchestration

- **QIR Parser**
  - `qir_bridge/qir_parser.py` - Parse QIR LLVM

### Key Principles

1. **Hardware Independence**: No knowledge of physical qubits, error correction, or specific hardware
2. **Static Analysis**: All optimizations are compile-time
3. **Standard Compliance**: Follows QIR specification
4. **Framework Agnostic**: Works with any quantum framework that produces QIR

### Interfaces

- **Input**: Quantum circuits from Qiskit, Cirq, PyQuil, etc.
- **Output**: Optimized QIR or QVM graph
- **No Dependencies**: Must not depend on QVM or QMK domains

---

## Domain 2: QVM Domain

**Purpose**: User-mode quantum virtual machine with capability-based execution model

**Scope**: Hardware-independent circuit representation and execution planning

### Components

- **QVM Graph Representation**
  - `qvm/` - QVM format specifications
  - `qvm/examples/` - Example QVM programs
  - Virtual qubit handles (VQ)
  - Event system
  - Dependency graphs

- **QVM Generator**
  - `qir_bridge/qvm_generator.py` - QIR → QVM conversion
  - `qir_bridge/converters.py` - Format conversions

- **User-mode Runtime** (Future)
  - JIT compilation
  - Resource planning
  - Capability management
  - Circuit validation

### Key Principles

1. **Capability-Based**: Operations require specific capabilities (CAP_ALLOC, CAP_TELEPORT, etc.)
2. **Virtual Resources**: Only virtual qubit handles, never physical IDs
3. **Hardware Parameterized**: Profiles specify QEC codes but not physical details
4. **Portable**: QVM graphs can run on any QMK-compatible backend

### Interfaces

- **Input**: QIR (from QIR domain)
- **Output**: QVM graph
- **Syscall Interface**: Communicates with QMK via qSyscalls
- **No Physical Access**: Cannot directly access hardware or physical qubits

---

## Domain 3: QMK Domain

**Purpose**: Supervisor-mode microkernel managing physical resources and error correction

**Scope**: Physical resource management, error correction, hardware interaction

### Components

- **Microkernel Core**
  - `kernel/qmk_server.py` - Main microkernel server
  - `kernel/session_manager.py` - Session management
  - `kernel/job_manager.py` - Job scheduling
  - `kernel/rpc_server.py` - RPC interface

- **Physical Resource Management**
  - `kernel/simulator/resource_manager.py` - Physical qubit allocation
  - `kernel/simulator/enhanced_executor.py` - Circuit execution
  - `kernel/simulator/logical_qubit.py` - Logical qubit simulation

- **Error Correction**
  - `kernel/qec/` - QEC implementations
  - `kernel/simulator/qec_profiles.py` - QEC profiles
  - `kernel/simulator/error_model.py` - Error modeling

- **Hardware Abstraction Layer (HAL)**
  - `kernel/hardware/` - Hardware interfaces
  - `kernel/simulator/` - Simulation backend

- **System Services**
  - `kernel/syscalls/` - Syscall implementations
  - `kernel/security/` - Security and isolation
  - `kernel/distributed/` - Distributed execution
  - `kernel/reversibility/` - Reversibility tracking

### Key Principles

1. **Supervisor Mode**: Full access to physical resources
2. **Hardware Aware**: Knows about physical qubits, error rates, topology
3. **Error Correction**: Implements logical qubits via QEC codes
4. **Isolation**: Enforces security boundaries between sessions
5. **Scheduling**: Manages physical resource allocation and timing

### Interfaces

- **Input**: QVM graphs (from QVM domain)
- **Output**: Physical execution results, telemetry
- **HAL Interface**: Communicates with hardware/simulators
- **Syscall Interface**: Provides services to user mode

---

## Separation of Concerns

### What Each Domain Knows

| Concern | QIR Domain | QVM Domain | QMK Domain |
|---------|-----------|-----------|-----------|
| **Physical Qubits** | ❌ No | ❌ No | ✅ Yes |
| **Virtual Qubits** | ❌ No | ✅ Yes | ✅ Yes |
| **Error Correction** | ❌ No | 📋 Profile only | ✅ Implementation |
| **Hardware Topology** | ❌ No | ❌ No | ✅ Yes |
| **Optimization** | ✅ Yes | ❌ No | ❌ No |
| **Capabilities** | ❌ No | ✅ Yes | ✅ Enforcement |
| **Scheduling** | ❌ No | ❌ No | ✅ Yes |

### Dependencies

```
QIR Domain:  Independent (no dependencies)
     ▼
QVM Domain:  Depends on QIR format only
     ▼
QMK Domain:  Depends on QVM format only
```

**Critical**: QIR domain must NEVER import from QVM or QMK domains

---

## Data Flow

### Compilation Pipeline

1. **User Code** (Qiskit/Cirq/PyQuil)
   ↓
2. **QIR Domain**: Translate to QIR
   ↓
3. **QIR Domain**: Optimize (14 passes)
   ↓
4. **QVM Domain**: Convert to QVM graph
   ↓
5. **QVM Domain**: Validate capabilities
   ↓
6. **QMK Domain**: Execute on physical hardware
   ↓
7. **Results** back to user

### Runtime Execution

```
User Mode (QVM Domain)
    │
    │ qSyscall: ALLOC_LQ(n=2, profile="Surface(d=7)")
    ▼
Supervisor Mode (QMK Domain)
    │ Allocate physical qubits
    │ Initialize error correction
    │ Return virtual handles
    ▼
User Mode receives: [VQ_0, VQ_1]
```

---

## File Organization

### Proposed Structure

```
qmk/
├── qir/                    # QIR Domain
│   ├── optimizer/
│   ├── translators/
│   ├── parser/
│   └── ir/
│
├── qvm/                    # QVM Domain
│   ├── graph/
│   ├── runtime/
│   ├── capabilities/
│   └── examples/
│
├── kernel/                 # QMK Domain
│   ├── core/              # Microkernel core
│   ├── qec/               # Error correction
│   ├── hardware/          # HAL
│   ├── simulator/         # Simulation backend
│   ├── syscalls/          # System calls
│   └── security/          # Security & isolation
│
├── docs/
├── tests/
└── examples/
```

---

## Design Principles

### 1. Separation of Concerns
- Each domain has a single, well-defined responsibility
- Clear interfaces between domains
- No circular dependencies

### 2. Privilege Separation
- QVM domain runs in user mode
- QMK domain runs in supervisor mode
- Syscall interface enforces boundaries

### 3. Hardware Independence
- QIR and QVM domains are hardware-agnostic
- Only QMK domain knows about physical resources
- Portability through abstraction

### 4. Capability-Based Security
- Operations require explicit capabilities
- QMK enforces capability checks
- Prevents unauthorized resource access

### 5. Modularity
- Each domain can be developed independently
- Clear testing boundaries
- Easy to swap implementations

---

## Testing Strategy

### QIR Domain Tests
- Optimizer pass correctness
- QIR parsing and generation
- Framework translation accuracy
- **No QVM or QMK dependencies**

### QVM Domain Tests
- Graph representation
- Capability validation
- QIR → QVM conversion
- **No physical resource tests**

### QMK Domain Tests
- Physical resource management
- Error correction implementation
- Scheduling and execution
- HAL integration

### Integration Tests
- End-to-end pipeline
- Cross-domain interfaces
- Syscall correctness

---

## Migration Path

### Phase 1: Documentation (Current)
- ✅ Define three domains clearly
- ✅ Document separation of concerns
- ✅ Identify components in each domain

### Phase 2: Code Organization
- Move QIR components to `qir/` directory
- Separate QVM runtime from kernel
- Reorganize kernel into clear subsystems

### Phase 3: Dependency Cleanup
- Remove QIR → QMK dependencies
- Ensure QVM → QMK uses only syscalls
- Verify no circular dependencies

### Phase 4: Interface Formalization
- Define formal QIR → QVM interface
- Define formal QVM → QMK syscall interface
- Document all interfaces

---

## Future Enhancements

### QIR Domain
- Additional optimization passes
- Better framework support
- QIR validation tools

### QVM Domain
- JIT compilation
- Advanced scheduling
- Distributed execution planning

### QMK Domain
- Multiple QEC code support
- Hardware-specific optimizations
- Advanced error mitigation

---

**Last Updated**: October 2025  
**Version**: 0.2.0  
**Status**: Architecture Defined ✅
