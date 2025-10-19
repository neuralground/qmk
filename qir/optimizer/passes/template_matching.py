"""
Template Matching Pass

Recognizes and replaces gate patterns with more efficient equivalents.

Common Templates:
- CNOT → H → CNOT → H = SWAP
- H → CNOT → H = CZ (with target/control swap)
- X → H → X → H = Z
- Multiple single-qubit rotations → combined rotation

Example:
  Before: CNOT(0,1) → H(0) → H(1) → CNOT(0,1) → H(0) → H(1)
  After:  SWAP(0,1)
  (6 gates → 1 gate, but SWAP = 3 CNOTs, so 6 → 3 gates)
"""

import time
import math
from typing import List, Optional, Tuple
from dataclasses import dataclass
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType


@dataclass
class GateTemplate:
    """
    Represents a gate pattern template.
    
    Attributes:
        pattern: List of (gate_type, qubit_indices) tuples
        replacement: List of (gate_type, qubit_indices) tuples
        name: Human-readable name
        cost_before: Gate count before
        cost_after: Gate count after
    """
    pattern: List[Tuple[InstructionType, List[int]]]
    replacement: List[Tuple[InstructionType, List[int]]]
    name: str
    cost_before: int
    cost_after: int
    
    def matches(self, instructions: List[QIRInstruction], start_idx: int) -> bool:
        """Check if pattern matches at given position."""
        if start_idx + len(self.pattern) > len(instructions):
            return False
        
        for i, (gate_type, qubit_indices) in enumerate(self.pattern):
            inst = instructions[start_idx + i]
            
            # Check gate type
            if inst.inst_type != gate_type:
                return False
            
            # Check qubit count
            if len(inst.qubits) != len(qubit_indices):
                return False
        
        return True
    
    def extract_qubits(
        self, 
        instructions: List[QIRInstruction], 
        start_idx: int
    ) -> List[QIRQubit]:
        """Extract the actual qubits involved in the pattern."""
        qubit_map = {}
        
        for i, (gate_type, qubit_indices) in enumerate(self.pattern):
            inst = instructions[start_idx + i]
            for j, qubit_idx in enumerate(qubit_indices):
                if qubit_idx not in qubit_map:
                    qubit_map[qubit_idx] = inst.qubits[j]
        
        return qubit_map
    
    def create_replacement(
        self, 
        qubit_map: dict
    ) -> List[QIRInstruction]:
        """Create replacement instructions using actual qubits."""
        replacements = []
        
        for gate_type, qubit_indices in self.replacement:
            qubits = [qubit_map[idx] for idx in qubit_indices]
            replacements.append(QIRInstruction(gate_type, qubits))
        
        return replacements


class TemplateMatchingPass(OptimizationPass):
    """
    Matches and replaces gate patterns with efficient equivalents.
    
    Uses a library of known templates to find optimization opportunities.
    """
    
    def __init__(self):
        super().__init__("TemplateMatching")
        self.templates = self._build_template_library()
    
    def _build_template_library(self) -> List[GateTemplate]:
        """Build library of known gate patterns."""
        templates = []
        
        # Template 1: CNOT-H-CNOT-H = SWAP
        # CNOT(0,1) → H(0) → H(1) → CNOT(0,1) → H(0) → H(1)
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.CNOT, [0, 1]),
                (InstructionType.H, [0]),
                (InstructionType.H, [1]),
                (InstructionType.CNOT, [0, 1]),
                (InstructionType.H, [0]),
                (InstructionType.H, [1]),
            ],
            replacement=[
                (InstructionType.SWAP, [0, 1]),
            ],
            name="CNOT-H sequence to SWAP",
            cost_before=6,
            cost_after=1  # Note: SWAP = 3 CNOTs in practice
        ))
        
        # Template 2: X-H-X-H = Z
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.X, [0]),
                (InstructionType.H, [0]),
                (InstructionType.X, [0]),
                (InstructionType.H, [0]),
            ],
            replacement=[
                (InstructionType.Z, [0]),
            ],
            name="X-H-X-H to Z",
            cost_before=4,
            cost_after=1
        ))
        
        # Template 3: H-X-H = Z
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.H, [0]),
                (InstructionType.X, [0]),
                (InstructionType.H, [0]),
            ],
            replacement=[
                (InstructionType.Z, [0]),
            ],
            name="H-X-H to Z",
            cost_before=3,
            cost_after=1
        ))
        
        # Template 4: H-Z-H = X
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.H, [0]),
                (InstructionType.Z, [0]),
                (InstructionType.H, [0]),
            ],
            replacement=[
                (InstructionType.X, [0]),
            ],
            name="H-Z-H to X",
            cost_before=3,
            cost_after=1
        ))
        
        # Template 5: S-S-S-S = Identity (remove)
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.S, [0]),
                (InstructionType.S, [0]),
                (InstructionType.S, [0]),
                (InstructionType.S, [0]),
            ],
            replacement=[],  # Remove entirely
            name="S^4 to Identity",
            cost_before=4,
            cost_after=0
        ))
        
        # Template 6: T-T-T-T-T-T-T-T = Identity
        templates.append(GateTemplate(
            pattern=[
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
                (InstructionType.T, [0]),
            ],
            replacement=[],
            name="T^8 to Identity",
            cost_before=8,
            cost_after=0
        ))
        
        return templates
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run template matching on the circuit.
        
        Scans for known patterns and replaces them.
        """
        start_time = time.time()
        
        changed = True
        iterations = 0
        max_iterations = 10
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            i = 0
            while i < len(circuit.instructions):
                # Try each template at this position
                matched = False
                
                for template in self.templates:
                    if template.matches(circuit.instructions, i):
                        # Extract qubits
                        qubit_map = template.extract_qubits(circuit.instructions, i)
                        
                        # Create replacement
                        replacements = template.create_replacement(qubit_map)
                        
                        # Remove old pattern
                        for _ in range(len(template.pattern)):
                            circuit.remove_instruction(i)
                        
                        # Insert replacements
                        for j, replacement in enumerate(replacements):
                            circuit.insert_instruction(i + j, replacement)
                        
                        # Update metrics
                        gates_saved = template.cost_before - template.cost_after
                        self.metrics.gates_removed += gates_saved
                        self.metrics.patterns_matched += 1
                        
                        changed = True
                        matched = True
                        break
                
                if not matched:
                    i += 1
        
        self.metrics.custom['iterations'] = iterations
        self.metrics.custom['templates_applied'] = self.metrics.patterns_matched
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are enough gates to match patterns."""
        return self.enabled and circuit.get_gate_count() >= 3
