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

; Create W state using recursive construction
; Algorithm:
; 1. Start with |1⟩ on first qubit
; 2. For each step, rotate and transfer excitation to next qubit
; 3. Uncompute rotation after transfer
;
; For 3 qubits: |W⟩ = (|100⟩ + |010⟩ + |001⟩)/√3

; Initialize first qubit to |1⟩
x0: APPLY_X q0

; Recursive distribution of excitation
.for i in 0..n_qubits-2
    ; Rotate qubit i to share excitation with next qubit
    ry{i}_fwd: APPLY_RY q{i}, theta={angles[i]}
    
    ; Transfer excitation to next qubit
    .set next_qubit = i + 1
    cnot{i}: APPLY_CNOT q{i}, q{next_qubit}
    
    ; Uncompute the rotation (apply inverse)
    .set neg_angle = -1 * angles[i]
    ry{i}_inv: APPLY_RY q{i}, theta={neg_angle}
.endfor

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
