# QIR Examples from External Front-Ends

This directory contains quantum programs written in various high-level languages that can be compiled to QIR (Quantum Intermediate Representation) and then executed on QMK.

## Overview

QMK's QIR bridge enables seamless integration with existing quantum development tools:

- **Q#** (Microsoft Quantum Development Kit)
- **Qiskit** (IBM Quantum)
- **Cirq** (Google Quantum AI)
- **PyQIR** (Direct QIR generation)

## Directory Structure

```
qir_examples/
├── qsharp/          # Q# source files
├── qiskit/          # Qiskit Python scripts
├── cirq/            # Cirq Python scripts
├── pyqir/           # Direct PyQIR examples
└── scripts/         # Compilation and testing scripts
```

## Prerequisites

### Q# (qsc compiler)

```bash
# Install Q# compiler
dotnet tool install -g Microsoft.Quantum.Compiler

# Or use Azure Quantum Development Kit
pip install azure-quantum qsharp
```

### Qiskit with QIR

```bash
pip install qiskit qiskit-qir pyqir
```

### Cirq with QIR

```bash
pip install cirq cirq-qir
```

### PyQIR

```bash
pip install pyqir
```

## Usage

### Compile Q# to QIR

```bash
# Compile a Q# program to QIR
qsc build qsharp/BellState.qs --qir --output qsharp/BellState.ll

# Or use the provided script
./scripts/compile_qsharp.sh qsharp/BellState.qs
```

### Generate QIR from Qiskit

```bash
# Run Qiskit script to generate QIR
python qiskit/bell_state.py --output qiskit/bell_state.ll

# Or use the provided script
./scripts/compile_qiskit.sh qiskit/bell_state.py
```

### Generate QIR from Cirq

```bash
# Run Cirq script to generate QIR
python cirq/bell_state.py --output cirq/bell_state.ll

# Or use the provided script
./scripts/compile_cirq.sh cirq/bell_state.py
```

## End-to-End Workflow

### 1. Write Quantum Program

Choose your preferred front-end and write your quantum algorithm.

### 2. Compile to QIR

Use the appropriate compiler to generate QIR:

```bash
# Q#
qsc build qsharp/BellState.qs --qir --output qsharp/BellState.ll

# Qiskit
python qiskit/bell_state.py --output qiskit/bell_state.ll

# Cirq
python cirq/bell_state.py --output cirq/bell_state.ll
```

### 3. Convert QIR to QVM

Use QMK's QIR bridge:

```bash
python -c "
from kernel.qir_bridge import QIRParser, QVMGraphGenerator
import json

# Parse QIR
parser = QIRParser()
with open('qsharp/BellState.ll') as f:
    functions = parser.parse(f.read())

# Generate QVM graph
generator = QVMGraphGenerator()
graph = generator.generate(functions['QMK__Examples__BellState__body'])

# Save as QVM JSON
with open('bell_state.qvm.json', 'w') as f:
    json.dump(graph, f, indent=2)
"
```

### 4. Execute on QMK

```bash
# Start QMK server
python -m kernel.qmk_server

# Execute the QVM graph
python examples/execute_qvm_graph.py bell_state.qvm.json
```

## Automated Testing

The test suite automatically compiles examples from all front-ends and verifies the QIR bridge:

```bash
# Run QIR integration tests
python -m pytest tests/integration/test_qir_frontends.py -v

# This will:
# 1. Detect available compilers (Q#, Qiskit, Cirq)
# 2. Compile example programs to QIR
# 3. Parse QIR and generate QVM graphs
# 4. Verify correctness
# 5. Clean up generated files
```

## Examples

### Q# Examples

- **BellState.qs** - Bell state preparation
- **Teleportation.qs** - Quantum teleportation protocol
- **GroverSearch.qs** - Grover's search algorithm
- **QFT.qs** - Quantum Fourier Transform

### Qiskit Examples

- **bell_state.py** - Bell state using Qiskit
- **vqe_h2.py** - VQE for H2 molecule
- **qaoa_maxcut.py** - QAOA for MaxCut problem

### Cirq Examples

- **bell_state.py** - Bell state using Cirq
- **supremacy_circuit.py** - Random circuit sampling
- **phase_estimation.py** - Quantum phase estimation

### PyQIR Examples

- **direct_qir.py** - Direct QIR generation
- **custom_gates.py** - Custom gate decompositions

## CI/CD Integration

The repository includes GitHub Actions workflows that:

1. Install required compilers (when available)
2. Compile all example programs
3. Run QIR bridge tests
4. Verify end-to-end functionality

See `.github/workflows/qir-integration.yml` for details.

## Notes

- **Generated QIR files (*.ll) are not committed to the repository**
- They are generated on-demand during testing
- Add `*.ll` to `.gitignore` to prevent accidental commits
- Source files (.qs, .py) are version controlled

## Troubleshooting

### Q# Compiler Not Found

```bash
# Install Q# compiler
dotnet tool install -g Microsoft.Quantum.Compiler

# Or use Docker
docker run -v $(pwd):/workspace mcr.microsoft.com/quantum/qsharp-compiler
```

### Qiskit QIR Not Available

```bash
# Ensure you have the QIR plugin
pip install qiskit-qir pyqir-generator
```

### Cirq QIR Not Available

```bash
# Install Cirq QIR support
pip install cirq-qir
```

## Contributing

When adding new examples:

1. Add source files to the appropriate directory
2. Update the compilation scripts if needed
3. Add tests to verify QIR generation
4. Document any special requirements

## References

- [QIR Specification](https://github.com/qir-alliance/qir-spec)
- [Q# Documentation](https://docs.microsoft.com/quantum)
- [Qiskit QIR](https://qiskit.org/documentation/qir/)
- [Cirq Documentation](https://quantumai.google/cirq)
- [QMK QIR Bridge](../docs/QIR-BRIDGE.md)
