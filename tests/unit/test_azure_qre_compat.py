"""
Unit tests for Azure QRE compatibility layer
"""

import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.azure_qre_compat import (
    AzureQubitParams,
    AzureQECScheme,
    parse_time_string,
    create_qre_config,
    compute_logical_qubit_resources,
    AZURE_QUBIT_PARAMS,
    AZURE_QEC_SCHEMES,
)


class TestAzureQubitParams(unittest.TestCase):
    """Test Azure qubit parameters."""
    
    def test_gate_based_params(self):
        """Test gate-based qubit parameters."""
        params = AzureQubitParams(
            name="test_gate",
            instruction_set="GateBased",
            one_qubit_gate_time="50 ns",
            two_qubit_gate_time="100 ns",
            one_qubit_gate_error_rate=1e-3,
        )
        
        self.assertEqual(params.instruction_set, "GateBased")
        self.assertEqual(params.one_qubit_gate_time, "50 ns")
    
    def test_majorana_params(self):
        """Test Majorana qubit parameters."""
        params = AzureQubitParams(
            name="test_maj",
            instruction_set="Majorana",
            two_qubit_joint_measurement_time="100 ns",
            two_qubit_joint_measurement_error_rate=1e-4,
        )
        
        self.assertEqual(params.instruction_set, "Majorana")
        self.assertIsNotNone(params.two_qubit_joint_measurement_time)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = AZURE_QUBIT_PARAMS["qubit_gate_ns_e4"]
        params_dict = params.to_dict()
        
        self.assertEqual(params_dict["name"], "qubit_gate_ns_e4")
        self.assertEqual(params_dict["instructionSet"], "GateBased")
        self.assertIn("oneQubitGateTime", params_dict)


class TestAzureQECScheme(unittest.TestCase):
    """Test Azure QEC scheme."""
    
    def test_qec_scheme_creation(self):
        """Test creating QEC scheme."""
        scheme = AzureQECScheme(
            name="surface_code",
            error_correction_threshold=0.01,
            crossing_prefactor=0.03,
        )
        
        self.assertEqual(scheme.name, "surface_code")
        self.assertEqual(scheme.error_correction_threshold, 0.01)
    
    def test_formula_evaluation_simple(self):
        """Test simple formula evaluation."""
        scheme = AzureQECScheme()
        context = {"codeDistance": 9}
        
        result = scheme.evaluate_formula("2 * codeDistance", context)
        self.assertEqual(result, 18)
    
    def test_formula_evaluation_complex(self):
        """Test complex formula evaluation."""
        scheme = AzureQECScheme()
        context = {
            "codeDistance": 9,
            "twoQubitGateTime": 0.05,  # 50 ns in µs
            "oneQubitMeasurementTime": 0.1,  # 100 ns in µs
        }
        
        formula = "(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * codeDistance"
        result = scheme.evaluate_formula(formula, context)
        
        expected = (4 * 0.05 + 2 * 0.1) * 9
        self.assertAlmostEqual(result, expected, places=5)
    
    def test_formula_with_power(self):
        """Test formula with exponentiation."""
        scheme = AzureQECScheme()
        context = {"codeDistance": 5}
        
        result = scheme.evaluate_formula("2 * codeDistance * codeDistance", context)
        self.assertEqual(result, 50)


class TestTimeStringParsing(unittest.TestCase):
    """Test time string parsing."""
    
    def test_parse_nanoseconds(self):
        """Test parsing nanoseconds."""
        self.assertAlmostEqual(parse_time_string("100 ns"), 0.1, places=5)
        self.assertAlmostEqual(parse_time_string("50 ns"), 0.05, places=5)
    
    def test_parse_microseconds(self):
        """Test parsing microseconds."""
        self.assertAlmostEqual(parse_time_string("100 µs"), 100.0, places=5)
        self.assertAlmostEqual(parse_time_string("100 us"), 100.0, places=5)
    
    def test_parse_milliseconds(self):
        """Test parsing milliseconds."""
        self.assertAlmostEqual(parse_time_string("1 ms"), 1000.0, places=5)
    
    def test_parse_seconds(self):
        """Test parsing seconds."""
        self.assertAlmostEqual(parse_time_string("1 s"), 1e6, places=5)
    
    def test_parse_invalid_unit(self):
        """Test parsing invalid unit raises error."""
        with self.assertRaises(ValueError):
            parse_time_string("100 invalid")


class TestPredefinedConfigs(unittest.TestCase):
    """Test predefined Azure QRE configurations."""
    
    def test_all_qubit_params_exist(self):
        """Test all predefined qubit params are available."""
        expected_params = [
            "qubit_gate_ns_e3", "qubit_gate_ns_e4",
            "qubit_gate_us_e3", "qubit_gate_us_e4",
            "qubit_maj_ns_e4", "qubit_maj_ns_e6",
        ]
        
        for name in expected_params:
            self.assertIn(name, AZURE_QUBIT_PARAMS)
            params = AZURE_QUBIT_PARAMS[name]
            self.assertEqual(params.name, name)
    
    def test_all_qec_schemes_exist(self):
        """Test all predefined QEC schemes are available."""
        expected_schemes = [
            "surface_code_gate_based",
            "surface_code_majorana",
            "floquet_code",
        ]
        
        for name in expected_schemes:
            self.assertIn(name, AZURE_QEC_SCHEMES)
            scheme = AZURE_QEC_SCHEMES[name]
            self.assertIsNotNone(scheme.name)


class TestCreateQREConfig(unittest.TestCase):
    """Test QRE config creation."""
    
    def test_create_basic_config(self):
        """Test creating basic QRE config."""
        config = create_qre_config(
            qubit_params="qubit_gate_ns_e4",
            qec_scheme="surface_code",
            code_distance=9
        )
        
        self.assertIn("qubitParams", config)
        self.assertIn("qecScheme", config)
        self.assertIn("codeDistance", config)
        self.assertEqual(config["codeDistance"], 9)
    
    def test_create_config_with_custom_params(self):
        """Test creating config with custom parameters."""
        custom = {
            "qecScheme": {
                "crossingPrefactor": 0.05
            }
        }
        
        config = create_qre_config(
            qubit_params="qubit_gate_ns_e3",
            qec_scheme="surface_code",
            code_distance=7,
            custom_params=custom
        )
        
        self.assertEqual(config["qecScheme"]["crossingPrefactor"], 0.05)
    
    def test_create_floquet_config(self):
        """Test creating Floquet code config."""
        config = create_qre_config(
            qubit_params="qubit_maj_ns_e6",
            qec_scheme="floquet_code",
            code_distance=9
        )
        
        self.assertEqual(config["qecScheme"]["name"], "floquet_code")


class TestComputeResources(unittest.TestCase):
    """Test resource computation."""
    
    def test_compute_surface_code_resources(self):
        """Test computing surface code resources."""
        config = create_qre_config(
            qubit_params="qubit_gate_ns_e4",
            qec_scheme="surface_code",
            code_distance=9
        )
        
        resources = compute_logical_qubit_resources(config)
        
        self.assertEqual(resources["code_distance"], 9)
        self.assertEqual(resources["physical_qubits_per_logical"], 162)  # 2 * 9^2
        self.assertGreater(resources["logical_cycle_time_us"], 0)
    
    def test_compute_floquet_code_resources(self):
        """Test computing Floquet code resources."""
        config = create_qre_config(
            qubit_params="qubit_maj_ns_e6",
            qec_scheme="floquet_code",
            code_distance=9
        )
        
        resources = compute_logical_qubit_resources(config)
        
        # Floquet: 4*d^2 + 8*(d-1)
        expected_qubits = 4 * 81 + 8 * 8
        self.assertEqual(resources["physical_qubits_per_logical"], expected_qubits)
    
    def test_resource_scaling(self):
        """Test resource scaling with distance."""
        distances = [5, 7, 9, 11, 13]
        
        for d in distances:
            config = create_qre_config(
                qubit_params="qubit_gate_ns_e4",
                qec_scheme="surface_code",
                code_distance=d
            )
            
            resources = compute_logical_qubit_resources(config)
            
            # Surface code: 2 * d^2
            expected_qubits = 2 * d * d
            self.assertEqual(resources["physical_qubits_per_logical"], expected_qubits)
            
            # Cycle time should scale with distance
            self.assertGreater(resources["logical_cycle_time_us"], 0)


if __name__ == "__main__":
    unittest.main()
