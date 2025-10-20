# QIR Optimization Passes - Individual Documentation

This directory contains comprehensive documentation for each optimization pass, with mini-tutorials, detailed examples, and research citations.

## Standard Passes (Production-Ready)

1. **[Gate Cancellation](01_gate_cancellation.md)** - Remove adjacent inverse gate pairs
2. **[Gate Commutation](02_gate_commutation.md)** - Reorder gates to enable optimizations
3. **[Gate Fusion](03_gate_fusion.md)** - Merge adjacent single-qubit gates
4. **[Dead Code Elimination](04_dead_code_elimination.md)** - Remove unused gates
5. **[Constant Propagation](05_constant_propagation.md)** - Simplify with known states
6. **[Template Matching](06_template_matching.md)** - Replace patterns with optimal equivalents
7. **[Measurement Deferral](07_measurement_deferral.md)** - Move measurements to end
8. **[Clifford+T Optimization](08_clifford_t_optimization.md)** - Minimize T-count
9. **[Magic State Optimization](09_magic_state_optimization.md)** - Optimize magic states
10. **[Gate Teleportation](10_gate_teleportation.md)** - Teleport gates for depth reduction
11. **[Uncomputation Optimization](11_uncomputation_optimization.md)** - Optimize reversible uncomputation
12. **[Lattice Surgery Optimization](12_lattice_surgery_optimization.md)** - Optimize surface code operations

## Hardware-Aware Passes (Production-Ready)

13. **[SWAP Insertion](18_swap_insertion.md)** - Insert SWAPs for hardware connectivity
14. **[Qubit Mapping](19_qubit_mapping.md)** - Map logical to physical qubits optimally
15. **[Measurement Canonicalization](20_measurement_canonicalization.md)** - Canonicalize measurement bases (v1 & v2)

## Experimental Passes (Cutting-Edge Research)

16. **[ZX-Calculus Optimization](13_zx_calculus_optimization.md)** - ZX-calculus rewrite rules
17. **[Phase Polynomial Optimization](14_phase_polynomial_optimization.md)** - Phase polynomial extraction
18. **[Synthesis-Based Optimization](15_synthesis_based_optimization.md)** - Optimal re-synthesis
19. **[Pauli Network Synthesis](16_pauli_network_synthesis.md)** - Pauli rotation optimization
20. **[Tensor Network Contraction](17_tensor_network_contraction.md)** - Tensor network optimization

## Documentation Format

Each pass document includes:

- **Overview**: Purpose and high-level description
- **Research Foundation**: Key papers with citations
- **Mini-Tutorial**: Theory and mathematical background
- **Detailed Examples**: 8-11 before/after examples with explanations
- **Common Patterns**: Frequently encountered patterns
- **Performance Metrics**: Typical and best-case reductions
- **Implementation Notes**: Algorithm and complexity
- **Usage**: Code examples
- **See Also**: Related passes

## Quick Reference

### By Gate Reduction
- **Best**: Template Matching (15-30%), Synthesis-Based (20-40%)
- **Good**: Gate Fusion (10-25%), Clifford+T (10-30%)
- **Always Run**: Gate Cancellation (5-15%), Dead Code (5-10%)

### By T-Count Reduction (Fault-Tolerant)
- **Best**: ZX-Calculus (20-40%), Phase Polynomial (10-30%)
- **Standard**: Clifford+T Optimization (10-30%)

### By CNOT Reduction
- **Best**: Pauli Network (30-50%)
- **Good**: ZX-Calculus (10-30%), Template Matching (10-20%)

### By Depth Reduction
- **Best**: Gate Teleportation (20-40%)
- **Good**: Synthesis-Based (15-30%), Tensor Network (15-30%)

## Total Statistics

- **Total Passes**: 20 (12 standard + 3 hardware-aware + 5 experimental)
- **Research Papers**: 30+ cited
- **Examples**: 170+ detailed examples
- **Documentation**: 12,000+ lines

## See Also

- [Main Optimization Guide](../OPTIMIZER_GUIDE.md)
- [Pipeline Guide](../PIPELINE_GUIDE.md)
- [Performance Comparison](../QIR_OPTIMIZATION_PASSES.md#performance-comparison)
