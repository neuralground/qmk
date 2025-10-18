"""
Unit tests for QEC profiles
"""

import unittest
import sys
import os

# Add parent directory to path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.qec_profiles import (
    QECProfile,
    surface_code,
    shyps_code,
    bacon_shor_code,
    parse_profile_string,
    get_profile,
)


class TestQECProfile(unittest.TestCase):
    """Test QECProfile class."""
    
    def test_profile_creation(self):
        """Test creating a QEC profile."""
        profile = QECProfile(
            code_family="surface_code",
            code_distance=9,
            physical_qubit_count=162,
            logical_cycle_time_us=1.0,
            physical_gate_error_rate=1e-3,
            measurement_error_rate=1e-2,
            idle_error_rate=1e-4,
            t1_us=100.0,
            t2_us=80.0,
        )
        
        self.assertEqual(profile.code_family, "surface_code")
        self.assertEqual(profile.code_distance, 9)
        self.assertEqual(profile.physical_qubit_count, 162)
        self.assertEqual(profile.logical_cycle_time_us, 1.0)
    
    def test_logical_error_rate(self):
        """Test logical error rate calculation."""
        profile = surface_code(distance=9, gate_error=1e-3)
        error_rate = profile.logical_error_rate()
        
        # Should be significantly suppressed below physical error rate
        self.assertLess(error_rate, 1e-3)
        self.assertGreater(error_rate, 0)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        profile = surface_code(distance=7)
        profile_dict = profile.to_dict()
        
        self.assertIn("qec_scheme", profile_dict)
        self.assertIn("error_budget", profile_dict)
        self.assertEqual(profile_dict["qec_scheme"]["code_distance"], 7)


class TestSurfaceCode(unittest.TestCase):
    """Test surface code profile generation."""
    
    def test_default_surface_code(self):
        """Test default surface code parameters."""
        profile = surface_code()
        
        self.assertEqual(profile.code_family, "surface_code")
        self.assertEqual(profile.code_distance, 9)
        self.assertEqual(profile.physical_qubit_count, 162)  # 2 * 9^2
    
    def test_surface_code_scaling(self):
        """Test surface code scales correctly with distance."""
        distances = [5, 7, 9, 11]
        
        for d in distances:
            profile = surface_code(distance=d)
            expected_qubits = 2 * d * d
            
            self.assertEqual(profile.code_distance, d)
            self.assertEqual(profile.physical_qubit_count, expected_qubits)
            self.assertGreater(profile.logical_cycle_time_us, 0)
    
    def test_surface_code_error_rates(self):
        """Test surface code with different error rates."""
        gate_errors = [1e-3, 1e-4, 1e-5]
        
        for err in gate_errors:
            profile = surface_code(distance=9, gate_error=err)
            
            self.assertEqual(profile.physical_gate_error_rate, err)
            self.assertEqual(profile.measurement_error_rate, err * 10)
            self.assertEqual(profile.idle_error_rate, err / 10)


class TestSHYPSCode(unittest.TestCase):
    """Test SHYPS code profile generation."""
    
    def test_shyps_code(self):
        """Test SHYPS code parameters."""
        profile = shyps_code(distance=9)
        
        self.assertEqual(profile.code_family, "SHYPS")
        self.assertEqual(profile.code_distance, 9)
        # SHYPS uses ~1.5 * d^2 qubits
        self.assertEqual(profile.physical_qubit_count, int(1.5 * 81))
    
    def test_shyps_vs_surface(self):
        """Test SHYPS uses fewer qubits than surface code."""
        d = 9
        shyps = shyps_code(distance=d)
        surface = surface_code(distance=d)
        
        # SHYPS should use fewer physical qubits
        self.assertLess(shyps.physical_qubit_count, surface.physical_qubit_count)


class TestBaconShorCode(unittest.TestCase):
    """Test Bacon-Shor code profile generation."""
    
    def test_bacon_shor_code(self):
        """Test Bacon-Shor code parameters."""
        profile = bacon_shor_code(distance=9)
        
        self.assertEqual(profile.code_family, "bacon_shor")
        self.assertEqual(profile.code_distance, 9)
        self.assertEqual(profile.physical_qubit_count, 81)  # d^2
    
    def test_bacon_shor_cycle_time(self):
        """Test Bacon-Shor has faster cycles than surface code."""
        d = 9
        bacon = bacon_shor_code(distance=d)
        surface = surface_code(distance=d)
        
        # Bacon-Shor should have faster syndrome extraction
        self.assertLess(bacon.logical_cycle_time_us, surface.logical_cycle_time_us)


class TestProfileParsing(unittest.TestCase):
    """Test profile string parsing."""
    
    def test_parse_surface_code(self):
        """Test parsing surface code string."""
        profile = parse_profile_string("logical:surface_code(d=9)")
        
        self.assertEqual(profile.code_family, "surface_code")
        self.assertEqual(profile.code_distance, 9)
    
    def test_parse_shyps(self):
        """Test parsing SHYPS string."""
        profile = parse_profile_string("logical:SHYPS(d=7)")
        
        self.assertEqual(profile.code_family, "SHYPS")
        self.assertEqual(profile.code_distance, 7)
    
    def test_parse_bacon_shor(self):
        """Test parsing Bacon-Shor string."""
        profile = parse_profile_string("logical:bacon_shor(d=5)")
        
        self.assertEqual(profile.code_family, "bacon_shor")
        self.assertEqual(profile.code_distance, 5)
    
    def test_parse_invalid_format(self):
        """Test parsing invalid format raises error."""
        with self.assertRaises(ValueError):
            parse_profile_string("invalid_format")
        
        with self.assertRaises(ValueError):
            parse_profile_string("logical:unknown_code(d=9)")


class TestStandardProfiles(unittest.TestCase):
    """Test standard profile library."""
    
    def test_get_standard_profile(self):
        """Test getting standard profiles."""
        profile = get_profile("surface_d9")
        
        self.assertEqual(profile.code_family, "surface_code")
        self.assertEqual(profile.code_distance, 9)
    
    def test_all_standard_profiles(self):
        """Test all standard profiles are accessible."""
        standard_names = [
            "surface_d5", "surface_d7", "surface_d9", "surface_d13",
            "shyps_d5", "shyps_d7", "shyps_d9",
            "bacon_shor_d5", "bacon_shor_d7",
        ]
        
        for name in standard_names:
            profile = get_profile(name)
            self.assertIsNotNone(profile)
            self.assertGreater(profile.code_distance, 0)


if __name__ == "__main__":
    unittest.main()
