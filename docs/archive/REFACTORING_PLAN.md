# QMK Refactoring Plan

## Objective

Reorganize the codebase to clearly separate three architectural domains:
1. **QIR Domain** - Hardware-agnostic circuit representation and optimization
2. **QVM Domain** - User-mode virtual machine with capability-based execution
3. **QMK Domain** - Supervisor-mode microkernel managing physical resources

---

## Current State Analysis

### Current Directory Structure

```
qmk/
├── kernel/
│   ├── qir_bridge/          # ❌ MIXED: QIR + QVM components
│   │   ├── optimizer/       # ✅ QIR Domain
│   │   ├── qiskit_to_qir.py # ✅ QIR Domain
│   │   ├── cirq_to_qir.py   # ✅ QIR Domain
│   │   ├── qvm_generator.py # ⚠️ QVM Domain (misplaced)
│   │   └── converters.py    # ⚠️ QVM Domain (misplaced)
│   │
│   ├── simulator/           # ✅ QMK Domain
│   ├── qec/                 # ✅ QMK Domain
│   ├── hardware/            # ✅ QMK Domain
│   ├── syscalls/            # ✅ QMK Domain
│   ├── security/            # ✅ QMK Domain
│   ├── distributed/         # ✅ QMK Domain
│   ├── qmk_server.py        # ✅ QMK Domain
│   └── ...
│
├── qvm/                     # ⚠️ Only examples, missing runtime
│   └── examples/
│
├── tests/
│   ├── optimizer/           # ✅ QIR Domain tests
│   ├── integration/         # ❌ MIXED
│   └── unit/                # ❌ MIXED
│
└── examples/
```

### Problems Identified

1. **QIR components mixed with kernel**: `kernel/qir_bridge/` should be independent
2. **QVM generator in wrong place**: Should be in QVM domain, not kernel
3. **No clear QVM runtime**: User-mode components scattered
4. **Mixed test organization**: Tests don't reflect domain separation
5. **Import dependencies**: QIR code may import from kernel

---

## Target Structure

### Proposed Directory Organization

```
qmk/
├── qir/                           # QIR DOMAIN (fully independent)
│   ├── __init__.py
│   ├── optimizer/                 # Optimization passes
│   │   ├── __init__.py
│   │   ├── ir.py
│   │   ├── pass_base.py
│   │   ├── pass_manager.py
│   │   └── passes/
│   │       ├── constant_propagation.py
│   │       ├── dead_code_elimination.py
│   │       ├── gate_fusion.py
│   │       ├── measurement_canonicalization.py
│   │       ├── measurement_deferral.py
│   │       └── ... (11 more passes)
│   │
│   ├── translators/               # Front-end translators
│   │   ├── __init__.py
│   │   ├── qiskit_to_qir.py
│   │   ├── cirq_to_qir.py
│   │   └── pyquil_to_qir.py
│   │
│   ├── parser/                    # QIR parsing
│   │   ├── __init__.py
│   │   └── qir_parser.py
│   │
│   └── README.md                  # QIR domain documentation
│
├── qvm/                           # QVM DOMAIN (user-mode)
│   ├── __init__.py
│   ├── graph/                     # QVM graph representation
│   │   ├── __init__.py
│   │   ├── qvm_graph.py
│   │   └── validator.py
│   │
│   ├── generator/                 # QIR → QVM conversion
│   │   ├── __init__.py
│   │   ├── qvm_generator.py      # Moved from kernel/qir_bridge/
│   │   └── converters.py          # Moved from kernel/qir_bridge/
│   │
│   ├── runtime/                   # User-mode runtime (future)
│   │   ├── __init__.py
│   │   ├── jit.py
│   │   ├── planner.py
│   │   └── capabilities.py
│   │
│   ├── examples/                  # QVM example programs
│   │   ├── bell_measurement.qvm.json
│   │   ├── measurement_bases.qvm.json
│   │   └── ...
│   │
│   └── README.md                  # QVM domain documentation
│
├── kernel/                        # QMK DOMAIN (supervisor-mode)
│   ├── __init__.py
│   ├── core/                      # Microkernel core
│   │   ├── __init__.py
│   │   ├── qmk_server.py         # Moved from kernel/
│   │   ├── session_manager.py    # Moved from kernel/
│   │   ├── job_manager.py        # Moved from kernel/
│   │   └── rpc_server.py         # Moved from kernel/
│   │
│   ├── executor/                  # Circuit execution
│   │   ├── __init__.py
│   │   ├── enhanced_executor.py  # Moved from simulator/
│   │   └── resource_manager.py   # Moved from simulator/
│   │
│   ├── qec/                       # Error correction
│   │   ├── __init__.py
│   │   ├── surface_code.py
│   │   ├── profiles.py           # Moved from simulator/qec_profiles.py
│   │   └── ...
│   │
│   ├── simulator/                 # Logical qubit simulation
│   │   ├── __init__.py
│   │   ├── logical_qubit.py
│   │   ├── error_model.py
│   │   └── ...
│   │
│   ├── hardware/                  # Hardware abstraction layer
│   │   ├── __init__.py
│   │   ├── hal.py
│   │   └── ...
│   │
│   ├── syscalls/                  # System call implementations
│   │   ├── __init__.py
│   │   └── ...
│   │
│   ├── security/                  # Security & isolation
│   │   ├── __init__.py
│   │   └── ...
│   │
│   ├── distributed/               # Distributed execution
│   │   ├── __init__.py
│   │   └── ...
│   │
│   ├── reversibility/             # Reversibility tracking
│   │   ├── __init__.py
│   │   └── ...
│   │
│   └── README.md                  # QMK domain documentation
│
├── tests/
│   ├── qir/                       # QIR domain tests
│   │   ├── optimizer/
│   │   ├── translators/
│   │   └── parser/
│   │
│   ├── qvm/                       # QVM domain tests
│   │   ├── graph/
│   │   ├── generator/
│   │   └── runtime/
│   │
│   ├── kernel/                    # QMK domain tests
│   │   ├── executor/
│   │   ├── qec/
│   │   ├── simulator/
│   │   └── syscalls/
│   │
│   └── integration/               # Cross-domain integration tests
│       ├── end_to_end/
│       ├── qir_to_qvm/
│       └── qvm_to_kernel/
│
├── examples/
│   ├── qir/                       # QIR examples
│   ├── qvm/                       # QVM examples
│   └── algorithms/                # Complete algorithm examples
│
├── docs/
│   ├── ARCHITECTURE.md            # ✅ Updated
│   ├── REFACTORING_PLAN.md        # ✅ This document
│   ├── qir/                       # QIR domain docs
│   ├── qvm/                       # QVM domain docs
│   └── kernel/                    # QMK domain docs
│
└── README.md
```

---

## Migration Steps

### Phase 1: Create New Directory Structure ✅

```bash
# Create QIR domain directories
mkdir -p qir/optimizer/passes
mkdir -p qir/translators
mkdir -p qir/parser

# Create QVM domain directories
mkdir -p qvm/graph
mkdir -p qvm/generator
mkdir -p qvm/runtime

# Create reorganized kernel directories
mkdir -p kernel/core
mkdir -p kernel/executor

# Create test directories
mkdir -p tests/qir/optimizer
mkdir -p tests/qvm/generator
mkdir -p tests/kernel/executor
```

### Phase 2: Move QIR Domain Components

**Move optimizer:**
```bash
mv kernel/qir_bridge/optimizer/* qir/optimizer/
```

**Move translators:**
```bash
mv kernel/qir_bridge/qiskit_to_qir.py qir/translators/
mv kernel/qir_bridge/cirq_to_qir.py qir/translators/
mv kernel/qir_bridge/pyquil_to_qir.py qir/translators/
```

**Move parser:**
```bash
mv kernel/qir_bridge/qir_parser.py qir/parser/
```

**Move tests:**
```bash
mv tests/optimizer/* tests/qir/optimizer/
```

### Phase 3: Move QVM Domain Components

**Move QVM generator:**
```bash
mv kernel/qir_bridge/qvm_generator.py qvm/generator/
mv kernel/qir_bridge/converters.py qvm/generator/
```

**Move QVM examples:**
```bash
# Already in correct location: qvm/examples/
```

### Phase 4: Reorganize QMK Domain

**Move core components:**
```bash
mv kernel/qmk_server.py kernel/core/
mv kernel/session_manager.py kernel/core/
mv kernel/job_manager.py kernel/core/
mv kernel/rpc_server.py kernel/core/
```

**Move executor components:**
```bash
mv kernel/simulator/enhanced_executor.py kernel/executor/
mv kernel/simulator/resource_manager.py kernel/executor/
```

**Move QEC profiles:**
```bash
mv kernel/simulator/qec_profiles.py kernel/qec/profiles.py
```

### Phase 5: Update Imports

**QIR domain imports:**
```python
# Old:
from kernel.qir_bridge.optimizer.ir import QIRCircuit

# New:
from qir.optimizer.ir import QIRCircuit
```

**QVM domain imports:**
```python
# Old:
from kernel.qir_bridge.qvm_generator import QVMGenerator

# New:
from qvm.generator.qvm_generator import QVMGenerator
```

**QMK domain imports:**
```python
# Old:
from kernel.simulator.enhanced_executor import EnhancedExecutor

# New:
from kernel.executor.enhanced_executor import EnhancedExecutor
```

### Phase 6: Update Test Imports

**Update all test files to use new import paths**

### Phase 7: Verify Dependencies

**Check QIR domain has no QVM/QMK imports:**
```bash
# Should return nothing:
grep -r "from qvm" qir/
grep -r "from kernel" qir/
grep -r "import qvm" qir/
grep -r "import kernel" qir/
```

**Check QVM domain only imports QIR (not kernel):**
```bash
# Should return nothing:
grep -r "from kernel" qvm/
grep -r "import kernel" qvm/
```

### Phase 8: Update Documentation

- Add README.md to each domain directory
- Update all documentation references
- Update ARCHITECTURE.md with actual file locations
- Create domain-specific documentation

### Phase 9: Clean Up

```bash
# Remove old qir_bridge directory
rm -rf kernel/qir_bridge/

# Verify all tests still pass
python -m pytest tests/ -v
```

---

## Detailed File Moves

### QIR Domain Files

| Current Location | New Location |
|-----------------|--------------|
| `kernel/qir_bridge/optimizer/ir.py` | `qir/optimizer/ir.py` |
| `kernel/qir_bridge/optimizer/pass_base.py` | `qir/optimizer/pass_base.py` |
| `kernel/qir_bridge/optimizer/pass_manager.py` | `qir/optimizer/pass_manager.py` |
| `kernel/qir_bridge/optimizer/passes/*.py` | `qir/optimizer/passes/*.py` |
| `kernel/qir_bridge/qiskit_to_qir.py` | `qir/translators/qiskit_to_qir.py` |
| `kernel/qir_bridge/cirq_to_qir.py` | `qir/translators/cirq_to_qir.py` |
| `kernel/qir_bridge/pyquil_to_qir.py` | `qir/translators/pyquil_to_qir.py` |
| `kernel/qir_bridge/qir_parser.py` | `qir/parser/qir_parser.py` |

### QVM Domain Files

| Current Location | New Location |
|-----------------|--------------|
| `kernel/qir_bridge/qvm_generator.py` | `qvm/generator/qvm_generator.py` |
| `kernel/qir_bridge/converters.py` | `qvm/generator/converters.py` |
| `qvm/examples/*.json` | `qvm/examples/*.json` (no change) |

### QMK Domain Files

| Current Location | New Location |
|-----------------|--------------|
| `kernel/qmk_server.py` | `kernel/core/qmk_server.py` |
| `kernel/session_manager.py` | `kernel/core/session_manager.py` |
| `kernel/job_manager.py` | `kernel/core/job_manager.py` |
| `kernel/rpc_server.py` | `kernel/core/rpc_server.py` |
| `kernel/simulator/enhanced_executor.py` | `kernel/executor/enhanced_executor.py` |
| `kernel/simulator/resource_manager.py` | `kernel/executor/resource_manager.py` |
| `kernel/simulator/qec_profiles.py` | `kernel/qec/profiles.py` |

---

## Import Update Strategy

### 1. Create Import Compatibility Layer (Temporary)

Create `kernel/qir_bridge/__init__.py` with deprecation warnings:

```python
"""
Deprecated: This module has been moved.

QIR components are now in the 'qir' package.
QVM components are now in the 'qvm' package.
"""

import warnings

def _deprecated_import(old_path, new_path):
    warnings.warn(
        f"{old_path} is deprecated. Use {new_path} instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Provide backward compatibility
from qir.optimizer.ir import QIRCircuit as _QIRCircuit
from qir.optimizer.pass_manager import PassManager as _PassManager

class QIRCircuit(_QIRCircuit):
    def __init__(self, *args, **kwargs):
        _deprecated_import(
            "kernel.qir_bridge.optimizer.ir.QIRCircuit",
            "qir.optimizer.ir.QIRCircuit"
        )
        super().__init__(*args, **kwargs)

# ... similar for other classes
```

### 2. Update All Direct Imports

Use automated script to update imports:

```python
# update_imports.py
import os
import re

REPLACEMENTS = {
    'from kernel.qir_bridge.optimizer': 'from qir.optimizer',
    'from kernel.qir_bridge.qiskit_to_qir': 'from qir.translators.qiskit_to_qir',
    'from kernel.qir_bridge.qvm_generator': 'from qvm.generator.qvm_generator',
    'from kernel.simulator.enhanced_executor': 'from kernel.executor.enhanced_executor',
    # ... add all replacements
}

def update_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
    
    with open(filepath, 'w') as f:
        f.write(content)

# Run on all Python files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            update_file(os.path.join(root, file))
```

### 3. Remove Compatibility Layer

After all imports are updated and tests pass, remove the compatibility layer.

---

## Testing Strategy

### 1. Test Each Phase

After each move:
```bash
python -m pytest tests/ -v
```

### 2. Domain Isolation Tests

Create tests to verify domain boundaries:

```python
# tests/test_domain_isolation.py

def test_qir_domain_independence():
    """Verify QIR domain has no QVM/kernel imports."""
    import ast
    import os
    
    for root, dirs, files in os.walk('qir'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath) as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert not alias.name.startswith('qvm')
                            assert not alias.name.startswith('kernel')
                    elif isinstance(node, ast.ImportFrom):
                        assert not node.module.startswith('qvm')
                        assert not node.module.startswith('kernel')

def test_qvm_domain_no_kernel_imports():
    """Verify QVM domain doesn't import from kernel."""
    # Similar to above
```

### 3. Integration Tests

Verify cross-domain interfaces work:

```python
# tests/integration/test_qir_to_qvm.py

def test_qir_to_qvm_pipeline():
    """Test QIR → QVM conversion."""
    from qir.optimizer.ir import QIRCircuit
    from qvm.generator.qvm_generator import QVMGenerator
    
    circuit = QIRCircuit()
    # ... build circuit
    
    generator = QVMGenerator()
    qvm_graph = generator.generate(circuit)
    
    assert qvm_graph is not None
```

---

## Risk Mitigation

### Risks

1. **Breaking existing code**: Import paths change
2. **Test failures**: Tests may break during migration
3. **Circular dependencies**: May discover hidden dependencies
4. **Performance impact**: Import paths may affect load time

### Mitigation Strategies

1. **Incremental migration**: Move one domain at a time
2. **Compatibility layer**: Provide temporary backward compatibility
3. **Comprehensive testing**: Run full test suite after each phase
4. **Git branches**: Use feature branch for refactoring
5. **Rollback plan**: Can revert if issues arise

---

## Success Criteria

- [ ] All files moved to correct domain directories
- [ ] All imports updated to new paths
- [ ] All tests passing (181+ tests)
- [ ] No circular dependencies
- [ ] QIR domain has zero QVM/kernel imports
- [ ] QVM domain has zero kernel imports
- [ ] Documentation updated
- [ ] Domain README files created
- [ ] Architecture diagram reflects actual structure

---

## Timeline

### Estimated Effort

- **Phase 1** (Directory creation): 30 minutes
- **Phase 2** (Move QIR): 1-2 hours
- **Phase 3** (Move QVM): 1 hour
- **Phase 4** (Reorganize kernel): 1-2 hours
- **Phase 5** (Update imports): 2-3 hours
- **Phase 6** (Update tests): 1-2 hours
- **Phase 7** (Verify dependencies): 1 hour
- **Phase 8** (Documentation): 2-3 hours
- **Phase 9** (Cleanup): 1 hour

**Total**: 10-15 hours

### Recommended Approach

1. Do phases 1-3 in one session (QIR and QVM extraction)
2. Do phases 4-6 in another session (kernel reorganization)
3. Do phases 7-9 in final session (verification and cleanup)

---

## Post-Refactoring Benefits

1. **Clear Architecture**: Three domains clearly separated
2. **Better Testing**: Domain-specific test organization
3. **Easier Development**: Developers know where code belongs
4. **Reduced Coupling**: Enforced dependency boundaries
5. **Better Documentation**: Domain-specific docs
6. **Easier Onboarding**: Clear structure for new developers
7. **Future-Proof**: Ready for independent domain evolution

---

**Status**: Plan Defined ✅  
**Next Step**: Begin Phase 1 (Directory Creation)  
**Last Updated**: October 2025
