# Measurement Deferral Pass

**Category**: Standard Pass  
**Status**: Production-ready

---

## Overview

**Purpose**: Move measurements to the end of the circuit.

Measurement deferral uses the deferred measurement principle: measurements can be moved to the end of a circuit by replacing them with classical control. This enables more optimization opportunities.

---

## Research Foundation

**Key Papers:**

1. **Nielsen & Chuang (2010)**: "Quantum Computation and Quantum Information"
   - Chapter 4: Deferred measurement principle
   - Foundational textbook

2. **Gottesman (1998)**: "The Heisenberg Representation of Quantum Computers"
   - Measurement commutation rules
   - https://arxiv.org/abs/quant-ph/9807006

3. **Aaronson & Gottesman (2004)**: "Improved Simulation of Stabilizer Circuits"
   - Measurement in stabilizer circuits
   - https://arxiv.org/abs/quant-ph/0406196

---

## Mini-Tutorial

### Deferred Measurement Principle

**Key Idea**: Measurements can be moved to circuit end

**Transformation**:
```
Measure → Use result
  ↓
Quantum gate → Measure at end
```

### Why This Works

**Quantum-Classical Equivalence**:
- Classical control based on measurement
- Can be replaced with quantum controlled gate
- Measurement deferred to end

### Benefits

- **More optimization**: Gates can be optimized across measurement boundaries
- **Simpler analysis**: All measurements at end
- **Better parallelization**: Quantum gates can run in parallel
- **Cleaner circuits**: Separation of quantum and classical

---

## Detailed Examples

### Example 1: Basic Deferral

```
Before:
  q0: ─H─[M]─
  q1: ───────X (controlled on q0)

After:
  q0: ─H─────[M]
  q1: ─CNOT──────

Explanation: Replace classical control with quantum gate
Benefit: Enables H-CNOT optimization

Why this works:
  If q0=|0⟩: X not applied → CNOT with control=|0⟩
  If q0=|1⟩: X applied → CNOT with control=|1⟩
```

### Example 2: Enabling Cancellation

```
Before:
  q0: ─H─[M]─H─

After (defer measurement):
  q0: ─H─H─[M]

Then (cancel H-H):
  q0: ─[M]

Explanation: Deferring measurement enables H-H cancellation
Savings: 2 H gates removed
```

### Example 3: Multiple Measurements

```
Before:
  q0: ─H─[M]─────
  q1: ───────[M]─
  q2: ─X─────────

After:
  q0: ─H─[M]
  q1: ───[M]
  q2: ─X─[M] (optional)

Explanation: Move all measurements to end
Benefit: Cleaner circuit structure
```

### Example 4: Measurement-Based Control

```
Before:
  q0: ─H─[M]─
  if (q0 == 1):
    q1: ─X─

After:
  q0: ─H─●─[M]
  q1: ───⊕────

Explanation: Replace if-statement with CNOT
Benefit: Quantum gate instead of classical control
```

### Example 5: Teleportation Pattern

```
Before:
  q0: ─●─[M]─────
  q1: ─⊕───[M]───
  q2: ─────────X (controlled on q0,q1)

After:
  q0: ─●─────[M]
  q1: ─⊕─────[M]
  q2: ─────X─────

Explanation: Defer measurements in teleportation
Benefit: Can optimize quantum part separately
```

### Example 6: Mid-Circuit Measurement

```
Before:
  q0: ─H─●─[M]─────
  q1: ───⊕─────H─X─

After:
  q0: ─H─●─────[M]
  q1: ───⊕─H─X─────

Explanation: Move measurement to end
Benefit: Enables optimization of q1 gates
```

### Example 7: Conditional Phase

```
Before:
  q0: ─H─[M]─
  if (q0 == 1):
    q1: ─Z─

After:
  q0: ─H─●─[M]
  q1: ───●────

Explanation: Replace conditional Z with CZ
Benefit: Quantum gate enables more optimization
```

### Example 8: Reset Operation

```
Before:
  q0: ─H─[M]─|0⟩ (reset)

After:
  q0: ─H─[M]
  (handle reset separately)

Explanation: Defer measurement, handle reset classically
Benefit: Simplifies quantum circuit
```

### Example 9: Adaptive Circuit

```
Before:
  q0: ─H─[M]─────────
  q1: ───────RY(θ)─── (θ depends on q0)

After (if possible):
  q0: ─H─────────[M]
  q1: ───RY(θ₀,θ₁)───

Explanation: Replace adaptive angle with controlled rotation
Benefit: Removes measurement dependency
```

### Example 10: Real-World VQE

```
Before:
  q0: ─RY(θ)─[M]─────
  q1: ───────────H─X─ (if q0==1)

After:
  q0: ─RY(θ)─●─[M]
  q1: ───────⊕─H─X─

Then optimize:
  q0: ─RY(θ)─●─[M]
  q1: ───────⊕─H─X─

Explanation: Defer measurement, enable optimization
```

---

## Transformation Rules

### Classical Control → Quantum Gate

```
if (M == 0): Apply I
if (M == 1): Apply X
  ↓
Apply CNOT (controlled on M)
```

### Measurement Commutation

```
[M]─Gate → Gate─[M] (if gate commutes with measurement)

Example:
[M]─Z → Z─[M] (Z commutes with Z-basis measurement)
```

### Limitations

```
Cannot defer if:
- Result used for classical computation
- Result sent to classical system
- Adaptive angles depend on result
```

---

## Performance

- **Direct gate reduction**: Minimal
- **Enables other optimizations**: 5-15% additional
- **Overhead**: Low (few ms)
- **Best with**: Cancellation, Fusion, Commutation passes
- **Most effective on**: Circuits with mid-circuit measurements

---

## Implementation Notes

**Algorithm**:
1. Identify mid-circuit measurements
2. Check if measurement can be deferred
3. Replace classical control with quantum gates
4. Move measurement to end
5. Verify correctness

**Complexity**: O(n) where n = number of gates

**Conservative**: Only defer when safe

---

## Usage

```python
from qir.optimizer.passes import MeasurementDeferralPass

# Create pass
pass_obj = MeasurementDeferralPass()

# Apply to circuit
optimized_circuit = pass_obj.run(circuit)

# Check metrics
print(f"Measurements deferred: {pass_obj.metrics.measurements_deferred}")
```

---

## Common Patterns

### 1. Conditional X
```
if (M==1): X → CNOT
```

### 2. Conditional Z
```
if (M==1): Z → CZ
```

### 3. Teleportation
```
Defer measurements in teleportation protocol
```

### 4. Error Correction
```
Defer syndrome measurements when possible
```

---

## See Also

- [Gate Commutation](02_gate_commutation.md) - Enables deferral
- [Gate Cancellation](01_gate_cancellation.md) - Benefits from deferral
- [Dead Code Elimination](04_dead_code_elimination.md) - Removes unused measurements
