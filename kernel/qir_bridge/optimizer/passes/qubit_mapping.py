"""
Qubit Mapping Pass

Intelligently maps logical qubits to physical qubits to minimize SWAP overhead.

Strategy:
- Analyze circuit to find frequently interacting qubit pairs
- Place frequently interacting qubits close together on hardware
- Minimize total distance for all two-qubit gates

Example:
  Circuit: CNOT(0,1), CNOT(1,2), CNOT(0,1)
  Analysis: (0,1) interact 2x, (1,2) interact 1x
  
  Linear topology: 0-1-2
  Good mapping: logical 0→physical 0, logical 1→physical 1, logical 2→physical 2
  (All interactions are adjacent!)
"""

import time
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRQubit
from ..topology import HardwareTopology


class QubitMappingPass(OptimizationPass):
    """
    Maps logical qubits to physical qubits to minimize SWAP overhead.
    
    Uses a greedy heuristic:
    1. Build interaction graph (which qubits interact)
    2. Find most frequently interacting pairs
    3. Place them close together on hardware topology
    """
    
    def __init__(self, topology: HardwareTopology):
        """
        Initialize qubit mapping pass.
        
        Args:
            topology: Hardware topology defining connectivity
        """
        super().__init__("QubitMapping")
        self.topology = topology
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run qubit mapping on the circuit.
        
        Creates an optimized logical-to-physical mapping and updates
        qubit references in the circuit.
        """
        start_time = time.time()
        
        # Analyze circuit interactions
        interactions = self._analyze_interactions(circuit)
        
        # Create optimal mapping
        mapping = self._create_mapping(circuit, interactions)
        
        # Store mapping in circuit metadata for SWAP insertion to use
        circuit.metadata['qubit_mapping'] = mapping
        
        # Track how good the mapping is
        total_distance = self._calculate_total_distance(interactions, mapping)
        self.metrics.custom['total_distance'] = total_distance
        self.metrics.custom['avg_distance'] = (
            total_distance / len(interactions) if interactions else 0
        )
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _analyze_interactions(self, circuit: QIRCircuit) -> Dict[Tuple[QIRQubit, QIRQubit], int]:
        """
        Analyze which qubits interact and how frequently.
        
        Returns:
            Dict mapping (qubit1, qubit2) -> interaction count
        """
        interactions = defaultdict(int)
        
        for inst in circuit.instructions:
            if inst.is_two_qubit_gate():
                q0, q1 = inst.qubits[0], inst.qubits[1]
                # Normalize order (smaller id first)
                pair = tuple(sorted([q0, q1], key=lambda q: q.id))
                interactions[pair] += 1
        
        return dict(interactions)
    
    def _create_mapping(
        self,
        circuit: QIRCircuit,
        interactions: Dict[Tuple[QIRQubit, QIRQubit], int]
    ) -> Dict[QIRQubit, int]:
        """
        Create logical-to-physical qubit mapping.
        
        Uses greedy heuristic:
        1. Sort qubit pairs by interaction frequency
        2. Place most frequently interacting pairs adjacent
        3. Fill in remaining qubits
        
        Args:
            circuit: Circuit to map
            interactions: Interaction frequency data
        
        Returns:
            Dict mapping logical qubit -> physical qubit index
        """
        mapping = {}
        used_physical = set()
        
        if not interactions:
            # No interactions - use identity mapping
            for i, (qid, qubit) in enumerate(sorted(circuit.qubits.items())):
                if i < self.topology.num_qubits:
                    mapping[qubit] = i
                    used_physical.add(i)
            return mapping
        
        # Sort pairs by interaction frequency (most frequent first)
        sorted_pairs = sorted(interactions.items(), key=lambda x: -x[1])
        
        # Place most frequently interacting pair first
        if sorted_pairs:
            (q0, q1), _ = sorted_pairs[0]
            # Place on adjacent physical qubits
            mapping[q0] = 0
            mapping[q1] = 1 if self.topology.are_connected(0, 1) else self._find_nearest_to(0, used_physical)
            used_physical.add(mapping[q0])
            used_physical.add(mapping[q1])
        
        # Place remaining qubits from interaction pairs
        for (q0, q1), count in sorted_pairs[1:]:
            if q0 not in mapping and q1 not in mapping:
                # Neither placed yet - find good spot
                phys = self._find_free_adjacent_pair(used_physical)
                if phys:
                    mapping[q0] = phys[0]
                    mapping[q1] = phys[1]
                    used_physical.update(phys)
            elif q0 in mapping and q1 not in mapping:
                # q0 placed, place q1 near it
                phys_q1 = self._find_nearest_to(mapping[q0], used_physical)
                mapping[q1] = phys_q1
                used_physical.add(phys_q1)
            elif q1 in mapping and q0 not in mapping:
                # q1 placed, place q0 near it
                phys_q0 = self._find_nearest_to(mapping[q1], used_physical)
                mapping[q0] = phys_q0
                used_physical.add(phys_q0)
        
        # Place any remaining qubits
        for qubit in circuit.qubits.values():
            if qubit not in mapping:
                for i in range(self.topology.num_qubits):
                    if i not in used_physical:
                        mapping[qubit] = i
                        used_physical.add(i)
                        break
        
        return mapping
    
    def _find_nearest_to(self, physical: int, used: Set[int]) -> int:
        """Find nearest free physical qubit to given position."""
        for distance in range(1, self.topology.num_qubits):
            for candidate in range(self.topology.num_qubits):
                if candidate not in used:
                    if self.topology.get_distance(physical, candidate) == distance:
                        return candidate
        # Fallback: return any free qubit
        for i in range(self.topology.num_qubits):
            if i not in used:
                return i
        return 0  # Should never reach here
    
    def _find_free_adjacent_pair(self, used: Set[int]) -> Tuple[int, int]:
        """Find a pair of adjacent free physical qubits."""
        for i in range(self.topology.num_qubits):
            if i not in used:
                for j in self.topology.get_neighbors(i):
                    if j not in used:
                        return (i, j)
        return None
    
    def _calculate_total_distance(
        self,
        interactions: Dict[Tuple[QIRQubit, QIRQubit], int],
        mapping: Dict[QIRQubit, int]
    ) -> float:
        """
        Calculate total weighted distance for all interactions.
        
        Lower is better - means qubits are placed closer together.
        """
        total = 0
        for (q0, q1), count in interactions.items():
            if q0 in mapping and q1 in mapping:
                phys0 = mapping[q0]
                phys1 = mapping[q1]
                distance = self.topology.get_distance(phys0, phys1)
                total += distance * count
        return total
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are qubits to map."""
        return self.enabled and len(circuit.qubits) > 0
