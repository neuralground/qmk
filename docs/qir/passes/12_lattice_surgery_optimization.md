# Lattice Surgery Optimization Pass

**Category**: Standard Pass  
**Status**: Production-ready

---

## Overview

**Purpose**: Optimize surface code lattice surgery operations.

Lattice surgery is a technique for performing logical operations on surface codes by merging and splitting code patches.

---

## Research Foundation

**Key Papers:**

1. **Horsman et al. (2012)**: "Surface code quantum computing by lattice surgery"
   - Lattice surgery foundation
   - https://arxiv.org/abs/1111.4022

2. **Litinski (2019)**: "A Game of Surface Codes"
   - Lattice surgery protocols
   - https://arxiv.org/abs/1808.02892

3. **Fowler & Gidney (2018)**: "Low overhead quantum computation using lattice surgery"
   - Optimization techniques
   - https://arxiv.org/abs/1808.06709

---

## Mini-Tutorial

### What is Lattice Surgery?

**Lattice surgery** = Performing operations by merging/splitting surface code patches

**Operations**:
- **Merge**: Combine two patches
- **Split**: Separate patches
- **Measure**: Extract information

### Why Optimize?

- **Reduce space-time volume**: Fewer physical qubits × time
- **Minimize merges/splits**: Expensive operations
- **Optimize routing**: Better patch placement

---

## Performance

- **Space-time volume reduction**: 20-40% typical
- **Critical for**: Surface code implementations
- **Best for**: Fault-tolerant quantum computers

---

## See Also

- [Magic State Optimization](09_magic_state_optimization.md) - Magic state management
- [Clifford+T Optimization](08_clifford_t_optimization.md) - T-count reduction
