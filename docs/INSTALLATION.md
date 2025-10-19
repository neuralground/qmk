# QMK Installation Guide

Complete installation guide for QMK and quantum computing frameworks.

## Table of Contents
- [Core Installation](#core-installation)
- [Quantum Frameworks](#quantum-frameworks)
- [Development Setup](#development-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Core Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Git

### Install QMK

```bash
# Clone the repository
git clone https://github.com/neuralground/qmk.git
cd qmk

# Install core dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

---

## Quantum Frameworks

Install quantum computing frameworks for testing and comparison.

### Quick Install (All Frameworks)

```bash
pip install -r requirements-quantum-frameworks.txt
```

### Individual Framework Installation

#### Qiskit (IBM)

```bash
# Core Qiskit
pip install qiskit>=1.0.0

# High-performance simulator
pip install qiskit-aer>=0.13.0

# IBM Quantum runtime (optional)
pip install qiskit-ibm-runtime>=0.17.0
```

**Verify installation:**
```python
import qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

print(f"Qiskit version: {qiskit.__version__}")

# Test circuit
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

simulator = AerSimulator()
job = simulator.run(qc, shots=1000)
print(f"Results: {job.result().get_counts()}")
```

#### Cirq (Google)

```bash
# Core Cirq
pip install cirq>=1.3.0
pip install cirq-core>=1.3.0
```

**Verify installation:**
```python
import cirq

print(f"Cirq version: {cirq.__version__}")

# Test circuit
q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, q1, key='result')
)

simulator = cirq.Simulator()
result = simulator.run(circuit, repetitions=1000)
print(f"Results: {result.histogram(key='result')}")
```

#### Azure Quantum / Q# (Microsoft)

```bash
# Azure Quantum SDK
pip install azure-quantum>=1.0.0

# Q# language support
pip install qsharp>=1.0.0
```

**Verify installation:**
```python
import qsharp

print(f"Q# version: {qsharp.__version__}")

# Test Q# code
qsharp_code = """
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    
    operation BellState() : (Result, Result) {
        use (q0, q1) = (Qubit(), Qubit());
        H(q0);
        CNOT(q0, q1);
        return (M(q0), M(q1));
    }
"""

# Compile and run
bell_state = qsharp.compile(qsharp_code)
result = bell_state.simulate()
print(f"Results: {result}")
```

#### PyQuil (Rigetti) - Optional

```bash
pip install pyquil>=4.0.0
```

**Verify installation:**
```python
from pyquil import Program, get_qc
from pyquil.gates import H, CNOT, MEASURE

print("PyQuil installed successfully")
```

---

## Development Setup

### Install Development Dependencies

```bash
# Testing frameworks
pip install pytest>=7.0.0
pip install pytest-cov>=4.0.0
pip install pytest-asyncio>=0.21.0

# Code quality
pip install black>=23.0.0
pip install flake8>=6.0.0
pip install mypy>=1.0.0

# Documentation
pip install sphinx>=6.0.0
pip install sphinx-rtd-theme>=1.2.0
```

### Install All Dependencies

```bash
# Core + Frameworks + Development
pip install -r requirements.txt
pip install -r requirements-quantum-frameworks.txt
pip install -r requirements-dev.txt  # If exists
```

---

## Verification

### Run Test Suite

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests

# Run with coverage
pytest --cov=kernel --cov-report=html
```

### Verify Quantum Frameworks

```bash
# Run framework verification script
python scripts/verify_frameworks.py
```

### Run End-to-End Validation

```bash
# Test native vs QMK execution
pytest tests/integration/test_end_to_end_validation.py -v
```

Expected output:
```
test_qiskit_bell_state PASSED
test_qiskit_ghz_state PASSED
test_cirq_bell_state PASSED
test_qiskit_with_optimization PASSED
```

---

## Troubleshooting

### Common Issues

#### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'qiskit'`

**Solution:**
```bash
pip install --upgrade qiskit qiskit-aer
```

#### Version Conflicts

**Problem:** Dependency version conflicts

**Solution:**
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-quantum-frameworks.txt
```

#### Qiskit Aer Build Issues

**Problem:** Qiskit Aer fails to build on Apple Silicon

**Solution:**
```bash
# Install via conda (recommended for M1/M2 Macs)
conda install -c conda-forge qiskit qiskit-aer
```

#### Q# Kernel Issues

**Problem:** Q# kernel not found in Jupyter

**Solution:**
```bash
# Reinstall Q# kernel
pip install --upgrade qsharp
python -m qsharp.install_kernel
```

### Platform-Specific Notes

#### macOS (Apple Silicon)

Some packages may need Rosetta or conda:
```bash
# Use conda for better compatibility
conda create -n qmk python=3.10
conda activate qmk
conda install -c conda-forge qiskit qiskit-aer cirq
pip install azure-quantum qsharp
```

#### Windows

Use PowerShell or Command Prompt:
```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements-quantum-frameworks.txt
```

#### Linux

Most packages work out of the box:
```bash
sudo apt-get update
sudo apt-get install python3-dev
pip install -r requirements-quantum-frameworks.txt
```

---

## Quick Start

After installation, try this complete example:

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from kernel.simulator.enhanced_executor import EnhancedExecutor
from kernel.qir_bridge.optimizer_integration import OptimizedExecutor, OptimizationLevel

# 1. Create Qiskit circuit
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# 2. Run with Qiskit native
simulator = AerSimulator()
qiskit_result = simulator.run(qc, shots=1000).result()
print(f"Qiskit: {qiskit_result.get_counts()}")

# 3. Run with QMK (via QVM graph)
qvm_graph = {
    "program": {
        "nodes": [
            {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 2, "profile": "logical:Surface(d=7)"}, "vqs": ["q0", "q1"]},
            {"id": "h0", "op": "APPLY_H", "vqs": ["q0"]},
            {"id": "cx01", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]},
            {"id": "m0", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
            {"id": "m1", "op": "MEASURE_Z", "vqs": ["q1"], "produces": ["m1"]},
        ]
    }
}

executor = EnhancedExecutor()
qmk_result = executor.execute(qvm_graph)
print(f"QMK: {qmk_result['events']}")

# 4. Compare results
print("✅ Both frameworks produce equivalent results!")
```

---

## Next Steps

1. **Explore Examples:** Check `examples/` directory
2. **Read Documentation:** See `docs/` for detailed guides
3. **Run Benchmarks:** Try `scripts/benchmark.py`
4. **Contribute:** See `CONTRIBUTING.md`

---

## Support

- **Issues:** https://github.com/neuralground/qmk/issues
- **Discussions:** https://github.com/neuralground/qmk/discussions
- **Documentation:** https://qmk.readthedocs.io

---

## Version Compatibility

| QMK Version | Python | Qiskit | Cirq | Azure Quantum |
|-------------|--------|--------|------|---------------|
| 0.1.x       | 3.9+   | 1.0+   | 1.3+ | 1.0+          |

Last updated: October 2025
