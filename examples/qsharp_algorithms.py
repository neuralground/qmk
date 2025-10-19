"""
Q# Algorithm Examples

Collection of quantum algorithms implemented in Q# for testing
the QIR conversion and optimization pipeline.

Note: Q# code is provided as strings and would be compiled/executed
through the Q# runtime.
"""

from typing import Dict


# Bell State
BELL_STATE = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    
    @EntryPoint()
    operation BellState() : (Result, Result) {
        use (q0, q1) = (Qubit(), Qubit());
        H(q0);
        CNOT(q0, q1);
        let r0 = M(q0);
        let r1 = M(q1);
        return (r0, r1);
    }
}
"""

# GHZ State
GHZ_STATE = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    
    @EntryPoint()
    operation GHZState(n : Int) : Result[] {
        use qubits = Qubit[n];
        H(qubits[0]);
        for i in 1..n-1 {
            CNOT(qubits[0], qubits[i]);
        }
        return MeasureEachZ(qubits);
    }
}
"""

# Deutsch-Jozsa Algorithm
DEUTSCH_JOZSA = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    
    operation BalancedOracle(x : Qubit[], y : Qubit) : Unit {
        for q in x {
            CNOT(q, y);
        }
    }
    
    @EntryPoint()
    operation DeutschJozsa(n : Int) : Result[] {
        use x = Qubit[n];
        use y = Qubit();
        
        // Initialize
        X(y);
        ApplyToEach(H, x);
        H(y);
        
        // Apply oracle
        BalancedOracle(x, y);
        
        // Final Hadamards
        ApplyToEach(H, x);
        
        // Measure
        return MeasureEachZ(x);
    }
}
"""

# Bernstein-Vazirani Algorithm
BERNSTEIN_VAZIRANI = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    
    operation SecretStringOracle(x : Qubit[], y : Qubit, secret : Bool[]) : Unit {
        for i in 0..Length(x)-1 {
            if secret[i] {
                CNOT(x[i], y);
            }
        }
    }
    
    @EntryPoint()
    operation BernsteinVazirani(secret : Bool[]) : Result[] {
        let n = Length(secret);
        use x = Qubit[n];
        use y = Qubit();
        
        // Initialize
        X(y);
        ApplyToEach(H, x);
        H(y);
        
        // Apply oracle
        SecretStringOracle(x, y, secret);
        
        // Final Hadamards
        ApplyToEach(H, x);
        
        // Measure
        return MeasureEachZ(x);
    }
}
"""

# Grover's Search
GROVER_SEARCH = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    
    operation Oracle(qubits : Qubit[], marked : Int) : Unit {
        use ancilla = Qubit();
        X(ancilla);
        H(ancilla);
        
        // Mark the target state
        let binary = IntAsBoolArray(marked, Length(qubits));
        for i in 0..Length(qubits)-1 {
            if not binary[i] {
                X(qubits[i]);
            }
        }
        
        Controlled X(qubits, ancilla);
        
        for i in 0..Length(qubits)-1 {
            if not binary[i] {
                X(qubits[i]);
            }
        }
        
        H(ancilla);
        X(ancilla);
    }
    
    operation DiffusionOperator(qubits : Qubit[]) : Unit {
        ApplyToEach(H, qubits);
        ApplyToEach(X, qubits);
        
        use ancilla = Qubit();
        X(ancilla);
        H(ancilla);
        Controlled X(qubits, ancilla);
        H(ancilla);
        X(ancilla);
        
        ApplyToEach(X, qubits);
        ApplyToEach(H, qubits);
    }
    
    @EntryPoint()
    operation GroverSearch(n : Int, marked : Int) : Result[] {
        use qubits = Qubit[n];
        
        // Initialize superposition
        ApplyToEach(H, qubits);
        
        // Grover iterations
        let iterations = Round(PI() / 4.0 * Sqrt(IntAsDouble(2^n)));
        for _ in 1..iterations {
            Oracle(qubits, marked);
            DiffusionOperator(qubits);
        }
        
        return MeasureEachZ(qubits);
    }
}
"""

# Quantum Fourier Transform
QFT = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    
    operation QFT(qubits : Qubit[]) : Unit {
        let n = Length(qubits);
        for j in 0..n-1 {
            H(qubits[j]);
            for k in j+1..n-1 {
                Controlled R1([qubits[k]], (PI() / PowD(2.0, IntAsDouble(k-j)), qubits[j]));
            }
        }
        
        // Swap qubits
        for i in 0..n/2-1 {
            SWAP(qubits[i], qubits[n-1-i]);
        }
    }
    
    @EntryPoint()
    operation QuantumFourierTransform(n : Int) : Result[] {
        use qubits = Qubit[n];
        
        // Prepare initial state
        H(qubits[0]);
        
        // Apply QFT
        QFT(qubits);
        
        return MeasureEachZ(qubits);
    }
}
"""

# Quantum Phase Estimation
PHASE_ESTIMATION = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    
    operation ControlledU(control : Qubit, target : Qubit, phase : Double, power : Int) : Unit {
        let angle = phase * IntAsDouble(power);
        Controlled R1([control], (angle, target));
    }
    
    operation InverseQFT(qubits : Qubit[]) : Unit {
        let n = Length(qubits);
        
        // Reverse swaps
        for i in 0..n/2-1 {
            SWAP(qubits[i], qubits[n-1-i]);
        }
        
        // Inverse QFT
        for j in 0..n-1 {
            let idx = n - 1 - j;
            for k in 0..idx-1 {
                Controlled R1([qubits[k]], (-PI() / PowD(2.0, IntAsDouble(idx-k)), qubits[idx]));
            }
            H(qubits[idx]);
        }
    }
    
    @EntryPoint()
    operation PhaseEstimation(phase : Double, nCounting : Int) : Result[] {
        use counting = Qubit[nCounting];
        use eigenstate = Qubit();
        
        // Initialize eigenstate
        X(eigenstate);
        
        // Initialize counting qubits
        ApplyToEach(H, counting);
        
        // Controlled unitaries
        for i in 0..nCounting-1 {
            ControlledU(counting[i], eigenstate, 2.0 * PI() * phase, 2^i);
        }
        
        // Inverse QFT
        InverseQFT(counting);
        
        return MeasureEachZ(counting);
    }
}
"""

# Quantum Teleportation
TELEPORTATION = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    
    @EntryPoint()
    operation Teleportation() : Result {
        use msg = Qubit();
        use here = Qubit();
        use there = Qubit();
        
        // Prepare state to teleport
        H(msg);
        T(msg);
        
        // Create Bell pair
        H(here);
        CNOT(here, there);
        
        // Bell measurement
        CNOT(msg, here);
        H(msg);
        
        let m1 = M(msg);
        let m2 = M(here);
        
        // Corrections
        if m2 == One { X(there); }
        if m1 == One { Z(there); }
        
        return M(there);
    }
}
"""

# Superdense Coding
SUPERDENSE_CODING = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    
    @EntryPoint()
    operation SuperdenseCoding(bit1 : Bool, bit2 : Bool) : (Result, Result) {
        use q0 = Qubit();
        use q1 = Qubit();
        
        // Create Bell pair
        H(q0);
        CNOT(q0, q1);
        
        // Encode message
        if bit2 { X(q0); }
        if bit1 { Z(q0); }
        
        // Decode
        CNOT(q0, q1);
        H(q0);
        
        let r0 = M(q0);
        let r1 = M(q1);
        
        return (r0, r1);
    }
}
"""

# VQE Ansatz
VQE_ANSATZ = """
namespace Quantum.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Arrays;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Math;
    
    operation RotationLayer(qubits : Qubit[], theta : Double, phi : Double) : Unit {
        for q in qubits {
            Ry(theta, q);
            Rz(phi, q);
        }
    }
    
    operation EntanglingLayer(qubits : Qubit[]) : Unit {
        let n = Length(qubits);
        for i in 0..n-2 {
            CNOT(qubits[i], qubits[i+1]);
        }
    }
    
    @EntryPoint()
    operation VQEAnsatz(n : Int, depth : Int) : Result[] {
        use qubits = Qubit[n];
        
        // Initial rotation
        for q in qubits {
            Ry(PI() / 4.0, q);
        }
        
        // Variational layers
        for _ in 1..depth {
            EntanglingLayer(qubits);
            RotationLayer(qubits, PI() / 3.0, PI() / 6.0);
        }
        
        return MeasureEachZ(qubits);
    }
}
"""


# Dictionary of all algorithms
ALGORITHMS: Dict[str, str] = {
    "bell_state": BELL_STATE,
    "ghz_state": GHZ_STATE,
    "deutsch_jozsa": DEUTSCH_JOZSA,
    "bernstein_vazirani": BERNSTEIN_VAZIRANI,
    "grover_search": GROVER_SEARCH,
    "qft": QFT,
    "phase_estimation": PHASE_ESTIMATION,
    "teleportation": TELEPORTATION,
    "superdense_coding": SUPERDENSE_CODING,
    "vqe_ansatz": VQE_ANSATZ,
}


if __name__ == "__main__":
    # List all algorithms
    print("Q# Algorithm Examples")
    print("=" * 60)
    
    for name in ALGORITHMS.keys():
        print(f"✅ {name}")
    
    print(f"\nTotal: {len(ALGORITHMS)} algorithms")
    print("\nNote: These are Q# source code strings.")
    print("Use qsharp.compile() to compile and execute them.")
