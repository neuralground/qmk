"""
Optimizer Integration for QMK Execution Pipeline

Integrates the QIR optimizer into the QMK execution flow.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from .optimizer import (
    QIRCircuit, PassManager, OptimizationMetrics,
    QIRToIRConverter, IRToQVMConverter
)
from .optimizer.passes import (
    GateCancellationPass,
    GateCommutationPass,
    GateFusionPass,
    DeadCodeEliminationPass,
    ConstantPropagationPass,
    SWAPInsertionPass,
    QubitMappingPass,
    TemplateMatchingPass,
    MeasurementDeferralPass,
    CliffordTPlusOptimizationPass,
    MagicStateOptimizationPass,
    GateTeleportationPass,
    UncomputationOptimizationPass,
    LatticeSurgeryOptimizationPass,
)
from .optimizer.topology import HardwareTopology


class OptimizationLevel(Enum):
    """Optimization levels."""
    NONE = 0          # No optimization
    BASIC = 1         # Basic gate-level optimizations
    STANDARD = 2      # Gate + circuit-level optimizations
    AGGRESSIVE = 3    # All optimizations except FTQC
    FTQC = 4          # Full fault-tolerant optimization


class OptimizedExecutor:
    """
    Wrapper that adds optimization to QMK execution.
    
    Integrates the QIR optimizer into the execution pipeline:
    QIR → Optimize → QVM → Execute
    """
    
    def __init__(
        self,
        executor,
        optimization_level: OptimizationLevel = OptimizationLevel.STANDARD,
        topology: Optional[HardwareTopology] = None,
        custom_passes: Optional[List] = None
    ):
        """
        Initialize optimized executor.
        
        Args:
            executor: Base executor (e.g., EnhancedExecutor)
            optimization_level: Level of optimization to apply
            topology: Hardware topology for topology-aware passes
            custom_passes: Custom optimization passes
        """
        self.executor = executor
        self.optimization_level = optimization_level
        self.topology = topology or HardwareTopology.all_to_all(100)
        self.custom_passes = custom_passes
        
        # Build pass manager based on level
        self.pass_manager = self._build_pass_manager()
        
        # Track metrics
        self.last_metrics: Optional[Dict[str, Any]] = None
    
    def _build_pass_manager(self) -> PassManager:
        """Build pass manager based on optimization level."""
        passes = []
        
        if self.optimization_level == OptimizationLevel.NONE:
            return PassManager([])
        
        # Phase 1: Gate-Level (BASIC and above)
        if self.optimization_level.value >= OptimizationLevel.BASIC.value:
            passes.extend([
                GateCommutationPass(),
                GateFusionPass(),
                GateCancellationPass(),
            ])
        
        # Phase 2: Circuit-Level (STANDARD and above)
        if self.optimization_level.value >= OptimizationLevel.STANDARD.value:
            passes.extend([
                ConstantPropagationPass(),
                DeadCodeEliminationPass(),
            ])
        
        # Phase 3: Topology-Aware (AGGRESSIVE and above)
        if self.optimization_level.value >= OptimizationLevel.AGGRESSIVE.value:
            passes.extend([
                QubitMappingPass(self.topology),
                SWAPInsertionPass(self.topology),
            ])
        
        # Phase 4: Advanced (AGGRESSIVE and above)
        if self.optimization_level.value >= OptimizationLevel.AGGRESSIVE.value:
            passes.extend([
                TemplateMatchingPass(),
                MeasurementDeferralPass(),
            ])
        
        # Phase 5: Fault-Tolerant (FTQC only)
        if self.optimization_level == OptimizationLevel.FTQC:
            passes.extend([
                CliffordTPlusOptimizationPass(),
                MagicStateOptimizationPass(),
                GateTeleportationPass(self.topology),
                UncomputationOptimizationPass(),
                LatticeSurgeryOptimizationPass(),
            ])
        
        # Add custom passes
        if self.custom_passes:
            passes.extend(self.custom_passes)
        
        return PassManager(passes)
    
    def execute_qir(self, qir_program: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QIR program with optimization.
        
        Args:
            qir_program: QIR program string
            **kwargs: Additional arguments for executor
        
        Returns:
            Execution result with optimization metrics
        """
        # Convert QIR to IR
        converter = QIRToIRConverter()
        circuit = converter.convert(qir_program)
        
        # Optimize
        optimized_circuit = self.pass_manager.run(circuit)
        
        # Convert to QVM
        qvm_converter = IRToQVMConverter()
        qvm_graph = qvm_converter.convert(optimized_circuit)
        
        # Execute
        result = self.executor.execute(qvm_graph, **kwargs)
        
        # Add optimization metrics
        result['optimization'] = {
            'level': self.optimization_level.name,
            'summary': self.pass_manager.get_summary(),
            'metrics': {
                'initial_gates': circuit.get_gate_count(),
                'final_gates': optimized_circuit.get_gate_count(),
                'reduction': circuit.get_gate_count() - optimized_circuit.get_gate_count(),
                'reduction_percent': (
                    (circuit.get_gate_count() - optimized_circuit.get_gate_count()) 
                    / circuit.get_gate_count() * 100
                    if circuit.get_gate_count() > 0 else 0
                ),
            }
        }
        
        self.last_metrics = result['optimization']
        
        return result
    
    def execute(self, qvm_graph: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute QVM graph directly (no optimization).
        
        Args:
            qvm_graph: QVM graph
            **kwargs: Additional arguments
        
        Returns:
            Execution result
        """
        return self.executor.execute(qvm_graph, **kwargs)
    
    def get_optimization_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of last optimization."""
        return self.last_metrics


def create_optimized_executor(
    executor_class,
    optimization_level: str = "standard",
    topology_type: str = "all_to_all",
    **executor_kwargs
):
    """
    Factory function to create an optimized executor.
    
    Args:
        executor_class: Executor class to wrap
        optimization_level: "none", "basic", "standard", "aggressive", "ftqc"
        topology_type: "linear", "grid", "all_to_all", "ibm_falcon"
        **executor_kwargs: Arguments for base executor
    
    Returns:
        OptimizedExecutor instance
    """
    # Create base executor
    executor = executor_class(**executor_kwargs)
    
    # Parse optimization level
    level_map = {
        "none": OptimizationLevel.NONE,
        "basic": OptimizationLevel.BASIC,
        "standard": OptimizationLevel.STANDARD,
        "aggressive": OptimizationLevel.AGGRESSIVE,
        "ftqc": OptimizationLevel.FTQC,
    }
    level = level_map.get(optimization_level.lower(), OptimizationLevel.STANDARD)
    
    # Create topology
    if topology_type == "linear":
        topology = HardwareTopology.linear(50)
    elif topology_type == "grid":
        topology = HardwareTopology.grid(10, 10)
    elif topology_type == "ibm_falcon":
        topology = HardwareTopology.ibm_falcon()
    else:  # all_to_all
        topology = HardwareTopology.all_to_all(100)
    
    return OptimizedExecutor(executor, level, topology)
