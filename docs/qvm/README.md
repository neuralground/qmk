# QVM Domain Documentation

Quantum Virtual Machine (QVM) - Graph format and execution model.

## Overview

The QVM domain defines the quantum virtual machine specification, instruction set, and execution model. QVM uses a graph-based representation with resource handles and linearity verification.

## Key Documents

1. **[QVM Specification](SPECIFICATION.md)** ⭐
   - Complete QVM specification
   - Resource handles (VQ, CH, EV, CAP, BND)
   - Graph structure and format
   - Verification rules
   - Execution semantics

2. **[Instruction Reference](INSTRUCTION_REFERENCE.md)**
   - All 20 operations documented
   - Capability requirements
   - Reversibility classification
   - Examples for each operation

3. **[Assembly Language](ASSEMBLY_LANGUAGE.md)**
   - Human-readable QVM assembly
   - Simpler syntax than JSON
   - Full round-trip conversion
   - Assembler and disassembler tools

4. **[Measurement Bases](MEASUREMENT_BASES.md)**
   - Measurement basis documentation
   - Supported bases (Z, X, Y, Bell)

## Quick Start

```json
{
  "program": {
    "nodes": [
      {
        "id": "n1",
        "op": "ALLOC_LQ",
        "vqs": ["vq0"],
        "args": {"profile": "logical:surface_code(d=7)"}
      },
      {
        "id": "n2",
        "op": "APPLY_H",
        "vqs": ["vq0"],
        "args": {}
      },
      {
        "id": "n3",
        "op": "MEASURE_Z",
        "vqs": ["vq0"],
        "produces": ["ev0"],
        "args": {}
      }
    ]
  }
}
```

## Features

### Resource Handles
- **VQ** (Virtual Qubit): Logical qubits
- **CH** (Channel): Cross-tenant entanglement
- **EV** (Event): Measurement outcomes
- **CAP** (Capability): Operation permissions
- **BND** (Bond): Magic state resources

### Operations (20 total)
- Allocation: ALLOC_LQ, FREE_LQ
- Gates: APPLY_H, APPLY_X, APPLY_Y, APPLY_Z, APPLY_S, APPLY_T, APPLY_CNOT, APPLY_CZ, APPLY_SWAP, APPLY_RZ
- Measurements: MEASURE_Z, MEASURE_X, MEASURE_BELL
- Channels: OPEN_CHAN, CLOSE_CHAN
- Magic States: INJECT_T_STATE
- Teleportation: TELEPORT_CNOT
- Reversibility: BEGIN_REV, END_REV

### Verification
- Linearity checking (use-once semantics)
- Capability verification
- DAG validation
- Type checking

## Tools

- **Validator**: `qvm/tools/qvm_validate.py`
- **Assembler**: `qvm/tools/qvm_asm.py`
- **Disassembler**: `qvm/tools/qvm_disasm.py`

## Examples

See `qvm/examples/` for complete examples:
- Bell state preparation
- Quantum teleportation
- GHZ state
- Conditional correction
- Reversible segments

## See Also

- [Main Documentation Index](../INDEX.md)
- [QIR Domain](../qir/)
- [QMK Domain](../qmk/)
