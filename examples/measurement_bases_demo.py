#!/usr/bin/env python3
"""
Measurement Bases Demonstration

Shows how to use all measurement bases in QMK:
- Z-basis (computational)
- X-basis (Hadamard)
- Y-basis
- Arbitrary angle
- Bell basis (two-qubit)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from kernel.simulator.logical_qubit import LogicalQubit, LogicalState
from kernel.simulator.qec_profiles import parse_profile_string


def demo_z_basis():
    """Demonstrate Z-basis measurement."""
    print("=" * 60)
    print("Z-Basis Measurement (Computational Basis)")
    print("=" * 60)
    
    profile = parse_profile_string("logical:Surface(d=7)")
    
    # Measure |0⟩
    qubit = LogicalQubit("q0", profile, seed=42)
    qubit.state = LogicalState.ZERO
    outcome = qubit.measure("Z", 0.0)
    print(f"Measuring |0⟩ in Z-basis: {outcome} (expected: 0)")
    
    # Measure |1⟩
    qubit = LogicalQubit("q1", profile, seed=42)
    qubit.state = LogicalState.ONE
    outcome = qubit.measure("Z", 0.0)
    print(f"Measuring |1⟩ in Z-basis: {outcome} (expected: 1)")
    
    # Measure |+⟩ (superposition)
    qubit = LogicalQubit("q2", profile, seed=42)
    qubit.apply_gate("H", 0.0)  # Create |+⟩
    outcome = qubit.measure("Z", 0.0)
    print(f"Measuring |+⟩ in Z-basis: {outcome} (random: 0 or 1)")
    print()


def demo_x_basis():
    """Demonstrate X-basis measurement."""
    print("=" * 60)
    print("X-Basis Measurement (Hadamard Basis)")
    print("=" * 60)
    
    profile = parse_profile_string("logical:Surface(d=7)")
    
    # Measure |+⟩
    qubit = LogicalQubit("q0", profile, seed=42)
    qubit.state = LogicalState.PLUS
    outcome = qubit.measure("X", 0.0)
    print(f"Measuring |+⟩ in X-basis: {outcome} (expected: 0)")
    
    # Measure |-⟩
    qubit = LogicalQubit("q1", profile, seed=42)
    qubit.state = LogicalState.MINUS
    outcome = qubit.measure("X", 0.0)
    print(f"Measuring |-⟩ in X-basis: {outcome} (expected: 1)")
    
    # Measure |0⟩ (computational basis)
    qubit = LogicalQubit("q2", profile, seed=42)
    qubit.state = LogicalState.ZERO
    outcome = qubit.measure("X", 0.0)
    print(f"Measuring |0⟩ in X-basis: {outcome} (random: 0 or 1)")
    print()


def demo_y_basis():
    """Demonstrate Y-basis measurement."""
    print("=" * 60)
    print("Y-Basis Measurement")
    print("=" * 60)
    
    profile = parse_profile_string("logical:Surface(d=7)")
    
    # Measure |+⟩ (approximates |+i⟩)
    qubit = LogicalQubit("q0", profile, seed=42)
    qubit.state = LogicalState.PLUS
    outcome = qubit.measure("Y", 0.0)
    print(f"Measuring |+⟩ in Y-basis: {outcome} (expected: 0)")
    
    # Measure |-⟩ (approximates |-i⟩)
    qubit = LogicalQubit("q1", profile, seed=42)
    qubit.state = LogicalState.MINUS
    outcome = qubit.measure("Y", 0.0)
    print(f"Measuring |-⟩ in Y-basis: {outcome} (expected: 1)")
    
    print("\nY-basis is useful for:")
    print("  - Y-error detection in QEC")
    print("  - Complete state tomography")
    print("  - Measurement-based quantum computing")
    print()


def demo_arbitrary_angle():
    """Demonstrate arbitrary angle measurement."""
    print("=" * 60)
    print("Arbitrary Angle Measurement")
    print("=" * 60)
    
    import math
    profile = parse_profile_string("logical:Surface(d=7)")
    
    # Measure at angle 0 (Z-basis)
    qubit = LogicalQubit("q0", profile, seed=42)
    qubit.state = LogicalState.ZERO
    outcome = qubit.measure("ANGLE", 0.0, angle=0.0)
    print(f"Measuring |0⟩ at angle 0 (Z-basis): {outcome}")
    
    # Measure at angle π/2 (X-basis)
    qubit = LogicalQubit("q1", profile, seed=42)
    qubit.state = LogicalState.PLUS
    outcome = qubit.measure("ANGLE", 0.0, angle=math.pi/2)
    print(f"Measuring |+⟩ at angle π/2 (X-basis): {outcome}")
    
    # Measure at angle π/4
    qubit = LogicalQubit("q2", profile, seed=42)
    qubit.state = LogicalState.ZERO
    outcome = qubit.measure("ANGLE", 0.0, angle=math.pi/4)
    print(f"Measuring |0⟩ at angle π/4: {outcome}")
    
    print("\nArbitrary angle measurements enable:")
    print("  - Generalized measurements")
    print("  - Quantum state tomography")
    print("  - Adaptive measurement protocols")
    print()


def demo_bell_basis():
    """Demonstrate Bell basis measurement."""
    print("=" * 60)
    print("Bell Basis Measurement (Two-Qubit)")
    print("=" * 60)
    
    profile = parse_profile_string("logical:Surface(d=7)")
    
    # Create and measure Bell state |Φ+⟩
    qubit1 = LogicalQubit("q0", profile, seed=42)
    qubit2 = LogicalQubit("q1", profile, seed=42)
    
    # Prepare |Φ+⟩ = (|00⟩ + |11⟩)/√2
    qubit1.apply_gate("H", 0.0)
    from kernel.simulator.logical_qubit import TwoQubitGate
    TwoQubitGate.apply_cnot(qubit1, qubit2, 0.0)
    
    # Perform Bell measurement
    outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
        qubit1, qubit2, 0.0
    )
    
    print(f"Prepared Bell state |Φ+⟩")
    print(f"Measurement outcomes: ({outcome1}, {outcome2})")
    print(f"Bell state index: {bell_index}")
    print()
    
    # Explain Bell states
    print("Bell States:")
    print("  Index 0: |Φ+⟩ = (|00⟩ + |11⟩)/√2  → measures as (0,0)")
    print("  Index 1: |Ψ+⟩ = (|01⟩ + |10⟩)/√2  → measures as (0,1)")
    print("  Index 2: |Φ-⟩ = (|00⟩ - |11⟩)/√2  → measures as (1,0)")
    print("  Index 3: |Ψ-⟩ = (|01⟩ - |10⟩)/√2  → measures as (1,1)")
    print()
    
    print("Bell measurements are essential for:")
    print("  - Quantum teleportation")
    print("  - Entanglement swapping")
    print("  - Superdense coding")
    print("  - Quantum repeaters")
    print()


def demo_state_tomography():
    """Demonstrate state tomography using multiple bases."""
    print("=" * 60)
    print("Quantum State Tomography")
    print("=" * 60)
    
    profile = parse_profile_string("logical:Surface(d=7)")
    
    print("To fully characterize a qubit state, measure in X, Y, and Z bases:")
    print()
    
    # Prepare a state
    qubit = LogicalQubit("q0", profile, seed=42)
    qubit.apply_gate("H", 0.0)  # Create |+⟩
    print("Prepared state: |+⟩ = (|0⟩ + |1⟩)/√2")
    print()
    
    # Measure in different bases (need multiple copies)
    results = {"Z": [], "X": [], "Y": []}
    
    for i in range(10):
        # Z-basis
        q = LogicalQubit(f"qz{i}", profile, seed=i)
        q.state = LogicalState.PLUS
        results["Z"].append(q.measure("Z", 0.0))
        
        # X-basis
        q = LogicalQubit(f"qx{i}", profile, seed=i)
        q.state = LogicalState.PLUS
        results["X"].append(q.measure("X", 0.0))
        
        # Y-basis
        q = LogicalQubit(f"qy{i}", profile, seed=i)
        q.state = LogicalState.PLUS
        results["Y"].append(q.measure("Y", 0.0))
    
    print("Measurement statistics (10 shots each):")
    print(f"  Z-basis: {results['Z'].count(0)} zeros, {results['Z'].count(1)} ones")
    print(f"  X-basis: {results['X'].count(0)} zeros, {results['X'].count(1)} ones")
    print(f"  Y-basis: {results['Y'].count(0)} zeros, {results['Y'].count(1)} ones")
    print()
    print("For |+⟩ state:")
    print("  Z-basis: ~50% each (random)")
    print("  X-basis: 100% zeros (eigenstate)")
    print("  Y-basis: ~50% each (not eigenstate)")
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  QMK Measurement Bases Demonstration".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    demo_z_basis()
    demo_x_basis()
    demo_y_basis()
    demo_arbitrary_angle()
    demo_bell_basis()
    demo_state_tomography()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("QMK supports comprehensive measurement capabilities:")
    print("  ✓ All Pauli bases (X, Y, Z)")
    print("  ✓ Arbitrary angle measurements")
    print("  ✓ Bell basis (two-qubit joint measurements)")
    print("  ✓ Complete state tomography")
    print()
    print("These measurements are essential for:")
    print("  • Quantum algorithms")
    print("  • Error correction")
    print("  • Quantum communication")
    print("  • State characterization")
    print()


if __name__ == "__main__":
    main()
