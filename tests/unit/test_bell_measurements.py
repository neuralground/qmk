"""
Test Bell basis measurements.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.simulator.logical_qubit import LogicalQubit, LogicalState
from kernel.simulator.qec_profiles import parse_profile_string


class TestBellMeasurements(unittest.TestCase):
    """Test Bell basis measurements on two qubits."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile = parse_profile_string("logical:Surface(d=7)")
    
    def test_bell_measurement_on_phi_plus(self):
        """Test Bell measurement on |Φ+⟩ = (|00⟩ + |11⟩)/√2."""
        # Create Bell state |Φ+⟩
        qubit1 = LogicalQubit("q0", self.profile, seed=42)
        qubit2 = LogicalQubit("q1", self.profile, seed=42)
        
        # Prepare |Φ+⟩: H(q0), CNOT(q0, q1)
        qubit1.apply_gate("H", 0.0)
        from kernel.simulator.logical_qubit import TwoQubitGate
        TwoQubitGate.apply_cnot(qubit1, qubit2, 0.0)
        
        # Perform Bell measurement
        outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
            qubit1, qubit2, 0.0
        )
        
        # Should measure |Φ+⟩ (index 0) which gives 00
        self.assertEqual(bell_index, 0, f"Should measure |Φ+⟩ (index 0), got {bell_index}")
        self.assertEqual(outcome1, 0, "First outcome should be 0")
        self.assertEqual(outcome2, 0, "Second outcome should be 0")
    
    def test_bell_measurement_indices(self):
        """Test that Bell measurement returns correct indices."""
        # Test all four possible outcomes map to correct indices
        test_cases = [
            (0, 0, 0),  # |Φ+⟩
            (1, 0, 2),  # |Φ-⟩
            (0, 1, 1),  # |Ψ+⟩
            (1, 1, 3),  # |Ψ-⟩
        ]
        
        for expected_o1, expected_o2, expected_index in test_cases:
            # Create qubits in computational basis
            qubit1 = LogicalQubit("q0", self.profile, seed=42)
            qubit2 = LogicalQubit("q1", self.profile, seed=42)
            
            # Set to specific computational state
            if expected_o1 == 1:
                qubit1.state = LogicalState.ONE
            if expected_o2 == 1:
                qubit2.state = LogicalState.ONE
            
            # Perform Bell measurement
            outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
                qubit1, qubit2, 0.0
            )
            
            # Check index calculation
            calculated_index = outcome1 * 2 + outcome2
            self.assertEqual(bell_index, calculated_index,
                           f"Bell index should match calculation: {outcome1}*2 + {outcome2}")
    
    def test_bell_measurement_on_entangled_pair(self):
        """Test Bell measurement preserves entanglement statistics."""
        # Run multiple times to check statistics
        results = []
        for i in range(50):
            qubit1 = LogicalQubit(f"q0_{i}", self.profile, seed=i)
            qubit2 = LogicalQubit(f"q1_{i}", self.profile, seed=i)
            
            # Create Bell state
            qubit1.apply_gate("H", 0.0)
            from kernel.simulator.logical_qubit import TwoQubitGate
            TwoQubitGate.apply_cnot(qubit1, qubit2, 0.0)
            
            # Measure
            outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
                qubit1, qubit2, 0.0
            )
            
            results.append((outcome1, outcome2, bell_index))
        
        # All measurements should give the same Bell state (|Φ+⟩)
        # since we're measuring the state we prepared
        bell_indices = [r[2] for r in results]
        
        # Most should be index 0 (|Φ+⟩)
        # Allow some variation due to errors and different seeds
        phi_plus_count = bell_indices.count(0)
        self.assertGreater(phi_plus_count, 20,
                          f"Should measure |Φ+⟩ most of the time, got {phi_plus_count}/50")
    
    def test_bell_measurement_on_separable_state(self):
        """Test Bell measurement on separable (non-entangled) state."""
        # Create separable state |00⟩
        qubit1 = LogicalQubit("q0", self.profile, seed=42)
        qubit2 = LogicalQubit("q1", self.profile, seed=42)
        
        # Both in |0⟩ state (default)
        self.assertEqual(qubit1.state, LogicalState.ZERO)
        self.assertEqual(qubit2.state, LogicalState.ZERO)
        
        # Perform Bell measurement
        outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
            qubit1, qubit2, 0.0
        )
        
        # Should measure 00 (index 0)
        self.assertEqual(outcome1, 0, "First outcome should be 0")
        self.assertEqual(outcome2, 0, "Second outcome should be 0")
        self.assertEqual(bell_index, 0, "Bell index should be 0")
    
    def test_bell_measurement_on_product_state(self):
        """Test Bell measurement on |+⟩|0⟩ product state."""
        qubit1 = LogicalQubit("q0", self.profile, seed=42)
        qubit2 = LogicalQubit("q1", self.profile, seed=42)
        
        # Prepare |+⟩|0⟩
        qubit1.apply_gate("H", 0.0)
        
        # Perform Bell measurement
        outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
            qubit1, qubit2, 0.0
        )
        
        # Should get random outcomes
        # Just verify it completes without error
        self.assertIn(outcome1, [0, 1], "Outcome should be 0 or 1")
        self.assertIn(outcome2, [0, 1], "Outcome should be 0 or 1")
        self.assertIn(bell_index, [0, 1, 2, 3], "Bell index should be 0-3")
    
    def test_bell_measurement_collapses_state(self):
        """Test that Bell measurement collapses both qubits."""
        qubit1 = LogicalQubit("q0", self.profile, seed=42)
        qubit2 = LogicalQubit("q1", self.profile, seed=42)
        
        # Create superposition
        qubit1.apply_gate("H", 0.0)
        qubit2.apply_gate("H", 0.0)
        
        # Perform Bell measurement
        outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
            qubit1, qubit2, 0.0
        )
        
        # Both qubits should be in computational basis after measurement
        self.assertIn(qubit1.state, [LogicalState.ZERO, LogicalState.ONE],
                     "Qubit 1 should collapse to computational basis")
        self.assertIn(qubit2.state, [LogicalState.ZERO, LogicalState.ONE],
                     "Qubit 2 should collapse to computational basis")
    
    def test_bell_state_identification(self):
        """Test identification of different Bell states."""
        # This tests the Bell measurement protocol
        # Bell measurement should distinguish between the four Bell states
        
        # |Φ+⟩ = (|00⟩ + |11⟩)/√2 → should give 00
        qubit1 = LogicalQubit("q0", self.profile, seed=42)
        qubit2 = LogicalQubit("q1", self.profile, seed=42)
        qubit1.apply_gate("H", 0.0)
        from kernel.simulator.logical_qubit import TwoQubitGate
        TwoQubitGate.apply_cnot(qubit1, qubit2, 0.0)
        
        o1, o2, idx = LogicalQubit.measure_bell_basis(qubit1, qubit2, 0.0)
        self.assertEqual(idx, 0, "|Φ+⟩ should give index 0")


if __name__ == '__main__':
    unittest.main()
