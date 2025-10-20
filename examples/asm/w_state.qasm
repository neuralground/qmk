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

; Create W state (simplified construction)
; Initialize first qubit to |1⟩
x0: APPLY_X q0

; Distribute excitation across all qubits
; Note: angles should be passed as a list from Python
.for i in 0..n_qubits-2
    ry{i}: APPLY_RY q{i}, theta={angles[i]}
    .set next_qubit = i + 1
    cnot{i}: APPLY_CNOT q{i}, q{next_qubit}
.endfor

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
