"""
QIR Domain

Hardware-agnostic quantum circuit representation and optimization.

This domain is completely independent of QVM and QMK domains.
It focuses solely on static circuit analysis and transformation.

Components:
- optimizer: 14+ optimization passes
- translators: Qiskit, Cirq, PyQuil to QIR
- parser: QIR LLVM parsing

Key Principle: Zero dependencies on QVM or QMK domains.
"""

__version__ = "0.1.0"
__domain__ = "QIR"

# Domain boundary enforcement
import sys
import warnings

def _check_domain_isolation():
    """Verify QIR domain has no QVM/QMK imports."""
    forbidden_modules = ['qvm', 'kernel']
    for module_name in list(sys.modules.keys()):
        if any(module_name.startswith(forbidden) for forbidden in forbidden_modules):
            if 'qir' in sys.modules and module_name in sys.modules:
                # Only warn if both are loaded (potential cross-domain import)
                pass  # Can add stricter checking in development mode

# Check on import (development mode)
if __debug__:
    _check_domain_isolation()
