#!/bin/bash
# Setup script for quantum computing frameworks

set -e  # Exit on error

echo "=========================================="
echo "QMK Quantum Frameworks Setup"
echo "=========================================="
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment is active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo
    echo "⚠️  Warning: No virtual environment detected"
    echo "It's recommended to use a virtual environment:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
    echo
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo
echo "Installing quantum computing frameworks..."
echo

# Install frameworks
pip install --upgrade pip

echo "→ Installing Qiskit..."
pip install qiskit>=1.0.0 qiskit-aer>=0.13.0

echo "→ Installing Cirq..."
pip install cirq>=1.3.0

echo "→ Installing Azure Quantum / Q#..."
pip install azure-quantum>=1.0.0 qsharp>=1.0.0

echo "→ Installing optional frameworks..."
pip install pyquil>=4.0.0 || echo "⚠️  PyQuil installation failed (optional)"

echo
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo

# Run verification
echo "Running verification..."
python3 scripts/verify_frameworks.py

echo
echo "Setup complete! 🎉"
echo
echo "Next steps:"
echo "  1. Run tests: pytest tests/integration/test_end_to_end_validation.py -v"
echo "  2. Try examples: python examples/bell_state.py"
echo "  3. Read docs: cat docs/INSTALLATION.md"
echo
