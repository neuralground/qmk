"""
Optimization Passes

Collection of optimization passes for QIR circuits.
"""

from .gate_cancellation import GateCancellationPass
from .gate_commutation import GateCommutationPass
from .gate_fusion import GateFusionPass
from .dead_code_elimination import DeadCodeEliminationPass
from .constant_propagation import ConstantPropagationPass
from .swap_insertion import SWAPInsertionPass
from .qubit_mapping import QubitMappingPass
from .template_matching import TemplateMatchingPass

__all__ = [
    'GateCancellationPass',
    'GateCommutationPass',
    'GateFusionPass',
    'DeadCodeEliminationPass',
    'ConstantPropagationPass',
    'SWAPInsertionPass',
    'QubitMappingPass',
    'TemplateMatchingPass',
]
