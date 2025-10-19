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
from .measurement_deferral import MeasurementDeferralPass
from .clifford_t_optimization import CliffordTPlusOptimizationPass
from .magic_state_optimization import MagicStateOptimizationPass
from .gate_teleportation import GateTeleportationPass

__all__ = [
    'GateCancellationPass',
    'GateCommutationPass',
    'GateFusionPass',
    'DeadCodeEliminationPass',
    'ConstantPropagationPass',
    'SWAPInsertionPass',
    'QubitMappingPass',
    'TemplateMatchingPass',
    'MeasurementDeferralPass',
    'CliffordTPlusOptimizationPass',
    'MagicStateOptimizationPass',
    'GateTeleportationPass',
]
