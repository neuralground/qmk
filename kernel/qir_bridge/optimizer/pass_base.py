"""
Optimization Pass Base Classes

Provides infrastructure for implementing optimization passes.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .ir import QIRCircuit
from .metrics import OptimizationMetrics


class OptimizationPass(ABC):
    """
    Base class for optimization passes.
    
    Each optimization pass implements a single transformation on the circuit.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.metrics = OptimizationMetrics()
    
    @abstractmethod
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run the optimization pass on a circuit.
        
        Args:
            circuit: Input circuit
        
        Returns:
            Optimized circuit (may be the same object if modified in-place)
        """
        pass
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """
        Check if this pass should run on the given circuit.
        
        Override this to add preconditions.
        """
        return self.enabled
    
    def get_metrics(self) -> OptimizationMetrics:
        """Get metrics collected during optimization."""
        return self.metrics
    
    def reset_metrics(self):
        """Reset metrics for this pass."""
        self.metrics = OptimizationMetrics()
    
    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({status})"


class PassManager:
    """
    Manages a sequence of optimization passes.
    
    Runs passes in order and collects metrics.
    """
    
    def __init__(self, passes: Optional[List[OptimizationPass]] = None):
        self.passes: List[OptimizationPass] = passes or []
        self.verbose = False
        self.validate = True  # Validate circuit after each pass
    
    def add_pass(self, optimization_pass: OptimizationPass):
        """Add an optimization pass to the manager."""
        self.passes.append(optimization_pass)
    
    def remove_pass(self, pass_name: str):
        """Remove a pass by name."""
        self.passes = [p for p in self.passes if p.name != pass_name]
    
    def enable_pass(self, pass_name: str):
        """Enable a specific pass."""
        for p in self.passes:
            if p.name == pass_name:
                p.enabled = True
    
    def disable_pass(self, pass_name: str):
        """Disable a specific pass."""
        for p in self.passes:
            if p.name == pass_name:
                p.enabled = False
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run all enabled passes on the circuit.
        
        Args:
            circuit: Input circuit
        
        Returns:
            Optimized circuit
        """
        current_circuit = circuit
        
        if self.verbose:
            print(f"Starting optimization with {len(self.passes)} passes")
            print(f"Initial: {current_circuit}")
        
        for i, opt_pass in enumerate(self.passes):
            if not opt_pass.should_run(current_circuit):
                if self.verbose:
                    print(f"  Skipping {opt_pass.name} (preconditions not met)")
                continue
            
            if self.verbose:
                print(f"\nPass {i+1}/{len(self.passes)}: {opt_pass.name}")
                print(f"  Before: {current_circuit.get_gate_count()} gates, "
                      f"depth {current_circuit.get_depth()}")
            
            # Run the pass
            opt_pass.reset_metrics()
            current_circuit = opt_pass.run(current_circuit)
            
            if self.verbose:
                print(f"  After: {current_circuit.get_gate_count()} gates, "
                      f"depth {current_circuit.get_depth()}")
                metrics = opt_pass.get_metrics()
                if metrics.gates_removed > 0:
                    print(f"  Removed {metrics.gates_removed} gates")
                if metrics.gates_added > 0:
                    print(f"  Added {metrics.gates_added} gates")
            
            # Validate if enabled
            if self.validate:
                self._validate_circuit(current_circuit, opt_pass.name)
        
        if self.verbose:
            print(f"\nOptimization complete")
            print(f"Final: {current_circuit}")
        
        return current_circuit
    
    def _validate_circuit(self, circuit: QIRCircuit, pass_name: str):
        """
        Validate circuit structure.
        
        Checks for basic invariants that should hold after any pass.
        """
        # Check that all qubits in instructions exist
        for inst in circuit.instructions:
            for qubit in inst.qubits:
                if qubit.id not in circuit.qubits:
                    raise ValueError(
                        f"Pass {pass_name} produced invalid circuit: "
                        f"instruction uses non-existent qubit {qubit.id}"
                    )
        
        # Check that result registers are tracked
        for inst in circuit.instructions:
            if inst.result and inst.result not in circuit.results:
                raise ValueError(
                    f"Pass {pass_name} produced invalid circuit: "
                    f"result {inst.result} not tracked"
                )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all passes and their metrics."""
        return {
            'total_passes': len(self.passes),
            'enabled_passes': sum(1 for p in self.passes if p.enabled),
            'passes': [
                {
                    'name': p.name,
                    'enabled': p.enabled,
                    'metrics': p.get_metrics().to_dict()
                }
                for p in self.passes
            ]
        }
    
    def __repr__(self):
        enabled_count = sum(1 for p in self.passes if p.enabled)
        return f"PassManager({enabled_count}/{len(self.passes)} passes enabled)"
