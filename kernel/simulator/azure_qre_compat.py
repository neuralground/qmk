"""
Azure Quantum Resource Estimator (QRE) Compatibility Layer

Provides full compatibility with Azure QRE configuration format and semantics.
Supports both predefined and custom QEC schemes with formula-based parameters.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class AzureQubitParams:
    """
    Azure QRE qubit parameters.
    
    Matches Azure QRE schema exactly for compatibility.
    """
    name: str
    instruction_set: str  # "GateBased" or "Majorana"
    
    # Gate-based parameters
    one_qubit_measurement_time: Optional[str] = None  # e.g., "100 ns"
    one_qubit_gate_time: Optional[str] = None
    two_qubit_gate_time: Optional[str] = None
    t_gate_time: Optional[str] = None
    
    # Majorana parameters
    two_qubit_joint_measurement_time: Optional[str] = None
    
    # Error rates
    one_qubit_measurement_error_rate: float = 1e-3
    one_qubit_gate_error_rate: Optional[float] = None
    two_qubit_gate_error_rate: Optional[float] = None
    two_qubit_joint_measurement_error_rate: Optional[float] = None
    t_gate_error_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Azure QRE JSON format."""
        result = {
            "name": self.name,
            "instructionSet": self.instruction_set,
            "oneQubitMeasurementTime": self.one_qubit_measurement_time,
            "oneQubitMeasurementErrorRate": self.one_qubit_measurement_error_rate,
        }
        
        if self.instruction_set == "GateBased":
            result.update({
                "oneQubitGateTime": self.one_qubit_gate_time,
                "twoQubitGateTime": self.two_qubit_gate_time,
                "tGateTime": self.t_gate_time,
                "oneQubitGateErrorRate": self.one_qubit_gate_error_rate,
                "twoQubitGateErrorRate": self.two_qubit_gate_error_rate,
                "tGateErrorRate": self.t_gate_error_rate,
            })
        elif self.instruction_set == "Majorana":
            result.update({
                "twoQubitJointMeasurementTime": self.two_qubit_joint_measurement_time,
                "tGateTime": self.t_gate_time,
                "twoQubitJointMeasurementErrorRate": self.two_qubit_joint_measurement_error_rate,
                "tGateErrorRate": self.t_gate_error_rate,
            })
        
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class AzureQECScheme:
    """
    Azure QRE quantum error correction scheme.
    
    Supports both predefined schemes (surface_code, floquet_code) and custom schemes.
    """
    name: Optional[str] = None  # "surface_code" or "floquet_code"
    error_correction_threshold: float = 0.01
    crossing_prefactor: float = 0.03
    distance_coefficient_power: int = 0
    logical_cycle_time: str = "oneQubitMeasurementTime"  # Formula string
    physical_qubits_per_logical_qubit: str = "2 * codeDistance * codeDistance"  # Formula string
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Azure QRE JSON format."""
        result = {
            "errorCorrectionThreshold": self.error_correction_threshold,
            "crossingPrefactor": self.crossing_prefactor,
            "distanceCoefficientPower": self.distance_coefficient_power,
            "logicalCycleTime": self.logical_cycle_time,
            "physicalQubitsPerLogicalQubit": self.physical_qubits_per_logical_qubit,
        }
        
        if self.name:
            result["name"] = self.name
        
        return result
    
    def evaluate_formula(self, formula: str, context: Dict[str, Any]) -> float:
        """
        Evaluate a formula string with given context.
        
        Supports Azure QRE formula syntax with variables:
        - oneQubitGateTime, twoQubitGateTime, oneQubitMeasurementTime, etc.
        - codeDistance (eccDistance in Azure docs)
        
        Args:
            formula: Formula string (e.g., "(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * codeDistance")
            context: Dictionary of variable values
        
        Returns:
            Evaluated result
        """
        # Convert camelCase to snake_case for Python variable names
        formula_normalized = formula
        for key in context:
            # Replace camelCase with actual values
            camel_key = self._to_camel_case(key)
            if camel_key in formula_normalized:
                formula_normalized = formula_normalized.replace(camel_key, str(context[key]))
        
        # Also support direct snake_case
        for key, value in context.items():
            formula_normalized = formula_normalized.replace(key, str(value))
        
        # Evaluate the formula
        try:
            result = eval(formula_normalized, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate formula '{formula}': {e}")
    
    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])


# Predefined Azure QRE qubit parameters
AZURE_QUBIT_PARAMS = {
    "qubit_gate_ns_e3": AzureQubitParams(
        name="qubit_gate_ns_e3",
        instruction_set="GateBased",
        one_qubit_measurement_time="100 ns",
        one_qubit_gate_time="50 ns",
        two_qubit_gate_time="50 ns",
        t_gate_time="50 ns",
        one_qubit_measurement_error_rate=1e-3,
        one_qubit_gate_error_rate=1e-3,
        two_qubit_gate_error_rate=1e-3,
        t_gate_error_rate=1e-3,
    ),
    "qubit_gate_ns_e4": AzureQubitParams(
        name="qubit_gate_ns_e4",
        instruction_set="GateBased",
        one_qubit_measurement_time="100 ns",
        one_qubit_gate_time="50 ns",
        two_qubit_gate_time="50 ns",
        t_gate_time="50 ns",
        one_qubit_measurement_error_rate=1e-4,
        one_qubit_gate_error_rate=1e-4,
        two_qubit_gate_error_rate=1e-4,
        t_gate_error_rate=1e-4,
    ),
    "qubit_gate_us_e3": AzureQubitParams(
        name="qubit_gate_us_e3",
        instruction_set="GateBased",
        one_qubit_measurement_time="100 µs",
        one_qubit_gate_time="100 µs",
        two_qubit_gate_time="100 µs",
        t_gate_time="100 µs",
        one_qubit_measurement_error_rate=1e-3,
        one_qubit_gate_error_rate=1e-3,
        two_qubit_gate_error_rate=1e-3,
        t_gate_error_rate=1e-6,
    ),
    "qubit_gate_us_e4": AzureQubitParams(
        name="qubit_gate_us_e4",
        instruction_set="GateBased",
        one_qubit_measurement_time="100 µs",
        one_qubit_gate_time="100 µs",
        two_qubit_gate_time="100 µs",
        t_gate_time="100 µs",
        one_qubit_measurement_error_rate=1e-4,
        one_qubit_gate_error_rate=1e-4,
        two_qubit_gate_error_rate=1e-4,
        t_gate_error_rate=1e-6,
    ),
    "qubit_maj_ns_e4": AzureQubitParams(
        name="qubit_maj_ns_e4",
        instruction_set="Majorana",
        one_qubit_measurement_time="100 ns",
        two_qubit_joint_measurement_time="100 ns",
        t_gate_time="100 ns",
        one_qubit_measurement_error_rate=1e-4,
        two_qubit_joint_measurement_error_rate=1e-4,
        t_gate_error_rate=0.05,
    ),
    "qubit_maj_ns_e6": AzureQubitParams(
        name="qubit_maj_ns_e6",
        instruction_set="Majorana",
        one_qubit_measurement_time="100 ns",
        two_qubit_joint_measurement_time="100 ns",
        t_gate_time="100 ns",
        one_qubit_measurement_error_rate=1e-6,
        two_qubit_joint_measurement_error_rate=1e-6,
        t_gate_error_rate=0.01,
    ),
}


# Predefined Azure QRE QEC schemes
AZURE_QEC_SCHEMES = {
    "surface_code_gate_based": AzureQECScheme(
        name="surface_code",
        error_correction_threshold=0.01,
        crossing_prefactor=0.03,
        distance_coefficient_power=0,
        logical_cycle_time="(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * codeDistance",
        physical_qubits_per_logical_qubit="2 * codeDistance * codeDistance",
    ),
    "surface_code_majorana": AzureQECScheme(
        name="surface_code",
        error_correction_threshold=0.0015,
        crossing_prefactor=0.08,
        distance_coefficient_power=0,
        logical_cycle_time="20 * oneQubitMeasurementTime * codeDistance",
        physical_qubits_per_logical_qubit="2 * codeDistance * codeDistance",
    ),
    "floquet_code": AzureQECScheme(
        name="floquet_code",
        error_correction_threshold=0.01,
        crossing_prefactor=0.07,
        distance_coefficient_power=0,
        logical_cycle_time="3 * oneQubitMeasurementTime * codeDistance",
        physical_qubits_per_logical_qubit="4 * codeDistance * codeDistance + 8 * (codeDistance - 1)",
    ),
}


def parse_time_string(time_str: str) -> float:
    """
    Parse Azure QRE time string to microseconds.
    
    Args:
        time_str: Time string (e.g., "100 ns", "50 µs", "1 ms")
    
    Returns:
        Time in microseconds
    """
    time_str = time_str.strip()
    
    # Extract number and unit
    match = re.match(r'([\d.]+)\s*(\w+)', time_str)
    if not match:
        raise ValueError(f"Invalid time string: {time_str}")
    
    value = float(match.group(1))
    unit = match.group(2).lower()
    
    # Convert to microseconds
    conversions = {
        'ns': 1e-3,
        'us': 1.0,
        'µs': 1.0,
        'ms': 1e3,
        's': 1e6,
    }
    
    if unit not in conversions:
        raise ValueError(f"Unknown time unit: {unit}")
    
    return value * conversions[unit]


def create_qre_config(qubit_params: str = "qubit_gate_ns_e3",
                      qec_scheme: str = "surface_code",
                      code_distance: int = 9,
                      custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a complete Azure QRE-compatible configuration.
    
    Args:
        qubit_params: Predefined qubit parameter name
        qec_scheme: QEC scheme name ("surface_code" or "floquet_code")
        code_distance: Code distance
        custom_params: Optional custom parameter overrides
    
    Returns:
        Complete Azure QRE configuration dictionary
    """
    # Get predefined parameters
    if qubit_params not in AZURE_QUBIT_PARAMS:
        raise ValueError(f"Unknown qubit params: {qubit_params}")
    
    qubits = AZURE_QUBIT_PARAMS[qubit_params]
    
    # Select QEC scheme based on instruction set
    if qec_scheme == "surface_code":
        if qubits.instruction_set == "GateBased":
            qec = AZURE_QEC_SCHEMES["surface_code_gate_based"]
        else:
            qec = AZURE_QEC_SCHEMES["surface_code_majorana"]
    elif qec_scheme == "floquet_code":
        qec = AZURE_QEC_SCHEMES["floquet_code"]
    else:
        raise ValueError(f"Unknown QEC scheme: {qec_scheme}")
    
    # Build configuration
    config = {
        "qubitParams": qubits.to_dict(),
        "qecScheme": qec.to_dict(),
        "codeDistance": code_distance,
    }
    
    # Apply custom overrides
    if custom_params:
        if "qubitParams" in custom_params:
            config["qubitParams"].update(custom_params["qubitParams"])
        if "qecScheme" in custom_params:
            config["qecScheme"].update(custom_params["qecScheme"])
        if "codeDistance" in custom_params:
            config["codeDistance"] = custom_params["codeDistance"]
    
    return config


def compute_logical_qubit_resources(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute logical qubit resources from Azure QRE configuration.
    
    Args:
        config: Azure QRE configuration
    
    Returns:
        Dictionary with computed resources
    """
    qubits = config["qubitParams"]
    qec = config["qecScheme"]
    code_distance = config.get("codeDistance", 9)
    
    # Parse time values
    context = {
        "code_distance": code_distance,
        "codeDistance": code_distance,  # Azure uses this name
    }
    
    # Add time parameters
    if "oneQubitMeasurementTime" in qubits:
        context["one_qubit_measurement_time"] = parse_time_string(qubits["oneQubitMeasurementTime"])
        context["oneQubitMeasurementTime"] = context["one_qubit_measurement_time"]
    
    if "oneQubitGateTime" in qubits:
        context["one_qubit_gate_time"] = parse_time_string(qubits["oneQubitGateTime"])
        context["oneQubitGateTime"] = context["one_qubit_gate_time"]
    
    if "twoQubitGateTime" in qubits:
        context["two_qubit_gate_time"] = parse_time_string(qubits["twoQubitGateTime"])
        context["twoQubitGateTime"] = context["two_qubit_gate_time"]
    
    if "twoQubitJointMeasurementTime" in qubits:
        context["two_qubit_joint_measurement_time"] = parse_time_string(qubits["twoQubitJointMeasurementTime"])
        context["twoQubitJointMeasurementTime"] = context["two_qubit_joint_measurement_time"]
    
    # Create QEC scheme object for formula evaluation
    qec_obj = AzureQECScheme(
        name=qec.get("name"),
        error_correction_threshold=qec.get("errorCorrectionThreshold", 0.01),
        crossing_prefactor=qec.get("crossingPrefactor", 0.03),
        distance_coefficient_power=qec.get("distanceCoefficientPower", 0),
        logical_cycle_time=qec.get("logicalCycleTime", "oneQubitMeasurementTime"),
        physical_qubits_per_logical_qubit=qec.get("physicalQubitsPerLogicalQubit", "2 * codeDistance * codeDistance")
    )
    
    logical_cycle_time_us = qec_obj.evaluate_formula(qec["logicalCycleTime"], context)
    physical_qubits = int(qec_obj.evaluate_formula(qec["physicalQubitsPerLogicalQubit"], context))
    
    return {
        "code_distance": code_distance,
        "logical_cycle_time_us": logical_cycle_time_us,
        "physical_qubits_per_logical": physical_qubits,
        "error_correction_threshold": qec.get("errorCorrectionThreshold", 0.01),
        "crossing_prefactor": qec.get("crossingPrefactor", 0.03),
    }
