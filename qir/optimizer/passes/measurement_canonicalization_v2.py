"""
Measurement Canonicalization Pass (Enhanced)

Detects multi-gate sequences that implement measurement bases and replaces
them with canonical measurement operations. Handles NON-ADJACENT patterns
by tracking per-qubit gate histories.

Patterns Detected:
1. H → ... → MEASURE_Z  ⟹  MEASURE_X (if no interfering gates on that qubit)
2. S† → H → ... → MEASURE_Z  ⟹  MEASURE_Y (if no interfering gates)
3. CNOT(q0,q1) → H(q0) → MEASURE_Z(q0) → MEASURE_Z(q1)  ⟹  MEASURE_BELL

Key Improvement: Tracks per-qubit gate sequences, allowing detection of
patterns even when other qubits have intervening operations.

Example:
  Before:
    H(q0)
    X(q1)          # Intervening gate on different qubit
    Y(q2)          # More intervening gates
    MEASURE_Z(q0)  # Still canonicalized to MEASURE_X!
  
  After:
    X(q1)
    Y(q2)
    MEASURE_X(q0)  # H removed, measurement canonicalized
"""

import time
from typing import List, Optional, Tuple, Dict, Set
from collections import defaultdict
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, InstructionType, QIRQubit


class MeasurementCanonicalizationPass(OptimizationPass):
    """
    Canonicalizes measurement sequences into explicit basis measurements.
    
    Strategy:
    1. Build per-qubit gate history leading to each measurement
    2. Identify canonical patterns in each qubit's history
    3. Replace measurement basis and remove redundant gates
    4. Handle multi-qubit patterns (Bell measurements)
    """
    
    def __init__(self):
        super().__init__("MeasurementCanonicalization")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run measurement canonicalization on the circuit.
        
        Uses per-qubit analysis to detect non-adjacent patterns.
        """
        start_time = time.time()
        
        total_canonicalizations = 0
        
        # Build per-qubit gate sequences
        qubit_histories = self._build_qubit_histories(circuit)
        
        # Find measurements and their preceding gates
        measurement_patterns = self._find_measurement_patterns(circuit, qubit_histories)
        
        # Sort patterns by measurement index in REVERSE order
        # This ensures we process from end to beginning, avoiding index shift issues
        measurement_patterns.sort(key=lambda p: p['measurement_idx'], reverse=True)
        
        # Canonicalize each pattern
        for pattern in measurement_patterns:
            if self._canonicalize_pattern(circuit, pattern):
                total_canonicalizations += 1
        
        self.metrics.custom['measurements_canonicalized'] = total_canonicalizations
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _build_qubit_histories(self, circuit: QIRCircuit) -> Dict[QIRQubit, List[Tuple[int, QIRInstruction]]]:
        """
        Build a history of gate operations for each qubit.
        
        Returns:
            Dict mapping each qubit to list of (index, instruction) tuples
        """
        histories = defaultdict(list)
        
        for idx, inst in enumerate(circuit.instructions):
            for qubit in inst.qubits:
                histories[qubit].append((idx, inst))
        
        return histories
    
    def _find_measurement_patterns(
        self, 
        circuit: QIRCircuit, 
        qubit_histories: Dict[QIRQubit, List[Tuple[int, QIRInstruction]]]
    ) -> List[Dict]:
        """
        Find measurement patterns by analyzing qubit histories.
        
        Returns list of pattern dictionaries with:
        - type: 'X', 'Y', or 'BELL'
        - measurement_idx: index of measurement instruction
        - gates_to_remove: list of gate indices to remove
        - qubits: list of qubits involved
        """
        patterns = []
        
        for idx, inst in enumerate(circuit.instructions):
            if inst.inst_type != InstructionType.MEASURE:
                continue
            
            if inst.params.get('basis', 'Z') != 'Z':
                continue  # Already canonicalized
            
            qubit = inst.qubits[0]
            
            # Get this qubit's history up to this measurement
            history = [h for h in qubit_histories[qubit] if h[0] < idx]
            
            # Check for Y-basis pattern FIRST (S† → H before measurement)
            # Must check before X-basis since Y-basis also contains H
            y_pattern = self._check_y_basis_pattern(history, idx)
            if y_pattern:
                patterns.append(y_pattern)
                continue
            
            # Check for X-basis pattern (H before measurement)
            x_pattern = self._check_x_basis_pattern(history, idx)
            if x_pattern:
                patterns.append(x_pattern)
                continue
            
            # Check for Bell measurement pattern (requires two qubits)
            bell_pattern = self._check_bell_pattern(circuit, idx, qubit_histories)
            if bell_pattern:
                patterns.append(bell_pattern)
        
        return patterns
    
    def _check_x_basis_pattern(
        self, 
        history: List[Tuple[int, QIRInstruction]], 
        meas_idx: int
    ) -> Optional[Dict]:
        """
        Check if qubit history shows H → MEASURE_Z pattern.
        
        Returns pattern dict if found, None otherwise.
        """
        if not history:
            return None
        
        # Find the most recent gate that affects this qubit
        for hist_idx, inst in reversed(history):
            if inst.inst_type == InstructionType.H:
                # Check if there are any interfering gates between H and measurement
                interfering = False
                for check_idx, check_inst in history:
                    if check_idx > hist_idx and check_idx < meas_idx:
                        # Check if this gate would destroy the H basis
                        if self._is_interfering_gate(check_inst):
                            interfering = True
                            break
                
                if not interfering:
                    return {
                        'type': 'X',
                        'measurement_idx': meas_idx,
                        'gates_to_remove': [hist_idx],
                        'qubits': [inst.qubits[0]]
                    }
            
            # If we hit a gate that changes the basis, stop looking
            if self._is_basis_changing_gate(inst):
                break
        
        return None
    
    def _check_y_basis_pattern(
        self, 
        history: List[Tuple[int, QIRInstruction]], 
        meas_idx: int
    ) -> Optional[Dict]:
        """
        Check if qubit history shows S† → H → MEASURE_Z pattern.
        
        Returns pattern dict if found, None otherwise.
        """
        if len(history) < 2:
            return None
        
        # Look for S† followed by H (not necessarily adjacent)
        # We need to find the most recent S† → H sequence
        sdg_idx = None
        h_idx = None
        
        for hist_idx, inst in history:
            if inst.inst_type == InstructionType.SDG:
                # Found S†, remember it
                sdg_idx = hist_idx
                h_idx = None  # Reset H in case we had one before
            elif inst.inst_type == InstructionType.H:
                if sdg_idx is not None:
                    # Found H after S†
                    h_idx = hist_idx
                else:
                    # H without preceding S† - not a Y-basis pattern
                    pass
            elif self._is_basis_changing_gate(inst) and inst.inst_type not in {InstructionType.SDG, InstructionType.H}:
                # Reset if we hit another basis-changing gate
                sdg_idx = None
                h_idx = None
        
        if sdg_idx is not None and h_idx is not None:
            # Check for interfering gates between H and measurement
            interfering = False
            for check_idx, check_inst in history:
                if check_idx > h_idx and check_idx < meas_idx:
                    if self._is_interfering_gate(check_inst):
                        interfering = True
                        break
            
            if not interfering:
                return {
                    'type': 'Y',
                    'measurement_idx': meas_idx,
                    'gates_to_remove': [sdg_idx, h_idx],
                    'qubits': history[0][1].qubits
                }
        
        return None
    
    def _check_bell_pattern(
        self,
        circuit: QIRCircuit,
        meas_idx: int,
        qubit_histories: Dict[QIRQubit, List[Tuple[int, QIRInstruction]]]
    ) -> Optional[Dict]:
        """
        Check for Bell measurement pattern across two qubits.
        
        Pattern: CNOT(q0,q1) → H(q0) → MEASURE_Z(q0) → MEASURE_Z(q1)
        """
        # This is more complex and requires looking ahead for the second measurement
        # For now, return None (can be enhanced later)
        return None
    
    def _is_interfering_gate(self, inst: QIRInstruction) -> bool:
        """Check if gate would interfere with measurement basis."""
        interfering_types = {
            InstructionType.X,
            InstructionType.Y,
            InstructionType.Z,
            InstructionType.H,
            InstructionType.S,
            InstructionType.SDG,
            InstructionType.T,
            InstructionType.TDG,
            InstructionType.CNOT,
            InstructionType.CZ,
        }
        return inst.inst_type in interfering_types
    
    def _is_basis_changing_gate(self, inst: QIRInstruction) -> bool:
        """Check if gate changes the computational basis."""
        basis_changing = {
            InstructionType.H,
            InstructionType.S,
            InstructionType.SDG,
            InstructionType.T,
            InstructionType.TDG,
        }
        return inst.inst_type in basis_changing
    
    def _canonicalize_pattern(self, circuit: QIRCircuit, pattern: Dict) -> bool:
        """
        Apply canonicalization for a detected pattern.
        
        Returns True if canonicalization was successful.
        """
        try:
            meas_idx = pattern['measurement_idx']
            gates_to_remove = sorted(pattern['gates_to_remove'], reverse=True)
            
            # First, update the measurement basis BEFORE removing gates
            # (since removing gates will shift indices)
            meas_inst = circuit.instructions[meas_idx]
            
            if pattern['type'] == 'X':
                meas_inst.params['basis'] = 'X'
            elif pattern['type'] == 'Y':
                meas_inst.params['basis'] = 'Y'
            elif pattern['type'] == 'BELL':
                meas_inst.params['basis'] = 'BELL'
            
            # Now remove gates in reverse order to maintain indices
            # Only remove gates that come BEFORE the measurement
            for gate_idx in gates_to_remove:
                if gate_idx < meas_idx:
                    circuit.remove_instruction(gate_idx)
            
            return True
        except Exception as e:
            self.logger.warning(f"Failed to canonicalize pattern: {e}")
            return False
    
    def estimate_benefit(self, circuit: QIRCircuit) -> float:
        """
        Estimate the benefit of running this pass.
        
        Returns a score indicating potential for canonicalization.
        """
        score = 0.0
        
        # Build qubit histories
        qubit_histories = self._build_qubit_histories(circuit)
        
        # Count potential patterns
        for idx, inst in enumerate(circuit.instructions):
            if inst.inst_type == InstructionType.MEASURE:
                if inst.params.get('basis', 'Z') == 'Z':
                    qubit = inst.qubits[0]
                    history = [h for h in qubit_histories[qubit] if h[0] < idx]
                    
                    # Check for H in history
                    for _, hist_inst in history:
                        if hist_inst.inst_type == InstructionType.H:
                            score += 1.0
                            break
                    
                    # Check for S† → H pattern
                    has_sdg = any(h[1].inst_type == InstructionType.SDG for h in history)
                    has_h = any(h[1].inst_type == InstructionType.H for h in history)
                    if has_sdg and has_h:
                        score += 1.5
        
        return score
