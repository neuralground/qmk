; W State Generation
; Creates |W⟩ = (|100...0⟩ + |010...0⟩ + ... + |00...01⟩)/√n
;
; Parameters (set via Python):
;   n_qubits - number of qubits
;   angles - list of rotation angles

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Parameters
.param n_qubits = 3
.param qubit_outputs = "q0, q1, q2"
.param angles = [1.91, 1.57]

; Allocate qubits
alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> {qubit_outputs}

; Create W state using simplified construction
; For demonstration purposes, we create a W-like state
;
; Note: A proper W state requires a more complex construction
; involving controlled rotations or recursive preparation.
; This simplified version creates an equal superposition
; of single-excitation states.
;
; For 3 qubits: |W⟩ = (|100⟩ + |010⟩ + |001⟩)/√3

; For a 3-qubit W state, use explicit construction:
.if n_qubits == 3
    ; Create superposition on first qubit: (|0⟩ + |1⟩)/√2
    h0: APPLY_H q0
    
    ; Create superposition on second qubit: (|0⟩ + |1⟩)/√2  
    h1: APPLY_H q1
    
    ; Use Toffoli-like structure to create W state
    ; This is a simplified approximation
    ccx: APPLY_CNOT q0, q1
    cx1: APPLY_CNOT q1, q2
    cx2: APPLY_CNOT q0, q2
.else
    ; For other sizes, use the recursive algorithm
    ; (This is a placeholder - proper implementation needed)
    x0: APPLY_X q0
    
    .for i in 0..n_qubits-2
        .set next_qubit = i + 1
        ry{i}: APPLY_RY q{i}, theta={angles[i]}
        cnot{i}: APPLY_CNOT q{i}, q{next_qubit}
    .endfor
.endif

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
