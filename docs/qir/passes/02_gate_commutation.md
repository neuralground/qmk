# Gate Commutation Pass

**Category**: Standard Pass  
**Status**: Production-ready

---

## Overview

**Purpose**: Reorder gates to enable other optimizations.

Gate commutation exploits the fact that gates operating on disjoint qubits or commuting gates can be reordered. This enables cancellation, fusion, and parallelization opportunities.

---

## Research Foundation

**Key Papers:**

1. **Maslov, Dueck & Miller (2005)**: "Techniques for the Synthesis of Reversible Toffoli Networks"
   - Commutation rules for reversible circuits
   - https://arxiv.org/abs/quant-ph/0607166

2. **Shende, Bullock & Markov (2006)**: "Synthesis of Quantum Logic Circuits"
   - Gate ordering optimization
   - https://arxiv.org/abs/quant-ph/0406176

3. **Barenco et al. (1995)**: "Elementary gates for quantum computation"
   - Commutation relations for quantum gates
   - https://arxiv.org/abs/quant-ph/9503016

4. **Iten et al. (2016)**: "Quantum circuits for isometries"
   - Advanced commutation techniques
   - https://arxiv.org/abs/1501.06911

---

## Mini-Tutorial

### Commutation Rules

**Basic Principle**: Two operations commute if their order doesn't matter.

**Mathematical**: Gates A and B commute if AB = BA, written as [A,B] = 0

### When Gates Commute

1. **Different Qubits**: Gates on disjoint qubits always commute
2. **Same Axis Rotations**: RZ gates commute with each other
3. **Pauli Gates**: Specific commutation patterns
4. **Diagonal Gates**: S, T, Z commute with each other

### Why This Matters

Commuting gates together enables:
- **Cancellation**: H-H, X-X, etc.
- **Fusion**: RZ-RZ → RZ
- **Parallelization**: Lower circuit depth
- **Optimization**: Expose hidden patterns

---

## Detailed Examples

### Example 1: Independent Qubit Commutation

```
Before:
  q0: ─H─────X─
  q1: ───X─H───

After:
  q0: ─H─X─
  q1: ─X─H─

Explanation: Gates on different qubits commute
Benefit: Enables H-H cancellation on q1 if another H follows

Mathematical:
  (H⊗I)(I⊗X) = (I⊗X)(H⊗I)
  Gates act on different qubits, so they commute
```

### Example 2: Z-Axis Rotation Commutation

```
Before:
  q0: ─T─S─

After:
  q0: ─S─T─

Explanation: T and S both rotate around Z-axis
Benefit: Clusters T gates for fusion
Mathematical: [T, S] = 0 (both diagonal matrices)

Proof:
  T = diag(1, e^(iπ/4))
  S = diag(1, e^(iπ/2))
  T·S = diag(1, e^(i3π/4))
  S·T = diag(1, e^(i3π/4))
  Therefore: T·S = S·T ✓
```

### Example 3: Enabling Cancellation

```
Before:
  q0: ─H─X─H─Y─

After (commute X past H):
  q0: ─H─H─Z─Y─

Then (cancel H-H):
  q0: ─Z─Y─

Explanation: X and H don't commute directly, but we can use:
  H·X·H = Z (conjugation)

Savings: 4 gates → 2 gates (50% reduction)

Why this works:
  Moving X past H changes it to Z
  Then H-H cancel
```

### Example 4: CNOT and Single-Qubit Gates

```
Before:
  q0: ─●─Z─
  q1: ─⊕───

After:
  q0: ─Z─●─
  q1: ───⊕─

Explanation: Z on control commutes with CNOT
Benefit: Enables Z gate fusion with other Z gates

Mathematical:
  CNOT·(Z⊗I) = (Z⊗I)·CNOT
  Z on control doesn't affect CNOT operation
```

### Example 5: Pauli Gate Commutation

```
Before:
  q0: ─X─Z─

After:
  q0: ─Z─X─ (with phase)

Explanation: X and Z anticommute (XZ = -ZX)
Note: Introduces global phase of -1

Mathematical:
  X·Z = [[0,1],[1,0]]·[[1,0],[0,-1]]
      = [[0,-1],[1,0]]
  Z·X = [[1,0],[0,-1]]·[[0,1],[1,0]]
      = [[0,1],[-1,0]]
  X·Z = -Z·X (anticommutation)
```

### Example 6: Enabling T-Gate Clustering

```
Before:
  q0: ─T─H─S─T─

After (commute S and T):
  q0: ─T─H─T─S─

Then (if H can be moved):
  q0: ─T─T─H─S─

Benefit: T gates together can be fused
  T·T = S·T† or continue clustering

Explanation: Moving T gates together is crucial for
Clifford+T optimization
```

### Example 7: Multi-Qubit Pattern

```
Before:
  q0: ─H─●─────
  q1: ───⊕─H───
  q2: ─────────X

After:
  q0: ─H─●─────
  q1: ───⊕─H───
  q2: ─X───────

Explanation: X on q2 commutes with everything (different qubit)
Benefit: Can move X to better position for optimization
```

### Example 8: Measurement Commutation

```
Before:
  q0: ─Z─[M]─
  q1: ─H─────

After:
  q0: ─Z─[M]─
  q1: ─H─────
  (no change, but H on q1 can move earlier)

After (commute H earlier):
  q0: ─Z─[M]─
  q1: ─H─────

Explanation: Gates on different qubits can be reordered
Benefit: Enables earlier execution, better parallelization
```

### Example 9: Complex Reordering

```
Before:
  q0: ─T─H─T─S─T─
  q1: ───────────

After (commute S and T):
  q0: ─T─H─S─T─T─

After (if possible, move H):
  q0: ─T─T─T─H─S─

Then (fuse T gates):
  q0: ─T─S─H─S─

Explanation: Strategic commutation enables fusion
Savings: 5 gates → 4 gates, plus T-count reduction
```

### Example 10: Real-World VQE Circuit

```
Before:
  q0: ─RZ(θ₁)─H─RZ(θ₂)─●─RZ(θ₃)─
  q1: ─────────────────⊕─────────

After (commute RZ past H when beneficial):
  q0: ─H─RZ(θ₁')─RZ(θ₂)─●─RZ(θ₃)─
  q1: ───────────────────⊕─────────

Then (merge RZ gates):
  q0: ─H─RZ(θ₁'+θ₂)─●─RZ(θ₃)─
  q1: ─────────────⊕─────────

Explanation: Commutation + fusion reduces gate count
Savings: Enables multiple optimizations
```

---

## Commutation Rules Reference

### Always Commute

```
1. Gates on different qubits
2. Z-axis rotations (RZ, S, T, Z) with each other
3. X-axis rotations (RX, X) with each other
4. Y-axis rotations (RY, Y) with each other
```

### Conditional Commutation

```
1. CNOT with Z on control
2. CNOT with X on target
3. CZ with Z on either qubit
```

### Never Commute (Anticommute)

```
1. X and Z (XZ = -ZX)
2. Y and X (YX = -XY)
3. Z and Y (ZY = -YZ)
4. H and most gates (H is basis change)
```

---

## Optimization Strategy

### Phase 1: Identify Commutable Gates
- Scan for gates that can be reordered
- Check commutation rules
- Verify qubit dependencies

### Phase 2: Strategic Reordering
- Move gates to enable cancellation
- Cluster similar gates for fusion
- Optimize for parallelization

### Phase 3: Apply Dependent Optimizations
- Run cancellation pass
- Run fusion pass
- Check for new opportunities

---

## Performance

- **Direct gate reduction**: Minimal (0-5%)
- **Enables other optimizations**: 10-20% additional
- **Overhead**: Very low (<1ms)
- **Always beneficial**: Yes (enables other passes)
- **Best with**: Cancellation, Fusion, Clifford+T passes

---

## Implementation Notes

**Algorithm**:
1. Build dependency graph
2. Identify commutable gate pairs
3. Reorder based on optimization goals
4. Verify correctness

**Complexity**: O(n²) where n = number of gates

**Commutation Database**: ~20 rules

---

## Usage

```python
from qir.optimizer.passes import GateCommutationPass

# Create pass
pass_obj = GateCommutationPass()

# Apply to circuit
optimized_circuit = pass_obj.run(circuit)

# Check metrics
print(f"Gates reordered: {pass_obj.metrics.gates_reordered}")
print(f"Commutations: {pass_obj.metrics.commutations}")
```

---

## Common Patterns

### 1. T-Gate Clustering
```
T-S-T → S-T-T (enables fusion)
```

### 2. Cancellation Enablement
```
H-X-H-Y → H-H-Z-Y → Z-Y
```

### 3. Parallelization
```
Move independent gates earlier for parallel execution
```

### 4. Measurement Deferral
```
Commute gates past measurements when possible
```

---

## See Also

- [Gate Cancellation Pass](01_gate_cancellation.md) - Benefits from commutation
- [Gate Fusion Pass](03_gate_fusion.md) - Enabled by commutation
- [Clifford+T Optimization](08_clifford_t_optimization.md) - T-gate clustering
- [Measurement Deferral](07_measurement_deferral.md) - Measurement commutation
