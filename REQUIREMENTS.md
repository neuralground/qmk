# QMK Requirements Guide

This document explains the different requirements files and how to use them.

## Requirements Files

### `requirements.txt` - Full Installation
**Use for:** Production deployment, full feature set

Includes:
- ✅ All quantum frameworks (Qiskit, Cirq, Azure Quantum, PyQuil)
- ✅ Testing frameworks (pytest, coverage)
- ✅ Code quality tools (black, flake8, mypy)
- ✅ Scientific computing (numpy, scipy, sympy)
- ✅ Visualization (matplotlib, seaborn, plotly)
- ✅ Development tools (Jupyter, IPython)
- ✅ Documentation (Sphinx)
- ✅ Utilities (pydantic, structlog, rich)

```bash
pip install -r requirements.txt
```

### `requirements-minimal.txt` - Minimal Installation
**Use for:** CI/CD, quick testing, minimal environments

Includes only:
- ✅ Core testing (pytest)
- ✅ Essential quantum (Qiskit + Aer)
- ✅ Scientific computing (numpy, scipy)
- ✅ Data validation (pydantic, jsonschema)

```bash
pip install -r requirements-minimal.txt
```

### `requirements-dev.txt` - Development Installation
**Use for:** Active development, contributing to QMK

Includes everything from `requirements.txt` plus:
- ✅ Advanced testing (pytest-benchmark, hypothesis)
- ✅ Code analysis (coverage, radon, bandit)
- ✅ Pre-commit hooks
- ✅ Profiling tools (line-profiler, memory-profiler)
- ✅ Advanced documentation tools
- ✅ Build tools (build, twine, wheel)

```bash
pip install -r requirements-dev.txt
```

### `requirements-quantum-frameworks.txt` - Quantum Only
**Use for:** When you only need quantum frameworks

Includes:
- ✅ Qiskit (IBM)
- ✅ Cirq (Google)
- ✅ Azure Quantum (Microsoft)
- ✅ PyQuil (Rigetti)
- ✅ Basic scientific computing

```bash
pip install -r requirements-quantum-frameworks.txt
```

## Installation Guide

### For Users

**Quick start (minimal):**
```bash
pip install -r requirements-minimal.txt
```

**Full installation:**
```bash
pip install -r requirements.txt
```

### For Developers

**Development setup:**
```bash
# Install all dev dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### For CI/CD

**GitHub Actions:**
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements-minimal.txt
```

## Dependency Management

### Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade qiskit
```

### Checking Installed Versions

```bash
# List all installed packages
pip list

# Show specific package info
pip show qiskit

# Check for outdated packages
pip list --outdated
```

### Creating Virtual Environment

**Recommended for development:**

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install requirements
pip install -r requirements-dev.txt
```

## Package Categories

### Testing
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-xdist` - Parallel testing

### Code Quality
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pylint` - Additional linting

### Quantum Frameworks
- `qiskit` - IBM Quantum
- `cirq` - Google Quantum
- `azure-quantum` - Microsoft Quantum
- `pyquil` - Rigetti Quantum

### Scientific Computing
- `numpy` - Numerical arrays
- `scipy` - Scientific algorithms
- `sympy` - Symbolic math
- `matplotlib` - Plotting

### Development Tools
- `jupyter` - Notebooks
- `ipython` - Enhanced shell
- `sphinx` - Documentation
- `pre-commit` - Git hooks

## Optional Dependencies

Some packages are commented out in `requirements.txt`:

### Performance
```bash
# Uncomment in requirements.txt or install separately
pip install numba cython networkx
```

### Machine Learning
```bash
# For quantum ML applications
pip install torch tensorflow pennylane
```

## Troubleshooting

### Installation Failures

**Qiskit issues:**
```bash
# Try installing without dependencies first
pip install --no-deps qiskit
pip install -r requirements-minimal.txt
```

**Azure Quantum issues:**
```bash
# Azure Quantum may require additional setup
pip install azure-quantum --upgrade
```

**Compilation errors:**
```bash
# Install build tools
pip install --upgrade setuptools wheel
```

### Dependency Conflicts

```bash
# Create fresh environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt
```

### Version Pinning

For reproducible environments, pin versions:
```bash
# Generate pinned requirements
pip freeze > requirements-pinned.txt

# Install from pinned
pip install -r requirements-pinned.txt
```

## CI/CD Usage

### GitHub Actions

**Main tests:**
```yaml
pip install -r requirements-minimal.txt
python run_tests.py
```

**Qiskit tests:**
```yaml
pip install -r requirements-minimal.txt
python run_qiskit_tests.py
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt

COPY . .
CMD ["python", "run_tests.py"]
```

## Best Practices

1. **Use virtual environments** - Always isolate dependencies
2. **Pin versions for production** - Use `pip freeze` for reproducibility
3. **Minimal for CI** - Use `requirements-minimal.txt` for faster builds
4. **Full for development** - Use `requirements-dev.txt` for all tools
5. **Update regularly** - Keep dependencies current for security
6. **Test after updates** - Run full test suite after updating

## Summary

| File | Use Case | Install Time | Size |
|------|----------|--------------|------|
| `requirements-minimal.txt` | CI/CD, testing | ~2 min | ~200 MB |
| `requirements.txt` | Production, users | ~5 min | ~500 MB |
| `requirements-dev.txt` | Development | ~7 min | ~700 MB |
| `requirements-quantum-frameworks.txt` | Quantum only | ~4 min | ~400 MB |

Choose the right requirements file for your use case to optimize installation time and disk space.
