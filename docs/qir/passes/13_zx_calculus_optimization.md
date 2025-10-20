# ZX-Calculus Optimization Pass (EXPERIMENTAL)

**Category**: Experimental Pass  
**Status**: Experimental - Use with caution

---

## Overview

**Purpose**: Optimize using ZX-calculus rewrite rules.

ZX-calculus is a graphical language for quantum computing that represents circuits as diagrams with "spiders". It enables powerful simplifications through graphical rewrite rules.

---

## Research Foundation

**Key Papers:**

1. **Coecke & Kissinger (2017)**: "Picturing Quantum Processes"
   - Foundation of ZX-calculus
   - Complete axiomatization

2. **Kissinger & van de Wetering (2020)**: "PyZX: Large Scale Automated Diagrammatic Reasoning"
   - Practical ZX-calculus optimization
   - https://arxiv.org/abs/1904.04735

3. **Duncan et al. (2020)**: "Graph-theoretic Simplification of Quantum Circuits with the ZX-calculus"
   - Clifford simplification
   - https://arxiv.org/abs/1902.03178

4. **Kissinger & van de Wetering (2019)**: "Reducing T-count with the ZX-calculus"
   - T-count optimization
   - https://arxiv.org/abs/1903.10477

---

## Mini-Tutorial

### ZX-Calculus Basics

**Representation**:
- Circuits → ZX-diagrams (graphs)
- Gates → Spiders (Z or X basis)
- Wires → Edges

**Rewrite Rules**:
1. **Spider Fusion**: Z(α)·Z(β) = Z(α+β)
2. **Local Complementation**: Simplify H patterns
3. **Pivot**: Simplify CNOT patterns
4. **Phase Gadgets**: Extract phase polynomials

### Why This Works

ZX-calculus provides:
- **Graphical reasoning**: Visual optimization
- **Complete axiomatization**: Sound and complete
- **Powerful simplifications**: Beyond traditional methods

---

## Performance

- **Gate reduction**: 15-35% typical, up to 70% best case
- **T-count reduction**: 20-40% typical
- **CNOT reduction**: 10-30% typical
- **Overhead**: High (complex transformations)

---

## Status

**EXPERIMENTAL**: Use with caution in production

**Best for**:
- Clifford+T circuits
- Research and experimentation
- Maximum optimization

---

## See Also

- [Clifford+T Optimization](08_clifford_t_optimization.md) - T-count reduction
- [Phase Polynomial Optimization](14_phase_polynomial_optimization.md) - Related technique
- [Template Matching](06_template_matching.md) - Pattern-based optimization
