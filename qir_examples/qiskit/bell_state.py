#!/usr/bin/env python3
"""
Bell State in Qiskit with QIR export.

This example shows how to:
1. Create a quantum circuit in Qiskit
2. Export to QIR format
3. Use with QMK's QIR bridge
"""

import argparse
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

try:
    from qiskit_qir import to_qir_module
    HAS_QIR = True
except ImportError:
    print("Warning: qiskit-qir not installed. Install with: pip install qiskit-qir")
    HAS_QIR = False


def create_bell_state():
    """Create a Bell state circuit."""
    # Create quantum and classical registers
    qr = QuantumRegister(2, 'q')
    cr = ClassicalRegister(2, 'c')
    circuit = QuantumCircuit(qr, cr, name='bell_state')
    
    # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
    circuit.h(qr[0])
    circuit.cx(qr[0], qr[1])
    
    # Measure both qubits
    circuit.measure(qr[0], cr[0])
    circuit.measure(qr[1], cr[1])
    
    return circuit


def export_to_qir(circuit, output_file=None):
    """Export circuit to QIR format."""
    if not HAS_QIR:
        print("Cannot export to QIR: qiskit-qir not installed")
        return None
    
    # Convert to QIR
    qir_module = to_qir_module(circuit)
    qir_str = str(qir_module)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(qir_str)
        print(f"QIR written to {output_file}")
    
    return qir_str


def main():
    parser = argparse.ArgumentParser(description='Generate Bell state QIR from Qiskit')
    parser.add_argument('--output', '-o', help='Output QIR file')
    parser.add_argument('--show-circuit', action='store_true', help='Display circuit')
    args = parser.parse_args()
    
    # Create circuit
    circuit = create_bell_state()
    
    if args.show_circuit:
        print("Qiskit Circuit:")
        print(circuit.draw(output='text'))
        print()
    
    # Export to QIR
    qir = export_to_qir(circuit, args.output)
    
    if qir and not args.output:
        print("Generated QIR:")
        print(qir)
    
    print("\nTo use with QMK:")
    print("  python -c \"")
    print("  from kernel.qir_bridge import QIRParser, QVMGraphGenerator")
    print("  parser = QIRParser()")
    print(f"  functions = parser.parse(open('{args.output or 'bell_state.ll'}').read())")
    print("  generator = QVMGraphGenerator()")
    print("  graph = generator.generate(list(functions.values())[0])")
    print("  print(graph)")
    print("  \"")


if __name__ == '__main__':
    main()
