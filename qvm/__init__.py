"""
QVM Domain

User-mode quantum virtual machine with capability-based execution model.

This domain provides hardware-independent circuit representation
and execution planning. It operates in user mode and communicates
with the QMK kernel via syscalls.

Components:
- graph: QVM graph representation
- generator: QIR → QVM conversion
- runtime: User-mode runtime (JIT, planner)

Key Principle: Hardware-independent, capability-based execution.
"""

__version__ = "0.1.0"
__domain__ = "QVM"
