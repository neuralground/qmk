"""
Unit tests for Checkpoint Manager
"""

import unittest
from kernel.reversibility.checkpoint_manager import CheckpointManager, Checkpoint
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.qec_profiles import parse_profile_string


class TestCheckpointManager(unittest.TestCase):
    """Test checkpoint management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = CheckpointManager(max_checkpoints=10)
        self.resource_manager = EnhancedResourceManager()
    
    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        # Allocate some qubits
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0", "q1"], profile)
        
        checkpoint = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=10,
            node_id="node_5",
            resource_manager=self.resource_manager
        )
        
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint.job_id, "job_1")
        self.assertEqual(checkpoint.epoch, 10)
        self.assertEqual(checkpoint.node_id, "node_5")
        self.assertIn("q0", checkpoint.qubit_states)
        self.assertIn("q1", checkpoint.qubit_states)
    
    def test_restore_checkpoint(self):
        """Test restoring from a checkpoint."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        checkpoint = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=5,
            node_id="node_3",
            resource_manager=self.resource_manager
        )
        
        # Modify state
        self.resource_manager.free_logical_qubits(["q0"])
        
        # Restore
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        result = self.manager.restore_checkpoint(
            checkpoint.checkpoint_id,
            self.resource_manager
        )
        
        self.assertEqual(result["checkpoint_id"], checkpoint.checkpoint_id)
        self.assertEqual(result["job_id"], "job_1")
        self.assertIn("q0", result["qubits_restored"])
    
    def test_get_checkpoint(self):
        """Test retrieving a checkpoint."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        checkpoint = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=1,
            node_id="node_1",
            resource_manager=self.resource_manager
        )
        
        retrieved = self.manager.get_checkpoint(checkpoint.checkpoint_id)
        self.assertEqual(retrieved.checkpoint_id, checkpoint.checkpoint_id)
        self.assertEqual(retrieved.job_id, "job_1")
    
    def test_get_checkpoint_not_found(self):
        """Test retrieving non-existent checkpoint."""
        with self.assertRaises(KeyError):
            self.manager.get_checkpoint("invalid_checkpoint")
    
    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        ckpt1 = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=1,
            node_id="node_1",
            resource_manager=self.resource_manager
        )
        
        ckpt2 = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=2,
            node_id="node_2",
            resource_manager=self.resource_manager
        )
        
        ckpt3 = self.manager.create_checkpoint(
            job_id="job_2",
            epoch=1,
            node_id="node_1",
            resource_manager=self.resource_manager
        )
        
        # List all checkpoints
        all_ckpts = self.manager.list_checkpoints()
        self.assertEqual(len(all_ckpts), 3)
        
        # List checkpoints for job_1
        job1_ckpts = self.manager.list_checkpoints(job_id="job_1")
        self.assertEqual(len(job1_ckpts), 2)
        
        # List checkpoints for job_2
        job2_ckpts = self.manager.list_checkpoints(job_id="job_2")
        self.assertEqual(len(job2_ckpts), 1)
    
    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        checkpoint = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=1,
            node_id="node_1",
            resource_manager=self.resource_manager
        )
        
        self.manager.delete_checkpoint(checkpoint.checkpoint_id)
        
        with self.assertRaises(KeyError):
            self.manager.get_checkpoint(checkpoint.checkpoint_id)
    
    def test_max_checkpoints_eviction(self):
        """Test that oldest checkpoint is evicted when limit reached."""
        manager = CheckpointManager(max_checkpoints=3)
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        ckpt1 = manager.create_checkpoint(
            job_id="job_1", epoch=1, node_id="n1",
            resource_manager=self.resource_manager
        )
        
        ckpt2 = manager.create_checkpoint(
            job_id="job_1", epoch=2, node_id="n2",
            resource_manager=self.resource_manager
        )
        
        ckpt3 = manager.create_checkpoint(
            job_id="job_1", epoch=3, node_id="n3",
            resource_manager=self.resource_manager
        )
        
        # Creating 4th checkpoint should evict the oldest
        ckpt4 = manager.create_checkpoint(
            job_id="job_1", epoch=4, node_id="n4",
            resource_manager=self.resource_manager
        )
        
        # ckpt1 should be evicted
        with self.assertRaises(KeyError):
            manager.get_checkpoint(ckpt1.checkpoint_id)
        
        # Others should still exist
        self.assertIsNotNone(manager.get_checkpoint(ckpt2.checkpoint_id))
        self.assertIsNotNone(manager.get_checkpoint(ckpt3.checkpoint_id))
        self.assertIsNotNone(manager.get_checkpoint(ckpt4.checkpoint_id))
    
    def test_checkpoint_metadata(self):
        """Test checkpoint with metadata."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        metadata = {
            "reason": "before_measurement",
            "custom_field": "test_value"
        }
        
        checkpoint = self.manager.create_checkpoint(
            job_id="job_1",
            epoch=1,
            node_id="node_1",
            resource_manager=self.resource_manager,
            metadata=metadata
        )
        
        self.assertEqual(checkpoint.metadata["reason"], "before_measurement")
        self.assertEqual(checkpoint.metadata["custom_field"], "test_value")
    
    def test_multiple_jobs(self):
        """Test checkpoints for multiple jobs."""
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.resource_manager.alloc_logical_qubits(["q0"], profile)
        
        # Create checkpoints for different jobs
        for job_num in range(1, 4):
            self.manager.create_checkpoint(
                job_id=f"job_{job_num}",
                epoch=1,
                node_id="node_1",
                resource_manager=self.resource_manager
            )
        
        # Each job should have its own checkpoint
        for job_num in range(1, 4):
            ckpts = self.manager.list_checkpoints(job_id=f"job_{job_num}")
            self.assertEqual(len(ckpts), 1)


if __name__ == "__main__":
    unittest.main()
