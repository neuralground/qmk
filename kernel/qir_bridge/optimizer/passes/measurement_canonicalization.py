"""
Measurement Canonicalization Pass

Detects multi-gate sequences that implement measurement bases and replaces
them with canonical measurement operations.

Patterns Detected:
1. H → MEASURE_Z → H  ⟹  MEASURE_X
2. S† → H → MEASURE_Z → H → S  ⟹  MEASURE_Y
3. CNOT(q0,q1) → H(q0) → MEASURE_Z(q0) → MEASURE_Z(q1)  ⟹  MEASURE_BELL(q0,q1)

Benefits:
- Simplifies circuit representation
- Makes measurement basis explicit
- Enables basis-specific optimizations
- Reduces gate count
- Improves readability

Example:
  Before:
    H(q0) → MEASURE_Z(q0)
  
  After:
    MEASURE_X(q0)
"""

import time
from typing import List, Optional, Tuple
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, InstructionType, QIRQubit


class MeasurementCanonicalizationPass(OptimizationPass):
    """
    Canonicalizes measurement sequences into explicit basis measurements.
    
    Strategy:
    1. Scan for measurement patterns
    2. Identify gate sequences before measurements
    3. Replace with canonical measurement operations
    4. Remove redundant gates
    """
    
    def __init__(self):
        super().__init__("MeasurementCanonicalization")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run measurement canonicalization on the circuit.
        
        Detects and replaces measurement basis patterns.
        """
        start_time = time.time()
        
        changes_made = True
        total_canonicalizations = 0
        
        while changes_made:
            changes_made = False
            
            # Check longer patterns first to avoid partial matches
            
            # Try Bell basis canonicalization (4 instructions)
            if self._canonicalize_bell_basis(circuit):
                changes_made = True
                total_canonicalizations += 1
            
            # Try Y-basis canonicalization (3 instructions)
            if self._canonicalize_y_basis(circuit):
                changes_made = True
                total_canonicalizations += 1
            
            # Try X-basis canonicalization (2 instructions)
            if self._canonicalize_x_basis(circuit):
                changes_made = True
                total_canonicalizations += 1
        
        self.metrics.custom['measurements_canonicalized'] = total_canonicalizations
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _canonicalize_x_basis(self, circuit: QIRCircuit) -> bool:
        """
        Detect and canonicalize X-basis measurements.
        
        Pattern: H → MEASURE_Z  ⟹  MEASURE_X
        
        Returns True if any canonicalization was performed.
        """
        instructions = circuit.instructions
        
        for i in range(len(instructions) - 1):
            inst1 = instructions[i]
            inst2 = instructions[i + 1]
            
            # Check for H followed by MEASURE_Z on same qubit
            if (inst1.inst_type == InstructionType.H and
                inst2.inst_type == InstructionType.MEASURE and
                inst2.params.get('basis', 'Z') == 'Z' and
                len(inst1.qubits) == 1 and
                len(inst2.qubits) == 1 and
                inst1.qubits[0] == inst2.qubits[0]):
                
                # Replace MEASURE_Z with MEASURE_X
                inst2.params['basis'] = 'X'
                
                # Remove the H gate
                circuit.remove_instruction(i)
                
                return True
        
        return False
    
    def _canonicalize_y_basis(self, circuit: QIRCircuit) -> bool:
        """
        Detect and canonicalize Y-basis measurements.
        
        Pattern: S† → H → MEASURE_Z  ⟹  MEASURE_Y
        
        Returns True if any canonicalization was performed.
        """
        instructions = circuit.instructions
        
        for i in range(len(instructions) - 2):
            inst1 = instructions[i]
            inst2 = instructions[i + 1]
            inst3 = instructions[i + 2]
            
            # Check for S† → H → MEASURE_Z on same qubit
            if (inst1.inst_type == InstructionType.SDG and
                inst2.inst_type == InstructionType.H and
                inst3.inst_type == InstructionType.MEASURE and
                inst3.params.get('basis', 'Z') == 'Z' and
                len(inst1.qubits) == 1 and
                len(inst2.qubits) == 1 and
                len(inst3.qubits) == 1 and
                inst1.qubits[0] == inst2.qubits[0] == inst3.qubits[0]):
                
                # Replace MEASURE_Z with MEASURE_Y
                inst3.params['basis'] = 'Y'
                
                # Remove S† and H gates (remove in reverse order to maintain indices)
                circuit.remove_instruction(i + 1)  # Remove H first
                circuit.remove_instruction(i)      # Then remove S†
                
                return True
        
        return False
    
    def _canonicalize_bell_basis(self, circuit: QIRCircuit) -> bool:
        """
        Detect and canonicalize Bell basis measurements.
        
        Pattern: CNOT(q0,q1) → H(q0) → MEASURE_Z(q0) → MEASURE_Z(q1)
                 ⟹  MEASURE_BELL(q0,q1)
        
        Returns True if any canonicalization was performed.
        """
        instructions = circuit.instructions
        
        for i in range(len(instructions) - 3):
            inst1 = instructions[i]
            inst2 = instructions[i + 1]
            inst3 = instructions[i + 2]
            inst4 = instructions[i + 3]
            
            # Check for CNOT → H → MEASURE_Z → MEASURE_Z pattern
            if (inst1.inst_type == InstructionType.CNOT and
                inst2.inst_type == InstructionType.H and
                inst3.inst_type == InstructionType.MEASURE and
                inst4.inst_type == InstructionType.MEASURE and
                inst3.params.get('basis', 'Z') == 'Z' and
                inst4.params.get('basis', 'Z') == 'Z' and
                len(inst1.qubits) == 2 and
                len(inst2.qubits) == 1 and
                len(inst3.qubits) == 1 and
                len(inst4.qubits) == 1):
                
                q0, q1 = inst1.qubits[0], inst1.qubits[1]
                
                # Check that H is on control qubit and both measurements match
                if (inst2.qubits[0] == q0 and
                    inst3.qubits[0] == q0 and
                    inst4.qubits[0] == q1):
                    
                    # Create Bell measurement instruction
                    bell_meas = QIRInstruction(
                        inst_type=InstructionType.MEASURE,
                        qubits=[q0, q1],
                        params={'basis': 'BELL'},
                        result=inst3.result,  # Use first measurement result
                        metadata={'bell_measurement': True}
                    )
                    
                    # Remove the four instructions in reverse order
                    circuit.remove_instruction(i + 3)  # MEASURE_Z(q1)
                    circuit.remove_instruction(i + 2)  # MEASURE_Z(q0)
                    circuit.remove_instruction(i + 1)  # H(q0)
                    circuit.remove_instruction(i)      # CNOT
                    
                    # Insert Bell measurement at position i
                    circuit.instructions.insert(i, bell_meas)
                    
                    return True
        
        return False
    
    def _find_pattern(
        self,
        circuit: QIRCircuit,
        pattern: List[InstructionType],
        start_idx: int = 0
    ) -> Optional[Tuple[int, List[QIRInstruction]]]:
        """
        Find a pattern of instructions in the circuit.
        
        Args:
            circuit: Circuit to search
            pattern: List of instruction types to match
            start_idx: Index to start searching from
        
        Returns:
            Tuple of (start_index, matched_instructions) or None
        """
        instructions = circuit.instructions
        
        for i in range(start_idx, len(instructions) - len(pattern) + 1):
            # Check if pattern matches
            match = True
            matched = []
            
            for j, inst_type in enumerate(pattern):
                if instructions[i + j].inst_type != inst_type:
                    match = False
                    break
                matched.append(instructions[i + j])
            
            if match:
                # Verify all instructions operate on same qubit(s)
                if self._same_qubits(matched):
                    return (i, matched)
        
        return None
    
    def _same_qubits(self, instructions: List[QIRInstruction]) -> bool:
        """Check if all instructions operate on the same qubit(s)."""
        if not instructions:
            return False
        
        first_qubits = set(instructions[0].qubits)
        
        for inst in instructions[1:]:
            if set(inst.qubits) != first_qubits:
                return False
        
        return True
    
    def estimate_benefit(self, circuit: QIRCircuit) -> float:
        """
        Estimate the benefit of running this pass.
        
        Returns a score indicating potential for canonicalization.
        """
        score = 0.0
        instructions = circuit.instructions
        
        # Count potential X-basis patterns (H before MEASURE)
        for i in range(len(instructions) - 1):
            if (instructions[i].inst_type == InstructionType.H and
                instructions[i + 1].inst_type == InstructionType.MEASURE):
                score += 1.0
        
        # Count potential Y-basis patterns (S† → H before MEASURE)
        for i in range(len(instructions) - 2):
            if (instructions[i].inst_type == InstructionType.SDG and
                instructions[i + 1].inst_type == InstructionType.H and
                instructions[i + 2].inst_type == InstructionType.MEASURE):
                score += 1.5
        
        # Count potential Bell patterns (CNOT → H → MEASURE → MEASURE)
        for i in range(len(instructions) - 3):
            if (instructions[i].inst_type == InstructionType.CNOT and
                instructions[i + 1].inst_type == InstructionType.H and
                instructions[i + 2].inst_type == InstructionType.MEASURE and
                instructions[i + 3].inst_type == InstructionType.MEASURE):
                score += 2.0
        
        return score
