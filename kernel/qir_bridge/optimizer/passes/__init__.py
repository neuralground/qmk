"""
Optimization Passes

Collection of optimization passes for QIR circuits.
"""

from .gate_cancellation import GateCancellationPass
from .gate_commutation import GateCommutationPass
from .gate_fusion import GateFusionPass

__all__ = [
    'GateCancellationPass',
    'GateCommutationPass',
    'GateFusionPass',
]
