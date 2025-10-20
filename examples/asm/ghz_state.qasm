; GHZ State Generation
; Creates |GHZ⟩ = (|00...0⟩ + |11...1⟩)/√2
;
; Parameters (set via Python):
;   n_qubits - number of qubits

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Parameters
.param n_qubits = 3
.param qubit_outputs = "q0, q1, q2"

; Allocate qubits
alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> {qubit_outputs}

; Create GHZ state
; Step 1: Put first qubit in superposition
h0: APPLY_H q0

; Step 2: Entangle all other qubits with first
.for i in 1..n_qubits-1
    cnot{i}: APPLY_CNOT q0, q{i}
.endfor

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
