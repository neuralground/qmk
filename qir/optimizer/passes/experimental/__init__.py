"""
Experimental Optimization Passes

EXPERIMENTAL: These passes implement cutting-edge research techniques
that may not be fully stable or production-ready. Use with caution.

These passes represent the state-of-the-art in quantum circuit optimization
and are based on recent research papers (2018-2024).
"""

from .zx_calculus_optimization import ZXCalculusOptimizationPass
from .phase_polynomial_optimization import PhasePolynomialOptimizationPass
from .synthesis_based_optimization import SynthesisBasedOptimizationPass
from .pauli_network_synthesis import PauliNetworkSynthesisPass
from .tensor_network_contraction import TensorNetworkContractionPass

__all__ = [
    'ZXCalculusOptimizationPass',
    'PhasePolynomialOptimizationPass',
    'SynthesisBasedOptimizationPass',
    'PauliNetworkSynthesisPass',
    'TensorNetworkContractionPass',
]
