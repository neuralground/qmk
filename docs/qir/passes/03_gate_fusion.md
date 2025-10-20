# Gate Fusion Pass

**Category**: Standard Pass  
**Status**: Production-ready

---

## Overview

**Purpose**: Merge adjacent single-qubit gates into a single operation.

Any sequence of single-qubit gates can be represented as a single unitary matrix. Gate fusion combines multiple gates into one, reducing gate count and depth.

---

## Research Foundation

**Key Papers:**

1. **Shende, Bullock & Markov (2006)**: "Synthesis of Quantum Logic Circuits"
   - Optimal single-qubit synthesis
   - KAK decomposition
   - https://arxiv.org/abs/quant-ph/0406176

2. **Vatan & Williams (2004)**: "Optimal Quantum Circuits for General Two-Qubit Gates"
   - Gate decomposition and synthesis
   - https://arxiv.org/abs/quant-ph/0308006

3. **Khaneja & Glaser (2001)**: "Cartan Decomposition of SU(2^n)"
   - Mathematical foundations
   - https://doi.org/10.1016/S0009-2614(01)00318-4

4. **Möttönen et al. (2004)**: "Decompositions of general quantum gates"
   - Universal decomposition techniques
   - https://arxiv.org/abs/quant-ph/0404089

---

## Mini-Tutorial

### Mathematical Background

**Key Principle**: Any single-qubit gate is in SU(2)

**Product Property**: Product of SU(2) matrices is also in SU(2)

**Universal Decomposition**: Any U ∈ SU(2) can be written as:
```
U = e^(iα) RZ(β)RY(γ)RZ(δ)
```

### Why This Works

Multiple rotations on same qubit can be combined:
- **Same axis**: RZ(α)·RZ(β) = RZ(α+β)
- **Different axes**: Use universal decomposition
- **General case**: Multiply matrices, decompose result

### Benefits

- **Reduced gate count**: n gates → 1 gate
- **Reduced depth**: n layers → 1 layer
- **Simpler circuit**: Easier to analyze
- **Better fidelity**: Fewer gate applications

---

## Detailed Examples

### Example 1: Same-Axis Rotation Fusion

```
Before:
  q0: ─RZ(π/4)─RZ(π/6)─RZ(π/3)─

After:
  q0: ─RZ(3π/4)─

Explanation: RZ(α)·RZ(β)·RZ(γ) = RZ(α+β+γ)
Calculation: π/4 + π/6 + π/3 = 3π/12 + 2π/12 + 4π/12 = 3π/4
Savings: 3 gates → 1 gate (67% reduction)

Mathematical:
  RZ(θ) = exp(-iθZ/2) = [[e^(-iθ/2), 0], [0, e^(iθ/2)]]
  RZ(α)·RZ(β) = RZ(α+β) (angles add)
```

### Example 2: Clifford Gate Fusion

```
Before:
  q0: ─H─S─H─

After:
  q0: ─S†─

Explanation: H·S·H = S† (conjugation by Hadamard)
Savings: 3 gates → 1 gate (67% reduction)

Mathematical:
  H·S·H = H·RZ(π/2)·H
        = RX(π/2)  (basis change)
        = S† in Z basis

Verification:
  H = (1/√2)[[1,1],[1,-1]]
  S = [[1,0],[0,i]]
  H·S·H = [[1,0],[0,-i]] = S†
```

### Example 3: RX-RZ-RX Pattern

```
Before:
  q0: ─RZ(θ₁)─RX(π/2)─RZ(θ₂)─RX(-π/2)─RZ(θ₃)─

After:
  q0: ─RZ(θ₁+θ₃)─RY(θ₂)─

Explanation: RX-RZ-RX pattern simplifies
Savings: 5 gates → 2 gates (60% reduction)

Identity: RX(π/2)·RZ(θ)·RX(-π/2) = RY(θ)

Why this works:
  RX(π/2) changes basis from Z to Y
  RZ(θ) in Y basis = RY(θ) in Z basis
  RX(-π/2) changes back
```

### Example 4: Pauli Gate Fusion

```
Before:
  q0: ─X─Y─Z─

After:
  q0: ─iY─  (or just Y with global phase)

Explanation: X·Y·Z = iY
Savings: 3 gates → 1 gate (67% reduction)

Mathematical:
  X = [[0,1],[1,0]]
  Y = [[0,-i],[i,0]]
  Z = [[1,0],[0,-1]]
  
  X·Y = [[i,0],[0,-i]] = iZ
  (X·Y)·Z = iZ·Z = iI·Z = iY
```

### Example 5: H-S-H-S Pattern

```
Before:
  q0: ─H─S─H─S─

After:
  q0: ─S†─S─ = ─I─ = (removed)

Explanation: H-S-H = S†, then S†·S = I
Savings: 4 gates → 0 gates (100% reduction!)

Step-by-step:
  1. H·S·H = S† (from Example 2)
  2. S†·S = I (inverse pair)
  3. Remove identity
```

### Example 6: Complex Clifford Sequence

```
Before:
  q0: ─H─S─S─H─

After:
  q0: ─Z─

Explanation: S·S = Z, then H·Z·H = Z
Savings: 4 gates → 1 gate (75% reduction)

Step-by-step:
  1. S·S = RZ(π/2)·RZ(π/2) = RZ(π) = Z
  2. H·Z·H = Z (Z commutes with H up to phase)
```

### Example 7: Rotation Angle Simplification

```
Before:
  q0: ─RZ(2π)─RZ(π/4)─

After:
  q0: ─RZ(π/4)─

Explanation: RZ(2π) = I (full rotation)
Savings: 2 gates → 1 gate (50% reduction)

Mathematical:
  RZ(2π) = exp(-i·2π·Z/2) = exp(-iπZ) = -I ≈ I (global phase)
  -I·RZ(π/4) = -RZ(π/4) ≈ RZ(π/4) (ignore global phase)
```

### Example 8: VQE Ansatz Optimization

```
Before (typical VQE layer):
  q0: ─RY(θ₁)─RZ(θ₂)─RY(θ₃)─

After (fused):
  q0: ─U(θ₁,θ₂,θ₃)─

Explanation: Three rotations → single unitary
Savings: 3 gates → 1 gate (67% reduction)

Implementation:
  Compute U = RY(θ₁)·RZ(θ₂)·RY(θ₃)
  Decompose back to minimal form if needed
  Or keep as single unitary
```

### Example 9: Arbitrary Single-Qubit Sequence

```
Before:
  q0: ─H─T─S─H─X─

After (compute product):
  q0: ─U─

Where U = H·T·S·H·X (single 2×2 unitary)

Explanation: Any sequence of single-qubit gates
can be fused into one gate

Savings: 5 gates → 1 gate (80% reduction)

Process:
  1. Multiply matrices: U = H·T·S·H·X
  2. Result is 2×2 unitary
  3. Optionally decompose to canonical form
```

### Example 10: Real-World Circuit

```
Before (QAOA circuit):
  q0: ─RZ(γ₁)─RX(β₁)─RZ(γ₂)─RX(β₂)─RZ(γ₃)─

After (fuse RZ gates):
  q0: ─RZ(γ₁)─RX(β₁)─RZ(γ₂)─RX(β₂)─RZ(γ₃)─

After (fuse RZ-RX-RZ):
  q0: ─U₁(γ₁,β₁,γ₂)─RX(β₂)─RZ(γ₃)─

After (continue):
  q0: ─U₁─U₂(β₂,γ₃)─

Savings: 5 gates → 2 gates (60% reduction)
```

---

## Fusion Rules

### Same-Axis Rotations
```
RX(α)·RX(β) = RX(α+β)
RY(α)·RY(β) = RY(α+β)
RZ(α)·RZ(β) = RZ(α+β)
```

### Clifford Conjugations
```
H·S·H = S†
H·T·H = T†
S·H·S† = H (with phase)
```

### Pauli Products
```
X·X = I
Y·Y = I
Z·Z = I
X·Y = iZ
Y·Z = iX
Z·X = iY
```

### Special Patterns
```
S·S = Z
T·T·T·T = Z
H·H = I
```

---

## Universal Decomposition

Any single-qubit unitary U can be decomposed as:

```
U = e^(iα) RZ(β)RY(γ)RZ(δ)
```

Where:
- α = global phase (often ignored)
- β, γ, δ = Euler angles

**Advantage**: Canonical form for comparison and optimization

---

## Performance

- **Gate reduction**: 10-25% typical, up to 80% best case
- **Depth reduction**: 10-20% typical
- **Overhead**: Low (few ms for typical circuits)
- **Most effective on**: Circuits with many single-qubit gates
- **Best with**: Commutation pass (enables more fusion)

---

## Implementation Notes

**Algorithm**:
1. Identify sequences of single-qubit gates on same qubit
2. Multiply gate matrices
3. Decompose result to canonical form (optional)
4. Replace sequence with fused gate

**Complexity**: O(n) where n = number of gates

**Matrix Multiplication**: 2×2 matrices, very fast

---

## Usage

```python
from qir.optimizer.passes import GateFusionPass

# Create pass
pass_obj = GateFusionPass()

# Apply to circuit
optimized_circuit = pass_obj.run(circuit)

# Check metrics
print(f"Gates fused: {pass_obj.metrics.gates_fused}")
print(f"Sequences merged: {pass_obj.metrics.sequences_merged}")
```

---

## Common Patterns

### 1. Rotation Merging
```
RZ-RZ-RZ → RZ (angles add)
```

### 2. Clifford Simplification
```
H-S-H → S†
```

### 3. Pauli Cancellation
```
X-X → I (removed)
```

### 4. VQE Layer Fusion
```
RY-RZ-RY → U (single gate)
```

---

## See Also

- [Gate Cancellation Pass](01_gate_cancellation.md) - Removes identity gates
- [Gate Commutation Pass](02_gate_commutation.md) - Enables fusion
- [Clifford+T Optimization](08_clifford_t_optimization.md) - Clifford fusion
- [Template Matching](06_template_matching.md) - Pattern-based fusion
