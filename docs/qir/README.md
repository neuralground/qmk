# QIR Domain Documentation

Quantum Intermediate Representation (QIR) - Circuit optimization and compilation.

## Overview

The QIR domain handles quantum circuit optimization, compilation, and transformation. It includes a world-class optimizer with 17 optimization passes based on cutting-edge research.

## Key Documents

1. **[QIR Optimization Passes](QIR_OPTIMIZATION_PASSES.md)** ⭐
   - Complete documentation for all 17 passes
   - 18+ research papers cited
   - Performance comparisons
   - Usage recommendations

2. **[Optimizer Guide](OPTIMIZER_GUIDE.md)**
   - How to use the optimizer
   - Configuration options
   - Best practices

3. **[Pipeline Guide](PIPELINE_GUIDE.md)**
   - Full QIR pipeline documentation
   - Multi-framework integration
   - End-to-end workflow

4. **[QIR Domain Overview](QIR_DOMAIN.md)**
   - Architecture and design
   - Component overview

5. **[Optimization Plan](OPTIMIZATION_PLAN.md)**
   - Optimization strategy
   - Future roadmap

## Quick Start

```python
from qir.optimizer import optimize_circuit
from qir.translators import qiskit_to_qir

# Convert Qiskit circuit to QIR
qir_circuit = qiskit_to_qir(qiskit_circuit)

# Optimize
optimized = optimize_circuit(qir_circuit, level=3)

# Results: 30-80% gate reduction typical
```

## Features

### Standard Passes (12)
- Gate Cancellation
- Gate Commutation
- Gate Fusion
- Dead Code Elimination
- Constant Propagation
- Template Matching
- Measurement Deferral
- Clifford+T Optimization
- Magic State Optimization
- Gate Teleportation
- Uncomputation Optimization
- Lattice Surgery Optimization

### Experimental Passes (5)
- ZX-Calculus Optimization
- Phase Polynomial Optimization
- Synthesis-Based Optimization
- Pauli Network Synthesis
- Tensor Network Contraction

## Performance

- **Gate reduction**: 30-80% typical
- **T-count reduction**: 70% typical
- **CNOT reduction**: 10-50% typical
- **Multi-framework**: Qiskit, Cirq, Q#

## Research Foundation

All passes are based on peer-reviewed research:
- 18+ papers cited
- Techniques from 2005-2024
- State-of-the-art algorithms

## See Also

- [Main Documentation Index](../INDEX.md)
- [QVM Domain](../qvm/)
- [Security Domain](../security/)
