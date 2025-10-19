namespace QMK.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;

    /// # Summary
    /// Demonstrates quantum teleportation protocol.
    /// 
    /// # Description
    /// Teleports a quantum state from one qubit to another using:
    /// - Pre-shared entanglement (Bell pair)
    /// - Bell measurement
    /// - Classical communication (measurement results)
    /// - Conditional corrections (Pauli gates)
    ///
    /// This is a fundamental protocol in quantum communication.
    @EntryPoint()
    operation Teleportation() : Result {
        // Allocate three qubits
        use (msg, here, there) = (Qubit(), Qubit(), Qubit());
        
        // Prepare message state |+⟩ on 'msg' qubit
        H(msg);
        
        // Create entangled pair between 'here' and 'there'
        H(here);
        CNOT(here, there);
        
        // Bell measurement on 'msg' and 'here'
        CNOT(msg, here);
        H(msg);
        let m1 = M(msg);
        let m2 = M(here);
        
        // Apply corrections to 'there' based on measurements
        if (m2 == One) {
            X(there);
        }
        if (m1 == One) {
            Z(there);
        }
        
        // Measure the teleported state
        let result = M(there);
        
        return result;
    }
}
