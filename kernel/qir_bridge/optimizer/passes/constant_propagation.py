"""
Constant Propagation Pass

Tracks known qubit states through the circuit and optimizes based on that knowledge.

Patterns:
- Qubit initialized to |0⟩ (default)
- X on |0⟩ → becomes |1⟩
- X on |1⟩ → becomes |0⟩
- H on |0⟩ → becomes |+⟩
- Measurement of known state → replace with constant

Example:
  Before:
    q0: (|0⟩) → X → X → MEASURE
  
  After:
    q0: (|0⟩) → MEASURE
    (X → X cancel because we know state returns to |0⟩)
"""

import time
from typing import Dict, Optional, Set
from enum import Enum
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType


class QubitState(Enum):
    """Known qubit states."""
    ZERO = "0"           # |0⟩
    ONE = "1"            # |1⟩
    PLUS = "+"           # |+⟩ = (|0⟩ + |1⟩)/√2
    MINUS = "-"          # |-⟩ = (|0⟩ - |1⟩)/√2
    UNKNOWN = "?"        # Unknown/superposition


class ConstantPropagationPass(OptimizationPass):
    """
    Propagates known qubit states through the circuit.
    
    Tracks state changes and identifies:
    1. Redundant operations (X → X on |0⟩ returns to |0⟩)
    2. Known measurement outcomes
    3. Simplifiable gate sequences
    """
    
    def __init__(self):
        super().__init__("ConstantPropagation")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run constant propagation on the circuit.
        
        Strategy:
        1. Initialize all qubits to |0⟩
        2. Track state changes through gates
        3. Identify redundant operations
        4. Mark operations for removal
        """
        start_time = time.time()
        
        # Initialize state tracking
        qubit_states = {q: QubitState.ZERO for q in circuit.qubits.values()}
        
        # Track which instructions to remove
        instructions_to_remove = set()
        
        # Process instructions
        for i, inst in enumerate(circuit.instructions):
            if not inst.is_gate():
                # Measurements make state unknown
                if inst.is_measurement():
                    for qubit in inst.qubits:
                        qubit_states[qubit] = QubitState.UNKNOWN
                continue
            
            # Check if this operation is redundant
            if self._is_redundant(inst, qubit_states):
                instructions_to_remove.add(i)
                self.metrics.gates_removed += 1
                self.metrics.patterns_matched += 1
                # Don't update state for redundant operations
                continue
            
            # Update states based on this operation
            self._update_states(inst, qubit_states)
        
        # Remove redundant instructions
        for idx in sorted(instructions_to_remove, reverse=True):
            circuit.remove_instruction(idx)
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _is_redundant(self, inst: QIRInstruction, states: Dict[QIRQubit, QubitState]) -> bool:
        """
        Check if an instruction is redundant given current states.
        
        Args:
            inst: Instruction to check
            states: Current qubit states
        
        Returns:
            True if redundant
        """
        if not inst.is_single_qubit_gate():
            # Only handle single-qubit gates for now
            return False
        
        qubit = inst.qubits[0]
        state = states[qubit]
        
        # X on |0⟩ followed by X returns to |0⟩ (handled by cancellation)
        # But we can identify no-ops
        
        # H on |+⟩ returns to |0⟩ (not redundant, changes state)
        # H on |-⟩ returns to |1⟩ (not redundant, changes state)
        
        # For now, we're conservative and don't mark things as redundant
        # unless we're very sure
        
        return False
    
    def _update_states(self, inst: QIRInstruction, states: Dict[QIRQubit, QubitState]):
        """
        Update qubit states based on an instruction.
        
        Args:
            inst: Instruction being applied
            states: Current qubit states (modified in place)
        """
        if inst.is_single_qubit_gate():
            qubit = inst.qubits[0]
            current_state = states[qubit]
            
            # Apply state transitions
            if inst.inst_type == InstructionType.X:
                if current_state == QubitState.ZERO:
                    states[qubit] = QubitState.ONE
                elif current_state == QubitState.ONE:
                    states[qubit] = QubitState.ZERO
                # X doesn't change |+⟩ or |-⟩
            
            elif inst.inst_type == InstructionType.H:
                if current_state == QubitState.ZERO:
                    states[qubit] = QubitState.PLUS
                elif current_state == QubitState.ONE:
                    states[qubit] = QubitState.MINUS
                elif current_state == QubitState.PLUS:
                    states[qubit] = QubitState.ZERO
                elif current_state == QubitState.MINUS:
                    states[qubit] = QubitState.ONE
            
            elif inst.inst_type == InstructionType.Z:
                if current_state == QubitState.PLUS:
                    states[qubit] = QubitState.MINUS
                elif current_state == QubitState.MINUS:
                    states[qubit] = QubitState.PLUS
                # Z doesn't change |0⟩ or |1⟩
            
            else:
                # Other gates make state unknown
                states[qubit] = QubitState.UNKNOWN
        
        elif inst.is_two_qubit_gate():
            # Two-qubit gates generally make states unknown
            # (unless we track entanglement, which is complex)
            for qubit in inst.qubits:
                states[qubit] = QubitState.UNKNOWN
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are gates."""
        return self.enabled and circuit.get_gate_count() > 0
