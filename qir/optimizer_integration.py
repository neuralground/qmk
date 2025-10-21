"""
QIR Optimizer Integration

Integrates the QIR optimizer with the QMK executor.
Provides OptimizedExecutor that automatically optimizes circuits before execution.
"""

from enum import Enum
from typing import Dict, Any, Optional
from .optimizer import PassManager, QIRCircuit
from .optimizer.passes import GateCancellationPass, GateCommutationPass
from .optimizer.converters import QVMToIRConverter, IRToQVMConverter


class OptimizationLevel(Enum):
    """Optimization levels for circuit optimization."""
    NONE = 0
    BASIC = 1
    STANDARD = 2
    AGGRESSIVE = 3


class OptimizedExecutor:
    """
    Executor that automatically optimizes circuits before execution.
    
    Wraps an EnhancedExecutor and applies optimization passes based on
    the specified optimization level.
    """
    
    def __init__(self, executor, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        """
        Initialize optimized executor.
        
        Args:
            executor: EnhancedExecutor instance to wrap
            optimization_level: Level of optimization to apply
        """
        self.executor = executor
        self.optimization_level = optimization_level
        self.pass_manager = self._create_pass_manager()
    
    def _create_pass_manager(self) -> PassManager:
        """Create pass manager based on optimization level."""
        pm = PassManager()
        
        if self.optimization_level == OptimizationLevel.NONE:
            # No optimization
            pass
        elif self.optimization_level == OptimizationLevel.BASIC:
            # Basic gate cancellation
            pm.add_pass(GateCancellationPass())
        elif self.optimization_level == OptimizationLevel.STANDARD:
            # Gate cancellation + commutation
            pm.add_pass(GateCommutationPass())
            pm.add_pass(GateCancellationPass())
        elif self.optimization_level == OptimizationLevel.AGGRESSIVE:
            # Multiple rounds of optimization
            pm.add_pass(GateCommutationPass())
            pm.add_pass(GateCancellationPass())
            pm.add_pass(GateCommutationPass())
            pm.add_pass(GateCancellationPass())
        
        return pm
    
    def execute(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute QVM graph with optimization.
        
        Args:
            qvm_graph: QVM graph to execute
        
        Returns:
            Execution result
        """
        if self.optimization_level == OptimizationLevel.NONE:
            # No optimization - execute directly
            return self.executor.execute(qvm_graph)
        
        # Convert QVM to IR
        converter = QVMToIRConverter()
        ir_circuit = converter.convert(qvm_graph)
        
        # Apply optimization passes
        optimized_circuit = self.pass_manager.run(ir_circuit)
        
        # Convert back to QVM
        qvm_converter = IRToQVMConverter()
        optimized_qvm = qvm_converter.convert(optimized_circuit)
        
        # Execute optimized circuit
        return self.executor.execute(optimized_qvm)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the optimization.
        
        Returns:
            Dictionary with optimization statistics
        """
        return {
            'level': self.optimization_level.name,
            'passes': [pass_.__class__.__name__ for pass_ in self.pass_manager.passes]
        }
