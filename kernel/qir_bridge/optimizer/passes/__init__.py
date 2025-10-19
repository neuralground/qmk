"""
Optimization Passes

Collection of optimization passes for QIR circuits.
"""

from .gate_cancellation import GateCancellationPass
from .gate_commutation import GateCommutationPass
from .gate_fusion import GateFusionPass
from .dead_code_elimination import DeadCodeEliminationPass
from .constant_propagation import ConstantPropagationPass

__all__ = [
    'GateCancellationPass',
    'GateCommutationPass',
    'GateFusionPass',
    'DeadCodeEliminationPass',
    'ConstantPropagationPass',
]
