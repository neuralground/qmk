"""
Test measurement in different bases.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.simulator.logical_qubit import LogicalQubit, LogicalState
from kernel.simulator.qec_profiles import parse_profile_string


class TestMeasurementBases(unittest.TestCase):
    """Test measurement in Z, X, and Y bases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile = parse_profile_string("logical:Surface(d=7)")
    
    def test_z_basis_measurement(self):
        """Test Z-basis measurement on computational basis states."""
        # |0⟩ state
        qubit = LogicalQubit("q0", self.profile, seed=42)
        qubit.state = LogicalState.ZERO
        outcome = qubit.measure("Z", 0.0)
        self.assertEqual(outcome, 0, "Z measurement of |0⟩ should give 0")
        
        # |1⟩ state
        qubit = LogicalQubit("q1", self.profile, seed=42)
        qubit.state = LogicalState.ONE
        outcome = qubit.measure("Z", 0.0)
        self.assertEqual(outcome, 1, "Z measurement of |1⟩ should give 1")
    
    def test_x_basis_measurement(self):
        """Test X-basis measurement on Hadamard basis states."""
        # |+⟩ state
        qubit = LogicalQubit("q0", self.profile, seed=42)
        qubit.state = LogicalState.PLUS
        outcome = qubit.measure("X", 0.0)
        self.assertEqual(outcome, 0, "X measurement of |+⟩ should give 0")
        
        # |-⟩ state
        qubit = LogicalQubit("q1", self.profile, seed=42)
        qubit.state = LogicalState.MINUS
        outcome = qubit.measure("X", 0.0)
        self.assertEqual(outcome, 1, "X measurement of |-⟩ should give 1")
    
    def test_y_basis_measurement(self):
        """Test Y-basis measurement."""
        # |+⟩ state (approximates |+i⟩)
        qubit = LogicalQubit("q0", self.profile, seed=42)
        qubit.state = LogicalState.PLUS
        outcome = qubit.measure("Y", 0.0)
        self.assertEqual(outcome, 0, "Y measurement of |+⟩ should give 0")
        
        # |-⟩ state (approximates |-i⟩)
        qubit = LogicalQubit("q1", self.profile, seed=42)
        qubit.state = LogicalState.MINUS
        outcome = qubit.measure("Y", 0.0)
        self.assertEqual(outcome, 1, "Y measurement of |-⟩ should give 1")
    
    def test_z_measurement_on_superposition(self):
        """Test Z measurement on superposition gives random outcome."""
        # |+⟩ state measured in Z basis should give 50/50
        results = []
        for i in range(100):
            qubit = LogicalQubit(f"q{i}", self.profile, seed=i)
            qubit.state = LogicalState.PLUS
            outcome = qubit.measure("Z", 0.0)
            results.append(outcome)
        
        # Should have both 0 and 1 outcomes
        self.assertIn(0, results, "Should get some 0 outcomes")
        self.assertIn(1, results, "Should get some 1 outcomes")
        
        # Should be roughly 50/50 (allow 30-70% range)
        zeros = results.count(0)
        ratio = zeros / len(results)
        self.assertGreater(ratio, 0.3, f"Should have at least 30% zeros, got {ratio:.2%}")
        self.assertLess(ratio, 0.7, f"Should have at most 70% zeros, got {ratio:.2%}")
    
    def test_x_measurement_on_computational(self):
        """Test X measurement on computational basis gives random outcome."""
        # |0⟩ state measured in X basis should give 50/50
        results = []
        for i in range(100):
            qubit = LogicalQubit(f"q{i}", self.profile, seed=i)
            qubit.state = LogicalState.ZERO
            outcome = qubit.measure("X", 0.0)
            results.append(outcome)
        
        # Should have both 0 and 1 outcomes
        self.assertIn(0, results, "Should get some 0 outcomes")
        self.assertIn(1, results, "Should get some 1 outcomes")
    
    def test_arbitrary_angle_measurement(self):
        """Test measurement at arbitrary angles."""
        import math
        
        # Angle 0 (Z-basis)
        qubit = LogicalQubit("q0", self.profile, seed=42)
        qubit.state = LogicalState.ZERO
        outcome = qubit.measure("ANGLE", 0.0, angle=0.0)
        self.assertEqual(outcome, 0, "Angle 0 should behave like Z-basis")
        
        # Angle π/2 (X-basis)
        qubit = LogicalQubit("q1", self.profile, seed=42)
        qubit.state = LogicalState.PLUS
        outcome = qubit.measure("ANGLE", 0.0, angle=math.pi/2)
        self.assertEqual(outcome, 0, "Angle π/2 should behave like X-basis")
        
        # Angle π (-Z-basis)
        qubit = LogicalQubit("q2", self.profile, seed=42)
        qubit.state = LogicalState.ZERO
        outcome = qubit.measure("ANGLE", 0.0, angle=math.pi)
        self.assertEqual(outcome, 1, "Angle π should flip Z-basis result")
    
    def test_measurement_collapses_state(self):
        """Test that measurement collapses state to computational basis."""
        # Start in superposition
        qubit = LogicalQubit("q0", self.profile, seed=42)
        qubit.state = LogicalState.PLUS
        
        # Measure in Z basis
        outcome = qubit.measure("Z", 0.0)
        
        # State should now be collapsed to |0⟩ or |1⟩
        self.assertIn(qubit.state, [LogicalState.ZERO, LogicalState.ONE],
                     "State should collapse to computational basis after measurement")
        
        # State should match outcome
        if outcome == 0:
            self.assertEqual(qubit.state, LogicalState.ZERO)
        else:
            self.assertEqual(qubit.state, LogicalState.ONE)
    
    def test_invalid_basis_raises_error(self):
        """Test that invalid basis raises error."""
        qubit = LogicalQubit("q0", self.profile, seed=42)
        
        with self.assertRaises(ValueError):
            qubit.measure("INVALID", 0.0)


if __name__ == '__main__':
    unittest.main()
