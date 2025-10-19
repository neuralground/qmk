"""
Entanglement Tracker

Tracks multi-qubit entanglement beyond pairwise correlations.
Enables proper handling of GHZ states and other multi-qubit entangled states.
"""

from typing import Set, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class EntanglementGroup:
    """
    Represents a group of entangled qubits.
    
    For GHZ state |000⟩ + |111⟩, all qubits are in the same group
    and their measurements must be correlated.
    """
    qubit_ids: Set[str] = field(default_factory=set)
    measurement_outcome: Optional[int] = None  # Shared outcome for all qubits
    
    def add_qubit(self, qubit_id: str):
        """Add a qubit to this entanglement group."""
        self.qubit_ids.add(qubit_id)
    
    def remove_qubit(self, qubit_id: str):
        """Remove a qubit from this entanglement group."""
        self.qubit_ids.discard(qubit_id)
    
    def set_measurement(self, outcome: int):
        """Set the measurement outcome for all qubits in this group."""
        self.measurement_outcome = outcome
    
    def get_measurement(self) -> Optional[int]:
        """Get the shared measurement outcome."""
        return self.measurement_outcome
    
    def is_measured(self) -> bool:
        """Check if this group has been measured."""
        return self.measurement_outcome is not None
    
    def __len__(self):
        return len(self.qubit_ids)


class EntanglementTracker:
    """
    Tracks multi-qubit entanglement relationships.
    
    Maintains groups of entangled qubits and ensures their
    measurements are properly correlated.
    """
    
    def __init__(self):
        # Map from qubit ID to entanglement group
        self.qubit_to_group: Dict[str, EntanglementGroup] = {}
        
        # All entanglement groups
        self.groups: List[EntanglementGroup] = []
    
    def create_entanglement(self, qubit_ids: List[str]):
        """
        Create an entanglement group for the given qubits.
        
        If any qubits are already entangled, merge the groups.
        """
        # Find existing groups
        existing_groups = set()
        for qid in qubit_ids:
            if qid in self.qubit_to_group:
                existing_groups.add(self.qubit_to_group[qid])
        
        if existing_groups:
            # Merge all existing groups
            merged_group = existing_groups.pop()
            for group in existing_groups:
                merged_group.qubit_ids.update(group.qubit_ids)
                self.groups.remove(group)
            
            # Add new qubits
            for qid in qubit_ids:
                merged_group.add_qubit(qid)
                self.qubit_to_group[qid] = merged_group
        else:
            # Create new group
            new_group = EntanglementGroup(set(qubit_ids))
            self.groups.append(new_group)
            for qid in qubit_ids:
                self.qubit_to_group[qid] = new_group
    
    def get_group(self, qubit_id: str) -> Optional[EntanglementGroup]:
        """Get the entanglement group for a qubit."""
        return self.qubit_to_group.get(qubit_id)
    
    def is_entangled(self, qubit_id: str) -> bool:
        """Check if a qubit is entangled."""
        return qubit_id in self.qubit_to_group
    
    def get_entangled_qubits(self, qubit_id: str) -> Set[str]:
        """Get all qubits entangled with the given qubit."""
        group = self.get_group(qubit_id)
        if group:
            return group.qubit_ids - {qubit_id}
        return set()
    
    def set_measurement_outcome(self, qubit_id: str, outcome: int):
        """
        Set measurement outcome for a qubit and its entangled partners.
        
        All qubits in the same entanglement group will share this outcome.
        """
        group = self.get_group(qubit_id)
        if group:
            group.set_measurement(outcome)
    
    def get_measurement_outcome(self, qubit_id: str) -> Optional[int]:
        """Get the measurement outcome for a qubit's entanglement group."""
        group = self.get_group(qubit_id)
        if group:
            return group.get_measurement()
        return None
    
    def break_entanglement(self, qubit_id: str):
        """Break entanglement for a qubit (e.g., after measurement)."""
        group = self.get_group(qubit_id)
        if group:
            group.remove_qubit(qubit_id)
            del self.qubit_to_group[qubit_id]
            
            # Remove empty groups
            if len(group) == 0:
                self.groups.remove(group)
    
    def get_statistics(self) -> Dict:
        """Get statistics about entanglement."""
        return {
            'num_groups': len(self.groups),
            'num_entangled_qubits': len(self.qubit_to_group),
            'group_sizes': [len(g) for g in self.groups],
            'max_group_size': max([len(g) for g in self.groups], default=0)
        }
