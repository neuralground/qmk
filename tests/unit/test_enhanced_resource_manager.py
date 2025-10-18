"""
Unit tests for enhanced resource manager
"""

import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.qec_profiles import surface_code, shyps_code


class TestEnhancedResourceManager(unittest.TestCase):
    """Test enhanced resource manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rm = EnhancedResourceManager(max_physical_qubits=1000, seed=42)
    
    def test_initialization(self):
        """Test resource manager initialization."""
        self.assertEqual(self.rm.max_physical_qubits, 1000)
        self.assertEqual(self.rm.physical_qubits_used, 0)
        self.assertEqual(len(self.rm.logical_qubits), 0)
    
    def test_alloc_single_qubit(self):
        """Test allocating a single logical qubit."""
        profile = surface_code(distance=5)
        allocated = self.rm.alloc_logical_qubits(["q0"], profile)
        
        self.assertEqual(len(allocated), 1)
        self.assertEqual(allocated[0][0], "q0")
        self.assertEqual(allocated[0][1], profile.physical_qubit_count)
        self.assertEqual(self.rm.physical_qubits_used, profile.physical_qubit_count)
    
    def test_alloc_multiple_qubits(self):
        """Test allocating multiple logical qubits."""
        profile = surface_code(distance=5)
        allocated = self.rm.alloc_logical_qubits(["q0", "q1", "q2"], profile)
        
        self.assertEqual(len(allocated), 3)
        self.assertEqual(self.rm.physical_qubits_used, 3 * profile.physical_qubit_count)
        self.assertEqual(len(self.rm.logical_qubits), 3)
    
    def test_alloc_different_profiles(self):
        """Test allocating qubits with different profiles."""
        surface = surface_code(distance=5)
        shyps = shyps_code(distance=7)
        
        self.rm.alloc_logical_qubits(["q0"], surface)
        self.rm.alloc_logical_qubits(["q1"], shyps)
        
        expected_physical = surface.physical_qubit_count + shyps.physical_qubit_count
        self.assertEqual(self.rm.physical_qubits_used, expected_physical)
    
    def test_alloc_exceeds_capacity(self):
        """Test allocation fails when exceeding capacity."""
        # Create small resource manager
        small_rm = EnhancedResourceManager(max_physical_qubits=100, seed=42)
        
        profile = surface_code(distance=9)  # 162 physical qubits
        
        with self.assertRaises(RuntimeError) as ctx:
            small_rm.alloc_logical_qubits(["q0"], profile)
        
        self.assertIn("Insufficient physical qubits", str(ctx.exception))
    
    def test_alloc_duplicate_id(self):
        """Test allocating duplicate ID raises error."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0"], profile)
        
        with self.assertRaises(RuntimeError) as ctx:
            self.rm.alloc_logical_qubits(["q0"], profile)
        
        self.assertIn("already allocated", str(ctx.exception))
    
    def test_free_qubits(self):
        """Test freeing logical qubits."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        
        initial_used = self.rm.physical_qubits_used
        
        self.rm.free_logical_qubits(["q0"])
        
        self.assertEqual(
            self.rm.physical_qubits_used,
            initial_used - profile.physical_qubit_count
        )
        self.assertEqual(len(self.rm.logical_qubits), 1)
    
    def test_free_all_qubits(self):
        """Test freeing all qubits returns to initial state."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1", "q2"], profile)
        
        self.rm.free_logical_qubits(["q0", "q1", "q2"])
        
        self.assertEqual(self.rm.physical_qubits_used, 0)
        self.assertEqual(len(self.rm.logical_qubits), 0)
    
    def test_free_nonexistent_qubit(self):
        """Test freeing nonexistent qubit is silently ignored."""
        # Should not raise error
        self.rm.free_logical_qubits(["nonexistent"])
        self.assertEqual(self.rm.physical_qubits_used, 0)
    
    def test_get_logical_qubit(self):
        """Test getting logical qubit instance."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0"], profile)
        
        qubit = self.rm.get_logical_qubit("q0")
        
        self.assertEqual(qubit.qubit_id, "q0")
        self.assertEqual(qubit.profile.code_distance, 5)
    
    def test_get_nonexistent_qubit(self):
        """Test getting nonexistent qubit raises error."""
        with self.assertRaises(KeyError):
            self.rm.get_logical_qubit("nonexistent")
    
    def test_open_channel(self):
        """Test opening entanglement channel."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        
        self.rm.open_channel("ch0", "q0", "q1", fidelity=0.99)
        
        self.assertIn("ch0", self.rm.channels)
        self.assertEqual(self.rm.channels["ch0"]["vq_a"], "q0")
        self.assertEqual(self.rm.channels["ch0"]["vq_b"], "q1")
        self.assertEqual(self.rm.channels["ch0"]["fidelity"], 0.99)
    
    def test_open_duplicate_channel(self):
        """Test opening duplicate channel raises error."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        
        self.rm.open_channel("ch0", "q0", "q1")
        
        with self.assertRaises(RuntimeError):
            self.rm.open_channel("ch0", "q0", "q1")
    
    def test_close_channel(self):
        """Test closing channel."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        
        self.rm.open_channel("ch0", "q0", "q1")
        self.rm.close_channel("ch0")
        
        self.assertNotIn("ch0", self.rm.channels)
    
    def test_close_nonexistent_channel(self):
        """Test closing nonexistent channel is silently ignored."""
        # Should not raise error
        self.rm.close_channel("nonexistent")
    
    def test_resource_usage(self):
        """Test resource usage statistics."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        
        usage = self.rm.get_resource_usage()
        
        self.assertEqual(usage["logical_qubits_allocated"], 2)
        self.assertEqual(usage["physical_qubits_used"], 2 * profile.physical_qubit_count)
        self.assertGreater(usage["physical_qubits_available"], 0)
        self.assertGreater(usage["utilization"], 0)
        self.assertLess(usage["utilization"], 1)
    
    def test_telemetry(self):
        """Test comprehensive telemetry."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0"], profile)
        
        # Execute some operations
        qubit = self.rm.get_logical_qubit("q0")
        qubit.apply_gate("H", 0.0)
        qubit.measure("Z", 1.0)
        
        telemetry = self.rm.get_telemetry()
        
        self.assertIn("resource_usage", telemetry)
        self.assertIn("qubits", telemetry)
        self.assertIn("q0", telemetry["qubits"])
        self.assertEqual(telemetry["qubits"]["q0"]["gate_count"], 1)
        self.assertEqual(telemetry["qubits"]["q0"]["measurement_count"], 1)
    
    def test_advance_time(self):
        """Test time advancement."""
        self.assertEqual(self.rm.current_time_us, 0.0)
        
        self.rm.advance_time(10.0)
        self.assertEqual(self.rm.current_time_us, 10.0)
        
        self.rm.advance_time(5.5)
        self.assertEqual(self.rm.current_time_us, 15.5)
    
    def test_reset(self):
        """Test resource manager reset."""
        profile = surface_code(distance=5)
        self.rm.alloc_logical_qubits(["q0", "q1"], profile)
        self.rm.open_channel("ch0", "q0", "q1")
        self.rm.advance_time(100.0)
        
        self.rm.reset()
        
        self.assertEqual(len(self.rm.logical_qubits), 0)
        self.assertEqual(len(self.rm.channels), 0)
        self.assertEqual(self.rm.physical_qubits_used, 0)
        self.assertEqual(self.rm.current_time_us, 0.0)
    
    def test_deterministic_with_seed(self):
        """Test deterministic behavior with seed."""
        profile = surface_code(distance=5)
        
        # First run
        rm1 = EnhancedResourceManager(seed=42)
        rm1.alloc_logical_qubits(["q0"], profile)
        q1 = rm1.get_logical_qubit("q0")
        q1.apply_gate("H", 0.0)
        outcome1 = q1.measure("Z", 1.0)
        
        # Second run with same seed
        rm2 = EnhancedResourceManager(seed=42)
        rm2.alloc_logical_qubits(["q0"], profile)
        q2 = rm2.get_logical_qubit("q0")
        q2.apply_gate("H", 0.0)
        outcome2 = q2.measure("Z", 1.0)
        
        # Should get same outcome
        self.assertEqual(outcome1, outcome2)


if __name__ == "__main__":
    unittest.main()
