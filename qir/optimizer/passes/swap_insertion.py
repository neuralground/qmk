"""
SWAP Insertion Pass

Inserts SWAP gates to satisfy hardware connectivity constraints.

For hardware with limited connectivity, two-qubit gates can only be applied
to adjacent qubits. This pass inserts SWAPs to bring qubits together.

Example:
  Hardware: Linear topology 0-1-2-3
  Circuit: CNOT(0, 3)
  
  After SWAP insertion:
    SWAP(1, 2)
    SWAP(2, 3)
    CNOT(0, 3)  # Now 0 and 3 are adjacent
    SWAP(2, 3)  # Restore
    SWAP(1, 2)
"""

import time
from typing import Dict, List, Tuple, Set
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType
from ..topology import HardwareTopology


class SWAPInsertionPass(OptimizationPass):
    """
    Inserts SWAP gates to satisfy hardware connectivity.
    
    Strategy:
    1. Maintain mapping of logical qubits to physical qubits
    2. For each two-qubit gate, check if qubits are adjacent
    3. If not, insert SWAPs to bring them together
    4. Update mapping after each SWAP
    """
    
    def __init__(self, topology: HardwareTopology):
        """
        Initialize SWAP insertion pass.
        
        Args:
            topology: Hardware topology defining connectivity
        """
        super().__init__("SWAPInsertion")
        self.topology = topology
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run SWAP insertion on the circuit.
        
        Inserts SWAPs to satisfy topology constraints.
        """
        start_time = time.time()
        
        # Create initial mapping (logical -> physical)
        # For now, use identity mapping
        logical_to_physical = self._create_initial_mapping(circuit)
        
        # Process instructions and insert SWAPs as needed
        new_instructions = []
        
        for inst in circuit.instructions:
            if inst.is_two_qubit_gate():
                # Check if qubits are adjacent in current mapping
                logical_q0, logical_q1 = inst.qubits[0], inst.qubits[1]
                physical_q0 = logical_to_physical[logical_q0]
                physical_q1 = logical_to_physical[logical_q1]
                
                if not self.topology.are_connected(physical_q0, physical_q1):
                    # Need to insert SWAPs
                    swaps = self._find_swap_sequence(
                        physical_q0, physical_q1, logical_to_physical
                    )
                    
                    # Add SWAP instructions
                    for swap_q0, swap_q1 in swaps:
                        # Find logical qubits for these physical qubits
                        log_q0 = self._physical_to_logical(swap_q0, logical_to_physical)
                        log_q1 = self._physical_to_logical(swap_q1, logical_to_physical)
                        
                        swap_inst = QIRInstruction(
                            InstructionType.SWAP,
                            [log_q0, log_q1]
                        )
                        new_instructions.append(swap_inst)
                        
                        # Update mapping
                        logical_to_physical[log_q0] = swap_q1
                        logical_to_physical[log_q1] = swap_q0
                        
                        self.metrics.swap_gates_added += 1
                        self.metrics.gates_added += 1
            
            # Add the original instruction
            new_instructions.append(inst)
        
        # Replace circuit instructions
        circuit.instructions = new_instructions
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _create_initial_mapping(self, circuit: QIRCircuit) -> Dict[QIRQubit, int]:
        """
        Create initial logical to physical qubit mapping.
        
        For now, uses identity mapping (logical i -> physical i).
        A smarter approach would analyze the circuit first.
        """
        mapping = {}
        for i, (qid, qubit) in enumerate(sorted(circuit.qubits.items())):
            if i < self.topology.num_qubits:
                mapping[qubit] = i
            else:
                # More logical qubits than physical - error
                raise ValueError(
                    f"Circuit has {len(circuit.qubits)} qubits but "
                    f"topology only has {self.topology.num_qubits}"
                )
        return mapping
    
    def _find_swap_sequence(
        self,
        physical_q0: int,
        physical_q1: int,
        mapping: Dict[QIRQubit, int]
    ) -> List[Tuple[int, int]]:
        """
        Find sequence of SWAPs to bring two physical qubits adjacent.
        
        Uses a simple greedy approach: move q0 towards q1.
        
        Returns:
            List of (physical_qubit_0, physical_qubit_1) SWAP pairs
        """
        swaps = []
        
        # Find path from q0 to q1
        path = self.topology.find_path(physical_q0, physical_q1)
        
        if not path or len(path) < 2:
            return swaps
        
        # Move q0 along the path towards q1
        current_pos = physical_q0
        for next_pos in path[1:-1]:  # Don't include start or end
            swaps.append((current_pos, next_pos))
            current_pos = next_pos
        
        return swaps
    
    def _physical_to_logical(
        self,
        physical: int,
        mapping: Dict[QIRQubit, int]
    ) -> QIRQubit:
        """Find logical qubit mapped to given physical qubit."""
        for logical, phys in mapping.items():
            if phys == physical:
                return logical
        raise ValueError(f"No logical qubit mapped to physical {physical}")
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are two-qubit gates."""
        has_two_qubit = any(inst.is_two_qubit_gate() for inst in circuit.instructions)
        return self.enabled and has_two_qubit
