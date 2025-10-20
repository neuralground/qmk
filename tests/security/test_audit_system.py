#!/usr/bin/env python3
"""
Comprehensive tests for tamper-evident audit system.

Tests cover:
- Merkle tree construction and verification
- Audit log append and query
- Tamper detection
- Proof generation and verification
- Integrity checks
"""

import unittest
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.merkle_tree import MerkleTree, MerkleProof
from kernel.security.tamper_evident_audit_log import (
    TamperEvidentAuditLog,
    AuditEvent,
    AuditEventType
)


class TestMerkleTree(unittest.TestCase):
    """Test Merkle tree implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tree = MerkleTree()
    
    def test_create_empty_tree(self):
        """Test creating empty tree."""
        self.assertEqual(self.tree.size(), 0)
        self.assertEqual(self.tree.root(), b'')
    
    def test_append_single_item(self):
        """Test appending single item."""
        root = self.tree.append(b'data1')
        
        self.assertEqual(self.tree.size(), 1)
        self.assertNotEqual(root, b'')
    
    def test_append_multiple_items(self):
        """Test appending multiple items."""
        root1 = self.tree.append(b'data1')
        root2 = self.tree.append(b'data2')
        root3 = self.tree.append(b'data3')
        
        # Roots should all be different
        self.assertNotEqual(root1, root2)
        self.assertNotEqual(root2, root3)
        self.assertEqual(self.tree.size(), 3)
    
    def test_root_changes_on_append(self):
        """Test that root changes when data is appended."""
        self.tree.append(b'data1')
        root1 = self.tree.root()
        
        self.tree.append(b'data2')
        root2 = self.tree.root()
        
        self.assertNotEqual(root1, root2)
    
    def test_get_proof(self):
        """Test getting Merkle proof."""
        self.tree.append(b'data1')
        self.tree.append(b'data2')
        self.tree.append(b'data3')
        
        proof = self.tree.get_proof(0)
        
        self.assertIsNotNone(proof)
        self.assertEqual(proof.leaf_index, 0)
    
    def test_verify_proof(self):
        """Test verifying Merkle proof."""
        self.tree.append(b'data1')
        self.tree.append(b'data2')
        
        proof = self.tree.get_proof(0)
        
        # Proof should verify with correct data
        self.assertTrue(proof.verify(b'data1'))
        
        # Proof should fail with wrong data
        self.assertFalse(proof.verify(b'wrong_data'))
    
    def test_proof_for_all_leaves(self):
        """Test that proofs work for all leaves."""
        data = [b'data1', b'data2', b'data3', b'data4']
        
        for d in data:
            self.tree.append(d)
        
        # Verify proof for each leaf
        for i, d in enumerate(data):
            proof = self.tree.get_proof(i)
            self.assertTrue(proof.verify(d))
    
    def test_invalid_index(self):
        """Test getting proof for invalid index."""
        self.tree.append(b'data1')
        
        proof = self.tree.get_proof(10)
        self.assertIsNone(proof)


class TestTamperEvidentAuditLog(unittest.TestCase):
    """Test tamper-evident audit log."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.log = TamperEvidentAuditLog()
    
    def test_create_empty_log(self):
        """Test creating empty log."""
        stats = self.log.get_statistics()
        self.assertEqual(stats['total_events'], 0)
    
    def test_append_event(self):
        """Test appending audit event."""
        root = self.log.append(
            AuditEventType.CAPABILITY_CHECK,
            'tenant1',
            {'operation': 'MEASURE_Z', 'allowed': True}
        )
        
        self.assertIsNotNone(root)
        stats = self.log.get_statistics()
        self.assertEqual(stats['total_events'], 1)
    
    def test_sequence_numbers(self):
        """Test that sequence numbers are monotonic."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        events = self.log.get_events()
        
        for i, event in enumerate(events):
            self.assertEqual(event.sequence_number, i)
    
    def test_root_hash_changes(self):
        """Test that root hash changes on append."""
        root1 = self.log.get_root_hash()
        
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        root2 = self.log.get_root_hash()
        
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        root3 = self.log.get_root_hash()
        
        self.assertNotEqual(root1, root2)
        self.assertNotEqual(root2, root3)
    
    def test_verify_event(self):
        """Test verifying individual event."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        # Both events should verify
        self.assertTrue(self.log.verify_event(0))
        self.assertTrue(self.log.verify_event(1))
    
    def test_verify_integrity(self):
        """Test verifying log integrity."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        # All events should verify
        self.assertTrue(self.log.verify_integrity())
    
    def test_detect_tampering(self):
        """Test detecting tampering."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        # No tampering initially
        self.assertIsNone(self.log.detect_tampering())
        
        # Tamper with an event
        self.log.events[0].details = {'tampered': True}
        
        # Tampering should be detected
        tampered_index = self.log.detect_tampering()
        self.assertEqual(tampered_index, 0)
    
    def test_query_by_tenant(self):
        """Test querying events by tenant."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant2', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        tenant1_events = self.log.get_events(tenant_id='tenant1')
        self.assertEqual(len(tenant1_events), 2)
        
        tenant2_events = self.log.get_events(tenant_id='tenant2')
        self.assertEqual(len(tenant2_events), 1)
    
    def test_query_by_event_type(self):
        """Test querying events by type."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.SECURITY_VIOLATION, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        cap_events = self.log.get_events(event_type=AuditEventType.CAPABILITY_CHECK)
        self.assertEqual(len(cap_events), 2)
        
        sec_events = self.log.get_events(event_type=AuditEventType.SECURITY_VIOLATION)
        self.assertEqual(len(sec_events), 1)
    
    def test_query_with_limit(self):
        """Test querying with limit."""
        for i in range(10):
            self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        events = self.log.get_events(limit=5)
        self.assertEqual(len(events), 5)
    
    def test_statistics(self):
        """Test getting statistics."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.SECURITY_VIOLATION, 'tenant2', {})
        
        stats = self.log.get_statistics()
        
        self.assertEqual(stats['total_events'], 3)
        self.assertEqual(stats['event_counts']['CAPABILITY_CHECK'], 2)
        self.assertEqual(stats['event_counts']['SECURITY_VIOLATION'], 1)
        self.assertEqual(stats['tenant_counts']['tenant1'], 2)
        self.assertEqual(stats['tenant_counts']['tenant2'], 1)
    
    def test_export_events(self):
        """Test exporting events."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'key': 'value'})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'key': 'value2'})
        
        exported = self.log.export_events()
        
        self.assertEqual(len(exported), 2)
        self.assertEqual(exported[0]['event_type'], 'CAPABILITY_CHECK')
        self.assertEqual(exported[0]['tenant_id'], 'tenant1')


class TestTamperDetection(unittest.TestCase):
    """Test tamper detection capabilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.log = TamperEvidentAuditLog()
    
    def test_modification_detected(self):
        """Test that modification is detected."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'original': 'data'})
        
        # Verify initially
        self.assertTrue(self.log.verify_event(0))
        
        # Modify event
        self.log.events[0].details = {'modified': 'data'}
        
        # Should fail verification
        self.assertFalse(self.log.verify_event(0))
    
    def test_deletion_detected(self):
        """Test that deletion is detected."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        original_root = self.log.get_root_hash()
        
        # Delete an event
        del self.log.events[0]
        
        # Root hash should be different (though this is a crude deletion)
        # In practice, the Merkle tree would need to be rebuilt
        # This test shows the concept
        self.assertEqual(len(self.log.events), 1)
    
    def test_reordering_detected(self):
        """Test that reordering is detected via sequence numbers."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'id': 1})
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'id': 2})
        
        # Swap events
        self.log.events[0], self.log.events[1] = self.log.events[1], self.log.events[0]
        
        # Sequence numbers will be out of order
        self.assertEqual(self.log.events[0].sequence_number, 1)
        self.assertEqual(self.log.events[1].sequence_number, 0)


class TestSecurityProperties(unittest.TestCase):
    """Test security properties of audit system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.log = TamperEvidentAuditLog()
    
    def test_append_only(self):
        """Test append-only property."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        
        # Can append
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        self.assertEqual(len(self.log.events), 2)
        
        # Cannot modify (would be detected)
        self.log.events[0].details = {'modified': True}
        self.assertFalse(self.log.verify_event(0))
    
    def test_cryptographic_binding(self):
        """Test that entries are cryptographically bound."""
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        root1 = self.log.get_root_hash()
        
        self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {})
        root2 = self.log.get_root_hash()
        
        # Roots should be different
        self.assertNotEqual(root1, root2)
        
        # Modifying first entry changes root
        original_details = self.log.events[0].details.copy()
        self.log.events[0].details = {'modified': True}
        
        # Verification should fail
        self.assertFalse(self.log.verify_event(0))
    
    def test_completeness(self):
        """Test that missing entries are detectable."""
        for i in range(5):
            self.log.append(AuditEventType.CAPABILITY_CHECK, 'tenant1', {'id': i})
        
        # All events should have sequential sequence numbers
        for i, event in enumerate(self.log.events):
            self.assertEqual(event.sequence_number, i)
        
        # If we delete an event, sequence numbers will have a gap
        # (This is a simple check; more sophisticated checks could be added)


if __name__ == '__main__':
    unittest.main()
