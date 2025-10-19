namespace QMK.Examples {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Measurement;
    open Microsoft.Quantum.Canon;

    /// # Summary
    /// Grover's search algorithm for 2-qubit search space.
    /// 
    /// # Description
    /// Searches for a marked item in an unstructured database.
    /// For 2 qubits, searches 4 possible states: |00⟩, |01⟩, |10⟩, |11⟩
    /// 
    /// # Parameters
    /// - target: The marked state to search for (0-3)
    ///
    /// # Returns
    /// The measurement result (should match target with high probability)
    operation GroverSearch(target : Int) : Int {
        use qubits = Qubit[2];
        
        // Initialize to equal superposition
        ApplyToEach(H, qubits);
        
        // Apply Grover iteration (optimal for N=4 is 1 iteration)
        Oracle(qubits, target);
        Diffusion(qubits);
        
        // Measure
        let results = MultiM(qubits);
        
        // Convert to integer
        mutable value = 0;
        for i in 0..Length(results)-1 {
            if (results[i] == One) {
                set value = value + (1 <<< i);
            }
        }
        
        return value;
    }
    
    /// Oracle marks the target state with a phase flip
    operation Oracle(qubits : Qubit[], target : Int) : Unit {
        // Flip qubits that should be 0 in target
        for i in 0..Length(qubits)-1 {
            if ((target &&& (1 <<< i)) == 0) {
                X(qubits[i]);
            }
        }
        
        // Multi-controlled Z
        Controlled Z(qubits[1..Length(qubits)-1], qubits[0]);
        
        // Unflip
        for i in 0..Length(qubits)-1 {
            if ((target &&& (1 <<< i)) == 0) {
                X(qubits[i]);
            }
        }
    }
    
    /// Diffusion operator (inversion about average)
    operation Diffusion(qubits : Qubit[]) : Unit {
        ApplyToEach(H, qubits);
        ApplyToEach(X, qubits);
        
        Controlled Z(qubits[1..Length(qubits)-1], qubits[0]);
        
        ApplyToEach(X, qubits);
        ApplyToEach(H, qubits);
    }
}
