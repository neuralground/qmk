"""
Migration Manager

Manages quantum state migration between execution contexts.
Enables moving computation between resources at fence points.
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .checkpoint_manager import CheckpointManager, Checkpoint


@dataclass
class MigrationPoint:
    """
    Represents a valid migration point in execution.
    
    Migration points occur at:
    - FENCE operations (explicit synchronization)
    - Measurement operations (natural boundaries)
    - Between REV segments
    """
    node_id: str
    epoch: int
    is_fence: bool
    qubits_live: List[str]
    can_migrate: bool
    reason: Optional[str] = None


@dataclass
class MigrationRecord:
    """Record of a completed migration."""
    migration_id: str
    job_id: str
    from_context: str
    to_context: str
    checkpoint_id: str
    migration_point: MigrationPoint
    started_at: float
    completed_at: Optional[float] = None
    success: bool = False
    error: Optional[str] = None


class MigrationManager:
    """
    Manages quantum state migration at fence points.
    
    Provides:
    - Identification of migration points
    - State transfer between contexts
    - Migration validation
    - Rollback on migration failure
    """
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        """
        Initialize migration manager.
        
        Args:
            checkpoint_manager: CheckpointManager for state snapshots
        """
        self.checkpoint_manager = checkpoint_manager
        self.migration_records: Dict[str, MigrationRecord] = {}
        self.migration_counter = 0
    
    def identify_migration_points(self, graph: Dict) -> List[MigrationPoint]:
        """
        Identify valid migration points in a QVM graph.
        
        Args:
            graph: QVM graph dictionary
        
        Returns:
            List of MigrationPoint objects
        """
        migration_points = []
        nodes = {node['id']: node for node in graph['nodes']}
        
        # Build dependency graph to track qubit liveness
        live_qubits = self._analyze_qubit_liveness(graph)
        
        for node_id, node in nodes.items():
            op = node.get('op', '')
            
            # Check if this is a valid migration point
            is_fence = op == 'FENCE'
            is_measurement = op in ['MEASURE_Z', 'MEASURE_X']
            is_boundary = op in ['FREE_LQ', 'CLOSE_CHAN']
            
            if is_fence or is_measurement or is_boundary:
                # Get live qubits at this point
                qubits_at_point = live_qubits.get(node_id, [])
                
                # Determine if migration is possible
                can_migrate = True
                reason = None
                
                if not qubits_at_point:
                    can_migrate = False
                    reason = "No live qubits"
                
                # Estimate epoch (simplified)
                epoch = self._estimate_epoch(node_id, nodes)
                
                migration_point = MigrationPoint(
                    node_id=node_id,
                    epoch=epoch,
                    is_fence=is_fence,
                    qubits_live=qubits_at_point,
                    can_migrate=can_migrate,
                    reason=reason
                )
                
                migration_points.append(migration_point)
        
        return migration_points
    
    def initiate_migration(
        self,
        job_id: str,
        migration_point: MigrationPoint,
        from_context: str,
        to_context: str,
        resource_manager
    ) -> MigrationRecord:
        """
        Initiate state migration at a migration point.
        
        Args:
            job_id: Job identifier
            migration_point: MigrationPoint to migrate at
            from_context: Source execution context
            to_context: Destination execution context
            resource_manager: Resource manager with current state
        
        Returns:
            MigrationRecord tracking the migration
        
        Raises:
            RuntimeError: If migration cannot be initiated
        """
        if not migration_point.can_migrate:
            raise RuntimeError(
                f"Cannot migrate at {migration_point.node_id}: "
                f"{migration_point.reason}"
            )
        
        # Generate migration ID
        migration_id = f"mig_{job_id}_{self.migration_counter}"
        self.migration_counter += 1
        
        # Create checkpoint at migration point
        checkpoint = self.checkpoint_manager.create_checkpoint(
            job_id=job_id,
            epoch=migration_point.epoch,
            node_id=migration_point.node_id,
            resource_manager=resource_manager,
            metadata={
                "migration_id": migration_id,
                "from_context": from_context,
                "to_context": to_context
            }
        )
        
        # Create migration record
        record = MigrationRecord(
            migration_id=migration_id,
            job_id=job_id,
            from_context=from_context,
            to_context=to_context,
            checkpoint_id=checkpoint.checkpoint_id,
            migration_point=migration_point,
            started_at=time.time()
        )
        
        self.migration_records[migration_id] = record
        
        return record
    
    def complete_migration(
        self,
        migration_id: str,
        resource_manager,
        success: bool = True,
        error: Optional[str] = None
    ) -> MigrationRecord:
        """
        Complete a migration by restoring state in new context.
        
        Args:
            migration_id: Migration identifier
            resource_manager: Resource manager in new context
            success: Whether migration succeeded
            error: Optional error message if failed
        
        Returns:
            Updated MigrationRecord
        
        Raises:
            KeyError: If migration not found
        """
        if migration_id not in self.migration_records:
            raise KeyError(f"Migration '{migration_id}' not found")
        
        record = self.migration_records[migration_id]
        
        if success:
            # Restore checkpoint in new context
            self.checkpoint_manager.restore_checkpoint(
                record.checkpoint_id,
                resource_manager
            )
        
        # Update record
        record.completed_at = time.time()
        record.success = success
        record.error = error
        
        return record
    
    def validate_migration(
        self,
        migration_id: str,
        expected_state: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a migration completed correctly.
        
        Args:
            migration_id: Migration identifier
            expected_state: Optional expected quantum state
        
        Returns:
            (is_valid, error_message) tuple
        """
        if migration_id not in self.migration_records:
            return False, f"Migration '{migration_id}' not found"
        
        record = self.migration_records[migration_id]
        
        if not record.success:
            return False, f"Migration failed: {record.error}"
        
        if record.completed_at is None:
            return False, "Migration not completed"
        
        # Verify checkpoint exists
        try:
            checkpoint = self.checkpoint_manager.get_checkpoint(record.checkpoint_id)
        except KeyError:
            return False, "Checkpoint lost during migration"
        
        # Verify qubits
        expected_qubits = set(record.migration_point.qubits_live)
        actual_qubits = set(checkpoint.qubit_states.keys())
        
        if expected_qubits != actual_qubits:
            return False, f"Qubit mismatch: expected {expected_qubits}, got {actual_qubits}"
        
        return True, None
    
    def rollback_migration(
        self,
        migration_id: str,
        resource_manager
    ) -> Dict:
        """
        Rollback a failed migration.
        
        Args:
            migration_id: Migration identifier
            resource_manager: Resource manager to restore to
        
        Returns:
            Rollback result dictionary
        """
        if migration_id not in self.migration_records:
            raise KeyError(f"Migration '{migration_id}' not found")
        
        record = self.migration_records[migration_id]
        
        # Restore from checkpoint
        restore_result = self.checkpoint_manager.restore_checkpoint(
            record.checkpoint_id,
            resource_manager
        )
        
        return {
            "migration_id": migration_id,
            "rolled_back": True,
            "checkpoint_id": record.checkpoint_id,
            "qubits_restored": restore_result["qubits_restored"]
        }
    
    def get_migration_stats(self) -> Dict:
        """
        Get statistics about migrations.
        
        Returns:
            Dictionary with migration statistics
        """
        total = len(self.migration_records)
        successful = sum(1 for r in self.migration_records.values() if r.success)
        failed = sum(1 for r in self.migration_records.values() 
                    if r.completed_at and not r.success)
        in_progress = sum(1 for r in self.migration_records.values() 
                         if not r.completed_at)
        
        # Calculate average migration time
        completed = [r for r in self.migration_records.values() 
                    if r.completed_at]
        avg_time = (
            sum(r.completed_at - r.started_at for r in completed) / len(completed)
            if completed else 0
        )
        
        return {
            "total_migrations": total,
            "successful": successful,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": successful / total if total > 0 else 0,
            "avg_migration_time_sec": avg_time
        }
    
    def _analyze_qubit_liveness(self, graph: Dict) -> Dict[str, List[str]]:
        """
        Analyze which qubits are live at each node.
        
        Args:
            graph: QVM graph
        
        Returns:
            Dictionary mapping node_id to list of live qubit IDs
        """
        live_qubits = {}
        allocated_qubits = set()
        
        for node in graph['nodes']:
            node_id = node['id']
            op = node.get('op', '')
            
            # Track allocations
            if op == 'ALLOC_LQ':
                allocated_qubits.update(node.get('outputs', []))
            
            # Track deallocations
            elif op == 'FREE_LQ':
                for qid in node.get('qubits', []):
                    allocated_qubits.discard(qid)
            
            # Record live qubits at this point
            live_qubits[node_id] = list(allocated_qubits)
        
        return live_qubits
    
    def _estimate_epoch(self, node_id: str, nodes: Dict[str, Dict]) -> int:
        """
        Estimate execution epoch for a node.
        
        Args:
            node_id: Node identifier
            nodes: Dictionary of all nodes
        
        Returns:
            Estimated epoch number
        """
        # Simplified: count dependencies
        node = nodes[node_id]
        deps = node.get('deps', [])
        
        if not deps:
            return 0
        
        # Recursively count max depth
        max_depth = 0
        for dep in deps:
            if dep in nodes:
                dep_epoch = self._estimate_epoch(dep, nodes)
                max_depth = max(max_depth, dep_epoch + 1)
        
        return max_depth
    
    def list_migrations(self, job_id: Optional[str] = None) -> List[MigrationRecord]:
        """
        List migration records, optionally filtered by job.
        
        Args:
            job_id: Optional job ID to filter by
        
        Returns:
            List of MigrationRecord objects
        """
        if job_id:
            return [r for r in self.migration_records.values() if r.job_id == job_id]
        return list(self.migration_records.values())
