"""
QEC Code Profiles for Logical Qubit Simulation

Defines standard quantum error correction code configurations compatible
with Azure QRE parameter format. Each profile specifies:
- Physical qubit requirements
- Code distance
- Logical cycle time
- Error thresholds
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math

from .azure_qre_compat import (
    create_qre_config,
    compute_logical_qubit_resources,
    AZURE_QUBIT_PARAMS,
    AZURE_QEC_SCHEMES,
)


@dataclass
class QECProfile:
    """Quantum Error Correction code profile."""
    
    code_family: str
    code_distance: int
    physical_qubit_count: int
    logical_cycle_time_us: float
    
    # Error thresholds
    physical_gate_error_rate: float
    measurement_error_rate: float
    idle_error_rate: float
    
    # Coherence times
    t1_us: float
    t2_us: float
    
    # Decoder parameters
    decoder_type: str = "MWPM"  # Minimum Weight Perfect Matching
    decoder_cycle_time_us: float = 0.1
    
    def logical_error_rate(self) -> float:
        """
        Estimate logical error rate per logical cycle.
        
        Uses simplified threshold formula:
        P_L ≈ (p/p_th)^((d+1)/2) where p is physical error rate, p_th is threshold
        
        For surface codes, p_th ≈ 0.01 (1%)
        """
        p = self.physical_gate_error_rate
        p_th = 0.01  # Surface code threshold
        d = self.code_distance
        
        if p >= p_th:
            # Above threshold - code doesn't help
            return 1.0
        
        # Below threshold - exponential suppression
        return (p / p_th) ** ((d + 1) / 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Azure QRE-compatible dictionary format."""
        return {
            "qec_scheme": {
                "code_family": self.code_family,
                "code_distance": self.code_distance,
                "logical_cycle_time_us": self.logical_cycle_time_us,
                "physical_qubit_count": self.physical_qubit_count
            },
            "error_budget": {
                "physical_gate_error_rate": self.physical_gate_error_rate,
                "measurement_error_rate": self.measurement_error_rate,
                "idle_error_rate": self.idle_error_rate,
                "t1_us": self.t1_us,
                "t2_us": self.t2_us
            },
            "decoder": {
                "type": self.decoder_type,
                "cycle_time_us": self.decoder_cycle_time_us
            }
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'QECProfile':
        """Create profile from Azure QRE-compatible dictionary."""
        qec = config["qec_scheme"]
        err = config["error_budget"]
        dec = config.get("decoder", {})
        
        return cls(
            code_family=qec["code_family"],
            code_distance=qec["code_distance"],
            physical_qubit_count=qec["physical_qubit_count"],
            logical_cycle_time_us=qec["logical_cycle_time_us"],
            physical_gate_error_rate=err["physical_gate_error_rate"],
            measurement_error_rate=err["measurement_error_rate"],
            idle_error_rate=err["idle_error_rate"],
            t1_us=err["t1_us"],
            t2_us=err["t2_us"],
            decoder_type=dec.get("type", "MWPM"),
            decoder_cycle_time_us=dec.get("cycle_time_us", 0.1)
        )
    
    @classmethod
    def from_azure_qre(cls, qubit_params: str = "qubit_gate_ns_e3",
                       qec_scheme: str = "surface_code",
                       code_distance: int = 9,
                       custom_params: Optional[Dict[str, Any]] = None) -> 'QECProfile':
        """
        Create profile from Azure QRE configuration.
        
        Args:
            qubit_params: Azure QRE qubit parameter name
            qec_scheme: QEC scheme name ("surface_code" or "floquet_code")
            code_distance: Code distance
            custom_params: Optional custom parameter overrides
        
        Returns:
            QECProfile instance
        
        Example:
            >>> profile = QECProfile.from_azure_qre(
            ...     qubit_params="qubit_gate_ns_e4",
            ...     qec_scheme="surface_code",
            ...     code_distance=9
            ... )
        """
        # Create Azure QRE config
        qre_config = create_qre_config(qubit_params, qec_scheme, code_distance, custom_params)
        
        # Compute resources
        resources = compute_logical_qubit_resources(qre_config)
        
        # Extract error rates from qubit params
        qubits = qre_config["qubitParams"]
        
        # Get appropriate error rate based on instruction set
        if qubits.get("instructionSet") == "GateBased":
            gate_error = qubits.get("oneQubitGateErrorRate", 1e-3)
            measurement_error = qubits.get("oneQubitMeasurementErrorRate", 1e-3)
        else:  # Majorana
            gate_error = qubits.get("twoQubitJointMeasurementErrorRate", 1e-4)
            measurement_error = qubits.get("oneQubitMeasurementErrorRate", 1e-4)
        
        # Estimate idle error rate (typically 10x better than gate errors)
        idle_error = gate_error / 10
        
        # Use default coherence times (can be customized)
        t1_us = 100.0
        t2_us = 80.0
        
        return cls(
            code_family=qec_scheme,
            code_distance=resources["code_distance"],
            physical_qubit_count=resources["physical_qubits_per_logical"],
            logical_cycle_time_us=resources["logical_cycle_time_us"],
            physical_gate_error_rate=gate_error,
            measurement_error_rate=measurement_error,
            idle_error_rate=idle_error,
            t1_us=t1_us,
            t2_us=t2_us,
            decoder_type="MWPM",
            decoder_cycle_time_us=resources["logical_cycle_time_us"] / code_distance
        )


def surface_code(distance: int = 9, gate_error: float = 1e-3) -> QECProfile:
    """
    Standard surface code configuration.
    
    Physical qubits: d^2 data + (d^2 - 1) ancilla ≈ 2*d^2
    Logical cycle: ~d stabilizer rounds
    
    Args:
        distance: Code distance (odd integer, typically 5-21)
        gate_error: Physical gate error rate
    
    Returns:
        QECProfile for surface code
    """
    physical_qubits = 2 * distance * distance
    cycle_time_us = distance * 0.1  # ~100ns per stabilizer round
    
    return QECProfile(
        code_family="surface_code",
        code_distance=distance,
        physical_qubit_count=physical_qubits,
        logical_cycle_time_us=cycle_time_us,
        physical_gate_error_rate=gate_error,
        measurement_error_rate=gate_error * 10,  # Typically 10x worse
        idle_error_rate=gate_error / 10,  # Typically 10x better
        t1_us=100.0,
        t2_us=80.0,
        decoder_type="MWPM",
        decoder_cycle_time_us=0.1
    )


def shyps_code(distance: int = 9, gate_error: float = 1e-3) -> QECProfile:
    """
    SHYPS (Hastings-Haah) code configuration.
    
    More efficient than surface code for certain operations.
    Physical qubits: ~1.5*d^2 (better than surface code)
    
    Args:
        distance: Code distance
        gate_error: Physical gate error rate
    
    Returns:
        QECProfile for SHYPS code
    """
    physical_qubits = int(1.5 * distance * distance)
    cycle_time_us = distance * 0.12  # Slightly longer cycles
    
    return QECProfile(
        code_family="SHYPS",
        code_distance=distance,
        physical_qubit_count=physical_qubits,
        logical_cycle_time_us=cycle_time_us,
        physical_gate_error_rate=gate_error,
        measurement_error_rate=gate_error * 10,
        idle_error_rate=gate_error / 10,
        t1_us=100.0,
        t2_us=80.0,
        decoder_type="MWPM",
        decoder_cycle_time_us=0.12
    )


def bacon_shor_code(distance: int = 9, gate_error: float = 1e-3) -> QECProfile:
    """
    Bacon-Shor code configuration.
    
    Subsystem code with simpler syndrome extraction.
    Physical qubits: d^2
    
    Args:
        distance: Code distance
        gate_error: Physical gate error rate
    
    Returns:
        QECProfile for Bacon-Shor code
    """
    physical_qubits = distance * distance
    cycle_time_us = distance * 0.08  # Faster syndrome extraction
    
    return QECProfile(
        code_family="bacon_shor",
        code_distance=distance,
        physical_qubit_count=physical_qubits,
        logical_cycle_time_us=cycle_time_us,
        physical_gate_error_rate=gate_error,
        measurement_error_rate=gate_error * 10,
        idle_error_rate=gate_error / 10,
        t1_us=100.0,
        t2_us=80.0,
        decoder_type="gauge_fixing",
        decoder_cycle_time_us=0.08
    )


def qldpc_code(distance: int = 9, gate_error: float = 1e-3, rate: float = 0.1) -> QECProfile:
    """
    QLDPC (Quantum Low-Density Parity-Check) code configuration.
    
    More efficient encoding than surface codes with better rates.
    Physical qubits: ~d^2/rate (better scaling for high-rate codes)
    
    Args:
        distance: Code distance
        gate_error: Physical gate error rate
        rate: Code rate (k/n, typically 0.05-0.2 for good QLDPC codes)
    
    Returns:
        QECProfile for QLDPC code
    """
    # QLDPC codes have better qubit efficiency
    # Physical qubits ≈ d²/rate (vs 2d² for surface code)
    physical_qubits = int((distance * distance) / rate)
    
    # Longer cycle times due to more complex syndrome extraction
    cycle_time_us = distance * 0.15
    
    return QECProfile(
        code_family="QLDPC",
        code_distance=distance,
        physical_qubit_count=physical_qubits,
        logical_cycle_time_us=cycle_time_us,
        physical_gate_error_rate=gate_error,
        measurement_error_rate=gate_error * 10,
        idle_error_rate=gate_error / 10,
        t1_us=100.0,
        t2_us=80.0,
        decoder_type="BP",  # Belief Propagation
        decoder_cycle_time_us=0.15
    )


def parse_profile_string(profile_str: str) -> QECProfile:
    """
    Parse QEC profile from string format used in QVM graphs.
    
    Format: "logical:<code_family>(d=<distance>)"
    Examples:
        - "logical:surface_code(d=9)"
        - "logical:SHYPS(d=7)"
        - "logical:bacon_shor(d=5)"
    
    Args:
        profile_str: Profile string from QVM graph
    
    Returns:
        QECProfile instance
    
    Raises:
        ValueError: If profile string is malformed
    """
    if not profile_str.startswith("logical:"):
        raise ValueError(f"Profile must start with 'logical:': {profile_str}")
    
    # Remove "logical:" prefix
    spec = profile_str[8:]
    
    # Parse code family and distance
    if "(" not in spec or ")" not in spec:
        raise ValueError(f"Malformed profile spec: {spec}")
    
    code_family = spec[:spec.index("(")]
    params_str = spec[spec.index("(")+1:spec.index(")")]
    
    # Parse parameters
    params = {}
    for param in params_str.split(","):
        if "=" in param:
            key, value = param.strip().split("=")
            params[key.strip()] = int(value.strip())
    
    distance = params.get("d", 9)
    
    # Create profile based on code family
    code_family_lower = code_family.lower()
    
    if code_family_lower == "surface_code" or code_family_lower == "surface":
        return surface_code(distance)
    elif code_family_lower == "shyps":
        return shyps_code(distance)
    elif code_family_lower == "bacon_shor":
        return bacon_shor_code(distance)
    elif code_family_lower == "qldpc":
        # Extract rate if provided
        rate = params.get("rate", 0.1)
        return qldpc_code(distance, rate=rate)
    else:
        raise ValueError(f"Unknown code family: {code_family}")


# Standard profiles for quick access
STANDARD_PROFILES = {
    "surface_d5": surface_code(5),
    "surface_d7": surface_code(7),
    "surface_d9": surface_code(9),
    "surface_d13": surface_code(13),
    "shyps_d5": shyps_code(5),
    "shyps_d7": shyps_code(7),
    "shyps_d9": shyps_code(9),
    "bacon_shor_d5": bacon_shor_code(5),
    "bacon_shor_d7": bacon_shor_code(7),
    "qldpc_d9_r01": qldpc_code(9, rate=0.1),
    "qldpc_d9_r02": qldpc_code(9, rate=0.2),
    "qldpc_d13_r01": qldpc_code(13, rate=0.1),
}


def get_profile(name: str) -> QECProfile:
    """
    Get a standard QEC profile by name.
    
    Args:
        name: Profile name (e.g., "surface_d9", "shyps_d7")
    
    Returns:
        QECProfile instance
    
    Raises:
        KeyError: If profile name not found
    """
    return STANDARD_PROFILES[name]
