"""
Gate Commutation Pass

Reorders commuting gates to enable other optimizations (especially cancellation).

Commutation Rules:
- Single-qubit gates on different qubits always commute
- Two-qubit gates commute if they operate on disjoint qubit sets
- Measurements commute with gates on different qubits
- Some gates on the same qubit commute (e.g., Z and RZ)

Example:
  Before: H(q0) → X(q1) → H(q0)
  After:  X(q1) → H(q0) → H(q0)
  Then cancellation can remove H→H
"""

import time
from typing import List, Set, Tuple
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, InstructionType


class GateCommutationPass(OptimizationPass):
    """
    Reorders commuting gates to enable cancellation.
    
    Strategy:
    1. Scan for gates that could cancel if adjacent
    2. Check if intervening gates commute
    3. Bubble gates together if safe
    """
    
    def __init__(self, max_distance: int = 5):
        """
        Initialize gate commutation pass.
        
        Args:
            max_distance: Maximum distance to look ahead for commutation opportunities
        """
        super().__init__("GateCommutation")
        self.max_distance = max_distance
        
        # Gates that commute with each other on the same qubit
        self.commuting_same_qubit = {
            # Pauli Z commutes with phase gates
            (InstructionType.Z, InstructionType.RZ),
            (InstructionType.Z, InstructionType.S),
            (InstructionType.Z, InstructionType.T),
            (InstructionType.RZ, InstructionType.S),
            (InstructionType.RZ, InstructionType.T),
            (InstructionType.S, InstructionType.T),
            # Symmetric pairs
            (InstructionType.RZ, InstructionType.Z),
            (InstructionType.S, InstructionType.Z),
            (InstructionType.T, InstructionType.Z),
            (InstructionType.S, InstructionType.RZ),
            (InstructionType.T, InstructionType.RZ),
            (InstructionType.T, InstructionType.S),
        }
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run gate commutation on the circuit.
        
        Looks for opportunities to move gates closer together for cancellation.
        """
        start_time = time.time()
        
        changed = True
        iterations = 0
        max_iterations = 10  # Prevent infinite loops
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            # Look for commutation opportunities
            for i in range(len(circuit.instructions) - 1):
                inst1 = circuit.instructions[i]
                
                # Look ahead for a matching gate that could cancel
                for j in range(i + 1, min(i + self.max_distance + 1, len(circuit.instructions))):
                    inst2 = circuit.instructions[j]
                    
                    # Check if these could potentially cancel
                    if self._could_cancel(inst1, inst2):
                        # Check if we can commute inst2 forward to be adjacent to inst1
                        if self._can_commute_forward(circuit, i, j):
                            # Move inst2 to position i+1
                            self._move_instruction(circuit, j, i + 1)
                            changed = True
                            self.metrics.patterns_matched += 1
                            break
            
            if changed:
                self.metrics.gates_modified += 1
        
        self.metrics.custom['iterations'] = iterations
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _could_cancel(self, inst1: QIRInstruction, inst2: QIRInstruction) -> bool:
        """
        Check if two instructions could potentially cancel.
        
        This is a looser check than actual cancellation - just checks if they're
        the same type of gate on the same qubits.
        """
        if not (inst1.is_gate() and inst2.is_gate()):
            return False
        
        if inst1.qubits != inst2.qubits:
            return False
        
        # Self-inverse gates
        if inst1.inst_type == inst2.inst_type:
            if inst1.inst_type in [InstructionType.H, InstructionType.X, 
                                   InstructionType.Y, InstructionType.Z,
                                   InstructionType.CNOT, InstructionType.CZ,
                                   InstructionType.SWAP]:
                return True
        
        # Inverse pairs
        inverse_pairs = {
            (InstructionType.S, InstructionType.SDG),
            (InstructionType.SDG, InstructionType.S),
            (InstructionType.T, InstructionType.TDG),
            (InstructionType.TDG, InstructionType.T),
        }
        
        pair = (inst1.inst_type, inst2.inst_type)
        if pair in inverse_pairs:
            return True
        
        return False
    
    def _can_commute_forward(self, circuit: QIRCircuit, start: int, end: int) -> bool:
        """
        Check if instruction at 'end' can be moved forward to 'start+1'.
        
        This requires that the instruction commutes with all instructions
        between start and end.
        """
        inst_to_move = circuit.instructions[end]
        
        # Check commutation with all intervening instructions
        for i in range(start + 1, end):
            intervening = circuit.instructions[i]
            
            if not self._commutes_with(inst_to_move, intervening):
                return False
        
        return True
    
    def _commutes_with(self, inst1: QIRInstruction, inst2: QIRInstruction) -> bool:
        """
        Check if two instructions commute.
        
        Args:
            inst1: First instruction
            inst2: Second instruction
        
        Returns:
            True if they commute
        """
        # Get qubit sets
        qubits1 = set(inst1.qubits)
        qubits2 = set(inst2.qubits)
        
        # Different qubits always commute
        if not qubits1.intersection(qubits2):
            return True
        
        # Same qubits - need more careful analysis
        if not inst1.is_gate() or not inst2.is_gate():
            # Measurements don't commute with gates on same qubit
            return False
        
        # Check if these specific gate types commute on same qubit
        pair = (inst1.inst_type, inst2.inst_type)
        if pair in self.commuting_same_qubit:
            return True
        
        # Two-qubit gates with partial overlap
        if inst1.is_two_qubit_gate() and inst2.is_two_qubit_gate():
            # CNOTs with same control commute if targets are different
            if (inst1.inst_type == InstructionType.CNOT and 
                inst2.inst_type == InstructionType.CNOT):
                if inst1.qubits[0] == inst2.qubits[0]:  # Same control
                    if inst1.qubits[1] != inst2.qubits[1]:  # Different target
                        return True
        
        # Conservative: don't commute by default
        return False
    
    def _move_instruction(self, circuit: QIRCircuit, from_idx: int, to_idx: int):
        """
        Move an instruction from one position to another.
        
        Args:
            circuit: Circuit to modify
            from_idx: Source index
            to_idx: Destination index
        """
        if from_idx == to_idx:
            return
        
        # Remove from old position
        inst = circuit.instructions.pop(from_idx)
        
        # Insert at new position
        # Adjust index if we removed from before the target
        if from_idx < to_idx:
            to_idx -= 1
        
        circuit.instructions.insert(to_idx, inst)
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are enough gates to potentially commute."""
        return self.enabled and circuit.get_gate_count() >= 3
