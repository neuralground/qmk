"""
Tests for Linear Type System

Tests use-once semantics, consumption tracking, and linearity enforcement.
"""

import unittest
import time
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.types.linear_types import (
    LinearTypeSystem,
    LinearHandle,
    ResourceState,
    LinearityViolation,
    LinearityViolationType
)


class TestLinearHandle(unittest.TestCase):
    """Test LinearHandle functionality."""
    
    def test_handle_creation(self):
        """Test creating a linear handle."""
        handle = LinearHandle(
            handle_id="h1",
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        self.assertEqual(handle.handle_id, "h1")
        self.assertEqual(handle.resource_type, "VQ")
        self.assertEqual(handle.resource_id, "vq0")
        self.assertTrue(handle.is_valid())
        self.assertFalse(handle.is_consumed())
    
    def test_handle_consumption(self):
        """Test consuming a handle."""
        handle = LinearHandle(
            handle_id="h1",
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Consume handle
        handle.consume("MEASURE_Z")
        
        self.assertFalse(handle.is_valid())
        self.assertTrue(handle.is_consumed())
        self.assertEqual(handle.consumed_by, "MEASURE_Z")
        self.assertIsNotNone(handle.consumed_at)
    
    def test_double_consume_rejected(self):
        """Test that double consumption is rejected."""
        handle = LinearHandle(
            handle_id="h1",
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # First consumption
        handle.consume("MEASURE_Z")
        
        # Second consumption should fail
        with self.assertRaises(LinearityViolation) as cm:
            handle.consume("MEASURE_X")
        
        self.assertEqual(
            cm.exception.violation_type,
            LinearityViolationType.DOUBLE_CONSUME
        )
    
    def test_handle_move(self):
        """Test moving a handle."""
        handle = LinearHandle(
            handle_id="h1",
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Move handle
        new_id = handle.move()
        
        self.assertEqual(new_id, "h1")
        self.assertEqual(handle.state, ResourceState.MOVED)
        self.assertFalse(handle.is_valid())
        
        # Cannot consume moved handle
        with self.assertRaises(LinearityViolation) as cm:
            handle.consume("MEASURE_Z")
        
        self.assertEqual(
            cm.exception.violation_type,
            LinearityViolationType.MOVED_RESOURCE
        )


class TestLinearTypeSystem(unittest.TestCase):
    """Test LinearTypeSystem functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.linear_system = LinearTypeSystem()
    
    def test_create_handle(self):
        """Test creating a handle."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        self.assertIsNotNone(handle)
        self.assertTrue(handle.is_valid())
        self.assertEqual(handle.resource_type, "VQ")
        self.assertEqual(handle.resource_id, "vq0")
    
    def test_aliasing_prevented(self):
        """Test that aliasing is prevented."""
        # Create first handle
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Try to create second handle for same resource
        with self.assertRaises(LinearityViolation) as cm:
            handle2 = self.linear_system.create_handle(
                resource_type="VQ",
                resource_id="vq0",
                tenant_id="tenant_a"
            )
        
        self.assertEqual(
            cm.exception.violation_type,
            LinearityViolationType.ALIASING
        )
    
    def test_consume_handle(self):
        """Test consuming a handle."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Consume handle
        self.linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        
        self.assertFalse(handle.is_valid())
        self.assertTrue(handle.is_consumed())
        
        # Resource should be available for new handle
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        self.assertIsNotNone(handle2)
    
    def test_use_after_consume_rejected(self):
        """Test that use-after-consume is rejected."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Consume handle
        self.linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        
        # Try to consume again
        with self.assertRaises(LinearityViolation):
            self.linear_system.consume_handle(handle.handle_id, "MEASURE_X")
    
    def test_check_handle(self):
        """Test checking handle validity."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Should be valid
        self.assertTrue(self.linear_system.check_handle(handle.handle_id))
        
        # Consume
        self.linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        
        # Should be invalid
        self.assertFalse(self.linear_system.check_handle(handle.handle_id))
    
    def test_get_resource_handle(self):
        """Test getting handle by resource ID."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Get by resource ID
        retrieved = self.linear_system.get_resource_handle("vq0")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.handle_id, handle.handle_id)
    
    def test_get_tenant_handles(self):
        """Test getting all handles for a tenant."""
        # Create multiple handles
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq1",
            tenant_id="tenant_a"
        )
        handle3 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq2",
            tenant_id="tenant_b"
        )
        
        # Get tenant_a handles
        tenant_a_handles = self.linear_system.get_tenant_handles("tenant_a")
        self.assertEqual(len(tenant_a_handles), 2)
        
        # Get tenant_b handles
        tenant_b_handles = self.linear_system.get_tenant_handles("tenant_b")
        self.assertEqual(len(tenant_b_handles), 1)
    
    def test_cleanup_consumed_handles(self):
        """Test cleanup of consumed handles."""
        # Create and consume handles
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq1",
            tenant_id="tenant_a"
        )
        
        self.linear_system.consume_handle(handle1.handle_id, "MEASURE_Z")
        
        # Cleanup
        removed = self.linear_system.cleanup_consumed_handles()
        
        # Should remove 1 handle
        self.assertEqual(removed, 1)
        
        # handle1 should be gone
        self.assertIsNone(self.linear_system.get_handle(handle1.handle_id))
        
        # handle2 should remain
        self.assertIsNotNone(self.linear_system.get_handle(handle2.handle_id))
    
    def test_statistics(self):
        """Test statistics collection."""
        # Create handles
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq1",
            tenant_id="tenant_a"
        )
        
        # Consume one
        self.linear_system.consume_handle(handle1.handle_id, "MEASURE_Z")
        
        # Try to create alias (violation)
        try:
            self.linear_system.create_handle(
                resource_type="VQ",
                resource_id="vq1",
                tenant_id="tenant_a"
            )
        except LinearityViolation:
            pass
        
        # Get statistics
        stats = self.linear_system.get_statistics()
        
        self.assertEqual(stats["handles_created"], 2)
        self.assertEqual(stats["handles_consumed"], 1)
        self.assertEqual(stats["active_handles"], 1)
        self.assertEqual(stats["linearity_violations"], 1)
    
    def test_verify_linearity(self):
        """Test linearity verification."""
        # Create valid handles
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq1",
            tenant_id="tenant_a"
        )
        
        # Should be valid
        is_valid, violations = self.linear_system.verify_linearity()
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)


class TestLinearityViolations(unittest.TestCase):
    """Test linearity violation scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.linear_system = LinearTypeSystem()
    
    def test_use_after_free(self):
        """Test use-after-free detection."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Free (consume) the handle
        self.linear_system.consume_handle(handle.handle_id, "FREE_LQ")
        
        # Try to use after free
        with self.assertRaises(LinearityViolation) as cm:
            self.linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        
        self.assertEqual(
            cm.exception.violation_type,
            LinearityViolationType.DOUBLE_CONSUME
        )
    
    def test_double_free(self):
        """Test double-free detection."""
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # First free
        self.linear_system.consume_handle(handle.handle_id, "FREE_LQ")
        
        # Second free should fail
        with self.assertRaises(LinearityViolation):
            self.linear_system.consume_handle(handle.handle_id, "FREE_LQ")
    
    def test_aliasing_detection(self):
        """Test aliasing detection."""
        handle1 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        
        # Try to create alias
        with self.assertRaises(LinearityViolation) as cm:
            handle2 = self.linear_system.create_handle(
                resource_type="VQ",
                resource_id="vq0",
                tenant_id="tenant_a"
            )
        
        self.assertEqual(
            cm.exception.violation_type,
            LinearityViolationType.ALIASING
        )
        
        # Statistics should record violation
        stats = self.linear_system.get_statistics()
        self.assertGreater(stats["linearity_violations"], 0)


class TestResourceLifecycle(unittest.TestCase):
    """Test complete resource lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.linear_system = LinearTypeSystem()
    
    def test_allocate_use_free(self):
        """Test allocate → use → free lifecycle."""
        # Allocate
        handle = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        self.assertTrue(handle.is_valid())
        
        # Use (measure)
        self.linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        self.assertFalse(handle.is_valid())
        
        # Resource should be freed for reuse
        handle2 = self.linear_system.create_handle(
            resource_type="VQ",
            resource_id="vq0",
            tenant_id="tenant_a"
        )
        self.assertIsNotNone(handle2)
    
    def test_multiple_qubits_lifecycle(self):
        """Test lifecycle with multiple qubits."""
        # Allocate multiple qubits
        handles = []
        for i in range(3):
            handle = self.linear_system.create_handle(
                resource_type="VQ",
                resource_id=f"vq{i}",
                tenant_id="tenant_a"
            )
            handles.append(handle)
        
        # All should be valid
        for handle in handles:
            self.assertTrue(handle.is_valid())
        
        # Consume first two
        self.linear_system.consume_handle(handles[0].handle_id, "MEASURE_Z")
        self.linear_system.consume_handle(handles[1].handle_id, "MEASURE_X")
        
        # First two invalid, third still valid
        self.assertFalse(handles[0].is_valid())
        self.assertFalse(handles[1].is_valid())
        self.assertTrue(handles[2].is_valid())


if __name__ == '__main__':
    unittest.main()
