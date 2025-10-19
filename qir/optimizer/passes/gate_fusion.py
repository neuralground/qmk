"""
Gate Fusion Pass

Combines sequences of gates into single equivalent operations.

Fusion Rules:
- S → S = Z
- T → T → T → T = Z
- RZ(θ₁) → RZ(θ₂) = RZ(θ₁+θ₂)
- RX(θ₁) → RX(θ₂) = RX(θ₁+θ₂)
- RY(θ₁) → RY(θ₂) = RY(θ₁+θ₂)

Examples:
  S → S → Z (2 gates → 1 gate)
  RZ(π/4) → RZ(π/4) → RZ(π/2) (2 gates → 1 gate)
"""

import time
import math
from typing import List, Optional
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, InstructionType


class GateFusionPass(OptimizationPass):
    """
    Fuses sequences of gates into equivalent single gates.
    
    Looks for adjacent gates on the same qubits that can be combined.
    """
    
    def __init__(self):
        super().__init__("GateFusion")
        
        # Fusion rules: (gate1, gate2) -> result_gate
        self.fusion_rules = {
            # S → S = Z
            (InstructionType.S, InstructionType.S): InstructionType.Z,
            # T → T = S
            (InstructionType.T, InstructionType.T): InstructionType.S,
        }
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run gate fusion on the circuit.
        
        Iterates through instructions looking for fusible sequences.
        """
        start_time = time.time()
        
        changed = True
        iterations = 0
        max_iterations = 10
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            i = 0
            while i < len(circuit.instructions) - 1:
                inst1 = circuit.instructions[i]
                inst2 = circuit.instructions[i + 1]
                
                # Try to fuse these two instructions
                fused = self._try_fuse(inst1, inst2)
                
                if fused:
                    # Replace both instructions with the fused one
                    circuit.remove_instruction(i + 1)
                    circuit.remove_instruction(i)
                    circuit.insert_instruction(i, fused)
                    
                    # Update metrics
                    self.metrics.gates_removed += 1  # Net: 2 removed, 1 added
                    self.metrics.patterns_matched += 1
                    
                    changed = True
                    # Don't increment i - check if we can fuse again at this position
                else:
                    i += 1
        
        self.metrics.custom['iterations'] = iterations
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _try_fuse(self, inst1: QIRInstruction, inst2: QIRInstruction) -> Optional[QIRInstruction]:
        """
        Try to fuse two instructions.
        
        Args:
            inst1: First instruction
            inst2: Second instruction
        
        Returns:
            Fused instruction if possible, None otherwise
        """
        # Must be gates
        if not (inst1.is_gate() and inst2.is_gate()):
            return None
        
        # Must operate on same qubits
        if inst1.qubits != inst2.qubits:
            return None
        
        # Check simple fusion rules
        pair = (inst1.inst_type, inst2.inst_type)
        if pair in self.fusion_rules:
            result_type = self.fusion_rules[pair]
            return QIRInstruction(
                inst_type=result_type,
                qubits=inst1.qubits.copy()
            )
        
        # Check rotation gate fusion
        if inst1.inst_type == inst2.inst_type:
            if inst1.inst_type in [InstructionType.RX, InstructionType.RY, InstructionType.RZ]:
                theta1 = inst1.params.get('theta', 0)
                theta2 = inst2.params.get('theta', 0)
                theta_sum = theta1 + theta2
                
                # Normalize angle to [-2π, 2π]
                while theta_sum > 2 * math.pi:
                    theta_sum -= 2 * math.pi
                while theta_sum < -2 * math.pi:
                    theta_sum += 2 * math.pi
                
                # If angle is effectively zero, remove the gate
                if abs(theta_sum) < 1e-10:
                    # Return a marker that we should remove both gates
                    # We'll handle this by returning None and letting cancellation handle it
                    return None
                
                return QIRInstruction(
                    inst_type=inst1.inst_type,
                    qubits=inst1.qubits.copy(),
                    params={'theta': theta_sum}
                )
        
        # Check for T gate accumulation (4 T gates = Z)
        if inst1.inst_type == InstructionType.T and inst2.inst_type == InstructionType.T:
            # We already handle T → T = S above
            # This would be for counting multiple T gates
            pass
        
        # Check for S gate accumulation (2 S gates = Z)
        # Already handled above
        
        return None
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are gates to potentially fuse."""
        return self.enabled and circuit.get_gate_count() >= 2
