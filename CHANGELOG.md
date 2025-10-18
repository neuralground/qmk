# QMK Changelog

All notable changes to the Quantum Microkernel project.

## [Unreleased]

### Phase 2.3 - qSyscall ABI Implementation (Next)
- Session management
- Job submission and tracking
- RPC server
- Client library

---

## [0.2.0] - 2025-10-18

### Phase 2.2 - Enhanced Kernel with Logical Qubit Simulator ✅

#### Added
- **Enhanced Resource Manager** (`kernel/simulator/enhanced_resource_manager.py`)
  - Logical qubit allocation with QEC profiles
  - Virtual→logical qubit mapping
  - Physical qubit usage accounting
  - Channel management
  - Comprehensive telemetry
  - Deterministic execution with seeds

- **Enhanced Executor** (`kernel/simulator/enhanced_executor.py`)
  - Full QVM graph execution with logical qubits
  - All QVM operations: ALLOC_LQ, FREE_LQ, gates, measurements, channels
  - Capability checking (CAP_ALLOC, CAP_LINK, CAP_TELEPORT, CAP_MAGIC)
  - Guard-based conditional execution
  - Topological scheduling
  - Execution logging and telemetry

- **Test Suite Expansion**
  - 20 unit tests for enhanced resource manager
  - 10 integration tests for enhanced executor
  - **Total: 97 tests (100% passing)**

#### Changed
- Integrated logical qubit simulator with kernel executor
- Enhanced telemetry with error tracking
- Improved resource management

---

## [0.1.0] - 2025-10-17

### Phase 2.1 - Logical Qubit Simulator Core ✅

#### Added
- **QEC Profiles** (`kernel/simulator/qec_profiles.py`)
  - Surface Code, SHYPS, Bacon-Shor implementations
  - Parameterizable code distance and error rates
  - Profile parsing from QVM strings
  - Standard profile library

- **Azure QRE Compatibility** (`kernel/simulator/azure_qre_compat.py`)
  - Full Azure QRE configuration format support
  - All 6 predefined qubit parameters
  - All 3 QEC schemes (surface_code, floquet_code)
  - Formula evaluation engine
  - Time string parsing

- **Error Models** (`kernel/simulator/error_models.py`)
  - Depolarizing noise (X, Y, Z errors)
  - Coherence noise (T1, T2)
  - Measurement readout errors
  - Composite error model
  - Error tracking and telemetry

- **Logical Qubit Simulation** (`kernel/simulator/logical_qubit.py`)
  - Logical qubit with QEC protection
  - Single-qubit gates (H, S, X, Y, Z)
  - Two-qubit gates (CNOT)
  - Z-basis and X-basis measurements
  - Decoder cycle simulation
  - Comprehensive telemetry

- **Test Infrastructure**
  - Automated test runner (`run_tests.py`)
  - GitHub Actions CI/CD workflow
  - 67 unit tests (100% passing)
  - Test documentation

#### Documentation
- Azure QRE compatibility guide
- Implementation plan with 7 phases
- Test suite README

---

## [0.0.1] - 2025-10-17

### Phase 1 - Specifications & Validation ✅

#### Added
- **QVM Specification** (`docs/QVM-spec.md`)
  - 690+ lines, JVM-style structure
  - Complete resource handle semantics
  - Verification and execution semantics
  - Security model

- **QVM Instruction Reference** (`docs/QVM-instruction-reference.md`)
  - 20 operations fully documented
  - Capability requirements
  - Reversibility classification

- **qSyscall ABI Specification** (`docs/qsyscall-abi.md`)
  - 600+ lines
  - 8 core syscalls
  - Error handling
  - Usage patterns

- **JSON Schema** (`qvm/qvm_schema.json`)
  - Complete QVM format validation
  - Enum constraints for opcodes
  - Pattern validation

- **Enhanced Validator** (`qvm/tools/qvm_validate.py`)
  - JSON schema validation
  - Linearity checking
  - Capability verification
  - REV segment identification

- **Example Programs** (`qvm/examples/`)
  - bell_teleport_cnot.qvm.json
  - teleportation_demo.qvm.json
  - ghz_state.qvm.json
  - conditional_correction.qvm.json
  - reversible_segment.qvm.json

#### Documentation
- Design & architecture specification
- Documentation index with logical navigation
- Example program guide

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Categories
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
