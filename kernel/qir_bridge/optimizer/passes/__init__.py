"""
Optimization Passes

Collection of optimization passes for QIR circuits.
"""

from .gate_cancellation import GateCancellationPass

__all__ = [
    'GateCancellationPass',
]
