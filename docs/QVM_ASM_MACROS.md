# QVM Assembly Macro System

## Overview

The QVM Assembly language now supports a powerful macro system that allows you to write quantum circuits in pure assembly without Python code generation. This makes examples more concise, readable, and maintainable.

## Features

### 1. Variable Definitions (`.set`)

Define variables that can be used throughout your assembly:

```asm
.set n_qubits = 4
.set prefix = "q"
.set angle = pi / 4

h0: APPLY_H {prefix}0
rz: APPLY_RZ q0, theta={angle}
```

### 2. For Loops (`.for ... .endfor`)

Iterate over ranges or lists:

**Range syntax:**
```asm
.for i in 0..n_qubits-1
    h{i}: APPLY_H q{i}
.endfor
```

**List iteration:**
```asm
.set qubits = ["q0", "q1", "q2"]
.for q in qubits
    h_{q}: APPLY_H {q}
.endfor
```

**Nested loops:**
```asm
.for i in 0..2
    .for j in 0..2
        cnot{i}_{j}: APPLY_CNOT q{i}, q{j}
    .endfor
.endfor
```

### 3. Conditionals (`.if ... .else ... .endif`)

Conditional code generation:

```asm
.set oracle_type = "constant"

.if oracle_type == "constant"
    ; Identity oracle - do nothing
.else
    oracle: APPLY_X y
.endif
```

### 4. Macros (`.macro ... .endmacro`)

Define reusable circuit patterns:

```asm
.macro BELL_PAIR(q0, q1)
    h: APPLY_H {q0}
    cnot: APPLY_CNOT {q0}, {q1}
.endmacro

; Use the macro
BELL_PAIR(qA, qB)
BELL_PAIR(qC, qD)
```

**Macros with loops:**
```asm
.macro GHZ_STATE(qubits)
    h0: APPLY_H {qubits[0]}
    .for i in 1..len(qubits)-1
        cnot{i}: APPLY_CNOT {qubits[0]}, {qubits[i]}
    .endfor
.endmacro

.set my_qubits = ["q0", "q1", "q2", "q3"]
GHZ_STATE(my_qubits)
```

### 5. Include Files (`.include`)

Include external macro libraries:

```asm
.include "stdlib.qvm.asm"

; Now use macros from stdlib
BELL_PAIR(q0, q1)
GHZ_STATE(["q0", "q1", "q2", "q3"])
```

## Standard Library

The standard library (`qvm/asm/stdlib.qvm.asm`) provides common quantum circuit patterns:

### Basic Gates

- `BELL_PAIR(q0, q1)` - Create Bell pair |Φ+⟩
- `SWAP(q0, q1)` - SWAP two qubits using 3 CNOTs

### Multi-Qubit Entanglement

- `GHZ_STATE(qubits)` - Create GHZ state
- `QFT(qubits)` - Quantum Fourier Transform

### Algorithm Components

- `GROVER_ORACLE(target, qubits)` - Oracle for Grover's algorithm
- `GROVER_DIFFUSION(qubits)` - Diffusion operator
- `DJ_ORACLE_CONSTANT_0(qubits)` - Deutsch-Jozsa constant oracle
- `DJ_ORACLE_CONSTANT_1(y)` - Deutsch-Jozsa constant oracle
- `DJ_ORACLE_BALANCED_BIT(control, target, bit_index)` - Balanced oracle

### Utilities

- `SUPERPOSITION(qubits)` - Put all qubits in superposition
- `MEASURE_ALL(qubits)` - Measure all qubits
- `ALLOC_QUBITS(n, prefix, profile)` - Allocate n qubits

## Complete Examples

### Example 1: GHZ State (Pure ASM)

**Before (Python + ASM):**
```python
qubit_list = ", ".join([f"q{i}" for i in range(n_qubits)])
asm_lines = [
    f"alloc: ALLOC_LQ n={n_qubits}, profile=\"logical:Surface(d=3)\" -> {qubit_list}",
    "h0: APPLY_H q0",
]
for i in range(1, n_qubits):
    asm_lines.append(f"cnot{i}: APPLY_CNOT q0, q{i}")
asm = "\n".join(asm_lines)
return assemble(asm)
```

**After (Pure ASM with Macros):**
```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.set n_qubits = 4
.set qubit_list = [f"q{i}" for i in range(n_qubits)]

alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> {", ".join(qubit_list)}

; Create GHZ state
h0: APPLY_H q0
.for i in 1..n_qubits-1
    cnot{i}: APPLY_CNOT q0, q{i}
.endfor

; Measure all
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
```

### Example 2: Grover's Algorithm

**Pure ASM with Macros:**
```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.set n_qubits = 2
.set target = ["1", "1"]
.set n_iterations = 1

alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> q0, q1

; Initialize in superposition
h0: APPLY_H q0
h1: APPLY_H q1

; Grover iterations
.for iter in 0..n_iterations-1
    ; Oracle: mark target state
    .for i in 0..len(target)-1
        .if target[i] == "0"
            flip{iter}_{i}: APPLY_X q{i}
        .endif
    .endfor
    
    ; Controlled-Z
    h_cz{iter}: APPLY_H q1
    cnot_cz{iter}: APPLY_CNOT q0, q1
    h_cz2{iter}: APPLY_H q1
    
    ; Unflip
    .for i in 0..len(target)-1
        .if target[i] == "0"
            unflip{iter}_{i}: APPLY_X q{i}
        .endif
    .endfor
    
    ; Diffusion operator
    dh0{iter}: APPLY_H q0
    dh1{iter}: APPLY_H q1
    dx0{iter}: APPLY_X q0
    dx1{iter}: APPLY_X q1
    dh_cz{iter}: APPLY_H q1
    dcnot{iter}: APPLY_CNOT q0, q1
    dh_cz2{iter}: APPLY_H q1
    dx0_2{iter}: APPLY_X q0
    dx1_2{iter}: APPLY_X q1
    dh0_2{iter}: APPLY_H q0
    dh1_2{iter}: APPLY_H q1
.endfor

; Measure
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
```

### Example 3: Using Standard Library

```asm
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.include "stdlib.qvm.asm"

.set n = 4
.set qubits = [f"q{i}" for i in range(n)]

alloc: ALLOC_LQ n={n}, profile="logical:Surface(d=3)" -> {", ".join(qubits)}

; Create GHZ state using stdlib macro
GHZ_STATE(qubits)

; Measure all using stdlib macro
MEASURE_ALL(qubits)
```

## Variable Substitution

Variables are substituted using `{var}` syntax:

```asm
.set n = 4
.set prefix = "q"

; These will expand to: h0, h1, h2, h3
.for i in 0..n-1
    h{i}: APPLY_H {prefix}{i}
.endfor
```

## Evaluation Context

The macro system supports:

- **Arithmetic**: `n-1`, `2**i`, `pi/4`
- **String operations**: `f"q{i}"`, `", ".join(list)`
- **List comprehensions**: `[f"q{i}" for i in range(n)]`
- **Built-in functions**: `len()`, `range()`, `enumerate()`
- **Math constants**: `pi`, `math.sqrt()`, etc.

## Processing Phases

The macro preprocessor runs in these phases:

1. **Include** - Process `.include` directives
2. **Macro Definitions** - Parse and store `.macro` blocks
3. **Variables** - Process `.set` directives
4. **Loops** - Expand `.for` loops
5. **Conditionals** - Process `.if` statements
6. **Macro Calls** - Expand macro invocations
7. **Substitution** - Final variable substitution

## Best Practices

### 1. Use Descriptive Variable Names

```asm
.set n_counting_qubits = 3
.set work_qubit = "w0"
```

### 2. Comment Your Macros

```asm
.macro BELL_PAIR(q0, q1)
    ; Create Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2
    h: APPLY_H {q0}
    cnot: APPLY_CNOT {q0}, {q1}
.endmacro
```

### 3. Use Standard Library When Possible

```asm
.include "stdlib.qvm.asm"

; Use stdlib macros instead of reinventing
GHZ_STATE(my_qubits)
```

### 4. Keep Macros Focused

Each macro should do one thing well:

```asm
; Good: Focused macro
.macro HADAMARD_ALL(qubits)
    .for i in 0..len(qubits)-1
        h{i}: APPLY_H {qubits[i]}
    .endfor
.endmacro

; Better: Compose macros
HADAMARD_ALL(input_qubits)
GROVER_ORACLE(target, input_qubits)
HADAMARD_ALL(input_qubits)
```

## Integration with Python

You can still use Python to generate parameters:

```python
from qvm.tools.qvm_asm import assemble

def create_ghz_circuit(n_qubits):
    asm = f"""
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.set n_qubits = {n_qubits}
.set qubit_list = [f"q{{i}}" for i in range(n_qubits)]

alloc: ALLOC_LQ n={{n_qubits}}, profile="logical:Surface(d=3)" -> {{", ".join(qubit_list)}}

h0: APPLY_H q0
.for i in 1..n_qubits-1
    cnot{{i}}: APPLY_CNOT q0, q{{i}}
.endfor

.for i in 0..n_qubits-1
    m{{i}}: MEASURE_Z q{{i}} -> m{{i}}
.endfor
"""
    return assemble(asm)
```

## Debugging

To see the expanded assembly before parsing:

```python
from qvm.tools.qvm_asm_macros import preprocess

asm_with_macros = """
.set n = 2
.for i in 0..n-1
    h{i}: APPLY_H q{i}
.endfor
"""

expanded = preprocess(asm_with_macros)
print(expanded)
# Output:
# h0: APPLY_H q0
# h1: APPLY_H q1
```

## Limitations

1. **Variable scope**: Variables are global within a file
2. **Evaluation**: Uses Python `eval()` - be careful with untrusted input
3. **Recursion**: Macros cannot call themselves
4. **Complex conditionals**: Nested conditionals with variable substitution may need careful ordering

## Future Enhancements

Potential future additions:

- **Parameterized includes**: `.include "lib.asm" with n=4`
- **Macro overloading**: Multiple macros with same name, different arities
- **Local variables**: `.local` scope within macros
- **Assertions**: `.assert n > 0, "n must be positive"`
- **Debugging**: `.debug` directive to print variable values

## Summary

The macro system transforms QVM Assembly from a low-level representation to a high-level quantum circuit description language. Examples can now be written entirely in ASM, making them:

- ✅ **More concise** (70-80% less code)
- ✅ **More readable** (clear structure)
- ✅ **More maintainable** (easy to modify)
- ✅ **Reusable** (macros and includes)
- ✅ **Educational** (self-documenting)

**The QVM Assembly language is now a complete, powerful tool for quantum circuit development!**
