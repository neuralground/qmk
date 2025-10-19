"""
Unit tests for JobManager
"""

import unittest
import time
from kernel.core.job_manager import JobManager, JobState, JobPolicy


class TestJobManager(unittest.TestCase):
    """Test job management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = JobManager()
    
    def test_submit_job(self):
        """Test job submission."""
        graph = {
            "nodes": [
                {"id": "n1", "op": "ALLOC_LQ", "outputs": ["vq_1"]}
            ],
            "edges": []
        }
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        
        self.assertIn("job_id", result)
        self.assertEqual(result["state"], "QUEUED")
        self.assertIn("estimated_epochs", result)
    
    def test_submit_job_with_policy(self):
        """Test job submission with custom policy."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph,
            policy={
                "priority": 20,
                "seed": 42,
                "debug": True
            }
        )
        
        job_id = result["job_id"]
        job = self.manager.jobs[job_id]
        
        self.assertEqual(job.policy.priority, 20)
        self.assertEqual(job.policy.seed, 42)
        self.assertTrue(job.policy.debug)
    
    def test_get_job_status(self):
        """Test getting job status."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        job_id = result["job_id"]
        
        status = self.manager.get_job_status(job_id, "sess_1")
        
        self.assertEqual(status["job_id"], job_id)
        self.assertEqual(status["session_id"], "sess_1")
        self.assertIn("state", status)
        self.assertIn("progress", status)
    
    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job."""
        with self.assertRaises(KeyError):
            self.manager.get_job_status("invalid_job", "sess_1")
    
    def test_get_job_status_wrong_session(self):
        """Test getting status with wrong session."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        job_id = result["job_id"]
        
        with self.assertRaises(PermissionError):
            self.manager.get_job_status(job_id, "sess_2")
    
    def test_cancel_job(self):
        """Test job cancellation."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        job_id = result["job_id"]
        
        cancel_result = self.manager.cancel_job(job_id, "sess_1")
        
        self.assertEqual(cancel_result["state"], "CANCELLED")
        self.assertIn("cancelled_at_epoch", cancel_result)
    
    def test_cancel_job_not_found(self):
        """Test cancelling non-existent job."""
        with self.assertRaises(KeyError):
            self.manager.cancel_job("invalid_job", "sess_1")
    
    def test_cancel_job_wrong_session(self):
        """Test cancelling job with wrong session."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        job_id = result["job_id"]
        
        with self.assertRaises(PermissionError):
            self.manager.cancel_job(job_id, "sess_2")
    
    def test_cancel_already_cancelled(self):
        """Test cancelling already cancelled job."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job(
            session_id="sess_1",
            graph=graph
        )
        job_id = result["job_id"]
        
        self.manager.cancel_job(job_id, "sess_1")
        result2 = self.manager.cancel_job(job_id, "sess_1")
        
        self.assertEqual(result2["state"], "CANCELLED")
    
    def test_get_session_jobs(self):
        """Test getting all jobs for a session."""
        graph = {"nodes": [], "edges": []}
        
        result1 = self.manager.submit_job("sess_1", graph)
        result2 = self.manager.submit_job("sess_1", graph)
        result3 = self.manager.submit_job("sess_2", graph)
        
        sess1_jobs = self.manager.get_session_jobs("sess_1")
        sess2_jobs = self.manager.get_session_jobs("sess_2")
        
        self.assertEqual(len(sess1_jobs), 2)
        self.assertIn(result1["job_id"], sess1_jobs)
        self.assertIn(result2["job_id"], sess1_jobs)
        
        self.assertEqual(len(sess2_jobs), 1)
        self.assertIn(result3["job_id"], sess2_jobs)
    
    def test_cleanup_session_jobs(self):
        """Test cleaning up session jobs."""
        graph = {"nodes": [], "edges": []}
        
        result1 = self.manager.submit_job("sess_1", graph)
        result2 = self.manager.submit_job("sess_1", graph)
        
        job_id1 = result1["job_id"]
        job_id2 = result2["job_id"]
        
        self.manager.cleanup_session_jobs("sess_1")
        
        # Jobs should be removed
        self.assertNotIn(job_id1, self.manager.jobs)
        self.assertNotIn(job_id2, self.manager.jobs)
        self.assertNotIn("sess_1", self.manager.session_jobs)
    
    def test_job_state_transitions(self):
        """Test job state transitions."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        job = self.manager.jobs[job_id]
        
        # Initial state
        self.assertEqual(job.state, JobState.QUEUED)
        
        # Simulate state transitions
        job.state = JobState.VALIDATING
        self.assertEqual(job.state, JobState.VALIDATING)
        
        job.state = JobState.RUNNING
        self.assertEqual(job.state, JobState.RUNNING)
        
        job.state = JobState.COMPLETED
        self.assertEqual(job.state, JobState.COMPLETED)
    
    def test_job_progress_tracking(self):
        """Test job progress tracking."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        job = self.manager.jobs[job_id]
        
        # Update progress
        job.progress.current_epoch = 10
        job.progress.total_epochs = 50
        job.progress.nodes_executed = 3
        job.progress.nodes_total = 6
        
        status = self.manager.get_job_status(job_id, "sess_1")
        
        self.assertEqual(status["progress"]["current_epoch"], 10)
        self.assertEqual(status["progress"]["total_epochs"], 50)
        self.assertEqual(status["progress"]["nodes_executed"], 3)
        self.assertEqual(status["progress"]["nodes_total"], 6)
    
    def test_job_events_and_telemetry(self):
        """Test job events and telemetry."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        job = self.manager.jobs[job_id]
        
        # Add events and telemetry
        job.events = {"mA": 0, "mB": 1}
        job.telemetry = {
            "physical_qubits_used": 18,
            "execution_time_ms": 123
        }
        
        status = self.manager.get_job_status(job_id, "sess_1")
        
        self.assertEqual(status["events"], {"mA": 0, "mB": 1})
        self.assertEqual(status["telemetry"]["physical_qubits_used"], 18)
    
    def test_job_error_tracking(self):
        """Test job error tracking."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        job = self.manager.jobs[job_id]
        
        # Simulate error
        job.state = JobState.FAILED
        job.error = {
            "message": "Graph validation failed",
            "type": "ValidationError"
        }
        
        status = self.manager.get_job_status(job_id, "sess_1")
        
        self.assertEqual(status["state"], "FAILED")
        self.assertIn("error", status)
        self.assertEqual(status["error"]["message"], "Graph validation failed")
    
    def test_job_timing(self):
        """Test job timing tracking."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        job = self.manager.jobs[job_id]
        
        # Check created_at is set
        self.assertIsNotNone(job.created_at)
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.completed_at)
        
        # Simulate execution
        job.started_at = time.time()
        time.sleep(0.01)
        job.completed_at = time.time()
        
        status = self.manager.get_job_status(job_id, "sess_1")
        
        self.assertIn("started_at", status)
        self.assertIn("completed_at", status)
        self.assertGreater(status["completed_at"], status["started_at"])
    
    def test_wait_for_job_completed(self):
        """Test waiting for already completed job."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        # Mark as completed
        job = self.manager.jobs[job_id]
        job.state = JobState.COMPLETED
        job.completed_at = time.time()
        
        # Should return immediately
        status = self.manager.wait_for_job(job_id, "sess_1", timeout_ms=1000)
        
        self.assertEqual(status["state"], "COMPLETED")
    
    def test_wait_for_job_not_found(self):
        """Test waiting for non-existent job."""
        with self.assertRaises(KeyError):
            self.manager.wait_for_job("invalid_job", "sess_1")
    
    def test_wait_for_job_wrong_session(self):
        """Test waiting for job with wrong session."""
        graph = {"nodes": [], "edges": []}
        
        result = self.manager.submit_job("sess_1", graph)
        job_id = result["job_id"]
        
        with self.assertRaises(PermissionError):
            self.manager.wait_for_job(job_id, "sess_2")


if __name__ == "__main__":
    unittest.main()
