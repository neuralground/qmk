# QVM Assembly Language

**Version 0.1**

QVM Assembly Language provides a human-readable, text-based format for writing QVM programs. It offers a simpler syntax than JSON while maintaining full round-trip conversion capability.

---

## Table of Contents

1. [Overview](#overview)
2. [Syntax](#syntax)
3. [Directives](#directives)
4. [Instructions](#instructions)
5. [Examples](#examples)
6. [Tools](#tools)
7. [Comparison with JSON](#comparison-with-json)

---

## Overview

### Why Assembly Language?

- **Readable**: Much easier to read and write than JSON
- **Concise**: Less verbose, fewer braces and quotes
- **Round-trip**: Perfect conversion to/from JSON
- **Comments**: Native support for comments
- **Version control friendly**: Better diffs in git

### Design Principles

- One instruction per line
- Labels identify nodes
- Natural syntax for common patterns
- Full feature parity with JSON format

---

## Syntax

### Basic Structure

```asm
.version 0.1
.caps CAP_ALLOC CAP_TELEPORT

; Comment
label: OPCODE operands... -> outputs [guard] [caps]
```

### Line Format

```
label: OPCODE arg1, arg2, ... -> out1, out2 if condition [CAP_X]
  │      │      │                  │            │            │
  │      │      │                  │            │            └─ Capabilities (optional)
  │      │      │                  │            └─ Guard condition (optional)
  │      │      │                  └─ Output resources (optional)
  │      │      └─ Operands (qubits, channels, args)
  │      └─ Operation code
  └─ Node identifier
```

### Comments

```asm
; Full line comment

alloc: ALLOC_LQ n=2 -> q0, q1  ; Inline comment
```

---

## Directives

Directives start with `.` and configure the program.

### `.version`

Specifies the QVM version.

```asm
.version 0.1
```

### `.caps`

Declares required capabilities.

```asm
.caps CAP_ALLOC CAP_TELEPORT CAP_MAGIC
```

---

## Instructions

### Allocation

Allocate logical qubits with QEC profile.

```asm
alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
```

**Syntax**: `label: ALLOC_LQ n=<count>, profile="<profile>" -> <qubit_list> [CAP_ALLOC]`

### Single-Qubit Gates

```asm
h: APPLY_H q0
x: APPLY_X q0
y: APPLY_Y q0
z: APPLY_Z q0
s: APPLY_S q0
```

**Syntax**: `label: <GATE> <qubit>`

### Two-Qubit Gates

```asm
cnot: APPLY_CNOT q0, q1  ; control, target
```

**Syntax**: `label: APPLY_CNOT <control>, <target>`

### Measurements

```asm
m0: MEASURE_Z q0 -> m0
m1: MEASURE_X q1 -> m1
```

**Syntax**: `label: MEASURE_<BASIS> <qubit> -> <event>`

### Conditional Operations (Guards)

Execute operation only if condition is true.

```asm
; Simple condition
corr: APPLY_X q1 if m0==1

; AND condition
corr: APPLY_X q2 if m0==1 && m1==0

; OR condition
corr: APPLY_Z q2 if m0==1 || m1==1
```

**Syntax**: `label: <OP> <operands> if <event>==<value>`

### Fences

```asm
fence: FENCE_EPOCH
```

### Deallocation

```asm
free: FREE_LQ q0, q1, q2
```

**Syntax**: `label: FREE_LQ <qubit_list>`

---

## Examples

### Example 1: Bell State

```asm
.version 0.1
.caps CAP_ALLOC

; Simple Bell state preparation
; Creates |Φ+⟩ = (|00⟩ + |11⟩)/√2

alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
h: APPLY_H q0
cnot: APPLY_CNOT q0, q1
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
free: FREE_LQ q0, q1
```

### Example 2: GHZ State

```asm
.version 0.1
.caps CAP_ALLOC

; 3-qubit GHZ state
; |GHZ⟩ = (|000⟩ + |111⟩)/√2

alloc: ALLOC_LQ n=3, profile="logical:surface_code(d=5)" -> q0, q1, q2 [CAP_ALLOC]
h: APPLY_H q0
cnot1: APPLY_CNOT q0, q1
cnot2: APPLY_CNOT q0, q2
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
m2: MEASURE_Z q2 -> m2
free: FREE_LQ q0, q1, q2
```

### Example 3: Quantum Teleportation

```asm
.version 0.1
.caps CAP_ALLOC

; Quantum teleportation protocol
; Teleports state of q0 to q2 using entangled pair (q1, q2)

; Allocate qubits
alloc: ALLOC_LQ n=3, profile="logical:surface_code(d=3)" -> q0, q1, q2 [CAP_ALLOC]

; Prepare state to teleport on q0 (example: |+⟩)
prep: APPLY_H q0

; Create Bell pair between q1 and q2
bell_h: APPLY_H q1
bell_cnot: APPLY_CNOT q1, q2

; Bell measurement on q0 and q1
cnot_meas: APPLY_CNOT q0, q1
h_meas: APPLY_H q0
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1

; Conditional corrections on q2 based on measurement results
fence: FENCE_EPOCH
corr_x: APPLY_X q2 if m1==1
corr_z: APPLY_Z q2 if m0==1

; Verify teleportation
m2: MEASURE_Z q2 -> m2

; Cleanup
free: FREE_LQ q0, q1, q2
```

### Example 4: Conditional Error Correction

```asm
.version 0.1
.caps CAP_ALLOC

; Simple error correction with syndrome measurement

alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> data, ancilla [CAP_ALLOC]

; Prepare state
h_data: APPLY_H data

; Syndrome extraction
cnot: APPLY_CNOT data, ancilla
syndrome: MEASURE_Z ancilla -> s0

; Conditional correction
fence: FENCE_EPOCH
corr: APPLY_X data if s0==1

; Final measurement
final: MEASURE_Z data -> result

free: FREE_LQ data, ancilla
```

---

## Tools

### Assembler: `qvm_asm.py`

Convert assembly to JSON.

```bash
# Output to stdout
python qvm/tools/qvm_asm.py program.qvm.asm

# Output to file
python qvm/tools/qvm_asm.py program.qvm.asm program.qvm.json
```

### Disassembler: `qvm_disasm.py`

Convert JSON to assembly.

```bash
# Output to stdout
python qvm/tools/qvm_disasm.py program.qvm.json

# Output to file
python qvm/tools/qvm_disasm.py program.qvm.json program.qvm.asm
```

### Round-Trip Conversion

```bash
# JSON → Assembly → JSON
python qvm/tools/qvm_disasm.py original.qvm.json temp.qvm.asm
python qvm/tools/qvm_asm.py temp.qvm.asm reconstructed.qvm.json

# Assembly → JSON → Assembly
python qvm/tools/qvm_asm.py original.qvm.asm temp.qvm.json
python qvm/tools/qvm_disasm.py temp.qvm.json reconstructed.qvm.asm
```

---

## Comparison with JSON

### Assembly (12 lines)

```asm
.version 0.1
.caps CAP_ALLOC

alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
h: APPLY_H q0
cnot: APPLY_CNOT q0, q1
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
free: FREE_LQ q0, q1
```

### JSON (80 lines)

```json
{
  "version": "0.1",
  "program": {
    "nodes": [
      {
        "id": "alloc",
        "op": "ALLOC_LQ",
        "args": {
          "n": 2,
          "profile": "logical:surface_code(d=3)"
        },
        "vqs": ["q0", "q1"],
        "caps": ["CAP_ALLOC"]
      },
      {
        "id": "h",
        "op": "APPLY_H",
        "vqs": ["q0"]
      },
      {
        "id": "cnot",
        "op": "APPLY_CNOT",
        "vqs": ["q0", "q1"]
      },
      {
        "id": "m0",
        "op": "MEASURE_Z",
        "vqs": ["q0"],
        "produces": ["m0"]
      },
      {
        "id": "m1",
        "op": "MEASURE_Z",
        "vqs": ["q1"],
        "produces": ["m1"]
      },
      {
        "id": "free",
        "op": "FREE_LQ",
        "vqs": ["q0", "q1"]
      }
    ]
  },
  "resources": {
    "vqs": ["q0", "q1"],
    "chs": [],
    "events": ["m0", "m1"]
  },
  "caps": ["CAP_ALLOC"]
}
```

**Result**: Assembly is **85% shorter** and much more readable!

---

## Syntax Reference

### Operand Types

| Type | Prefix | Example | Description |
|------|--------|---------|-------------|
| Qubit | any | `q0`, `qA`, `data` | Virtual qubit handle |
| Channel | `ch` | `ch0`, `ch_AB` | Entanglement channel |
| Event | `ev` or output | `m0`, `ev_ready` | Measurement event |

### Guard Operators

| Operator | Syntax | Example |
|----------|--------|---------|
| Equality | `==` | `if m0==1` |
| AND | `&&` | `if m0==1 && m1==0` |
| OR | `\|\|` | `if m0==1 \|\| m1==1` |

### Argument Syntax

```asm
; Named arguments
op: OPCODE key1=value1, key2="string", key3=123

; Positional arguments (qubits)
op: OPCODE q0, q1, q2

; Mixed
op: OPCODE n=2, profile="surface_code(d=3)", q0, q1
```

---

## Best Practices

### 1. Use Descriptive Labels

```asm
; Good
bell_prep: APPLY_H q0
entangle: APPLY_CNOT q0, q1

; Bad
n1: APPLY_H q0
n2: APPLY_CNOT q0, q1
```

### 2. Add Comments

```asm
; Prepare Bell pair
h: APPLY_H q0
cnot: APPLY_CNOT q0, q1

; Measure both qubits
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
```

### 3. Group Related Operations

```asm
; === State Preparation ===
alloc: ALLOC_LQ n=3 -> q0, q1, q2 [CAP_ALLOC]
init: APPLY_H q0

; === Entanglement ===
cnot1: APPLY_CNOT q0, q1
cnot2: APPLY_CNOT q0, q2

; === Measurement ===
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
m2: MEASURE_Z q2 -> m2
```

### 4. Use Consistent Naming

```asm
; Qubits: q0, q1, q2 or descriptive names
; Events: m0, m1, m2 or descriptive names
; Labels: snake_case or descriptive
```

---

## Language Grammar (EBNF)

```ebnf
program     ::= directive* instruction*
directive   ::= "." identifier value*
instruction ::= label ":" opcode operands? outputs? guard? caps?
label       ::= identifier
opcode      ::= identifier
operands    ::= operand ("," operand)*
operand     ::= argument | identifier
argument    ::= identifier "=" value
outputs     ::= "->" identifier ("," identifier)*
guard       ::= "if" condition
condition   ::= simple_cond | and_cond | or_cond
simple_cond ::= identifier "==" number
and_cond    ::= condition "&&" condition
or_cond     ::= condition "||" condition
caps        ::= "[" identifier ("," identifier)* "]"
value       ::= number | string | identifier
```

---

## Future Extensions

Potential future additions to the assembly language:

- **Macros**: Define reusable instruction sequences
- **Variables**: Symbolic names for parameters
- **Includes**: Import other assembly files
- **Assertions**: Runtime checks for debugging
- **Optimization hints**: Directives for the compiler

---

## References

- [QVM Specification](QVM-spec.md)
- [QVM Instruction Reference](QVM-instruction-reference.md)
- [QVM Examples](../qvm/examples/)

---

**End of QVM Assembly Language Documentation**
