#!/usr/bin/env python3
"""
Azure Quantum Resource Estimator (QRE) Compatibility Example

Demonstrates how QMK uses Azure QRE configuration format for logical qubit simulation.
Shows both predefined and custom QEC schemes with formula-based parameters.
"""

import json
import sys
import os

# Add parent directory to path
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from kernel.simulator.qec_profiles import QECProfile
from kernel.simulator.azure_qre_compat import (
    create_qre_config,
    compute_logical_qubit_resources,
    AZURE_QUBIT_PARAMS,
    AZURE_QEC_SCHEMES,
)
from kernel.simulator.logical_qubit import LogicalQubit


def example_1_predefined_azure_qre():
    """Example 1: Using predefined Azure QRE configurations."""
    print("=" * 80)
    print("Example 1: Predefined Azure QRE Configurations")
    print("=" * 80)
    
    # Create profile using Azure QRE predefined parameters
    profile = QECProfile.from_azure_qre(
        qubit_params="qubit_gate_ns_e4",  # Gate-based, 100ns gates, 1e-4 error
        qec_scheme="surface_code",
        code_distance=9
    )
    
    print(f"\nProfile: {profile.code_family}")
    print(f"  Code distance: {profile.code_distance}")
    print(f"  Physical qubits per logical: {profile.physical_qubit_count}")
    print(f"  Logical cycle time: {profile.logical_cycle_time_us:.2f} µs")
    print(f"  Gate error rate: {profile.physical_gate_error_rate}")
    print(f"  Logical error rate: {profile.logical_error_rate():.2e}")
    
    # Create a logical qubit with this profile
    qubit = LogicalQubit("q0", profile, seed=42)
    
    # Run some operations
    qubit.apply_gate("H", time_us=0.0)
    qubit.apply_gate("S", time_us=1.0)
    outcome = qubit.measure("Z", time_us=2.0)
    
    print(f"\nMeasurement outcome: {outcome}")
    
    # Get telemetry
    telemetry = qubit.get_telemetry()
    print(f"\nTelemetry:")
    print(f"  Gates executed: {telemetry['gate_count']}")
    print(f"  Decoder cycles: {telemetry['decoder_cycles']}")
    print(f"  Total errors: {telemetry['error_breakdown']['total']}")


def example_2_all_predefined_configs():
    """Example 2: Compare all predefined Azure QRE configurations."""
    print("\n" + "=" * 80)
    print("Example 2: All Predefined Azure QRE Configurations")
    print("=" * 80)
    
    configs = [
        ("qubit_gate_ns_e3", "surface_code", 9),
        ("qubit_gate_ns_e4", "surface_code", 9),
        ("qubit_gate_us_e3", "surface_code", 9),
        ("qubit_gate_us_e4", "surface_code", 9),
        ("qubit_maj_ns_e4", "surface_code", 9),
        ("qubit_maj_ns_e6", "floquet_code", 9),
    ]
    
    print(f"\n{'Config':<25} {'Phys Qubits':<12} {'Cycle (µs)':<12} {'Log Error':<12}")
    print("-" * 80)
    
    for qubit_params, qec_scheme, distance in configs:
        try:
            profile = QECProfile.from_azure_qre(qubit_params, qec_scheme, distance)
            print(f"{qubit_params:<25} {profile.physical_qubit_count:<12} "
                  f"{profile.logical_cycle_time_us:<12.2f} {profile.logical_error_rate():<12.2e}")
        except Exception as e:
            print(f"{qubit_params:<25} Error: {e}")


def example_3_custom_qec_scheme():
    """Example 3: Custom QEC scheme with Azure QRE formula syntax."""
    print("\n" + "=" * 80)
    print("Example 3: Custom QEC Scheme")
    print("=" * 80)
    
    # Create custom QEC scheme using Azure QRE formula syntax
    custom_params = {
        "qecScheme": {
            "name": "custom_code",
            "errorCorrectionThreshold": 0.015,  # Higher threshold
            "crossingPrefactor": 0.05,
            "logicalCycleTime": "(6 * twoQubitGateTime + 3 * oneQubitMeasurementTime) * codeDistance",
            "physicalQubitsPerLogicalQubit": "3 * codeDistance * codeDistance",
        }
    }
    
    profile = QECProfile.from_azure_qre(
        qubit_params="qubit_gate_ns_e3",
        qec_scheme="surface_code",  # Base scheme
        code_distance=7,
        custom_params=custom_params
    )
    
    print(f"\nCustom QEC Scheme:")
    print(f"  Physical qubits: {profile.physical_qubit_count}")
    print(f"  Logical cycle time: {profile.logical_cycle_time_us:.2f} µs")
    print(f"  Error threshold: 0.015")


def example_4_raw_azure_qre_config():
    """Example 4: Using raw Azure QRE configuration format."""
    print("\n" + "=" * 80)
    print("Example 4: Raw Azure QRE Configuration")
    print("=" * 80)
    
    # Create Azure QRE config directly
    qre_config = create_qre_config(
        qubit_params="qubit_gate_ns_e4",
        qec_scheme="surface_code",
        code_distance=13
    )
    
    print("\nAzure QRE Configuration:")
    print(json.dumps(qre_config, indent=2))
    
    # Compute resources
    resources = compute_logical_qubit_resources(qre_config)
    
    print("\nComputed Resources:")
    print(json.dumps(resources, indent=2))


def example_5_distance_scaling():
    """Example 5: Code distance scaling analysis."""
    print("\n" + "=" * 80)
    print("Example 5: Code Distance Scaling")
    print("=" * 80)
    
    distances = [5, 7, 9, 11, 13, 15]
    
    print(f"\n{'Distance':<10} {'Phys Qubits':<15} {'Cycle (µs)':<15} {'Log Error':<15}")
    print("-" * 80)
    
    for d in distances:
        profile = QECProfile.from_azure_qre(
            qubit_params="qubit_gate_ns_e4",
            qec_scheme="surface_code",
            code_distance=d
        )
        print(f"{d:<10} {profile.physical_qubit_count:<15} "
              f"{profile.logical_cycle_time_us:<15.2f} {profile.logical_error_rate():<15.2e}")


def example_6_qvm_integration():
    """Example 6: Integration with QVM graph execution."""
    print("\n" + "=" * 80)
    print("Example 6: QVM Graph Integration")
    print("=" * 80)
    
    # Parse profile from QVM graph string (as used in examples)
    from kernel.simulator.qec_profiles import parse_profile_string
    
    profile_strings = [
        "logical:surface_code(d=9)",
        "logical:SHYPS(d=7)",
        "logical:bacon_shor(d=5)",
    ]
    
    print("\nQVM Profile Strings:")
    for profile_str in profile_strings:
        profile = parse_profile_string(profile_str)
        print(f"\n  {profile_str}")
        print(f"    → {profile.code_family}, d={profile.code_distance}")
        print(f"    → {profile.physical_qubit_count} physical qubits")
        print(f"    → {profile.logical_cycle_time_us:.2f} µs cycle time")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("QMK Azure Quantum Resource Estimator (QRE) Compatibility Examples")
    print("=" * 80)
    
    example_1_predefined_azure_qre()
    example_2_all_predefined_configs()
    example_3_custom_qec_scheme()
    example_4_raw_azure_qre_config()
    example_5_distance_scaling()
    example_6_qvm_integration()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
