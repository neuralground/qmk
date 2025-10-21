"""
QIR Translators

Front-end translators from various quantum frameworks to QIR.

Supported frameworks:
- Qiskit
- Cirq
"""

from .qiskit_to_qir import QiskitToQIRConverter
from .cirq_to_qir import CirqToQIRConverter

__all__ = ['QiskitToQIRConverter', 'CirqToQIRConverter']
