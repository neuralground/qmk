#!/usr/bin/env python3
"""
Bell State in Cirq with QIR export.

This example shows how to:
1. Create a quantum circuit in Cirq
2. Export to QIR format
3. Use with QMK's QIR bridge
"""

import argparse
import cirq

try:
    from cirq_qir import to_qir
    HAS_QIR = True
except ImportError:
    print("Warning: cirq-qir not installed. Install with: pip install cirq-qir")
    HAS_QIR = False


def create_bell_state():
    """Create a Bell state circuit in Cirq."""
    # Create qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)
    
    # Create circuit
    circuit = cirq.Circuit()
    
    # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
    circuit.append(cirq.H(q0))
    circuit.append(cirq.CNOT(q0, q1))
    
    # Measure both qubits
    circuit.append(cirq.measure(q0, key='m0'))
    circuit.append(cirq.measure(q1, key='m1'))
    
    return circuit


def export_to_qir(circuit, output_file=None):
    """Export circuit to QIR format."""
    if not HAS_QIR:
        print("Cannot export to QIR: cirq-qir not installed")
        return None
    
    # Convert to QIR
    qir_str = to_qir(circuit, name='bell_state')
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(qir_str)
        print(f"QIR written to {output_file}")
    
    return qir_str


def main():
    parser = argparse.ArgumentParser(description='Generate Bell state QIR from Cirq')
    parser.add_argument('--output', '-o', help='Output QIR file')
    parser.add_argument('--show-circuit', action='store_true', help='Display circuit')
    args = parser.parse_args()
    
    # Create circuit
    circuit = create_bell_state()
    
    if args.show_circuit:
        print("Cirq Circuit:")
        print(circuit)
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
