"""
QIR Optimization Framework

Provides infrastructure for QIR-to-QIR optimizations with validation.
"""

from .ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType
from .pass_base import OptimizationPass, PassManager
from .metrics import OptimizationMetrics
from .converters import QIRToIRConverter, IRToQVMConverter, QVMToIRConverter

__all__ = [
    'QIRCircuit',
    'QIRInstruction', 
    'QIRQubit',
    'InstructionType',
    'OptimizationPass',
    'PassManager',
    'OptimizationMetrics',
    'QIRToIRConverter',
    'IRToQVMConverter',
    'QVMToIRConverter',
]
