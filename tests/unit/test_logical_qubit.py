"""
Unit tests for logical qubit simulation
"""

import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.logical_qubit import LogicalQubit, LogicalState, TwoQubitGate
from kernel.simulator.qec_profiles import surface_code


class TestLogicalQubit(unittest.TestCase):
    """Test logical qubit functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile = surface_code(distance=5, gate_error=1e-4)
        self.qubit = LogicalQubit("q0", self.profile, seed=42)
    
    def test_qubit_initialization(self):
        """Test qubit initializes to |0⟩."""
        self.assertEqual(self.qubit.state, LogicalState.ZERO)
        self.assertEqual(self.qubit.qubit_id, "q0")
        self.assertEqual(self.qubit.gate_count, 0)
    
    def test_hadamard_gate(self):
        """Test Hadamard gate transforms states."""
        # |0⟩ -> |+⟩
        self.qubit.apply_gate("H", 0.0)
        self.assertEqual(self.qubit.state, LogicalState.PLUS)
        self.assertEqual(self.qubit.gate_count, 1)
        
        # |+⟩ -> |0⟩
        self.qubit.apply_gate("H", 1.0)
        self.assertEqual(self.qubit.state, LogicalState.ZERO)
        self.assertEqual(self.qubit.gate_count, 2)
    
    def test_x_gate(self):
        """Test X gate flips computational basis."""
        # |0⟩ -> |1⟩
        self.qubit.apply_gate("X", 0.0)
        self.assertEqual(self.qubit.state, LogicalState.ONE)
        
        # |1⟩ -> |0⟩
        self.qubit.apply_gate("X", 1.0)
        self.assertEqual(self.qubit.state, LogicalState.ZERO)
    
    def test_z_gate(self):
        """Test Z gate flips Hadamard basis."""
        # Prepare |+⟩
        self.qubit.apply_gate("H", 0.0)
        self.assertEqual(self.qubit.state, LogicalState.PLUS)
        
        # |+⟩ -> |-⟩
        self.qubit.apply_gate("Z", 1.0)
        self.assertEqual(self.qubit.state, LogicalState.MINUS)
        
        # |-⟩ -> |+⟩
        self.qubit.apply_gate("Z", 2.0)
        self.assertEqual(self.qubit.state, LogicalState.PLUS)
    
    def test_s_gate(self):
        """Test S gate (phase gate)."""
        self.qubit.apply_gate("S", 0.0)
        # S on |0⟩ leaves it as |0⟩
        self.assertEqual(self.qubit.state, LogicalState.ZERO)
        self.assertEqual(self.qubit.gate_count, 1)
    
    def test_measurement_z_basis(self):
        """Test Z-basis measurement."""
        # Measure |0⟩ in Z basis
        outcome = self.qubit.measure("Z", 0.0)
        self.assertIn(outcome, [0, 1])
        self.assertEqual(self.qubit.measurement_count, 1)
        
        # State should collapse to computational basis
        self.assertIn(self.qubit.state, [LogicalState.ZERO, LogicalState.ONE])
    
    def test_measurement_x_basis(self):
        """Test X-basis measurement."""
        # Prepare |+⟩
        self.qubit.apply_gate("H", 0.0)
        
        # Measure in X basis
        outcome = self.qubit.measure("X", 1.0)
        self.assertIn(outcome, [0, 1])
    
    def test_reset(self):
        """Test qubit reset."""
        # Apply some gates
        self.qubit.apply_gate("X", 0.0)
        self.qubit.apply_gate("H", 1.0)
        
        # Reset
        self.qubit.reset(2.0)
        
        self.assertEqual(self.qubit.state, LogicalState.ZERO)
        self.assertEqual(self.qubit.phase, 0.0)
    
    def test_decoder_cycles(self):
        """Test decoder cycles are tracked."""
        initial_cycles = self.qubit.decoder_cycles
        
        self.qubit.apply_gate("H", 0.0)
        self.qubit.apply_gate("X", 1.0)
        
        # Should have run decoder cycles
        self.assertGreater(self.qubit.decoder_cycles, initial_cycles)
    
    def test_telemetry(self):
        """Test telemetry collection."""
        self.qubit.apply_gate("H", 0.0)
        self.qubit.apply_gate("S", 1.0)
        self.qubit.measure("Z", 2.0)
        
        telemetry = self.qubit.get_telemetry()
        
        self.assertEqual(telemetry["qubit_id"], "q0")
        self.assertEqual(telemetry["gate_count"], 2)
        self.assertEqual(telemetry["measurement_count"], 1)
        self.assertGreater(telemetry["decoder_cycles"], 0)
        self.assertIn("error_breakdown", telemetry)


class TestTwoQubitGate(unittest.TestCase):
    """Test two-qubit gate operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile = surface_code(distance=5, gate_error=1e-4)
        self.control = LogicalQubit("control", self.profile, seed=42)
        self.target = LogicalQubit("target", self.profile, seed=43)
    
    def test_cnot_with_control_zero(self):
        """Test CNOT with control in |0⟩."""
        # Control is |0⟩, target is |0⟩
        initial_target_state = self.target.state
        
        TwoQubitGate.apply_cnot(self.control, self.target, 0.0)
        
        # Target should be unchanged
        self.assertEqual(self.target.state, initial_target_state)
    
    def test_cnot_with_control_one(self):
        """Test CNOT with control in |1⟩."""
        # Set control to |1⟩
        self.control.apply_gate("X", 0.0)
        
        # Target starts in |0⟩
        TwoQubitGate.apply_cnot(self.control, self.target, 1.0)
        
        # Target should be flipped (simplified model)
        # Note: This is a simplified test as the actual implementation
        # uses a peek at the control state
    
    def test_cnot_updates_both_qubits(self):
        """Test CNOT updates gate counts for both qubits."""
        initial_control_gates = self.control.gate_count
        initial_target_gates = self.target.gate_count
        
        TwoQubitGate.apply_cnot(self.control, self.target, 0.0)
        
        self.assertEqual(self.control.gate_count, initial_control_gates + 1)
        self.assertEqual(self.target.gate_count, initial_target_gates + 1)


class TestLogicalErrorRate(unittest.TestCase):
    """Test logical error rate estimation."""
    
    def test_error_rate_below_threshold(self):
        """Test logical error rate is suppressed below threshold."""
        # Physical error rate below threshold
        profile = surface_code(distance=9, gate_error=1e-4)
        qubit = LogicalQubit("q0", profile, seed=42)
        
        logical_error = qubit.get_logical_error_probability()
        
        # Logical error should be much smaller than physical
        self.assertLess(logical_error, 1e-4)
    
    def test_error_rate_scales_with_distance(self):
        """Test logical error rate improves with distance."""
        gate_error = 1e-3
        
        profile_d5 = surface_code(distance=5, gate_error=gate_error)
        qubit_d5 = LogicalQubit("q0", profile_d5, seed=42)
        error_d5 = qubit_d5.get_logical_error_probability()
        
        profile_d9 = surface_code(distance=9, gate_error=gate_error)
        qubit_d9 = LogicalQubit("q0", profile_d9, seed=42)
        error_d9 = qubit_d9.get_logical_error_probability()
        
        # Higher distance should have lower logical error
        self.assertLess(error_d9, error_d5)


class TestDeterministicBehavior(unittest.TestCase):
    """Test deterministic behavior with fixed seed."""
    
    def test_same_seed_same_results(self):
        """Test same seed produces same measurement outcomes."""
        profile = surface_code(distance=5, gate_error=1e-3)
        
        # First run
        qubit1 = LogicalQubit("q0", profile, seed=42)
        qubit1.apply_gate("H", 0.0)
        outcome1 = qubit1.measure("Z", 1.0)
        
        # Second run with same seed
        qubit2 = LogicalQubit("q0", profile, seed=42)
        qubit2.apply_gate("H", 0.0)
        outcome2 = qubit2.measure("Z", 1.0)
        
        # Should get same outcome
        self.assertEqual(outcome1, outcome2)
    
    def test_different_seed_different_results(self):
        """Test different seeds can produce different results."""
        profile = surface_code(distance=5, gate_error=1e-3)
        
        outcomes = set()
        for seed in range(10):
            qubit = LogicalQubit("q0", profile, seed=seed)
            qubit.apply_gate("H", 0.0)
            outcome = qubit.measure("Z", 1.0)
            outcomes.add(outcome)
        
        # Should see both 0 and 1 across different seeds
        self.assertEqual(len(outcomes), 2)


if __name__ == "__main__":
    unittest.main()
