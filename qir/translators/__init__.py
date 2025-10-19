"""
QIR Translators

Front-end translators from various quantum frameworks to QIR.

Supported frameworks:
- Qiskit
- Cirq
"""

from .qiskit_to_qir import QiskitToQIR
from .cirq_to_qir import CirqToQIR

__all__ = ['QiskitToQIR', 'CirqToQIR']
