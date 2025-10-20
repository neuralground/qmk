"""
Cirq Algorithm Examples

Collection of quantum algorithms implemented in Cirq for testing
the QIR conversion and optimization pipeline.
"""

import cirq
import numpy as np


def bell_state() -> cirq.Circuit:
    """
    Bell State (EPR Pair)
    
    Creates maximally entangled state: |00⟩ + |11⟩
    """
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.measure(q0, q1, key='result')
    )
    return circuit


def ghz_state(n: int = 3) -> cirq.Circuit:
    """
    GHZ State (Greenberger-Horne-Zeilinger)
    
    Creates n-qubit entangled state: |00...0⟩ + |11...1⟩
    """
    qubits = cirq.LineQubit.range(n)
    circuit = cirq.Circuit()
    
    circuit.append(cirq.H(qubits[0]))
    for i in range(n - 1):
        circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
    
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


def deutsch_jozsa(oracle_type: str = "balanced") -> cirq.Circuit:
    """
    Deutsch-Jozsa Algorithm
    
    Determines if a function is constant or balanced with one query.
    
    Args:
        oracle_type: "constant" or "balanced"
    """
    n = 3  # Number of input qubits
    qubits = cirq.LineQubit.range(n)
    ancilla = cirq.LineQubit(n)
    
    circuit = cirq.Circuit()
    
    # Initialize
    circuit.append(cirq.X(ancilla))
    circuit.append([cirq.H(q) for q in qubits + [ancilla]])
    
    # Oracle
    if oracle_type == "balanced":
        for q in qubits:
            circuit.append(cirq.CNOT(q, ancilla))
    
    # Final Hadamards
    circuit.append([cirq.H(q) for q in qubits])
    
    # Measure
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


def bernstein_vazirani(secret_string: str = "101") -> cirq.Circuit:
    """
    Bernstein-Vazirani Algorithm
    
    Finds a hidden binary string with one query.
    
    Args:
        secret_string: Hidden binary string to find
    """
    n = len(secret_string)
    qubits = cirq.LineQubit.range(n)
    ancilla = cirq.LineQubit(n)
    
    circuit = cirq.Circuit()
    
    # Initialize
    circuit.append(cirq.X(ancilla))
    circuit.append([cirq.H(q) for q in qubits + [ancilla]])
    
    # Oracle
    for i, bit in enumerate(reversed(secret_string)):
        if bit == '1':
            circuit.append(cirq.CNOT(qubits[i], ancilla))
    
    # Final Hadamards
    circuit.append([cirq.H(q) for q in qubits])
    
    # Measure
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


def grover_search(marked_state: int = 3, n_qubits: int = 3) -> cirq.Circuit:
    """
    Grover's Search Algorithm
    
    Searches for a marked state in an unsorted database.
    
    Args:
        marked_state: State to search for (as integer)
        n_qubits: Number of qubits
    """
    qubits = cirq.LineQubit.range(n_qubits)
    circuit = cirq.Circuit()
    
    # Initialize superposition
    circuit.append([cirq.H(q) for q in qubits])
    
    # Number of iterations
    iterations = int(np.pi / 4 * np.sqrt(2**n_qubits))
    
    for _ in range(iterations):
        # Oracle
        binary = format(marked_state, f'0{n_qubits}b')
        
        # Flip qubits that should be 0
        for i, bit in enumerate(binary):
            if bit == '0':
                circuit.append(cirq.X(qubits[i]))
        
        # Multi-controlled Z
        if n_qubits == 2:
            circuit.append(cirq.CZ(qubits[0], qubits[1]))
        elif n_qubits == 3:
            circuit.append(cirq.H(qubits[2]))
            circuit.append(cirq.CCX(qubits[0], qubits[1], qubits[2]))
            circuit.append(cirq.H(qubits[2]))
        
        # Flip back
        for i, bit in enumerate(binary):
            if bit == '0':
                circuit.append(cirq.X(qubits[i]))
        
        # Diffusion operator
        circuit.append([cirq.H(q) for q in qubits])
        circuit.append([cirq.X(q) for q in qubits])
        
        if n_qubits == 2:
            circuit.append(cirq.CZ(qubits[0], qubits[1]))
        elif n_qubits == 3:
            circuit.append(cirq.H(qubits[2]))
            circuit.append(cirq.CCX(qubits[0], qubits[1], qubits[2]))
            circuit.append(cirq.H(qubits[2]))
        
        circuit.append([cirq.X(q) for q in qubits])
        circuit.append([cirq.H(q) for q in qubits])
    
    # Measure
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


def quantum_fourier_transform(n: int = 3) -> cirq.Circuit:
    """
    Quantum Fourier Transform
    
    Implements the QFT on n qubits.
    """
    qubits = cirq.LineQubit.range(n)
    circuit = cirq.Circuit()
    
    # QFT circuit
    for j in range(n):
        circuit.append(cirq.H(qubits[j]))
        for k in range(j + 1, n):
            circuit.append(cirq.CZPowGate(exponent=1 / 2**(k - j))(qubits[k], qubits[j]))
    
    # Swap qubits
    for i in range(n // 2):
        circuit.append(cirq.SWAP(qubits[i], qubits[n - i - 1]))
    
    # Measure
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


def teleportation() -> cirq.Circuit:
    """
    Quantum Teleportation
    
    Teleports a quantum state using entanglement.
    """
    q0, q1, q2 = cirq.LineQubit.range(3)
    circuit = cirq.Circuit()
    
    # Prepare state to teleport
    circuit.append(cirq.H(q0))
    circuit.append(cirq.T(q0))
    
    # Create Bell pair
    circuit.append(cirq.H(q1))
    circuit.append(cirq.CNOT(q1, q2))
    
    # Bell measurement
    circuit.append(cirq.CNOT(q0, q1))
    circuit.append(cirq.H(q0))
    circuit.append(cirq.measure(q0, q1, key='bell'))
    
    # Note: Cirq doesn't support classical control easily
    # This is a simplified version
    circuit.append(cirq.measure(q2, key='result'))
    
    return circuit


def superdense_coding() -> cirq.Circuit:
    """
    Superdense Coding
    
    Sends 2 classical bits using 1 qubit.
    """
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit()
    
    # Create Bell pair
    circuit.append(cirq.H(q0))
    circuit.append(cirq.CNOT(q0, q1))
    
    # Encode message (11)
    circuit.append(cirq.Z(q0))
    circuit.append(cirq.X(q0))
    
    # Decode
    circuit.append(cirq.CNOT(q0, q1))
    circuit.append(cirq.H(q0))
    
    # Measure
    circuit.append(cirq.measure(q0, q1, key='result'))
    
    return circuit


def vqe_ansatz(n: int = 2, depth: int = 2) -> cirq.Circuit:
    """
    VQE Ansatz Circuit
    
    Variational circuit for VQE algorithm.
    
    Args:
        n: Number of qubits
        depth: Circuit depth
    """
    qubits = cirq.LineQubit.range(n)
    circuit = cirq.Circuit()
    
    # Initial layer
    for q in qubits:
        circuit.append(cirq.ry(np.pi / 4)(q))
    
    # Entangling layers
    for d in range(depth):
        # Entanglement
        for i in range(n - 1):
            circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
        
        # Rotation layer
        for q in qubits:
            circuit.append(cirq.ry(np.pi / 3)(q))
            circuit.append(cirq.rz(np.pi / 6)(q))
    
    # Measure
    circuit.append(cirq.measure(*qubits, key='result'))
    
    return circuit


# Dictionary of all algorithms
ALGORITHMS = {
    "bell_state": bell_state,
    "ghz_state": ghz_state,
    "deutsch_jozsa": deutsch_jozsa,
    "bernstein_vazirani": bernstein_vazirani,
    "grover_search": grover_search,
    "qft": quantum_fourier_transform,
    "teleportation": teleportation,
    "superdense_coding": superdense_coding,
    "vqe_ansatz": vqe_ansatz,
}


if __name__ == "__main__":
    # Test all algorithms
    print("Cirq Algorithm Examples")
    print("=" * 60)
    
    for name, func in ALGORITHMS.items():
        try:
            circuit = func()
            print(f"✅ {name}: {len(circuit.all_qubits())} qubits, {len(list(circuit.all_operations()))} gates")
        except Exception as e:
            print(f"❌ {name}: {e}")
