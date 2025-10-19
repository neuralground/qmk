"""
Unit tests for Handle Signer
"""

import unittest
import time
from kernel.security.handle_signer import HandleSigner


class TestHandleSigner(unittest.TestCase):
    """Test handle signing and verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signer = HandleSigner()
    
    def test_sign_handle(self):
        """Test signing a handle."""
        handle = self.signer.sign_handle(
            handle_id="vq_123",
            handle_type="VQ",
            tenant_id="tenant_1",
            session_id="sess_1"
        )
        
        self.assertEqual(handle.handle_id, "vq_123")
        self.assertEqual(handle.handle_type, "VQ")
        self.assertEqual(handle.tenant_id, "tenant_1")
        self.assertEqual(handle.session_id, "sess_1")
        self.assertIsNotNone(handle.signature)
    
    def test_verify_valid_handle(self):
        """Test verifying a valid handle."""
        handle = self.signer.sign_handle(
            "vq_123", "VQ", "tenant_1", "sess_1"
        )
        
        is_valid, error = self.signer.verify_handle("vq_123")
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_verify_nonexistent_handle(self):
        """Test verifying non-existent handle."""
        is_valid, error = self.signer.verify_handle("invalid_handle")
        
        self.assertFalse(is_valid)
        self.assertIn("not found", error)
    
    def test_verify_tenant_ownership(self):
        """Test verifying tenant ownership."""
        self.signer.sign_handle("vq_123", "VQ", "tenant_1", "sess_1")
        
        # Correct tenant
        is_valid, _ = self.signer.verify_handle("vq_123", expected_tenant_id="tenant_1")
        self.assertTrue(is_valid)
        
        # Wrong tenant
        is_valid, error = self.signer.verify_handle("vq_123", expected_tenant_id="tenant_2")
        self.assertFalse(is_valid)
        self.assertIn("different tenant", error)
    
    def test_verify_session_ownership(self):
        """Test verifying session ownership."""
        self.signer.sign_handle("vq_123", "VQ", "tenant_1", "sess_1")
        
        # Correct session
        is_valid, _ = self.signer.verify_handle("vq_123", expected_session_id="sess_1")
        self.assertTrue(is_valid)
        
        # Wrong session
        is_valid, error = self.signer.verify_handle("vq_123", expected_session_id="sess_2")
        self.assertFalse(is_valid)
        self.assertIn("different session", error)
    
    def test_handle_expiration(self):
        """Test handle expiration."""
        handle = self.signer.sign_handle(
            "vq_123", "VQ", "tenant_1", "sess_1",
            ttl_seconds=1
        )
        
        # Should be valid initially
        self.assertFalse(handle.is_expired())
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        self.assertTrue(handle.is_expired())
        
        # Verification should fail
        is_valid, error = self.signer.verify_handle("vq_123")
        self.assertFalse(is_valid)
        self.assertIn("expired", error)
    
    def test_revoke_handle(self):
        """Test revoking a handle."""
        self.signer.sign_handle("vq_123", "VQ", "tenant_1", "sess_1")
        
        self.signer.revoke_handle("vq_123")
        
        # Should no longer exist
        is_valid, error = self.signer.verify_handle("vq_123")
        self.assertFalse(is_valid)
    
    def test_revoke_session_handles(self):
        """Test revoking all handles for a session."""
        self.signer.sign_handle("vq_1", "VQ", "tenant_1", "sess_1")
        self.signer.sign_handle("vq_2", "VQ", "tenant_1", "sess_1")
        self.signer.sign_handle("vq_3", "VQ", "tenant_1", "sess_2")
        
        count = self.signer.revoke_session_handles("sess_1")
        
        self.assertEqual(count, 2)
        
        # sess_1 handles should be gone
        is_valid, _ = self.signer.verify_handle("vq_1")
        self.assertFalse(is_valid)
        
        # sess_2 handle should still exist
        is_valid, _ = self.signer.verify_handle("vq_3")
        self.assertTrue(is_valid)
    
    def test_cleanup_expired_handles(self):
        """Test cleaning up expired handles."""
        self.signer.sign_handle("vq_1", "VQ", "tenant_1", "sess_1", ttl_seconds=1)
        self.signer.sign_handle("vq_2", "VQ", "tenant_1", "sess_1")
        
        time.sleep(1.1)
        
        count = self.signer.cleanup_expired_handles()
        
        self.assertEqual(count, 1)
    
    def test_handle_stats(self):
        """Test getting handle statistics."""
        self.signer.sign_handle("vq_1", "VQ", "tenant_1", "sess_1")
        self.signer.sign_handle("ch_1", "CH", "tenant_1", "sess_1")
        
        stats = self.signer.get_handle_stats()
        
        self.assertEqual(stats["total_handles"], 2)
        self.assertEqual(stats["by_type"]["VQ"], 1)
        self.assertEqual(stats["by_type"]["CH"], 1)


if __name__ == "__main__":
    unittest.main()
