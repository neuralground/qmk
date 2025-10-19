"""
Gate Cancellation Pass

Removes adjacent inverse gate pairs that cancel each other out.

Examples:
  H → H → (removed)
  X → X → (removed)
  CNOT → CNOT → (removed)
  S → S† → (removed)
  T → T† → (removed)
"""

import time
from typing import List, Set
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, InstructionType


class GateCancellationPass(OptimizationPass):
    """
    Removes adjacent inverse gate pairs.
    
    Self-inverse gates (H, X, Y, Z, CNOT, SWAP):
      G → G → (removed)
    
    Inverse pairs (S/S†, T/T†):
      G → G† → (removed)
    
    Rotation gates with opposite angles:
      RZ(θ) → RZ(-θ) → (removed)
    """
    
    def __init__(self):
        super().__init__("GateCancellation")
        self.self_inverse_gates = {
            InstructionType.H,
            InstructionType.X,
            InstructionType.Y,
            InstructionType.Z,
            InstructionType.CNOT,
            InstructionType.CZ,
            InstructionType.SWAP,
        }
        
        self.inverse_pairs = {
            (InstructionType.S, InstructionType.SDG),
            (InstructionType.SDG, InstructionType.S),
            (InstructionType.T, InstructionType.TDG),
            (InstructionType.TDG, InstructionType.T),
        }
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run gate cancellation on the circuit.
        
        Iterates through instructions looking for adjacent cancellable pairs.
        """
        start_time = time.time()
        
        # Track which instructions to remove
        to_remove: Set[int] = set()
        
        i = 0
        while i < len(circuit.instructions) - 1:
            if i in to_remove:
                i += 1
                continue
            
            inst1 = circuit.instructions[i]
            inst2 = circuit.instructions[i + 1]
            
            # Check if they can cancel
            if self._can_cancel(inst1, inst2):
                # Mark both for removal
                to_remove.add(i)
                to_remove.add(i + 1)
                
                # Update metrics
                self.metrics.gates_removed += 2
                self.metrics.patterns_matched += 1
                
                # Track specific gate types
                if inst1.inst_type == InstructionType.CNOT:
                    self.metrics.cnot_removed += 2
                elif inst1.inst_type in [InstructionType.T, InstructionType.TDG]:
                    self.metrics.t_gates_removed += 2
                
                # Skip both instructions
                i += 2
            else:
                i += 1
        
        # Remove marked instructions (in reverse order to preserve indices)
        for idx in sorted(to_remove, reverse=True):
            circuit.remove_instruction(idx)
        
        # Record execution time
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _can_cancel(self, inst1: QIRInstruction, inst2: QIRInstruction) -> bool:
        """
        Check if two adjacent instructions cancel each other.
        
        Args:
            inst1: First instruction
            inst2: Second instruction
        
        Returns:
            True if they cancel
        """
        # Must operate on same qubits
        if inst1.qubits != inst2.qubits:
            return False
        
        # Must both be gates
        if not (inst1.is_gate() and inst2.is_gate()):
            return False
        
        # Check self-inverse gates
        if (inst1.inst_type in self.self_inverse_gates and
            inst1.inst_type == inst2.inst_type):
            return True
        
        # Check inverse pairs
        pair = (inst1.inst_type, inst2.inst_type)
        if pair in self.inverse_pairs:
            return True
        
        # Check rotation gates with opposite angles
        if inst1.inst_type == inst2.inst_type:
            if inst1.inst_type in [InstructionType.RX, InstructionType.RY, InstructionType.RZ]:
                theta1 = inst1.params.get('theta', 0)
                theta2 = inst2.params.get('theta', 0)
                # Check if angles are opposite (within tolerance)
                if abs(theta1 + theta2) < 1e-10:
                    return True
        
        return False
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are gates to potentially cancel."""
        return self.enabled and circuit.get_gate_count() >= 2
