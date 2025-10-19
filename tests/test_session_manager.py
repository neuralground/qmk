"""
Unit tests for SessionManager
"""

import unittest
from kernel.session_manager import SessionManager, SessionQuota


class TestSessionManager(unittest.TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = SessionManager()
    
    def test_negotiate_capabilities_all_valid(self):
        """Test capability negotiation with all valid capabilities."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC", "CAP_TELEPORT"]
        )
        
        self.assertIn("session_id", result)
        self.assertEqual(set(result["granted"]), {"CAP_ALLOC", "CAP_TELEPORT"})
        self.assertEqual(result["denied"], [])
        self.assertIn("quota", result)
    
    def test_negotiate_capabilities_invalid(self):
        """Test capability negotiation with invalid capabilities."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC", "CAP_INVALID"]
        )
        
        self.assertEqual(set(result["granted"]), {"CAP_ALLOC"})
        self.assertEqual(result["denied"], ["CAP_INVALID"])
    
    def test_negotiate_capabilities_custom_quota(self):
        """Test capability negotiation with custom quota."""
        custom_quota = SessionQuota(
            max_logical_qubits=50,
            max_channels=5,
            max_jobs=3
        )
        
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"],
            quota=custom_quota
        )
        
        self.assertEqual(result["quota"]["max_logical_qubits"], 50)
        self.assertEqual(result["quota"]["max_channels"], 5)
        self.assertEqual(result["quota"]["max_jobs"], 3)
    
    def test_get_session(self):
        """Test retrieving a session."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        session = self.manager.get_session(session_id)
        self.assertEqual(session.session_id, session_id)
        self.assertEqual(session.tenant_id, "tenant_1")
        self.assertIn("CAP_ALLOC", session.granted_caps)
    
    def test_get_session_not_found(self):
        """Test retrieving non-existent session."""
        with self.assertRaises(KeyError):
            self.manager.get_session("invalid_session")
    
    def test_validate_session(self):
        """Test session validation."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.assertTrue(self.manager.validate_session(session_id))
        self.assertFalse(self.manager.validate_session("invalid_session"))
    
    def test_check_capabilities(self):
        """Test capability checking."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC", "CAP_TELEPORT"]
        )
        session_id = result["session_id"]
        
        # Check present capabilities
        check = self.manager.check_capabilities(
            session_id,
            ["CAP_ALLOC"]
        )
        self.assertTrue(check["has_all"])
        self.assertEqual(check["missing"], [])
        
        # Check missing capabilities
        check = self.manager.check_capabilities(
            session_id,
            ["CAP_ALLOC", "CAP_MAGIC"]
        )
        self.assertFalse(check["has_all"])
        self.assertEqual(check["missing"], ["CAP_MAGIC"])
    
    def test_register_job(self):
        """Test job registration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.manager.register_job(session_id, "job_1")
        
        session = self.manager.get_session(session_id)
        self.assertIn("job_1", session.active_jobs)
    
    def test_register_job_quota_exceeded(self):
        """Test job registration with quota exceeded."""
        custom_quota = SessionQuota(max_jobs=2)
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"],
            quota=custom_quota
        )
        session_id = result["session_id"]
        
        self.manager.register_job(session_id, "job_1")
        self.manager.register_job(session_id, "job_2")
        
        with self.assertRaises(RuntimeError) as ctx:
            self.manager.register_job(session_id, "job_3")
        
        self.assertIn("quota exceeded", str(ctx.exception).lower())
    
    def test_unregister_job(self):
        """Test job unregistration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.manager.register_job(session_id, "job_1")
        self.manager.unregister_job(session_id, "job_1")
        
        session = self.manager.get_session(session_id)
        self.assertNotIn("job_1", session.active_jobs)
    
    def test_register_qubits(self):
        """Test qubit registration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.manager.register_qubits(session_id, ["vq_1", "vq_2"])
        
        session = self.manager.get_session(session_id)
        self.assertIn("vq_1", session.allocated_qubits)
        self.assertIn("vq_2", session.allocated_qubits)
    
    def test_register_qubits_quota_exceeded(self):
        """Test qubit registration with quota exceeded."""
        custom_quota = SessionQuota(max_logical_qubits=2)
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"],
            quota=custom_quota
        )
        session_id = result["session_id"]
        
        self.manager.register_qubits(session_id, ["vq_1", "vq_2"])
        
        with self.assertRaises(RuntimeError) as ctx:
            self.manager.register_qubits(session_id, ["vq_3"])
        
        self.assertIn("quota exceeded", str(ctx.exception).lower())
    
    def test_unregister_qubits(self):
        """Test qubit unregistration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.manager.register_qubits(session_id, ["vq_1", "vq_2"])
        self.manager.unregister_qubits(session_id, ["vq_1"])
        
        session = self.manager.get_session(session_id)
        self.assertNotIn("vq_1", session.allocated_qubits)
        self.assertIn("vq_2", session.allocated_qubits)
    
    def test_register_channel(self):
        """Test channel registration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_LINK"]
        )
        session_id = result["session_id"]
        
        self.manager.register_channel(session_id, "ch_1")
        
        session = self.manager.get_session(session_id)
        self.assertIn("ch_1", session.open_channels)
    
    def test_register_channel_quota_exceeded(self):
        """Test channel registration with quota exceeded."""
        custom_quota = SessionQuota(max_channels=1)
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_LINK"],
            quota=custom_quota
        )
        session_id = result["session_id"]
        
        self.manager.register_channel(session_id, "ch_1")
        
        with self.assertRaises(RuntimeError) as ctx:
            self.manager.register_channel(session_id, "ch_2")
        
        self.assertIn("quota exceeded", str(ctx.exception).lower())
    
    def test_unregister_channel(self):
        """Test channel unregistration."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_LINK"]
        )
        session_id = result["session_id"]
        
        self.manager.register_channel(session_id, "ch_1")
        self.manager.unregister_channel(session_id, "ch_1")
        
        session = self.manager.get_session(session_id)
        self.assertNotIn("ch_1", session.open_channels)
    
    def test_close_session(self):
        """Test session closure."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        session_id = result["session_id"]
        
        self.manager.close_session(session_id)
        
        self.assertFalse(self.manager.validate_session(session_id))
    
    def test_get_session_info(self):
        """Test getting session information."""
        result = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC", "CAP_TELEPORT"]
        )
        session_id = result["session_id"]
        
        self.manager.register_job(session_id, "job_1")
        self.manager.register_qubits(session_id, ["vq_1"])
        
        info = self.manager.get_session_info(session_id)
        
        self.assertEqual(info["session_id"], session_id)
        self.assertEqual(info["tenant_id"], "tenant_1")
        self.assertEqual(set(info["capabilities"]), {"CAP_ALLOC", "CAP_TELEPORT"})
        self.assertEqual(info["usage"]["active_jobs"], 1)
        self.assertEqual(info["usage"]["allocated_qubits"], 1)
    
    def test_multiple_sessions_same_tenant(self):
        """Test multiple sessions for the same tenant."""
        result1 = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_ALLOC"]
        )
        result2 = self.manager.negotiate_capabilities(
            tenant_id="tenant_1",
            requested=["CAP_TELEPORT"]
        )
        
        session_id1 = result1["session_id"]
        session_id2 = result2["session_id"]
        
        self.assertNotEqual(session_id1, session_id2)
        
        session1 = self.manager.get_session(session_id1)
        session2 = self.manager.get_session(session_id2)
        
        self.assertEqual(session1.tenant_id, "tenant_1")
        self.assertEqual(session2.tenant_id, "tenant_1")


if __name__ == "__main__":
    unittest.main()
