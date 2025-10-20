#!/usr/bin/env python3
"""
Comprehensive tests for isolation features.

Tests cover:
- Physical qubit isolation
- Tenant separation
- Resource quotas
- Timing isolation
- Cross-tenant access prevention
"""

import unittest
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.physical_qubit_allocator import (
    PhysicalQubitAllocator,
    ResourceError,
    QuotaExceededError,
    QubitState
)
from kernel.security.timing_isolator import (
    TimingIsolator,
    TimingMode
)


class TestPhysicalQubitAllocator(unittest.TestCase):
    """Test physical qubit allocator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.allocator = PhysicalQubitAllocator(total_qubits=10)
    
    def test_create_allocator(self):
        """Test creating allocator."""
        self.assertEqual(self.allocator.total_qubits, 10)
        self.assertEqual(self.allocator.get_available_count(), 10)
    
    def test_allocate_qubits(self):
        """Test allocating qubits."""
        qubits = self.allocator.allocate('tenant1', count=3)
        
        self.assertEqual(len(qubits), 3)
        self.assertEqual(self.allocator.get_available_count(), 7)
    
    def test_deallocate_qubits(self):
        """Test deallocating qubits."""
        qubits = self.allocator.allocate('tenant1', count=3)
        self.allocator.deallocate('tenant1', qubits)
        
        self.assertEqual(self.allocator.get_available_count(), 10)
    
    def test_verify_access_allowed(self):
        """Test verifying access for owned qubit."""
        qubits = self.allocator.allocate('tenant1', count=3)
        qubit_id = list(qubits)[0]
        
        self.assertTrue(self.allocator.verify_access('tenant1', qubit_id))
    
    def test_verify_access_denied(self):
        """Test verifying access for non-owned qubit."""
        qubits = self.allocator.allocate('tenant1', count=3)
        qubit_id = list(qubits)[0]
        
        # Different tenant should not have access
        self.assertFalse(self.allocator.verify_access('tenant2', qubit_id))
    
    def test_cannot_exceed_quota(self):
        """Test that tenants cannot exceed quota."""
        self.allocator.set_quota('tenant1', max_qubits=5)
        
        # Allocate up to quota
        self.allocator.allocate('tenant1', count=5)
        
        # Try to exceed quota
        with self.assertRaises(QuotaExceededError):
            self.allocator.allocate('tenant1', count=1)
    
    def test_insufficient_qubits(self):
        """Test error when insufficient qubits available."""
        # Set high quota so we hit resource limit, not quota limit
        self.allocator.set_quota('tenant1', max_qubits=30)
        
        with self.assertRaises(ResourceError):
            self.allocator.allocate('tenant1', count=20)
    
    def test_tenant_isolation(self):
        """Test that tenants are isolated."""
        qubits1 = self.allocator.allocate('tenant1', count=3)
        qubits2 = self.allocator.allocate('tenant2', count=3)
        
        # Qubits should be disjoint
        self.assertEqual(len(qubits1 & qubits2), 0)
        
        # Each tenant can only access their own qubits
        for qid in qubits1:
            self.assertTrue(self.allocator.verify_access('tenant1', qid))
            self.assertFalse(self.allocator.verify_access('tenant2', qid))
        
        for qid in qubits2:
            self.assertTrue(self.allocator.verify_access('tenant2', qid))
            self.assertFalse(self.allocator.verify_access('tenant1', qid))
    
    def test_cannot_deallocate_others_qubits(self):
        """Test that tenant cannot deallocate another tenant's qubits."""
        qubits = self.allocator.allocate('tenant1', count=3)
        
        # Tenant2 tries to deallocate tenant1's qubits
        with self.assertRaises(ValueError):
            self.allocator.deallocate('tenant2', qubits)
    
    def test_get_tenant_qubits(self):
        """Test getting tenant's allocated qubits."""
        qubits = self.allocator.allocate('tenant1', count=3)
        
        tenant_qubits = self.allocator.get_tenant_qubits('tenant1')
        self.assertEqual(qubits, tenant_qubits)
    
    def test_quota_tracking(self):
        """Test quota tracking."""
        self.allocator.set_quota('tenant1', max_qubits=5)
        
        quota = self.allocator.get_quota('tenant1')
        self.assertEqual(quota.max_qubits, 5)
        self.assertEqual(quota.allocated_qubits, 0)
        
        self.allocator.allocate('tenant1', count=3)
        
        quota = self.allocator.get_quota('tenant1')
        self.assertEqual(quota.allocated_qubits, 3)
        self.assertEqual(quota.remaining_quota(), 2)
    
    def test_mark_faulty(self):
        """Test marking qubit as faulty."""
        qubits = self.allocator.allocate('tenant1', count=3)
        qubit_id = list(qubits)[0]
        
        self.allocator.mark_faulty(qubit_id)
        
        # Qubit should be marked as faulty
        self.assertEqual(
            self.allocator.qubits[qubit_id].state,
            QubitState.FAULTY
        )
        
        # Should not be available
        self.assertNotIn(qubit_id, self.allocator._get_available_qubits())
    
    def test_statistics(self):
        """Test allocation statistics."""
        self.allocator.allocate('tenant1', count=3)
        self.allocator.allocate('tenant2', count=2)
        
        stats = self.allocator.get_statistics()
        
        self.assertEqual(stats['total_qubits'], 10)
        self.assertEqual(stats['allocated_qubits'], 5)
        self.assertEqual(stats['free_qubits'], 5)
        self.assertEqual(stats['active_tenants'], 2)
        self.assertEqual(stats['utilization'], 50.0)


class TestTimingIsolator(unittest.TestCase):
    """Test timing isolator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.isolator = TimingIsolator(
            mode=TimingMode.TIME_SLOTTED,
            time_slot_ms=50,
            noise_ms=10
        )
    
    def test_create_isolator(self):
        """Test creating timing isolator."""
        self.assertEqual(self.isolator.mode, TimingMode.TIME_SLOTTED)
        self.assertEqual(self.isolator.time_slot_ms, 50)
    
    def test_execute_isolated(self):
        """Test executing with timing isolation."""
        def fast_operation():
            time.sleep(0.01)  # 10ms
            return 42
        
        result = self.isolator.execute_isolated(
            operation=fast_operation,
            tenant_id='tenant1'
        )
        
        self.assertEqual(result, 42)
        self.assertEqual(self.isolator.total_executions, 1)
    
    def test_timing_normalization(self):
        """Test that timing is normalized."""
        def fast_op():
            time.sleep(0.01)
            return 1
        
        def slow_op():
            time.sleep(0.03)
            return 2
        
        # Execute both operations
        start1 = time.time()
        self.isolator.execute_isolated(fast_op, 'tenant1')
        time1 = time.time() - start1
        
        start2 = time.time()
        self.isolator.execute_isolated(slow_op, 'tenant1')
        time2 = time.time() - start2
        
        # Both should take similar time (within time slot + noise)
        # They should both be rounded to same time slot
        self.assertAlmostEqual(time1, time2, delta=0.02)
    
    def test_disabled_mode(self):
        """Test that disabled mode has no overhead."""
        isolator = TimingIsolator(mode=TimingMode.DISABLED)
        
        def operation():
            return 42
        
        start = time.time()
        result = isolator.execute_isolated(operation, 'tenant1')
        elapsed = time.time() - start
        
        self.assertEqual(result, 42)
        # Should be very fast with no isolation
        self.assertLess(elapsed, 0.01)
    
    def test_statistics(self):
        """Test timing statistics."""
        def operation():
            time.sleep(0.01)
            return 1
        
        # Execute multiple times
        for _ in range(5):
            self.isolator.execute_isolated(operation, 'tenant1')
        
        stats = self.isolator.get_statistics()
        
        self.assertEqual(stats['total_executions'], 5)
        self.assertGreater(stats['total_overhead_ms'], 0)
        self.assertGreater(stats['avg_overhead_ms'], 0)


class TestCrossTenantIsolation(unittest.TestCase):
    """Test cross-tenant isolation properties."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.allocator = PhysicalQubitAllocator(total_qubits=20)
    
    def test_no_qubit_sharing(self):
        """Test that qubits are never shared between tenants."""
        # Allocate for multiple tenants
        qubits1 = self.allocator.allocate('tenant1', count=5)
        qubits2 = self.allocator.allocate('tenant2', count=5)
        qubits3 = self.allocator.allocate('tenant3', count=5)
        
        # All allocations should be disjoint
        self.assertEqual(len(qubits1 & qubits2), 0)
        self.assertEqual(len(qubits1 & qubits3), 0)
        self.assertEqual(len(qubits2 & qubits3), 0)
    
    def test_access_control_enforcement(self):
        """Test that access control is enforced."""
        qubits1 = self.allocator.allocate('tenant1', count=5)
        qubits2 = self.allocator.allocate('tenant2', count=5)
        
        # Tenant1 can only access their qubits
        for qid in qubits1:
            self.assertTrue(self.allocator.verify_access('tenant1', qid))
            self.assertFalse(self.allocator.verify_access('tenant2', qid))
            self.assertFalse(self.allocator.verify_access('tenant3', qid))
        
        # Tenant2 can only access their qubits
        for qid in qubits2:
            self.assertTrue(self.allocator.verify_access('tenant2', qid))
            self.assertFalse(self.allocator.verify_access('tenant1', qid))
            self.assertFalse(self.allocator.verify_access('tenant3', qid))
    
    def test_resource_exhaustion_prevention(self):
        """Test that one tenant cannot exhaust resources."""
        self.allocator.set_quota('tenant1', max_qubits=10)
        self.allocator.set_quota('tenant2', max_qubits=10)
        
        # Tenant1 allocates up to quota
        self.allocator.allocate('tenant1', count=10)
        
        # Tenant2 should still be able to allocate
        qubits2 = self.allocator.allocate('tenant2', count=5)
        self.assertEqual(len(qubits2), 5)
    
    def test_proper_cleanup(self):
        """Test that qubits are properly cleaned up."""
        qubits = self.allocator.allocate('tenant1', count=5)
        
        # Deallocate with reset
        self.allocator.deallocate('tenant1', qubits, reset=True)
        
        # Qubits should be available again
        self.assertEqual(self.allocator.get_available_count(), 20)
        
        # Another tenant can allocate them
        qubits2 = self.allocator.allocate('tenant2', count=5)
        self.assertEqual(len(qubits2), 5)


class TestSecurityProperties(unittest.TestCase):
    """Test security properties of isolation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.allocator = PhysicalQubitAllocator(total_qubits=10)
    
    def test_exclusive_allocation(self):
        """Test exclusive allocation property."""
        qubits = self.allocator.allocate('tenant1', count=5)
        
        # Each qubit should be allocated to exactly one tenant
        for qid in qubits:
            qubit = self.allocator.qubits[qid]
            self.assertEqual(qubit.state, QubitState.ALLOCATED)
            self.assertEqual(qubit.tenant_id, 'tenant1')
    
    def test_fail_safe_defaults(self):
        """Test that access is denied by default."""
        # Unallocated qubit should deny access
        self.assertFalse(self.allocator.verify_access('tenant1', 0))
    
    def test_defense_in_depth(self):
        """Test multiple layers of protection."""
        qubits = self.allocator.allocate('tenant1', count=3)
        qubit_id = list(qubits)[0]
        
        # Layer 1: State check
        qubit = self.allocator.qubits[qubit_id]
        self.assertEqual(qubit.state, QubitState.ALLOCATED)
        
        # Layer 2: Tenant ownership check
        self.assertEqual(qubit.tenant_id, 'tenant1')
        
        # Layer 3: Access verification
        self.assertTrue(self.allocator.verify_access('tenant1', qubit_id))
        self.assertFalse(self.allocator.verify_access('tenant2', qubit_id))


if __name__ == '__main__':
    unittest.main()
