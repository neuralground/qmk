"""
Unit tests for Hardware Adapters
"""

import unittest
import time
from kernel.hardware import (
    SimulatedBackend, AzureQuantumBackend, BackendManager,
    HardwareStatus, JobStatus
)


# Sample circuit for testing
SAMPLE_CIRCUIT = {
    "name": "bell_state",
    "nodes": [
        {"node_id": "n0", "op": "ALLOC_LQ", "qubits": ["q0"]},
        {"node_id": "n1", "op": "ALLOC_LQ", "qubits": ["q1"]},
        {"node_id": "n2", "op": "H", "qubits": ["q0"]},
        {"node_id": "n3", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n4", "op": "MEASURE_Z", "qubits": ["q0"], "params": {"result": "r0"}},
        {"node_id": "n5", "op": "MEASURE_Z", "qubits": ["q1"], "params": {"result": "r1"}},
    ]
}


class TestSimulatedBackend(unittest.TestCase):
    """Test simulated backend."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = SimulatedBackend(num_qubits=10)
    
    def test_connect(self):
        """Test connection."""
        result = self.backend.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.backend.get_status(), HardwareStatus.ONLINE)
    
    def test_disconnect(self):
        """Test disconnection."""
        self.backend.connect()
        self.backend.disconnect()
        
        self.assertEqual(self.backend.get_status(), HardwareStatus.OFFLINE)
    
    def test_get_capabilities(self):
        """Test getting capabilities."""
        self.backend.connect()
        caps = self.backend.get_capabilities()
        
        self.assertEqual(caps.max_qubits, 10)
        self.assertIn("H", caps.supported_gates)
        self.assertIn("CNOT", caps.supported_gates)
        self.assertTrue(caps.has_mid_circuit_measurement)
    
    def test_get_calibration_data(self):
        """Test getting calibration data."""
        self.backend.connect()
        calib = self.backend.get_calibration_data()
        
        self.assertGreater(len(calib.qubit_t1), 0)
        self.assertGreater(len(calib.qubit_t2), 0)
        self.assertIn("single_qubit", calib.gate_fidelities)
    
    def test_submit_job(self):
        """Test job submission."""
        self.backend.connect()
        
        backend_job_id = self.backend.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=100
        )
        
        self.assertIsNotNone(backend_job_id)
        self.assertIn("sim_qpu", backend_job_id)
    
    def test_get_job_status(self):
        """Test getting job status."""
        self.backend.connect()
        
        backend_job_id = self.backend.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=100
        )
        
        # Wait for execution
        time.sleep(0.2)
        
        status = self.backend.get_job_status(backend_job_id)
        self.assertEqual(status, JobStatus.COMPLETED)
    
    def test_get_job_result(self):
        """Test getting job result."""
        self.backend.connect()
        
        backend_job_id = self.backend.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=100
        )
        
        # Wait for execution
        time.sleep(0.2)
        
        result = self.backend.get_job_result(backend_job_id)
        
        self.assertEqual(result.status, JobStatus.COMPLETED)
        self.assertIn("r0", result.measurements)
        self.assertIn("r1", result.measurements)
        self.assertEqual(len(result.measurements["r0"]), 100)
    
    def test_cancel_job(self):
        """Test job cancellation."""
        self.backend.connect()
        
        backend_job_id = self.backend.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=1000
        )
        
        # Try to cancel immediately
        cancelled = self.backend.cancel_job(backend_job_id)
        
        # May or may not succeed depending on timing
        self.assertIsInstance(cancelled, bool)


class TestAzureQuantumBackend(unittest.TestCase):
    """Test Azure Quantum backend."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = AzureQuantumBackend()
    
    def test_connect(self):
        """Test connection (stub)."""
        result = self.backend.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.backend.get_status(), HardwareStatus.ONLINE)
    
    def test_get_capabilities(self):
        """Test getting capabilities."""
        self.backend.connect()
        caps = self.backend.get_capabilities()
        
        self.assertGreater(caps.max_qubits, 0)
        self.assertIn("H", caps.supported_gates)
    
    def test_submit_job(self):
        """Test job submission (stub)."""
        self.backend.connect()
        
        backend_job_id = self.backend.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=100
        )
        
        self.assertIsNotNone(backend_job_id)
        self.assertIn("azure", backend_job_id)


class TestBackendManager(unittest.TestCase):
    """Test backend manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BackendManager()
    
    def test_register_backend(self):
        """Test backend registration."""
        backend = SimulatedBackend(backend_id="sim1")
        
        self.manager.register_backend(backend, set_as_default=True)
        
        self.assertIn("sim1", self.manager.backends)
        self.assertEqual(self.manager.default_backend, "sim1")
    
    def test_unregister_backend(self):
        """Test backend unregistration."""
        backend = SimulatedBackend(backend_id="sim1")
        self.manager.register_backend(backend)
        
        self.manager.unregister_backend("sim1")
        
        self.assertNotIn("sim1", self.manager.backends)
    
    def test_get_backend(self):
        """Test getting backend."""
        backend = SimulatedBackend(backend_id="sim1")
        self.manager.register_backend(backend)
        
        retrieved = self.manager.get_backend("sim1")
        
        self.assertEqual(retrieved.backend_id, "sim1")
    
    def test_list_backends(self):
        """Test listing backends."""
        backend1 = SimulatedBackend(backend_id="sim1")
        backend2 = SimulatedBackend(backend_id="sim2")
        
        self.manager.register_backend(backend1)
        self.manager.register_backend(backend2)
        
        backends = self.manager.list_backends()
        
        self.assertEqual(len(backends), 2)
    
    def test_submit_job(self):
        """Test job submission through manager."""
        backend = SimulatedBackend(backend_id="sim1")
        backend.connect()
        self.manager.register_backend(backend, set_as_default=True)
        
        backend_id, backend_job_id = self.manager.submit_job(
            "test_job_1",
            SAMPLE_CIRCUIT,
            shots=100
        )
        
        self.assertEqual(backend_id, "sim1")
        self.assertIsNotNone(backend_job_id)
    
    def test_get_health_status(self):
        """Test getting health status."""
        backend1 = SimulatedBackend(backend_id="sim1")
        backend1.connect()
        backend2 = SimulatedBackend(backend_id="sim2")
        
        self.manager.register_backend(backend1)
        self.manager.register_backend(backend2)
        
        health = self.manager.get_health_status()
        
        self.assertEqual(health["total_backends"], 2)
        self.assertEqual(health["online_backends"], 1)
        self.assertEqual(health["offline_backends"], 1)
    
    def test_select_best_backend(self):
        """Test backend selection."""
        backend1 = SimulatedBackend(backend_id="sim1", num_qubits=10)
        backend1.connect()
        backend2 = SimulatedBackend(backend_id="sim2", num_qubits=20)
        backend2.connect()
        
        self.manager.register_backend(backend1)
        self.manager.register_backend(backend2)
        
        # Require 15 qubits
        best = self.manager.select_best_backend({"qubits": 15})
        
        self.assertEqual(best, "sim2")


if __name__ == "__main__":
    unittest.main()
