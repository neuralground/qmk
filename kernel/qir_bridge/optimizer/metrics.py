"""
Optimization Metrics

Tracks statistics about optimization passes.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class OptimizationMetrics:
    """
    Metrics collected during optimization.
    
    Tracks changes made by an optimization pass.
    """
    # Gate statistics
    gates_removed: int = 0
    gates_added: int = 0
    gates_modified: int = 0
    
    # Specific gate types
    cnot_removed: int = 0
    cnot_added: int = 0
    t_gates_removed: int = 0
    t_gates_added: int = 0
    swap_gates_added: int = 0
    swap_gates_removed: int = 0
    
    # Circuit properties
    depth_reduction: int = 0
    qubit_reduction: int = 0
    
    # Pattern matching
    patterns_matched: int = 0
    patterns_replaced: int = 0
    
    # Execution statistics
    execution_time_ms: float = 0.0
    
    # Custom metrics
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def net_gate_change(self) -> int:
        """Calculate net change in gate count."""
        return self.gates_added - self.gates_removed
    
    def net_cnot_change(self) -> int:
        """Calculate net change in CNOT count."""
        return self.cnot_added - self.cnot_removed
    
    def net_t_change(self) -> int:
        """Calculate net change in T-gate count."""
        return self.t_gates_added - self.t_gates_removed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'gates_removed': self.gates_removed,
            'gates_added': self.gates_added,
            'gates_modified': self.gates_modified,
            'net_gate_change': self.net_gate_change(),
            'cnot_removed': self.cnot_removed,
            'cnot_added': self.cnot_added,
            'net_cnot_change': self.net_cnot_change(),
            't_gates_removed': self.t_gates_removed,
            't_gates_added': self.t_gates_added,
            'net_t_change': self.net_t_change(),
            'swap_gates_added': self.swap_gates_added,
            'swap_gates_removed': self.swap_gates_removed,
            'depth_reduction': self.depth_reduction,
            'qubit_reduction': self.qubit_reduction,
            'patterns_matched': self.patterns_matched,
            'patterns_replaced': self.patterns_replaced,
            'execution_time_ms': self.execution_time_ms,
            'custom': self.custom
        }
    
    def __repr__(self):
        parts = []
        if self.gates_removed > 0:
            parts.append(f"-{self.gates_removed} gates")
        if self.gates_added > 0:
            parts.append(f"+{self.gates_added} gates")
        if self.depth_reduction != 0:
            parts.append(f"depth {self.depth_reduction:+d}")
        if self.patterns_matched > 0:
            parts.append(f"{self.patterns_matched} patterns")
        
        if parts:
            return f"Metrics({', '.join(parts)})"
        return "Metrics(no changes)"
