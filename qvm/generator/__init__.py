"""
QVM Generator

Converts QIR circuits to QVM graph format.

This is the bridge between the QIR domain (hardware-agnostic optimization)
and the QVM domain (capability-based execution model).
"""

from .qvm_generator import QVMGenerator

__all__ = ['QVMGenerator']
