"""
Integration tests for qSyscall ABI

Tests the complete flow from client to kernel.
"""

import unittest
import json
from kernel.core.qmk_server import QMKServer
from runtime.client import QSyscallClient


class TestQSyscallIntegration(unittest.TestCase):
    """Integration tests for qSyscall ABI."""
    
    def setUp(self):
        """Set up test server."""
        self.server = QMKServer(socket_path="/tmp/qmk_test.sock")
        self.client = QSyscallClient(socket_path="/tmp/qmk_test.sock")
    
    def test_negotiate_capabilities(self):
        """Test capability negotiation via RPC."""
        result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC", "CAP_TELEPORT"]}
        )
        
        self.assertIn("session_id", result)
        self.assertEqual(set(result["granted"]), {"CAP_ALLOC", "CAP_TELEPORT"})
        self.assertIn("quota", result)
    
    def test_submit_job(self):
        """Test job submission via RPC."""
        # First negotiate capabilities
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id = caps_result["session_id"]
        
        # Submit job
        graph = {
            "nodes": [
                {"id": "n1", "op": "ALLOC_LQ", "outputs": ["vq_1"], "profile": "surface:d=3"}
            ],
            "edges": []
        }
        
        result = self.server.rpc_server.call_local(
            "q_submit",
            {
                "graph": graph,
                "session_id": session_id,
                "policy": {"priority": 10, "seed": 42}
            }
        )
        
        self.assertIn("job_id", result)
        self.assertEqual(result["state"], "QUEUED")
    
    def test_get_job_status(self):
        """Test getting job status via RPC."""
        # Negotiate and submit
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id = caps_result["session_id"]
        
        graph = {"nodes": [], "edges": []}
        submit_result = self.server.rpc_server.call_local(
            "q_submit",
            {"graph": graph, "session_id": session_id}
        )
        job_id = submit_result["job_id"]
        
        # Get status
        status = self.server.rpc_server.call_local(
            "q_status",
            {"job_id": job_id, "session_id": session_id}
        )
        
        self.assertEqual(status["job_id"], job_id)
        self.assertIn("state", status)
        self.assertIn("progress", status)
    
    def test_cancel_job(self):
        """Test job cancellation via RPC."""
        # Negotiate and submit
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id = caps_result["session_id"]
        
        graph = {"nodes": [], "edges": []}
        submit_result = self.server.rpc_server.call_local(
            "q_submit",
            {"graph": graph, "session_id": session_id}
        )
        job_id = submit_result["job_id"]
        
        # Cancel
        cancel_result = self.server.rpc_server.call_local(
            "q_cancel",
            {"job_id": job_id, "session_id": session_id}
        )
        
        self.assertEqual(cancel_result["state"], "CANCELLED")
    
    def test_capability_enforcement(self):
        """Test that capabilities are enforced."""
        # Negotiate without CAP_ALLOC
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_TELEPORT"]}
        )
        session_id = caps_result["session_id"]
        
        # Try to submit job that requires CAP_ALLOC
        graph = {
            "nodes": [
                {"id": "n1", "op": "ALLOC_LQ", "outputs": ["vq_1"]}
            ],
            "edges": []
        }
        
        with self.assertRaises(RuntimeError) as ctx:
            self.server.rpc_server.call_local(
                "q_submit",
                {"graph": graph, "session_id": session_id}
            )
        
        self.assertIn("capabilit", str(ctx.exception).lower())
    
    def test_session_isolation(self):
        """Test that sessions are isolated."""
        # Create two sessions
        caps1 = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id1 = caps1["session_id"]
        
        caps2 = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id2 = caps2["session_id"]
        
        # Submit job in session 1
        graph = {"nodes": [], "edges": []}
        submit_result = self.server.rpc_server.call_local(
            "q_submit",
            {"graph": graph, "session_id": session_id1}
        )
        job_id = submit_result["job_id"]
        
        # Try to access from session 2
        with self.assertRaises(PermissionError):
            self.server.rpc_server.call_local(
                "q_status",
                {"job_id": job_id, "session_id": session_id2}
            )
    
    def test_quota_enforcement(self):
        """Test that quotas are enforced."""
        from kernel.core.session_manager import SessionQuota
        
        # Create session with small quota
        custom_quota = SessionQuota(max_jobs=1)
        self.server.session_manager.default_quota = custom_quota
        
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id = caps_result["session_id"]
        
        graph = {"nodes": [], "edges": []}
        
        # Submit first job (should succeed)
        self.server.rpc_server.call_local(
            "q_submit",
            {"graph": graph, "session_id": session_id}
        )
        
        # Submit second job (should fail)
        with self.assertRaises(RuntimeError) as ctx:
            self.server.rpc_server.call_local(
                "q_submit",
                {"graph": graph, "session_id": session_id}
            )
        
        self.assertIn("quota", str(ctx.exception).lower())
    
    def test_open_channel(self):
        """Test opening an entanglement channel."""
        # Negotiate with CAP_LINK
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC", "CAP_LINK"]}
        )
        session_id = caps_result["session_id"]
        
        # Allocate qubits first
        from kernel.simulator.qec_profiles import parse_profile_string
        profile = parse_profile_string("logical:surface_code(d=3)")
        self.server.resource_manager.alloc_logical_qubits(["vq_1", "vq_2"], profile)
        
        # Open channel
        result = self.server.rpc_server.call_local(
            "q_open_chan",
            {
                "vq_a": "vq_1",
                "vq_b": "vq_2",
                "options": {"fidelity": 0.99},
                "session_id": session_id
            }
        )
        
        self.assertIn("channel_id", result)
        self.assertIn("actual_fidelity", result)
    
    def test_get_telemetry(self):
        """Test getting telemetry."""
        caps_result = self.server.rpc_server.call_local(
            "q_negotiate_caps",
            {"requested": ["CAP_ALLOC"]}
        )
        session_id = caps_result["session_id"]
        
        telemetry = self.server.rpc_server.call_local(
            "q_get_telemetry",
            {"session_id": session_id}
        )
        
        self.assertIn("resource_usage", telemetry)
        self.assertIn("qubits", telemetry)


if __name__ == "__main__":
    unittest.main()
