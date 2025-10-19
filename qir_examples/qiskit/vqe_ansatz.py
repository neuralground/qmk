#!/usr/bin/env python3
"""
VQE Ansatz in Qiskit with QIR export.

Demonstrates a parameterized circuit for Variational Quantum Eigensolver.
"""

import argparse
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

try:
    from qiskit_qir import to_qir_module
    HAS_QIR = True
except ImportError:
    print("Warning: qiskit-qir not installed")
    HAS_QIR = False


def create_vqe_ansatz(theta1=np.pi/4, theta2=np.pi/3, theta3=np.pi/6):
    """
    Create a VQE ansatz circuit with rotation gates.
    
    This is a simple ansatz for a 2-qubit system with parameterized rotations.
    """
    qr = QuantumRegister(2, 'q')
    cr = ClassicalRegister(2, 'c')
    circuit = QuantumCircuit(qr, cr, name='vqe_ansatz')
    
    # Layer 1: Single-qubit rotations
    circuit.ry(theta1, qr[0])
    circuit.ry(theta2, qr[1])
    
    # Entangling layer
    circuit.cx(qr[0], qr[1])
    
    # Layer 2: More rotations
    circuit.rz(theta3, qr[0])
    circuit.rz(theta3, qr[1])
    
    # Another entangling layer
    circuit.cx(qr[1], qr[0])
    
    # Final rotations
    circuit.ry(-theta1, qr[0])
    circuit.ry(-theta2, qr[1])
    
    # Measure
    circuit.measure(qr, cr)
    
    return circuit


def export_to_qir(circuit, output_file=None):
    """Export circuit to QIR format."""
    if not HAS_QIR:
        return None
    
    qir_module = to_qir_module(circuit)
    qir_str = str(qir_module)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(qir_str)
        print(f"QIR written to {output_file}")
    
    return qir_str


def main():
    parser = argparse.ArgumentParser(description='Generate VQE ansatz QIR from Qiskit')
    parser.add_argument('--output', '-o', help='Output QIR file')
    parser.add_argument('--theta1', type=float, default=np.pi/4, help='First rotation angle')
    parser.add_argument('--theta2', type=float, default=np.pi/3, help='Second rotation angle')
    parser.add_argument('--theta3', type=float, default=np.pi/6, help='Third rotation angle')
    parser.add_argument('--show-circuit', action='store_true', help='Display circuit')
    args = parser.parse_args()
    
    # Create circuit
    circuit = create_vqe_ansatz(args.theta1, args.theta2, args.theta3)
    
    if args.show_circuit:
        print("VQE Ansatz Circuit:")
        print(circuit.draw(output='text'))
        print()
    
    # Export to QIR
    qir = export_to_qir(circuit, args.output)
    
    if qir and not args.output:
        print("Generated QIR:")
        print(qir[:500] + "..." if len(qir) > 500 else qir)


if __name__ == '__main__':
    main()
