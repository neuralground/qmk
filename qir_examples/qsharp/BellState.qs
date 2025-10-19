namespace QMK.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;

    /// # Summary
    /// Creates a Bell state (maximally entangled pair) and measures both qubits.
    /// 
    /// # Description
    /// This operation demonstrates:
    /// - Qubit allocation
    /// - Hadamard gate
    /// - CNOT gate
    /// - Z-basis measurement
    /// - Qubit deallocation
    ///
    /// Expected output: Both measurements should be correlated (00 or 11)
    @EntryPoint()
    operation BellState() : (Result, Result) {
        // Allocate two qubits
        use (q0, q1) = (Qubit(), Qubit());
        
        // Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
        H(q0);
        CNOT(q0, q1);
        
        // Measure both qubits
        let r0 = M(q0);
        let r1 = M(q1);
        
        // Qubits are automatically released
        return (r0, r1);
    }
}
