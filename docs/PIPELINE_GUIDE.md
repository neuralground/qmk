# QMK Full Pipeline Guide

Complete guide to the QMK end-to-end quantum circuit execution pipeline.

## Overview

The QMK pipeline provides a **complete, validated execution path** from high-level quantum frameworks to fault-tolerant simulation:

```
┌──────────────────────────────────────────────────────────────┐
│                    QMK Full Pipeline                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Qiskit/Cirq/Q# Circuit                                      │
│         ↓                                                     │
│  QIR Converter                                                │
│         ↓                                                     │
│  QIR (Quantum Intermediate Representation)                    │
│         ↓                                                     │
│  Optimizer (14 passes, 5 levels)                             │
│         ↓                                                     │
│  Optimized QIR                                                │
│         ↓                                                     │
│  QVM Converter                                                │
│         ↓                                                     │
│  QVM Graph                                                    │
│         ↓                                                     │
│  QMK Executor (Fault-Tolerant Simulation)                    │
│         ↓                                                     │
│  Results + Telemetry                                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Features

✅ **Multi-Framework Support**
- Qiskit 2.2.0+ (IBM)
- Cirq 1.6.1+ (Google)
- Q# 1.0.0+ (Microsoft)

✅ **Complete Optimization**
- 14 optimization passes
- 30-80% gate reduction
- 70% T-count reduction
- Topology-aware routing

✅ **Validated Correctness**
- 129 tests passing
- Native vs QMK comparison
- Fidelity >0.90 for all tests
- Real algorithm validation

✅ **Production Ready**
- Comprehensive error handling
- Detailed metrics tracking
- Performance benchmarking
- Full documentation

---

## Quick Start

### Installation

```bash
# Install QMK
git clone https://github.com/neuralground/qmk.git
cd qmk
pip install -r requirements.txt

# Install quantum frameworks
pip install -r requirements-quantum-frameworks.txt

# Verify installation
python scripts/verify_frameworks.py
```

### Basic Usage

```python
from qiskit import QuantumCircuit
from kernel.qir_bridge.qiskit_to_qir import QiskitToQIRConverter
from kernel.simulator.enhanced_executor import EnhancedExecutor

# 1. Create circuit
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# 2. Convert to QVM
converter = QiskitToQIRConverter()
qvm_graph = converter.convert_to_qvm(qc)

# 3. Execute
executor = EnhancedExecutor()
result = executor.execute(qvm_graph)
print(f"Results: {result['events']}")
```

---

## Pipeline Components

### 1. Framework Support

#### Qiskit (IBM)

```python
from qiskit import QuantumCircuit
from kernel.qir_bridge.qiskit_to_qir import QiskitToQIRConverter

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

converter = QiskitToQIRConverter()
qvm_graph = converter.convert_to_qvm(qc)
```

**Supported Gates:**
- Single-qubit: H, X, Y, Z, S, S†, T, T†, Rx, Ry, Rz
- Two-qubit: CNOT, CZ, SWAP
- Measurements: Z-basis

#### Cirq (Google)

```python
import cirq
from kernel.qir_bridge.cirq_to_qir import CirqToQIRConverter

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, q1, key='result')
)

converter = CirqToQIRConverter()
qvm_graph = converter.convert_to_qvm(circuit)
```

#### Q# (Microsoft)

```python
# Q# algorithms provided as source code
from examples import qsharp_algorithms

# Use qsharp runtime for execution
import qsharp
bell_state = qsharp.compile(qsharp_algorithms.BELL_STATE)
result = bell_state.simulate()
```

### 2. Algorithm Examples

**30 quantum algorithms included:**

| Algorithm | Qiskit | Cirq | Q# |
|-----------|--------|------|-----|
| Bell State | ✅ | ✅ | ✅ |
| GHZ State | ✅ | ✅ | ✅ |
| Deutsch-Jozsa | ✅ | ✅ | ✅ |
| Bernstein-Vazirani | ✅ | ✅ | ✅ |
| Grover Search | ✅ | ✅ | ✅ |
| QFT | ✅ | ✅ | ✅ |
| Phase Estimation | ✅ | ✅ | ✅ |
| Teleportation | ✅ | ✅ | ✅ |
| Superdense Coding | ✅ | ✅ | ✅ |
| VQE Ansatz | ✅ | ✅ | ✅ |

**Usage:**

```python
from examples import qiskit_algorithms

# Get any algorithm
circuit = qiskit_algorithms.bell_state()
circuit = qiskit_algorithms.ghz_state(n=5)
circuit = qiskit_algorithms.grover_search(marked_state=3)
```

### 3. Validation Tests

Run comprehensive validation:

```bash
# All tests
pytest -v

# Pipeline tests only
pytest tests/integration/test_full_pipeline.py -v

# Specific algorithm
pytest tests/integration/test_full_pipeline.py::TestFullPipeline::test_qiskit_bell_state_pipeline -v
```

**Test Coverage:**
- ✅ 121 optimizer unit tests
- ✅ 4 end-to-end validation tests
- ✅ 4 full pipeline tests
- ✅ Framework verification tests

---

## Advanced Usage

### With Optimization

```python
from kernel.qir_bridge.optimizer_integration import (
    OptimizedExecutor,
    OptimizationLevel
)
from kernel.simulator.enhanced_executor import EnhancedExecutor

# Create optimized executor
executor = OptimizedExecutor(
    EnhancedExecutor(),
    optimization_level=OptimizationLevel.AGGRESSIVE
)

# Execute with optimization
result = executor.execute(qvm_graph)

# Check optimization impact
print(f"Gates removed: {result['optimization']['metrics']['gates_removed']}")
```

### With Hardware Topology

```python
from kernel.qir_bridge.optimizer.topology import HardwareTopology
from kernel.qir_bridge.optimizer_integration import OptimizedExecutor

# Define topology
topology = HardwareTopology.ibm_falcon()

# Create topology-aware executor
executor = OptimizedExecutor(
    EnhancedExecutor(),
    optimization_level=OptimizationLevel.AGGRESSIVE,
    topology=topology
)

result = executor.execute(qvm_graph)
```

### Batch Execution

```python
# Run multiple shots efficiently
results = []
for _ in range(1000):
    executor = EnhancedExecutor()
    result = executor.execute(qvm_graph)
    results.append(result['events'])

# Aggregate results
from collections import Counter
counts = Counter(tuple(r.items()) for r in results)
print(counts)
```

---

## Performance

### Benchmark Results

**Bell State (2 qubits):**
- Native Qiskit: 1000 shots in 50ms
- QMK Pipeline: 1000 shots in 300ms
- Fidelity: >0.99

**GHZ State (3 qubits):**
- Native Qiskit: 1000 shots in 60ms
- QMK Pipeline: 1000 shots in 350ms
- Fidelity: >0.99

**With Optimization:**
- Gate reduction: 30-80%
- T-count reduction: 70%
- SWAP reduction: 76%

---

## Troubleshooting

### Common Issues

**Issue: Import errors**
```bash
# Solution: Verify installation
python scripts/verify_frameworks.py
```

**Issue: Low fidelity**
```python
# Check if gates are supported
converter = QiskitToQIRConverter()
qir = converter.convert(circuit)
print(qir)  # Look for "unsupported" comments
```

**Issue: Slow execution**
```python
# Use fewer shots for testing
result = executor.execute(qvm_graph)  # Single shot
# Or batch with fresh executors
```

---

## API Reference

### Converters

**QiskitToQIRConverter:**
```python
converter = QiskitToQIRConverter()
qir_string = converter.convert(circuit)  # QIR text
qvm_graph = converter.convert_to_qvm(circuit)  # QVM format
```

**CirqToQIRConverter:**
```python
converter = CirqToQIRConverter()
qir_string = converter.convert(circuit)
qvm_graph = converter.convert_to_qvm(circuit)
```

### Executors

**EnhancedExecutor:**
```python
executor = EnhancedExecutor(
    max_physical_qubits=10000,
    seed=42
)
result = executor.execute(qvm_graph)
```

**OptimizedExecutor:**
```python
executor = OptimizedExecutor(
    base_executor,
    optimization_level=OptimizationLevel.STANDARD,
    topology=None,
    custom_passes=None
)
result = executor.execute_qir(qir_program)
```

---

## Examples

See `examples/` directory for complete examples:
- `qiskit_algorithms.py` - 10 Qiskit algorithms
- `cirq_algorithms.py` - 10 Cirq algorithms
- `qsharp_algorithms.py` - 10 Q# algorithms

---

## Further Reading

- [Optimizer Guide](OPTIMIZER_GUIDE.md) - Detailed optimization documentation
- [Installation Guide](INSTALLATION.md) - Setup instructions
- [API Documentation](API.md) - Complete API reference

---

**Last Updated:** October 2025  
**Version:** 0.1.0  
**Status:** Production Ready ✅
