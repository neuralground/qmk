# SWAP Insertion Pass

**Category**: Hardware-Aware Optimization  
**Priority**: HIGH  
**Complexity**: High  
**Impact**: Critical for hardware execution

---

## Overview

The SWAP Insertion Pass inserts SWAP gates to satisfy hardware connectivity constraints. Real quantum hardware has limited connectivity - not all qubits can directly interact with each other. This pass ensures that two-qubit gates only operate on adjacent qubits by inserting SWAPs to bring qubits together.

---

## Mini-Tutorial: Hardware Connectivity

### The Problem

**Ideal Quantum Computer**: All-to-all connectivity
```
q0 ←→ q1
 ↕  ×  ↕
q2 ←→ q3

Any qubit can interact with any other qubit directly.
```

**Real Quantum Hardware**: Limited connectivity
```
Linear: q0 — q1 — q2 — q3

Only adjacent qubits can interact directly:
- q0 can only interact with q1
- q1 can interact with q0 and q2
- q2 can interact with q1 and q3
- q3 can only interact with q2
```

### The Solution: SWAP Gates

A SWAP gate exchanges the states of two qubits:
```
SWAP(q0, q1): |ψ₀⟩|ψ₁⟩ → |ψ₁⟩|ψ₀⟩
```

**SWAP Decomposition**:
```
SWAP(a,b) = CNOT(a,b) → CNOT(b,a) → CNOT(a,b)
```

Cost: 3 CNOT gates

### How SWAP Insertion Works

**Problem**: Execute CNOT(q0, q3) on linear topology

**Solution**: Move qubits together using SWAPs
```
Initial: q0 — q1 — q2 — q3

Step 1: SWAP(q2, q3)
Result: q0 — q1 — q3 — q2

Step 2: SWAP(q1, q3)  
Result: q0 — q3 — q1 — q2

Step 3: CNOT(q0, q3)  ← Now adjacent!
Result: q0 — q3 — q1 — q2

Step 4: SWAP(q1, q3)  ← Restore
Result: q0 — q1 — q3 — q2

Step 5: SWAP(q2, q3)  ← Restore
Result: q0 — q1 — q2 — q3
```

**Cost**: 4 SWAPs + 1 CNOT = 13 CNOTs total (vs 1 CNOT ideal)

---

## Algorithm

### 1. Topology Representation

**Linear Topology**:
```python
edges = [(0,1), (1,2), (2,3)]
```

**Grid Topology**:
```
q0 — q1 — q2
 |    |    |
q3 — q4 — q5
```

### 2. Qubit Mapping

Maintain mapping: logical qubit → physical qubit
```python
mapping = {
    logical_q0: physical_0,
    logical_q1: physical_1,
    logical_q2: physical_2
}
```

### 3. SWAP Insertion Algorithm

```
For each two-qubit gate (q_a, q_b):
    1. Get physical positions: p_a = mapping[q_a], p_b = mapping[q_b]
    2. Check if p_a and p_b are adjacent in topology
    3. If not adjacent:
        a. Find shortest path from p_a to p_b
        b. Insert SWAPs along path to bring qubits together
        c. Update mapping after each SWAP
    4. Execute the two-qubit gate
    5. (Optional) Insert SWAPs to restore original positions
```

---

## Examples

### Example 1: Linear Topology - Simple Case

**Hardware**: Linear 0—1—2—3

**Circuit**:
```qir
; Before
CNOT q0, q2  ; q0 and q2 not adjacent
```

**After SWAP Insertion**:
```qir
; After
SWAP q1, q2   ; Move q2 closer to q0
CNOT q0, q1   ; Now q0 and q1 are adjacent (q1 has q2's state)
SWAP q1, q2   ; Restore positions
```

**Cost**: 2 SWAPs + 1 CNOT = 7 CNOTs

---

### Example 2: Multiple Non-Adjacent Gates

**Hardware**: Linear 0—1—2—3

**Circuit**:
```qir
; Before
CNOT q0, q3
CNOT q1, q2
```

**After SWAP Insertion**:
```qir
; After
; For CNOT(q0, q3)
SWAP q2, q3
SWAP q1, q2
CNOT q0, q1   ; q1 now has q3's state
SWAP q1, q2
SWAP q2, q3

; For CNOT(q1, q2) - already adjacent!
CNOT q1, q2
```

**Cost**: 4 SWAPs + 2 CNOTs = 14 CNOTs

---

### Example 3: Grid Topology

**Hardware**: 2×3 Grid
```
0 — 1 — 2
|   |   |
3 — 4 — 5
```

**Circuit**:
```qir
; Before
CNOT q0, q5  ; Opposite corners
```

**After SWAP Insertion** (one possible path):
```qir
; After
SWAP q1, q2   ; Move q5 towards q0
SWAP q2, q5
SWAP q1, q2
CNOT q0, q1   ; Now adjacent
SWAP q1, q2   ; Restore
SWAP q2, q5
SWAP q1, q2
```

**Cost**: 6 SWAPs + 1 CNOT = 19 CNOTs

---

### Example 4: Bell State on Linear Topology

**Hardware**: Linear 0—1—2—3

**Circuit**:
```qir
; Before
H q0
CNOT q0, q1  ; Adjacent - no SWAPs needed!
```

**After SWAP Insertion**:
```qir
; After (unchanged)
H q0
CNOT q0, q1  ; Already adjacent
```

**Cost**: 0 SWAPs + 1 CNOT = 1 CNOT

---

### Example 5: Optimized Path Finding

**Hardware**: Linear 0—1—2—3—4

**Circuit**:
```qir
; Before
CNOT q0, q4
```

**Naive Approach** (move q0 to q4):
```qir
SWAP q0, q1
SWAP q1, q2
SWAP q2, q3
SWAP q3, q4
CNOT q4, q4  ; Now adjacent (both at position 4)
; Restore: 4 more SWAPs
```
Cost: 8 SWAPs = 24 CNOTs

**Better Approach** (meet in middle):
```qir
SWAP q1, q2   ; Move q0 right
SWAP q0, q1
SWAP q3, q4   ; Move q4 left
SWAP q3, q4
CNOT q2, q3   ; Meet at positions 2 and 3
; Restore: 4 SWAPs
```
Cost: 8 SWAPs = 24 CNOTs (same, but more balanced)

---

## Common Topologies

### 1. Linear (IBM Q5)
```
0 — 1 — 2 — 3 — 4
```
- Simple path finding
- High SWAP overhead for distant qubits
- Good for: Sequential algorithms

### 2. T-Shape (IBM QX2)
```
    0
    |
1 — 2 — 3
    |
    4
```
- Central qubit (2) is hub
- Lower SWAP overhead
- Good for: Star-like interactions

### 3. Grid (Google Sycamore)
```
0 — 1 — 2 — 3
|   |   |   |
4 — 5 — 6 — 7
|   |   |   |
8 — 9 —10 —11
```
- 2D connectivity
- Moderate SWAP overhead
- Good for: 2D algorithms (QFT, etc.)

### 4. Heavy-Hex (IBM Quantum)
```
    0       2
   / \     / \
  1   3   4   5
   \ / \ / \ /
    6   7   8
```
- Higher connectivity
- Lower SWAP overhead
- Good for: General purpose

---

## SWAP Optimization Strategies

### 1. Greedy Shortest Path
```
For each gate, find shortest path and insert SWAPs
```
**Pros**: Simple, fast  
**Cons**: Not globally optimal

### 2. Lookahead
```
Consider next k gates when choosing SWAP path
```
**Pros**: Better global optimization  
**Cons**: Slower, more complex

### 3. SWAP Reduction
```
After insertion, remove redundant SWAPs:
- SWAP(a,b) → SWAP(a,b) = identity
- Commute SWAPs to enable cancellation
```

### 4. Temporary Mapping
```
Don't restore positions after each gate
Keep qubits where they end up if beneficial
```

---

## Performance Characteristics

### SWAP Overhead

**Linear Topology** (n qubits):
- Adjacent gates: 0 SWAPs
- Distance d gates: ~2d SWAPs
- Worst case (q0 to qn): ~2n SWAPs

**Grid Topology** (n×n):
- Adjacent gates: 0 SWAPs
- Distance d gates: ~2d SWAPs
- Worst case (corner to corner): ~4n SWAPs

### Success Criteria

From OPTIMIZATION_PLAN.md:
- **SWAP overhead**: <20% of total gates
- **Execution time**: <100ms for typical circuits

### Typical Results

**Bell State** (2 qubits):
- Linear topology: 0 SWAPs (already adjacent)
- Overhead: 0%

**GHZ State** (4 qubits):
- Linear topology: 0-2 SWAPs (depends on layout)
- Overhead: 0-15%

**Random Circuit** (10 qubits, 50 gates):
- Linear topology: 10-20 SWAPs
- Overhead: 20-40%

---

## Implementation Notes

### Qubit Mapping Integration

SWAP Insertion works best with Qubit Mapping:
```python
# First: Optimize qubit placement
mapping_pass = QubitMappingPass(topology)
circuit = mapping_pass.run(circuit)

# Then: Insert SWAPs for remaining non-adjacent gates
swap_pass = SWAPInsertionPass(topology)
circuit = swap_pass.run(circuit)
```

### Path Finding Algorithms

**Breadth-First Search** (BFS):
```python
def find_path(start, end, topology):
    queue = [(start, [start])]
    visited = {start}
    
    while queue:
        node, path = queue.pop(0)
        if node == end:
            return path
        
        for neighbor in topology.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None  # No path found
```

**Dijkstra's Algorithm** (for weighted graphs):
```python
def find_shortest_path(start, end, topology):
    # Use heap queue for efficiency
    # Consider edge weights (gate fidelities)
    ...
```

---

## Research & References

### Key Papers

1. **"Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices"**  
   Zulehner et al. (2018)  
   https://arxiv.org/abs/1712.04722
   - Optimal SWAP insertion algorithms
   - Heuristic approaches for large circuits

2. **"Noise-Adaptive Compiler Mappings for Noisy Intermediate-Scale Quantum Computers"**  
   Murali et al. (2019)  
   https://arxiv.org/abs/1901.11054
   - Considers hardware noise in mapping
   - Noise-aware SWAP insertion

3. **"A Survey on Quantum Computing Technology"**  
   Gill et al. (2022)  
   - Overview of hardware topologies
   - Connectivity constraints

### IBM Qiskit Implementation

Qiskit's transpiler uses sophisticated SWAP insertion:
```python
from qiskit.transpiler.passes import StochasticSwap, SabreSwap

# SABRE algorithm - state-of-the-art
pass = SabreSwap(coupling_map)
```

---

## Usage Example

```python
from qir.optimizer import QIRCircuit, PassManager
from qir.optimizer.passes import SwapInsertionPass
from qir.optimizer.topology import LinearTopology

# Create circuit
circuit = QIRCircuit()
q0 = circuit.add_qubit('q0')
q1 = circuit.add_qubit('q1')
q2 = circuit.add_qubit('q2')
q3 = circuit.add_qubit('q3')

# Add gates
circuit.add_gate('H', [q0])
circuit.add_gate('CNOT', [q0, q3])  # Not adjacent!
circuit.add_gate('CNOT', [q1, q2])  # Adjacent

# Define hardware topology
topology = LinearTopology(num_qubits=4)  # 0—1—2—3

# Run SWAP insertion
swap_pass = SwapInsertionPass(topology)
optimized = swap_pass.run(circuit)

# Check results
print(f"Original gates: {circuit.get_gate_count()}")
print(f"After SWAP insertion: {optimized.get_gate_count()}")
print(f"SWAPs added: {swap_pass.metrics.swap_gates_added}")
```

---

## Best Practices

### 1. Run After Qubit Mapping
```python
# Good: Optimize placement first
manager = PassManager([
    QubitMappingPass(topology),
    SwapInsertionPass(topology)
])
```

### 2. Consider Hardware Fidelities
```python
# Better: Use noise-aware topology
topology = NoisyTopology(coupling_map, fidelities)
swap_pass = SwapInsertionPass(topology)
```

### 3. Minimize SWAP Overhead
```python
# Best: Combine with other optimizations
manager = PassManager([
    QubitMappingPass(topology),      # Optimize placement
    GateCommutationPass(),            # Enable better routing
    SwapInsertionPass(topology),      # Insert SWAPs
    GateCancellationPass(),           # Remove redundant SWAPs
])
```

---

## Limitations

1. **Greedy Algorithm**: Not globally optimal
2. **No Lookahead**: Doesn't consider future gates
3. **Static Mapping**: Doesn't adapt during execution
4. **No Noise Consideration**: Doesn't account for gate fidelities

---

## Future Improvements

1. **SABRE Algorithm**: State-of-the-art SWAP insertion
2. **Lookahead**: Consider next k gates
3. **Noise-Aware**: Prefer high-fidelity paths
4. **Dynamic Mapping**: Adapt mapping during execution
5. **Machine Learning**: Learn optimal strategies

---

## See Also

- [Qubit Mapping Pass](19_qubit_mapping.md) - Optimizes initial placement
- [Gate Commutation Pass](02_gate_commutation.md) - Enables better routing
- [Template Matching Pass](06_template_matching.md) - Can reduce two-qubit gates

---

**Status**: ✅ Production Ready  
**Tested**: ✅ Yes  
**Benchmarked**: ⏳ In Progress
