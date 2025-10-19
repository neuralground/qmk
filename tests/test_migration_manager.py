"""
Unit tests for Migration Manager
"""

import unittest
from kernel.reversibility.migration_manager import MigrationManager, MigrationPoint
from kernel.reversibility.checkpoint_manager import CheckpointManager
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.qec_profiles import parse_profile_string


class TestMigrationManager(unittest.TestCase):
    """Test migration management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checkpoint_mgr = CheckpointManager()
        self.manager = MigrationManager(self.checkpoint_mgr)
        self.resource_mgr = EnhancedResourceManager()
    
    def test_identify_migration_points(self):
        """Test identifying migration points in graph."""
        graph = {
            "nodes": [
                {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0"]},
                {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
                {"id": "fence", "op": "FENCE", "deps": ["h"]},
                {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["fence"]},
                {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], "outputs": ["m0"], "deps": ["x"]},
                {"id": "free", "op": "FREE_LQ", "qubits": ["q0"], "deps": ["m"]}
            ],
            "edges": []
        }
        
        points = self.manager.identify_migration_points(graph)
        
        # Should find fence, measurement, and free as migration points
        self.assertGreaterEqual(len(points), 2)
        
        # Check fence point
        fence_points = [p for p in points if p.is_fence]
        self.assertEqual(len(fence_points), 1)
        self.assertTrue(fence_points[0].can_migrate)
    
    def test_initiate_migration(self):
        """Test initiating a migration."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_mgr.alloc_logical_qubits(["q0"], profile)
        
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=["q0"],
            can_migrate=True
        )
        
        record = self.manager.initiate_migration(
            job_id="job_1",
            migration_point=migration_point,
            from_context="context_a",
            to_context="context_b",
            resource_manager=self.resource_mgr
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.job_id, "job_1")
        self.assertEqual(record.from_context, "context_a")
        self.assertEqual(record.to_context, "context_b")
        self.assertIsNotNone(record.checkpoint_id)
    
    def test_complete_migration(self):
        """Test completing a migration."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_mgr.alloc_logical_qubits(["q0"], profile)
        
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=["q0"],
            can_migrate=True
        )
        
        record = self.manager.initiate_migration(
            job_id="job_1",
            migration_point=migration_point,
            from_context="context_a",
            to_context="context_b",
            resource_manager=self.resource_mgr
        )
        
        # Complete migration
        updated = self.manager.complete_migration(
            record.migration_id,
            self.resource_mgr,
            success=True
        )
        
        self.assertTrue(updated.success)
        self.assertIsNotNone(updated.completed_at)
    
    def test_validate_migration(self):
        """Test migration validation."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_mgr.alloc_logical_qubits(["q0"], profile)
        
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=["q0"],
            can_migrate=True
        )
        
        record = self.manager.initiate_migration(
            job_id="job_1",
            migration_point=migration_point,
            from_context="context_a",
            to_context="context_b",
            resource_manager=self.resource_mgr
        )
        
        self.manager.complete_migration(
            record.migration_id,
            self.resource_mgr,
            success=True
        )
        
        is_valid, error = self.manager.validate_migration(record.migration_id)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_rollback_migration(self):
        """Test rolling back a failed migration."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_mgr.alloc_logical_qubits(["q0"], profile)
        
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=["q0"],
            can_migrate=True
        )
        
        record = self.manager.initiate_migration(
            job_id="job_1",
            migration_point=migration_point,
            from_context="context_a",
            to_context="context_b",
            resource_manager=self.resource_mgr
        )
        
        # Simulate failure and rollback
        result = self.manager.rollback_migration(
            record.migration_id,
            self.resource_mgr
        )
        
        self.assertTrue(result["rolled_back"])
        self.assertEqual(result["migration_id"], record.migration_id)
    
    def test_migration_stats(self):
        """Test migration statistics."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_mgr.alloc_logical_qubits(["q0"], profile)
        
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=["q0"],
            can_migrate=True
        )
        
        # Create and complete a migration
        record = self.manager.initiate_migration(
            job_id="job_1",
            migration_point=migration_point,
            from_context="context_a",
            to_context="context_b",
            resource_manager=self.resource_mgr
        )
        
        self.manager.complete_migration(
            record.migration_id,
            self.resource_mgr,
            success=True
        )
        
        stats = self.manager.get_migration_stats()
        
        self.assertEqual(stats["total_migrations"], 1)
        self.assertEqual(stats["successful"], 1)
        self.assertEqual(stats["failed"], 0)
    
    def test_cannot_migrate_without_qubits(self):
        """Test that migration fails without live qubits."""
        migration_point = MigrationPoint(
            node_id="fence_1",
            epoch=5,
            is_fence=True,
            qubits_live=[],
            can_migrate=False,
            reason="No live qubits"
        )
        
        with self.assertRaises(RuntimeError):
            self.manager.initiate_migration(
                job_id="job_1",
                migration_point=migration_point,
                from_context="context_a",
                to_context="context_b",
                resource_manager=self.resource_mgr
            )


if __name__ == "__main__":
    unittest.main()
