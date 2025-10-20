"""
Qiskit Algorithm Examples

Collection of quantum algorithms implemented in Qiskit for testing
the QIR conversion and optimization pipeline.
"""

from qiskit import QuantumCircuit
import numpy as np


def bell_state() -> QuantumCircuit:
    """
    Bell State (EPR Pair)
    
    Creates maximally entangled state: |00⟩ + |11⟩
    """
    qc = QuantumCircuit(2, 2, name="Bell State")
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def ghz_state(n: int = 3) -> QuantumCircuit:
    """
    GHZ State (Greenberger-Horne-Zeilinger)
    
    Creates n-qubit entangled state: |00...0⟩ + |11...1⟩
    """
    qc = QuantumCircuit(n, n, name=f"GHZ-{n}")
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n), range(n))
    return qc


def deutsch_jozsa(oracle_type: str = "balanced") -> QuantumCircuit:
    """
    Deutsch-Jozsa Algorithm
    
    Determines if a function is constant or balanced with one query.
    
    Args:
        oracle_type: "constant" or "balanced"
    """
    n = 3  # Number of input qubits
    qc = QuantumCircuit(n + 1, n, name="Deutsch-Jozsa")
    
    # Initialize
    qc.x(n)  # Ancilla to |1⟩
    qc.h(range(n + 1))  # Hadamard on all qubits
    
    # Oracle
    if oracle_type == "balanced":
        # Balanced oracle: flip ancilla based on input
        for i in range(n):
            qc.cx(i, n)
    # Constant oracle: do nothing
    
    # Final Hadamards
    qc.h(range(n))
    
    # Measure
    qc.measure(range(n), range(n))
    
    return qc


def bernstein_vazirani(secret_string: str = "101") -> QuantumCircuit:
    """
    Bernstein-Vazirani Algorithm
    
    Finds a hidden binary string with one query.
    
    Args:
        secret_string: Hidden binary string to find
    """
    n = len(secret_string)
    qc = QuantumCircuit(n + 1, n, name="Bernstein-Vazirani")
    
    # Initialize
    qc.x(n)  # Ancilla to |1⟩
    qc.h(range(n + 1))  # Hadamard on all qubits
    
    # Oracle: apply CX for each '1' in secret string
    for i, bit in enumerate(reversed(secret_string)):
        if bit == '1':
            qc.cx(i, n)
    
    # Final Hadamards
    qc.h(range(n))
    
    # Measure
    qc.measure(range(n), range(n))
    
    return qc


def grover_search(marked_state: int = 3, n_qubits: int = 3) -> QuantumCircuit:
    """
    Grover's Search Algorithm
    
    Searches for a marked state in an unsorted database.
    
    Args:
        marked_state: State to search for (as integer)
        n_qubits: Number of qubits
    """
    qc = QuantumCircuit(n_qubits, n_qubits, name="Grover Search")
    
    # Initialize superposition
    qc.h(range(n_qubits))
    
    # Number of iterations
    iterations = int(np.pi / 4 * np.sqrt(2**n_qubits))
    
    for _ in range(iterations):
        # Oracle: mark the target state
        # Convert marked_state to binary and apply multi-controlled Z
        binary = format(marked_state, f'0{n_qubits}b')
        
        # Flip qubits that should be 0
        for i, bit in enumerate(binary):
            if bit == '0':
                qc.x(i)
        
        # Multi-controlled Z gate
        if n_qubits == 2:
            qc.cz(0, 1)
        elif n_qubits == 3:
            qc.h(2)
            qc.ccx(0, 1, 2)
            qc.h(2)
        
        # Flip back
        for i, bit in enumerate(binary):
            if bit == '0':
                qc.x(i)
        
        # Diffusion operator
        qc.h(range(n_qubits))
        qc.x(range(n_qubits))
        
        # Multi-controlled Z
        if n_qubits == 2:
            qc.cz(0, 1)
        elif n_qubits == 3:
            qc.h(2)
            qc.ccx(0, 1, 2)
            qc.h(2)
        
        qc.x(range(n_qubits))
        qc.h(range(n_qubits))
    
    # Measure
    qc.measure(range(n_qubits), range(n_qubits))
    
    return qc


def quantum_fourier_transform(n: int = 3) -> QuantumCircuit:
    """
    Quantum Fourier Transform
    
    Implements the QFT on n qubits.
    """
    qc = QuantumCircuit(n, n, name=f"QFT-{n}")
    
    # QFT circuit
    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            qc.cp(np.pi / 2**(k - j), k, j)
    
    # Swap qubits
    for i in range(n // 2):
        qc.swap(i, n - i - 1)
    
    # Measure
    qc.measure(range(n), range(n))
    
    return qc


def phase_estimation(phase: float = 0.25, n_counting: int = 3) -> QuantumCircuit:
    """
    Quantum Phase Estimation
    
    Estimates the phase of a unitary operator.
    
    Args:
        phase: Phase to estimate (as fraction of 2π)
        n_counting: Number of counting qubits
    """
    n_total = n_counting + 1
    qc = QuantumCircuit(n_total, n_counting, name="Phase Estimation")
    
    # Initialize eigenstate
    qc.x(n_counting)
    
    # Initialize counting qubits
    qc.h(range(n_counting))
    
    # Controlled unitary operations
    for i in range(n_counting):
        repetitions = 2**i
        angle = 2 * np.pi * phase * repetitions
        qc.cp(angle, i, n_counting)
    
    # Inverse QFT on counting qubits
    for j in reversed(range(n_counting)):
        for k in range(j):
            qc.cp(-np.pi / 2**(j - k), k, j)
        qc.h(j)
    
    # Measure counting qubits
    qc.measure(range(n_counting), range(n_counting))
    
    return qc


def teleportation() -> QuantumCircuit:
    """
    Quantum Teleportation
    
    Teleports a quantum state using entanglement.
    """
    qc = QuantumCircuit(3, 3, name="Teleportation")
    
    # Prepare state to teleport (arbitrary state on qubit 0)
    qc.h(0)
    qc.t(0)
    
    # Create Bell pair between qubits 1 and 2
    qc.h(1)
    qc.cx(1, 2)
    
    # Bell measurement on qubits 0 and 1
    qc.cx(0, 1)
    qc.h(0)
    qc.measure([0, 1], [0, 1])
    
    # Conditional operations on qubit 2
    qc.x(2).c_if(1, 1)
    qc.z(2).c_if(0, 1)
    
    # Measure final state
    qc.measure(2, 2)
    
    return qc


def superdense_coding() -> QuantumCircuit:
    """
    Superdense Coding
    
    Sends 2 classical bits using 1 qubit.
    """
    qc = QuantumCircuit(2, 2, name="Superdense Coding")
    
    # Create Bell pair
    qc.h(0)
    qc.cx(0, 1)
    
    # Encode message (11)
    qc.z(0)
    qc.x(0)
    
    # Decode
    qc.cx(0, 1)
    qc.h(0)
    
    # Measure
    qc.measure([0, 1], [0, 1])
    
    return qc


def vqe_ansatz(n: int = 2, depth: int = 2) -> QuantumCircuit:
    """
    VQE Ansatz Circuit
    
    Variational circuit for VQE algorithm.
    
    Args:
        n: Number of qubits
        depth: Circuit depth
    """
    qc = QuantumCircuit(n, n, name=f"VQE-{n}-{depth}")
    
    # Initial layer
    for i in range(n):
        qc.ry(np.pi / 4, i)
    
    # Entangling layers
    for d in range(depth):
        # Entanglement
        for i in range(n - 1):
            qc.cx(i, i + 1)
        
        # Rotation layer
        for i in range(n):
            qc.ry(np.pi / 3, i)
            qc.rz(np.pi / 6, i)
    
    # Measure
    qc.measure(range(n), range(n))
    
    return qc


# Dictionary of all algorithms
ALGORITHMS = {
    "bell_state": bell_state,
    "ghz_state": ghz_state,
    "deutsch_jozsa": deutsch_jozsa,
    "bernstein_vazirani": bernstein_vazirani,
    "grover_search": grover_search,
    "qft": quantum_fourier_transform,
    "phase_estimation": phase_estimation,
    "teleportation": teleportation,
    "superdense_coding": superdense_coding,
    "vqe_ansatz": vqe_ansatz,
}


if __name__ == "__main__":
    # Test all algorithms
    print("Qiskit Algorithm Examples")
    print("=" * 60)
    
    for name, func in ALGORITHMS.items():
        try:
            circuit = func()
            print(f"✅ {name}: {circuit.num_qubits} qubits, {len(circuit)} gates")
        except Exception as e:
            print(f"❌ {name}: {e}")
