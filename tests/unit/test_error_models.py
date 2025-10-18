"""
Unit tests for error models
"""

import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.error_models import (
    ErrorEvent,
    DepolarizingNoise,
    CoherenceNoise,
    MeasurementNoise,
    CompositeErrorModel,
)


class TestErrorEvent(unittest.TestCase):
    """Test error event representation."""
    
    def test_error_event_creation(self):
        """Test creating an error event."""
        event = ErrorEvent(
            error_type="X",
            qubit_id="q0",
            time_us=1.0,
            corrected=False
        )
        
        self.assertEqual(event.error_type, "X")
        self.assertEqual(event.qubit_id, "q0")
        self.assertEqual(event.time_us, 1.0)
        self.assertFalse(event.corrected)


class TestDepolarizingNoise(unittest.TestCase):
    """Test depolarizing noise model."""
    
    def test_no_error_with_zero_rate(self):
        """Test no errors occur with zero error rate."""
        model = DepolarizingNoise(seed=42)
        
        for _ in range(100):
            error = model.apply_gate_noise("q0", 0.0, 0.0)
            self.assertIsNone(error)
    
    def test_errors_with_high_rate(self):
        """Test errors occur with high error rate."""
        model = DepolarizingNoise(seed=42)
        error_count = 0
        
        for _ in range(1000):
            error = model.apply_gate_noise("q0", 1.0, 0.0)  # 100% error rate
            if error:
                error_count += 1
        
        # Should get errors most of the time
        self.assertGreater(error_count, 900)
    
    def test_error_types(self):
        """Test all Pauli error types can occur."""
        model = DepolarizingNoise(seed=42)
        error_types = set()
        
        for _ in range(1000):
            error = model.apply_gate_noise("q0", 1.0, 0.0)
            if error:
                error_types.add(error)
        
        # Should see X, Y, and Z errors
        self.assertIn("X", error_types)
        self.assertIn("Y", error_types)
        self.assertIn("Z", error_types)
    
    def test_idle_noise_scales_with_duration(self):
        """Test idle noise probability scales with duration."""
        model = DepolarizingNoise(seed=42)
        
        # Short duration should have fewer errors
        short_errors = sum(
            1 for _ in range(1000)
            if model.apply_idle_noise("q0", 1e-4, 1.0, 0.0)
        )
        
        model = DepolarizingNoise(seed=42)
        
        # Long duration should have more errors
        long_errors = sum(
            1 for _ in range(1000)
            if model.apply_idle_noise("q0", 1e-4, 100.0, 0.0)
        )
        
        self.assertGreater(long_errors, short_errors)


class TestCoherenceNoise(unittest.TestCase):
    """Test coherence noise model."""
    
    def test_t2_constraint(self):
        """Test T2 <= 2*T1 constraint."""
        # Valid: T2 < 2*T1
        model = CoherenceNoise(t1_us=100.0, t2_us=80.0, seed=42)
        self.assertEqual(model.t1_us, 100.0)
        
        # Invalid: T2 > 2*T1
        with self.assertRaises(ValueError):
            CoherenceNoise(t1_us=100.0, t2_us=250.0, seed=42)
    
    def test_t1_decay_probability(self):
        """Test T1 decay probability increases with time."""
        model = CoherenceNoise(t1_us=100.0, t2_us=80.0, seed=42)
        
        # Short duration: few decays
        short_decays = sum(
            1 for _ in range(1000)
            if model.apply_t1_decay("q0", 1.0, 0.0)
        )
        
        model = CoherenceNoise(t1_us=100.0, t2_us=80.0, seed=42)
        
        # Long duration: more decays
        long_decays = sum(
            1 for _ in range(1000)
            if model.apply_t1_decay("q0", 100.0, 0.0)
        )
        
        self.assertGreater(long_decays, short_decays)
    
    def test_t2_dephasing(self):
        """Test T2 dephasing occurs."""
        model = CoherenceNoise(t1_us=100.0, t2_us=50.0, seed=42)
        
        dephasing_count = sum(
            1 for _ in range(1000)
            if model.apply_t2_dephasing("q0", 50.0, 0.0)
        )
        
        # Should see some dephasing events
        self.assertGreater(dephasing_count, 0)


class TestMeasurementNoise(unittest.TestCase):
    """Test measurement noise model."""
    
    def test_no_error_with_zero_rate(self):
        """Test no measurement errors with zero rate."""
        model = MeasurementNoise(seed=42)
        
        for outcome in [0, 1]:
            for _ in range(100):
                result = model.apply_measurement_error("q0", outcome, 0.0, 0.0)
                self.assertEqual(result, outcome)
    
    def test_bit_flip_with_high_rate(self):
        """Test measurement errors flip bits."""
        model = MeasurementNoise(seed=42)
        
        flips = sum(
            1 for _ in range(1000)
            if model.apply_measurement_error("q0", 0, 1.0, 0.0) == 1
        )
        
        # With 100% error rate, should flip most of the time
        self.assertGreater(flips, 900)
    
    def test_symmetric_errors(self):
        """Test errors are symmetric for 0 and 1."""
        model = MeasurementNoise(seed=42)
        error_rate = 0.1
        
        flips_0 = sum(
            1 for _ in range(1000)
            if model.apply_measurement_error("q0", 0, error_rate, 0.0) == 1
        )
        
        model = MeasurementNoise(seed=42)
        
        flips_1 = sum(
            1 for _ in range(1000)
            if model.apply_measurement_error("q0", 1, error_rate, 0.0) == 0
        )
        
        # Should be roughly equal (within statistical variation)
        self.assertAlmostEqual(flips_0, flips_1, delta=50)


class TestCompositeErrorModel(unittest.TestCase):
    """Test composite error model."""
    
    def test_composite_model_creation(self):
        """Test creating composite error model."""
        model = CompositeErrorModel(
            gate_error_rate=1e-3,
            measurement_error_rate=1e-2,
            idle_error_rate=1e-4,
            t1_us=100.0,
            t2_us=80.0,
            seed=42
        )
        
        self.assertEqual(model.gate_error_rate, 1e-3)
        self.assertEqual(model.measurement_error_rate, 1e-2)
    
    def test_all_error_sources(self):
        """Test all error sources are applied."""
        model = CompositeErrorModel(
            gate_error_rate=0.5,  # High rate for testing
            measurement_error_rate=0.5,
            idle_error_rate=0.5,
            t1_us=100.0,
            t2_us=80.0,
            seed=42
        )
        
        # Apply gate errors
        for _ in range(100):
            model.apply_gate_errors("q0", 0.0)
        
        # Apply idle errors
        for _ in range(100):
            model.apply_idle_errors("q0", 10.0, 0.0)
        
        # Apply measurement errors
        for _ in range(100):
            model.apply_measurement_errors("q0", 0, 0.0)
        
        # Should have errors from all sources
        breakdown = model.get_error_breakdown()
        self.assertGreater(breakdown["depolarizing"], 0)
        self.assertGreater(breakdown["coherence"], 0)
        self.assertGreater(breakdown["measurement"], 0)
        self.assertGreater(breakdown["total"], 0)
    
    def test_error_tracking(self):
        """Test error tracking across all models."""
        model = CompositeErrorModel(
            gate_error_rate=1.0,  # 100% for testing
            measurement_error_rate=1.0,
            idle_error_rate=1.0,
            t1_us=100.0,
            t2_us=80.0,
            seed=42
        )
        
        # Generate some errors
        model.apply_gate_errors("q0", 0.0)
        model.apply_measurement_errors("q0", 0, 0.0)
        
        total = model.get_total_errors()
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()
