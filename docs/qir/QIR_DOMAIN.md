# QIR Domain

## Overview

The **QIR Domain** is responsible for hardware-agnostic quantum circuit representation and optimization. It operates entirely independently of the QVM and QMK domains, focusing solely on static circuit analysis and transformation.

## Purpose

- Translate quantum circuits from various frameworks (Qiskit, Cirq, PyQuil) to QIR
- Optimize circuits using 14+ optimization passes
- Provide intermediate representation (IR) for circuit manipulation
- Enable framework-agnostic circuit analysis

## Key Principle

**Hardware Independence**: The QIR domain has ZERO knowledge of:
- Physical qubits
- Error correction codes
- Hardware topology
- Execution scheduling
- Virtual qubit handles

## Components

### 1. Front-end Translators

**Location**: `qir/translators/`

Converts quantum circuits from various frameworks to QIR format.

**Supported Frameworks**:
- **Qiskit** (`qiskit_to_qir.py`)
- **Cirq** (`cirq_to_qir.py`)
- **PyQuil** (`pyquil_to_qir.py`)

**Example**:
```python
from qir.translators.qiskit_to_qir import QiskitToQIR
from qiskit import QuantumCircuit

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

translator = QiskitToQIR()
qir_circuit = translator.translate(qc)
```

### 2. QIR Optimizer

**Location**: `qir/optimizer/`

Performs static optimization on QIR circuits using multiple passes.

**Optimization Passes** (14 total):

1. **Constant Propagation** - Propagates known qubit states
2. **Dead Code Elimination** - Removes unused operations
3. **Gate Fusion** - Combines adjacent gates
4. **Gate Cancellation** - Removes inverse gate pairs
5. **Commutation Analysis** - Reorders commuting gates
6. **Measurement Deferral** - Moves measurements to end
7. **Measurement Canonicalization** - Simplifies measurement patterns
8. **Rotation Merging** - Combines rotation gates
9. **Single Qubit Optimization** - Optimizes single-qubit sequences
10. **Two Qubit Reduction** - Reduces two-qubit gate count
11. **Peephole Optimization** - Pattern-based local optimization
12. **Redundancy Elimination** - Removes redundant operations
13. **Template Matching** - Replaces patterns with efficient equivalents
14. **Circuit Simplification** - Overall circuit simplification

**Example**:
```python
from qir.optimizer.pass_manager import PassManager
from qir.optimizer.ir import QIRCircuit

circuit = QIRCircuit()
# ... build circuit

manager = PassManager()
manager.add_pass('constant_propagation')
manager.add_pass('dead_code_elimination')
manager.add_pass('gate_fusion')

optimized = manager.run(circuit)
print(f"Gates reduced: {circuit.gate_count()} → {optimized.gate_count()}")
```

### 3. Intermediate Representation (IR)

**Location**: `qir/optimizer/ir.py`

Provides mutable representation for circuit manipulation.

**Key Classes**:
- `QIRCircuit` - Circuit representation
- `QIRInstruction` - Individual instruction
- `QIRQubit` - Qubit reference
- `InstructionType` - Instruction types enum

**Example**:
```python
from qir.optimizer.ir import QIRCircuit, QIRInstruction, InstructionType, QIRQubit

circuit = QIRCircuit()
q0 = QIRQubit("q0", 0)
q1 = QIRQubit("q1", 1)

circuit.add_qubit(q0)
circuit.add_qubit(q1)

circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
```

### 4. QIR Parser

**Location**: `qir/parser/`

Parses QIR LLVM format into IR.

**Example**:
```python
from qir.parser.qir_parser import QIRParser

parser = QIRParser()
circuit = parser.parse_file("circuit.ll")
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Front-end Frameworks            │
│    (Qiskit, Cirq, PyQuil, etc.)         │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│          QIR Translators                │
│  • Framework-specific conversion        │
│  • Gate mapping                         │
│  • Measurement handling                 │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│      QIR Intermediate Representation    │
│  • Mutable circuit structure            │
│  • Instruction graph                    │
│  • Qubit tracking                       │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│          QIR Optimizer                  │
│  • 14 optimization passes               │
│  • Static analysis                      │
│  • Pattern matching                     │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│         Optimized QIR Output            │
│  → To QVM Domain for execution          │
└─────────────────────────────────────────┘
```

## Optimization Pipeline

### Default Pipeline

```python
from qir.optimizer.pass_manager import PassManager

manager = PassManager()
manager.add_default_passes()  # Adds recommended pass sequence

# Default sequence:
# 1. Constant Propagation
# 2. Dead Code Elimination
# 3. Gate Cancellation
# 4. Commutation Analysis
# 5. Gate Fusion
# 6. Rotation Merging
# 7. Measurement Canonicalization
# 8. Measurement Deferral
# 9. Peephole Optimization
# 10. Circuit Simplification
```

### Custom Pipeline

```python
manager = PassManager()

# Add specific passes
manager.add_pass('gate_fusion')
manager.add_pass('measurement_canonicalization')
manager.add_pass('dead_code_elimination')

# Run with metrics
result = manager.run(circuit)
print(manager.get_metrics())
```

## Design Principles

### 1. Framework Agnostic

The QIR domain works with any quantum framework that can produce QIR. It doesn't favor any particular framework.

### 2. Static Analysis Only

All optimizations are performed at compile-time. No runtime information is used or required.

### 3. Correctness First

Optimizations must preserve circuit semantics. Aggressive optimization is avoided if correctness cannot be guaranteed.

### 4. Composable Passes

Optimization passes are independent and composable. They can be run in any order (though some orders are more effective).

### 5. Zero Dependencies

The QIR domain has no dependencies on QVM or QMK domains. It can be used standalone.

## Testing

### Test Organization

```
tests/qir/
├── optimizer/
│   ├── test_constant_propagation.py
│   ├── test_dead_code_elimination.py
│   ├── test_gate_fusion.py
│   ├── test_measurement_canonicalization.py
│   └── ... (14 pass tests)
│
├── translators/
│   ├── test_qiskit_to_qir.py
│   ├── test_cirq_to_qir.py
│   └── test_pyquil_to_qir.py
│
└── parser/
    └── test_qir_parser.py
```

### Running Tests

```bash
# All QIR tests
python -m pytest tests/qir/ -v

# Specific domain
python -m pytest tests/qir/optimizer/ -v

# Specific pass
python -m pytest tests/qir/optimizer/test_gate_fusion.py -v
```

### Test Coverage

- **128+ optimizer tests** covering all passes
- **Framework translator tests** for Qiskit, Cirq, PyQuil
- **IR manipulation tests**
- **Parser tests**

## Metrics and Telemetry

Each optimization pass tracks metrics:

```python
pass_obj = ConstantPropagationPass()
result = pass_obj.run(circuit)

metrics = pass_obj.metrics
print(f"Execution time: {metrics.execution_time_ms}ms")
print(f"Gates removed: {metrics.custom['gates_removed']}")
print(f"Qubits propagated: {metrics.custom['qubits_propagated']}")
```

## Best Practices

### 1. Use Pass Manager

Always use `PassManager` rather than running passes manually:

```python
# Good
manager = PassManager()
manager.add_default_passes()
result = manager.run(circuit)

# Avoid
pass1 = ConstantPropagationPass()
circuit = pass1.run(circuit)
pass2 = DeadCodeEliminationPass()
circuit = pass2.run(circuit)
# ... tedious and error-prone
```

### 2. Check Metrics

Always check optimization metrics to verify improvements:

```python
original_gates = circuit.gate_count()
optimized = manager.run(circuit)
optimized_gates = optimized.gate_count()

improvement = (original_gates - optimized_gates) / original_gates * 100
print(f"Gate count reduced by {improvement:.1f}%")
```

### 3. Validate Correctness

Use circuit equivalence checking when available:

```python
from qir.optimizer.validation import circuits_equivalent

assert circuits_equivalent(original, optimized)
```

### 4. Profile Performance

For large circuits, profile optimization time:

```python
import time

start = time.time()
optimized = manager.run(circuit)
duration = time.time() - start

print(f"Optimization took {duration:.2f}s for {circuit.gate_count()} gates")
```

## Common Patterns

### Pattern 1: Framework Translation + Optimization

```python
from qir.translators.qiskit_to_qir import QiskitToQIR
from qir.optimizer.pass_manager import PassManager

# Translate
translator = QiskitToQIR()
qir_circuit = translator.translate(qiskit_circuit)

# Optimize
manager = PassManager()
manager.add_default_passes()
optimized = manager.run(qir_circuit)
```

### Pattern 2: Custom Optimization Pipeline

```python
manager = PassManager()

# Aggressive optimization
manager.add_pass('constant_propagation')
manager.add_pass('dead_code_elimination')
manager.add_pass('gate_fusion')
manager.add_pass('rotation_merging')
manager.add_pass('gate_cancellation')
manager.add_pass('peephole_optimization')
manager.add_pass('circuit_simplification')

# Run multiple times for fixed-point
for i in range(3):
    circuit = manager.run(circuit)
    if manager.get_metrics()['total_changes'] == 0:
        break
```

### Pattern 3: Measurement-Focused Optimization

```python
manager = PassManager()

# Focus on measurement optimization
manager.add_pass('measurement_canonicalization')
manager.add_pass('measurement_deferral')
manager.add_pass('dead_code_elimination')

optimized = manager.run(circuit)
```

## Limitations

### What QIR Domain Cannot Do

1. **No Runtime Optimization**: Cannot optimize based on runtime information
2. **No Hardware Awareness**: Cannot optimize for specific hardware topology
3. **No Error Correction**: Cannot insert error correction codes
4. **No Resource Allocation**: Cannot allocate physical qubits
5. **No Execution**: Cannot execute circuits

These are responsibilities of the QVM and QMK domains.

## Future Enhancements

### Planned Features

1. **More Optimization Passes**
   - Loop optimization
   - Quantum-classical optimization
   - Advanced template matching

2. **Better Analysis**
   - Circuit depth analysis
   - Critical path identification
   - Resource estimation

3. **Verification Tools**
   - Formal verification
   - Equivalence checking
   - Property testing

4. **Performance**
   - Parallel optimization
   - Incremental optimization
   - Caching

## Integration with Other Domains

### QIR → QVM

The QIR domain outputs optimized circuits that are converted to QVM format:

```python
from qir.optimizer.pass_manager import PassManager
from qvm.generator.qvm_generator import QVMGenerator

# Optimize in QIR domain
manager = PassManager()
optimized_qir = manager.run(qir_circuit)

# Convert to QVM domain
generator = QVMGenerator()
qvm_graph = generator.generate(optimized_qir)
```

**Important**: QIR domain never imports from QVM domain. The conversion is one-way.

## Resources

- **QIR Specification**: https://github.com/qir-alliance/qir-spec
- **Optimizer Documentation**: See `docs/OPTIMIZER_GUIDE.md`
- **Pass Development**: See `qir/optimizer/pass_base.py`

---

**Domain**: QIR (Hardware-agnostic)  
**Dependencies**: None (fully independent)  
**Output**: Optimized QIR circuits  
**Status**: Production Ready ✅
