# QVM Circuit Library

Reusable quantum circuit components for building complex quantum algorithms.

## Library Components

### Quantum Fourier Transform

**File:** `qft.qasm`

**Purpose:** Transforms |x⟩ → (1/√N) Σ exp(2πixy/N)|y⟩

**Parameters:**
- `n_qubits` - Number of qubits
- `qubit_prefix` - Prefix for qubit names

**Complexity:** O(n²) gates

**Applications:** Shor's algorithm, phase estimation, quantum simulation

---

### Quantum Adders

#### Draper Adder

**File:** `draper_adder.qasm`

**Purpose:** QFT-based addition: b = a + b (mod 2^n)

**Parameters:**
- `n_bits` - Number of bits
- `a_prefix`, `b_prefix` - Register prefixes

**Complexity:** O(n²) gates

**Advantages:** No ancilla qubits needed

#### Cuccaro Adder

**File:** `cuccaro_adder.qasm`

**Purpose:** Ripple-carry addition with minimal ancilla

**Parameters:**
- `n_bits` - Number of bits
- `a_prefix`, `b_prefix` - Register prefixes
- `carry_qubit` - Carry qubit name

**Complexity:** O(n) gates

**Advantages:** Linear gate count, one ancilla

---

### Arithmetic Circuits

#### Comparator

**File:** `comparator.qasm`

**Purpose:** Compares two registers: |a⟩|b⟩|0⟩ → |a⟩|b⟩|a>b⟩

**Parameters:**
- `n_bits` - Number of bits
- `a_prefix`, `b_prefix` - Register prefixes
- `result_qubit` - Output qubit

**Complexity:** O(n) gates

#### Modular Exponentiation

**File:** `modular_exp.qasm`

**Purpose:** Computes |x⟩|y⟩ → |x⟩|y * a^x mod N⟩

**Parameters:**
- `n_control`, `n_work` - Qubit counts
- `a`, `N` - Base and modulus
- `control_prefix`, `work_prefix` - Prefixes

**Status:** Framework (requires quantum adder for full implementation)

---

### Algorithm Components

#### Phase Estimation

**File:** `phase_estimation.qasm`

**Purpose:** Estimates eigenvalue phase of unitary operator

**Parameters:**
- `n_precision` - Precision qubits
- `n_eigenstate` - Eigenstate qubits
- `precision_prefix`, `eigenstate_prefix` - Prefixes

**Complexity:** O(n²) for QFT + O(n × U_complexity)

**Applications:** Shor's algorithm, quantum simulation, HHL algorithm

#### Amplitude Amplification

**File:** `amplitude_amplification.qasm`

**Purpose:** Grover operator for amplitude amplification

**Parameters:**
- `n_qubits` - Number of qubits
- `qubit_prefix` - Prefix
- `oracle_type` - Oracle documentation

**Complexity:** O(n) gates per iteration, O(√N) iterations needed

**Applications:** Grover's search, quantum counting, optimization

#### Grover Oracle

**File:** `grover_oracle.qasm`

**Purpose:** Oracle templates for Grover's algorithm

**Parameters:**
- `n_qubits` - Number of qubits
- `target_state` - Target state to mark
- `oracle_mode` - "single", "multi", or "function"

**Modes:**
- Single: Marks one state
- Multi: Marks multiple states
- Function: Marks states satisfying condition

---

### Error Correction

#### Syndrome Extraction

**File:** `syndrome_extraction.qasm`

**Purpose:** Extracts error syndromes for QEC

**Parameters:**
- `n_data`, `n_ancilla` - Qubit counts
- `data_prefix`, `ancilla_prefix` - Prefixes
- `code_type` - "repetition", "surface", or "custom"

**Codes Supported:**
- Repetition code (3-qubit)
- Surface code (framework)
- Custom codes (extensible)

---

## Usage Examples

### Example 1: Using QFT

```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate qubits
alloc: ALLOC_LQ n=4, profile="logical:Surface(d=3)" -> q0, q1, q2, q3

; Prepare state
.for i in 0..3
    h_{i}: APPLY_H q{i}
.endfor

; Apply QFT
.set n_qubits = 4
.set qubit_prefix = "q"
.include "qvm/lib/qft.qasm"

; Measure
.for i in 0..3
    m_{i}: MEASURE_Z q{i} -> m{i}
.endfor
```

### Example 2: Using Draper Adder

```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate two 4-bit registers
alloc: ALLOC_LQ n=8, profile="logical:Surface(d=3)" -> a0, a1, a2, a3, b0, b1, b2, b3

; Prepare a = 5 (0101)
x_a0: APPLY_X a0
x_a2: APPLY_X a2

; Prepare b = 3 (0011)
x_b0: APPLY_X b0
x_b1: APPLY_X b1

; Add: b = a + b = 8 (1000)
.set n_bits = 4
.set a_prefix = "a"
.set b_prefix = "b"
.include "qvm/lib/draper_adder.qasm"

; Measure result
.for i in 0..3
    m_b{i}: MEASURE_Z b{i} -> mb{i}
.endfor
```

### Example 3: Phase Estimation

```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate qubits
alloc: ALLOC_LQ n=6, profile="logical:Surface(d=3)" -> prec_0, prec_1, prec_2, prec_3, eigen_0, eigen_1

; Prepare eigenstate
x_eigen: APPLY_X eigen_0

; Apply phase estimation
.set n_precision = 4
.set n_eigenstate = 2
.set precision_prefix = "prec"
.set eigenstate_prefix = "eigen"
.set unitary_name = "U"
.include "qvm/lib/phase_estimation.qasm"

; Measure precision qubits
.for i in 0..3
    m_{i}: MEASURE_Z prec_{i} -> m{i}
.endfor
```

---

## Design Principles

### 1. Parameterization
All library components are parameterized for flexibility:
- Qubit counts
- Register names
- Algorithm-specific parameters

### 2. Composability
Components can be combined to build complex algorithms:
```
Shor's = Superposition + Modular Exp + QFT + Measurement
Phase Est = Superposition + Controlled-U + Inverse QFT
```

### 3. Documentation
Each component includes:
- Purpose and algorithm description
- Parameter documentation
- Complexity analysis
- Usage examples

### 4. Extensibility
Framework provided for:
- Custom oracles
- Different code types
- Algorithm variations

---

## Adding New Components

To add a new library component:

1. **Create the file** in `qvm/lib/`
   - Use `.qasm` suffix
   - Follow naming convention (lowercase, underscores)

2. **Document parameters** at the top
   ```asm
   ; Component Name
   ;
   ; Purpose: Brief description
   ;
   ; Parameters:
   ;   param1 - Description
   ;   param2 - Description
   ```

3. **Implement with .param**
   ```asm
   .version 0.1
   ; .param n_qubits = 4
   ; .param qubit_prefix = "q"
   ```

4. **Add to this README**
   - Component description
   - Parameters
   - Complexity
   - Usage example

5. **Test the component**
   - Create test circuit
   - Verify correctness
   - Document edge cases

---

## Complexity Reference

| Component | Gates | Space | Notes |
|-----------|-------|-------|-------|
| QFT | O(n²) | n qubits | No ancilla |
| Draper Adder | O(n²) | 2n qubits | Uses QFT |
| Cuccaro Adder | O(n) | 2n+1 qubits | One ancilla |
| Comparator | O(n) | 2n+1 qubits | One ancilla |
| Phase Est | O(n²) | n+m qubits | + U complexity |
| Amp Amp | O(n) | n qubits | Per iteration |
| Syndrome Ext | O(n) | n+k qubits | k ancilla |

---

## Future Components

Planned additions:
- Takahashi adder (optimized)
- Modular multiplication (full implementation)
- Modular inverse
- Surface code operations
- Steane code operations
- QAOA mixer/cost operators
- Variational ansatzes
- Quantum walk operators

---

## References

- Nielsen & Chuang, "Quantum Computation and Quantum Information"
- Draper, "Addition on a Quantum Computer", arXiv:quant-ph/0008033
- Cuccaro et al., "A new quantum ripple-carry addition circuit", arXiv:quant-ph/0410184
- Grover, "A fast quantum mechanical algorithm for database search"
- Shor, "Polynomial-Time Algorithms for Prime Factorization"
