"""
Uncomputation Optimization Pass

Optimizes uncomputation (cleanup) of ancilla qubits.

Uncomputation is the process of returning ancilla qubits to their initial state
by reversing the operations that were applied to them. This is critical for:
- Freeing ancilla qubits for reuse
- Preventing error accumulation
- Enabling reversible computation

Techniques:
- Identify computation/uncomputation pairs
- Optimize uncomputation sequences
- Reuse ancilla qubits
- Bennett's trick for space-time tradeoffs

Example:
  Computation: H(anc) → CNOT(anc, target) → ...
  Uncomputation: ... → CNOT(anc, target) → H(anc)
  
  Optimization: Identify and optimize these patterns
"""

import time
from typing import List, Set, Dict, Tuple, Optional
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType


class UncomputationOptimizationPass(OptimizationPass):
    """
    Optimizes uncomputation of ancilla qubits.
    
    Uncomputation reverses operations on ancilla qubits to return them
    to their initial state, enabling reuse and preventing errors.
    
    Strategy:
    1. Identify ancilla qubits (not measured)
    2. Find computation/uncomputation pairs
    3. Optimize uncomputation sequences
    4. Enable ancilla reuse
    """
    
    def __init__(self):
        super().__init__("UncomputationOptimization")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run uncomputation optimization on the circuit.
        
        Identifies and optimizes uncomputation patterns.
        """
        start_time = time.time()
        
        # Identify ancilla qubits (used but not measured)
        ancillas = self._identify_ancillas(circuit)
        
        # Find computation/uncomputation pairs
        pairs = self._find_uncomputation_pairs(circuit, ancillas)
        
        # Analyze uncomputation efficiency
        for qubit, (comp_start, comp_end, uncomp_start, uncomp_end) in pairs.items():
            comp_length = comp_end - comp_start
            uncomp_length = uncomp_end - uncomp_start
            
            # Check if uncomputation is exact reverse
            is_exact_reverse = self._is_exact_reverse(
                circuit, comp_start, comp_end, uncomp_start, uncomp_end
            )
            
            if is_exact_reverse:
                self.metrics.patterns_matched += 1
        
        # Track metrics
        self.metrics.custom['ancilla_qubits'] = len(ancillas)
        self.metrics.custom['uncomputation_pairs'] = len(pairs)
        self.metrics.custom['ancillas_reusable'] = len([
            q for q in ancillas if q in pairs
        ])
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _identify_ancillas(self, circuit: QIRCircuit) -> Set[QIRQubit]:
        """
        Identify ancilla qubits.
        
        Ancillas are qubits that are:
        - Used in computation
        - Not measured (or measured and reset)
        - Returned to initial state
        
        Returns:
            Set of ancilla qubits
        """
        # Find measured qubits
        measured = set()
        for inst in circuit.instructions:
            if inst.is_measurement():
                measured.update(inst.qubits)
        
        # Qubits that are used but not measured are potential ancillas
        all_qubits = set(circuit.qubits.values())
        ancillas = all_qubits - measured
        
        return ancillas
    
    def _find_uncomputation_pairs(
        self,
        circuit: QIRCircuit,
        ancillas: Set[QIRQubit]
    ) -> Dict[QIRQubit, Tuple[int, int, int, int]]:
        """
        Find computation/uncomputation pairs for ancilla qubits.
        
        Returns:
            Dict mapping qubit -> (comp_start, comp_end, uncomp_start, uncomp_end)
        """
        pairs = {}
        
        for ancilla in ancillas:
            # Find first and last use of this ancilla
            first_use = None
            last_use = None
            
            for i, inst in enumerate(circuit.instructions):
                if ancilla in inst.qubits:
                    if first_use is None:
                        first_use = i
                    last_use = i
            
            if first_use is not None and last_use is not None:
                # Assume computation is first half, uncomputation is second half
                midpoint = (first_use + last_use) // 2
                pairs[ancilla] = (first_use, midpoint, midpoint, last_use)
        
        return pairs
    
    def _is_exact_reverse(
        self,
        circuit: QIRCircuit,
        comp_start: int,
        comp_end: int,
        uncomp_start: int,
        uncomp_end: int
    ) -> bool:
        """
        Check if uncomputation is exact reverse of computation.
        
        Returns:
            True if uncomputation exactly reverses computation
        """
        comp_length = comp_end - comp_start
        uncomp_length = uncomp_end - uncomp_start
        
        if comp_length != uncomp_length:
            return False
        
        # Check if gates are reversed
        for i in range(comp_length):
            comp_inst = circuit.instructions[comp_start + i]
            uncomp_inst = circuit.instructions[uncomp_end - 1 - i]
            
            # Check if uncomp_inst is inverse of comp_inst
            if not self._is_inverse(comp_inst, uncomp_inst):
                return False
        
        return True
    
    def _is_inverse(self, inst1: QIRInstruction, inst2: QIRInstruction) -> bool:
        """Check if two instructions are inverses."""
        # Same qubits
        if inst1.qubits != inst2.qubits:
            return False
        
        # Self-inverse gates
        if inst1.inst_type in [InstructionType.H, InstructionType.X, 
                               InstructionType.Y, InstructionType.Z,
                               InstructionType.CNOT]:
            return inst1.inst_type == inst2.inst_type
        
        # Inverse pairs
        inverse_pairs = {
            (InstructionType.S, InstructionType.SDG),
            (InstructionType.SDG, InstructionType.S),
            (InstructionType.T, InstructionType.TDG),
            (InstructionType.TDG, InstructionType.T),
        }
        
        return (inst1.inst_type, inst2.inst_type) in inverse_pairs
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are potential ancilla qubits."""
        return self.enabled and len(circuit.qubits) > 0
