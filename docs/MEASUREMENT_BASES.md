# Measurement Bases in QMK

Complete documentation for measurement support across the QMK stack.

## Supported Measurement Bases

### Single-Qubit Measurements

**Z-Basis (Computational)**
- Eigenstates: |0⟩, |1⟩
- QVM operation: `MEASURE_Z`
- QIR: `__quantum__qis__mz__body`
- Use case: Standard computational basis measurement

**X-Basis (Hadamard)**
- Eigenstates: |+⟩ = (|0⟩+|1⟩)/√2, |-⟩ = (|0⟩-|1⟩)/√2
- QVM operation: `MEASURE_X`
- QIR: `__quantum__qis__mx__body`
- Use case: Hadamard basis measurement, X-error detection

**Y-Basis**
- Eigenstates: |+i⟩ = (|0⟩+i|1⟩)/√2, |-i⟩ = (|0⟩-i|1⟩)/√2
- QVM operation: `MEASURE_Y`
- QIR: `__quantum__qis__my__body`
- Use case: Y-error detection, state tomography

**Arbitrary Angle**
- Measurement at angle θ from Z-axis
- QVM operation: `MEASURE_ANGLE` with `angle` parameter
- QIR: `__quantum__qis__measure__body` with angle parameter
- Use case: Generalized measurements, tomography

### Two-Qubit Measurements

**Bell Basis**
- Measures joint state of two qubits
- Distinguishes four Bell states:
  - |Φ+⟩ = (|00⟩ + |11⟩)/√2  → 00
  - |Ψ+⟩ = (|01⟩ + |10⟩)/√2  → 01
  - |Φ-⟩ = (|00⟩ - |11⟩)/√2  → 10
  - |Ψ-⟩ = (|01⟩ - |10⟩)/√2  → 11
- QVM operation: `MEASURE_BELL`
- QIR: `__quantum__qis__measure_bell__body`
- Use case: Quantum teleportation, entanglement swapping

## QVM Format

### Single-Qubit Measurement

```json
{
  "id": "measure_z",
  "op": "MEASURE_Z",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

```json
{
  "id": "measure_x",
  "op": "MEASURE_X",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

```json
{
  "id": "measure_y",
  "op": "MEASURE_Y",
  "vqs": ["q0"],
  "produces": ["m0"]
}
```

### Bell Basis Measurement

```json
{
  "id": "bell_measure",
  "op": "MEASURE_BELL",
  "vqs": ["q0", "q1"],
  "produces": ["m0", "m1"]
}
```

Or with combined Bell state index:

```json
{
  "id": "bell_measure",
  "op": "MEASURE_BELL",
  "vqs": ["q0", "q1"],
  "produces": ["bell_index"]
}
```

## QIR Support

### Measurement Operations

**Z-Basis:**
```llvm
%result = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
```

**X-Basis:**
```llvm
%result = call i1 @__quantum__qis__mx__body(%Qubit* %q0)
```

**Y-Basis:**
```llvm
%result = call i1 @__quantum__qis__my__body(%Qubit* %q0)
```

**Bell Basis:**
```llvm
%result = call {i1, i1} @__quantum__qis__measure_bell__body(%Qubit* %q0, %Qubit* %q1)
```

## Optimizer Support

### Measurement Deferral Pass

The measurement deferral optimization pass handles all measurement bases:

- Defers measurements to end of circuit when possible
- Preserves measurement basis
- Handles basis-dependent commutation rules

**Commutation Rules:**
- Z measurements commute with Z, S, T gates
- X measurements commute with X, H gates
- Y measurements have complex commutation rules
- Bell measurements don't commute (joint operation)

### Dead Code Elimination

- Removes unused measurements
- Preserves measurements that affect control flow
- Works with all measurement bases

### Constant Propagation

- Tracks measurement outcomes
- Propagates known values
- Basis-aware optimization

## Python API

### Single-Qubit Measurements

```python
from kernel.simulator.logical_qubit import LogicalQubit

qubit = LogicalQubit("q0", profile)

# Z-basis
outcome = qubit.measure("Z", time_us=0.0)

# X-basis
outcome = qubit.measure("X", time_us=0.0)

# Y-basis
outcome = qubit.measure("Y", time_us=0.0)

# Arbitrary angle
import math
outcome = qubit.measure("ANGLE", time_us=0.0, angle=math.pi/4)
```

### Bell Basis Measurement

```python
from kernel.simulator.logical_qubit import LogicalQubit

qubit1 = LogicalQubit("q0", profile)
qubit2 = LogicalQubit("q1", profile)

# Perform Bell measurement
outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
    qubit1, qubit2, time_us=0.0
)

# bell_index identifies which Bell state:
# 0: |Φ+⟩, 1: |Ψ+⟩, 2: |Φ-⟩, 3: |Ψ-⟩
```

## Framework Support

### Qiskit

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)

# Z-basis (default)
qc.measure(0, 0)

# X-basis (via H gate)
qc.h(0)
qc.measure(0, 0)

# Y-basis (via S†·H gates)
qc.sdg(0)
qc.h(0)
qc.measure(0, 0)

# Bell measurement (via CNOT·H)
qc.cx(0, 1)
qc.h(0)
qc.measure([0, 1], [0, 1])
```

### Cirq

```python
import cirq

q0, q1 = cirq.LineQubit.range(2)

# Z-basis
cirq.measure(q0, key='m0')

# X-basis
cirq.H(q0)
cirq.measure(q0, key='m0')

# Y-basis
cirq.S(q0)**-1
cirq.H(q0)
cirq.measure(q0, key='m0')

# Bell measurement
cirq.CNOT(q0, q1)
cirq.H(q0)
cirq.measure(q0, q1, key='result')
```

## Implementation Notes

### Measurement Protocol

**Z-Basis:**
- Direct measurement in computational basis
- No basis change needed

**X-Basis:**
- Apply H gate before Z measurement
- Equivalent to measuring in Hadamard basis

**Y-Basis:**
- Apply S†·H gates before Z measurement
- Rotates Y eigenstates to Z eigenstates

**Bell Basis:**
- Apply CNOT(q0, q1)
- Apply H(q0)
- Measure both in Z-basis
- Outcomes identify Bell state

### State Collapse

All measurements are **destructive** and collapse the quantum state:
- Single-qubit measurements collapse to computational basis
- Bell measurements collapse both qubits to computational basis
- Measurement outcomes are probabilistic for superposition states

### Error Modeling

Measurement errors are applied according to QEC profile:
- Physical measurement errors
- Readout errors
- Syndrome extraction errors (for error correction)

## Use Cases

### Quantum Algorithms

- **Deutsch-Jozsa**: Z-basis measurements
- **Grover's Algorithm**: Z-basis measurements
- **Quantum Teleportation**: Bell basis measurements
- **Superdense Coding**: Bell basis measurements

### Quantum Error Correction

- **Syndrome Extraction**: X and Z basis measurements
- **State Tomography**: X, Y, Z basis measurements
- **Process Tomography**: All measurement bases

### Quantum Communication

- **Quantum Key Distribution**: X and Z basis measurements
- **Entanglement Verification**: Bell basis measurements
- **Quantum Repeaters**: Bell basis measurements

## Testing

Comprehensive test coverage:
- 8 single-qubit measurement tests
- 7 Bell basis measurement tests
- Integration with optimizer
- End-to-end validation

## Future Extensions

### Planned Features

- **Generalized measurements**: POVM support
- **Weak measurements**: Non-destructive measurements
- **Adaptive measurements**: Measurement-based quantum computing
- **Multi-qubit measurements**: GHZ basis, W basis

### Research Directions

- **Measurement-based QC**: One-way quantum computing
- **Quantum steering**: Non-local measurements
- **Contextuality**: Measurement context dependence

---

**Last Updated:** October 2025  
**Version:** 0.1.0  
**Status:** Production Ready ✅
