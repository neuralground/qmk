"""
Dead Code Elimination Pass

Removes operations on qubits that are never measured or used.

Patterns:
- Qubit allocated but never measured → remove all operations
- Operations after final measurement → remove
- Unused ancilla qubits → remove entirely
- Gates that don't affect measured qubits → remove

Example:
  Before:
    q0: H → X → MEASURE
    q1: H → X → (no measurement)
  
  After:
    q0: H → X → MEASURE
    (q1 operations removed)
"""

import time
from typing import Set, Dict, List
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit


class DeadCodeEliminationPass(OptimizationPass):
    """
    Removes dead code from circuits.
    
    A qubit's operations are dead code if:
    1. The qubit is never measured
    2. The qubit doesn't affect any measured qubits
    3. Operations occur after the qubit's final measurement
    """
    
    def __init__(self):
        super().__init__("DeadCodeElimination")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run dead code elimination on the circuit.
        
        Strategy:
        1. Identify which qubits are measured
        2. Build dependency graph (which qubits affect which)
        3. Mark live qubits (measured or affect measured)
        4. Remove operations on dead qubits
        5. Remove operations after final measurements
        """
        start_time = time.time()
        
        # Find measured qubits
        measured_qubits = self._find_measured_qubits(circuit)
        
        if not measured_qubits:
            # No measurements - all operations are potentially dead
            # But we'll be conservative and keep everything
            self.metrics.execution_time_ms = (time.time() - start_time) * 1000
            return circuit
        
        # Build dependency graph
        dependencies = self._build_dependencies(circuit)
        
        # Find live qubits (measured or affect measured)
        live_qubits = self._find_live_qubits(measured_qubits, dependencies)
        
        # Find last measurement for each qubit
        last_measurements = self._find_last_measurements(circuit)
        
        # Remove dead operations
        instructions_to_remove = set()
        
        for i, inst in enumerate(circuit.instructions):
            # Skip non-gate operations
            if not inst.is_gate():
                continue
            
            # Check if any qubit in this instruction is dead
            all_dead = True
            for qubit in inst.qubits:
                if qubit in live_qubits:
                    all_dead = False
                    break
            
            if all_dead:
                # All qubits are dead - remove this instruction
                instructions_to_remove.add(i)
                self.metrics.gates_removed += 1
                continue
            
            # Check if this operation is after a qubit's final measurement
            for qubit in inst.qubits:
                if qubit in last_measurements:
                    last_meas_idx = last_measurements[qubit]
                    if i > last_meas_idx:
                        # Operation after final measurement - dead code
                        instructions_to_remove.add(i)
                        self.metrics.gates_removed += 1
                        break
        
        # Remove marked instructions (in reverse order)
        for idx in sorted(instructions_to_remove, reverse=True):
            circuit.remove_instruction(idx)
        
        # Track qubit reduction
        dead_qubits = set(circuit.qubits.values()) - live_qubits
        self.metrics.qubit_reduction = len(dead_qubits)
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _find_measured_qubits(self, circuit: QIRCircuit) -> Set[QIRQubit]:
        """Find all qubits that are measured."""
        measured = set()
        for inst in circuit.instructions:
            if inst.is_measurement():
                measured.update(inst.qubits)
        return measured
    
    def _build_dependencies(self, circuit: QIRCircuit) -> Dict[QIRQubit, Set[QIRQubit]]:
        """
        Build dependency graph showing which qubits affect which.
        
        For two-qubit gates, both qubits affect each other.
        
        Returns:
            Dict mapping qubit -> set of qubits it affects
        """
        dependencies = {q: set() for q in circuit.qubits.values()}
        
        for inst in circuit.instructions:
            if inst.is_two_qubit_gate():
                # Two-qubit gates create mutual dependencies
                q0, q1 = inst.qubits[0], inst.qubits[1]
                dependencies[q0].add(q1)
                dependencies[q1].add(q0)
        
        return dependencies
    
    def _find_live_qubits(
        self, 
        measured: Set[QIRQubit], 
        dependencies: Dict[QIRQubit, Set[QIRQubit]]
    ) -> Set[QIRQubit]:
        """
        Find all live qubits (measured or affect measured qubits).
        
        Uses transitive closure to find all qubits that affect measured qubits.
        """
        live = set(measured)
        changed = True
        
        # Iterate until no new live qubits are found
        while changed:
            changed = False
            new_live = set()
            
            for qubit in dependencies.keys():
                if qubit in live:
                    continue
                
                # Check if this qubit affects any live qubit
                if dependencies[qubit].intersection(live):
                    new_live.add(qubit)
                    changed = True
            
            live.update(new_live)
        
        return live
    
    def _find_last_measurements(self, circuit: QIRCircuit) -> Dict[QIRQubit, int]:
        """
        Find the index of the last measurement for each qubit.
        
        Returns:
            Dict mapping qubit -> index of last measurement
        """
        last_measurements = {}
        
        for i, inst in enumerate(circuit.instructions):
            if inst.is_measurement():
                for qubit in inst.qubits:
                    last_measurements[qubit] = i
        
        return last_measurements
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are gates and measurements."""
        has_gates = circuit.get_gate_count() > 0
        has_measurements = any(inst.is_measurement() for inst in circuit.instructions)
        return self.enabled and has_gates and has_measurements
