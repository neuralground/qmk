"""
Checkpoint Manager

Manages checkpoints for quantum state snapshots.
"""

import time
import copy
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Checkpoint:
    """Represents a quantum state checkpoint."""
    checkpoint_id: str
    job_id: str
    epoch: int
    node_id: str
    qubit_states: Dict[str, any]
    classical_registers: Dict[str, int]
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class CheckpointManager:
    """Manages quantum state checkpoints."""
    
    def __init__(self, max_checkpoints: int = 100):
        self.max_checkpoints = max_checkpoints
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.job_checkpoints: Dict[str, List[str]] = {}
        self.checkpoint_counter = 0
    
    def create_checkpoint(
        self,
        job_id: str,
        epoch: int,
        node_id: str,
        resource_manager,
        metadata: Optional[Dict] = None
    ) -> Checkpoint:
        """Create a checkpoint."""
        if len(self.checkpoints) >= self.max_checkpoints:
            self._evict_oldest_checkpoint()
        
        checkpoint_id = f"ckpt_{job_id}_{self.checkpoint_counter}"
        self.checkpoint_counter += 1
        
        qubit_states = self._snapshot_qubits(resource_manager)
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            epoch=epoch,
            node_id=node_id,
            qubit_states=qubit_states,
            classical_registers={},
            metadata=metadata or {}
        )
        
        self.checkpoints[checkpoint_id] = checkpoint
        
        if job_id not in self.job_checkpoints:
            self.job_checkpoints[job_id] = []
        self.job_checkpoints[job_id].append(checkpoint_id)
        
        return checkpoint
    
    def restore_checkpoint(self, checkpoint_id: str, resource_manager) -> Dict:
        """Restore from checkpoint."""
        if checkpoint_id not in self.checkpoints:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")
        
        checkpoint = self.checkpoints[checkpoint_id]
        restored_qubits = self._restore_qubits(checkpoint.qubit_states, resource_manager)
        
        return {
            "checkpoint_id": checkpoint_id,
            "job_id": checkpoint.job_id,
            "epoch": checkpoint.epoch,
            "qubits_restored": restored_qubits
        }
    
    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint:
        """Get checkpoint by ID."""
        if checkpoint_id not in self.checkpoints:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")
        return self.checkpoints[checkpoint_id]
    
    def list_checkpoints(self, job_id: Optional[str] = None) -> List[Checkpoint]:
        """List checkpoints."""
        if job_id:
            checkpoint_ids = self.job_checkpoints.get(job_id, [])
            return [self.checkpoints[cid] for cid in checkpoint_ids if cid in self.checkpoints]
        return list(self.checkpoints.values())
    
    def delete_checkpoint(self, checkpoint_id: str):
        """Delete checkpoint."""
        if checkpoint_id in self.checkpoints:
            checkpoint = self.checkpoints[checkpoint_id]
            job_id = checkpoint.job_id
            
            if job_id in self.job_checkpoints:
                self.job_checkpoints[job_id].remove(checkpoint_id)
                if not self.job_checkpoints[job_id]:
                    del self.job_checkpoints[job_id]
            
            del self.checkpoints[checkpoint_id]
    
    def _snapshot_qubits(self, resource_manager) -> Dict:
        """Snapshot qubit states."""
        snapshot = {}
        for vq_id, qubit in resource_manager.logical_qubits.items():
            snapshot[vq_id] = {
                "state": copy.deepcopy(qubit.state),
                "profile": qubit.profile.to_dict()
            }
        return snapshot
    
    def _restore_qubits(self, qubit_states: Dict, resource_manager) -> List[str]:
        """Restore qubit states."""
        restored = []
        for vq_id, state_data in qubit_states.items():
            if vq_id in resource_manager.logical_qubits:
                qubit = resource_manager.logical_qubits[vq_id]
                qubit.state = copy.deepcopy(state_data["state"])
                restored.append(vq_id)
        return restored
    
    def _evict_oldest_checkpoint(self):
        """Evict oldest checkpoint."""
        if not self.checkpoints:
            return
        oldest_id = min(self.checkpoints.keys(), 
                       key=lambda k: self.checkpoints[k].created_at)
        self.delete_checkpoint(oldest_id)
