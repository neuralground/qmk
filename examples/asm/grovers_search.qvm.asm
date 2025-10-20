; Grover's Search Algorithm
; Searches for a marked item in an unsorted database
;
; Parameters (set via Python):
;   target_state - list like ["1", "1"] for target |11⟩
;   n_iterations - number of Grover iterations

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Grover's search for 2-qubit target
alloc: ALLOC_LQ n=2, profile="logical:Surface(d=3)" -> q0, q1

; Initialize in equal superposition
h0: APPLY_H q0
h1: APPLY_H q1

; Grover iterations
.for iter in 0..n_iterations-1
    ; === Oracle: Mark target state ===
    ; Flip bits that should be 0 in target
    .if target_state[0] == "0"
        oracle_x0_{iter}: APPLY_X q0
    .endif
    .if target_state[1] == "0"
        oracle_x1_{iter}: APPLY_X q1
    .endif
    
    ; Controlled-Z (mark the state)
    oracle_h_{iter}: APPLY_H q1
    oracle_cnot_{iter}: APPLY_CNOT q0, q1
    oracle_h2_{iter}: APPLY_H q1
    
    ; Flip back
    .if target_state[1] == "0"
        oracle_unx1_{iter}: APPLY_X q1
    .endif
    .if target_state[0] == "0"
        oracle_unx0_{iter}: APPLY_X q0
    .endif
    
    ; === Diffusion Operator ===
    ; Apply H to all
    diff_h0_{iter}: APPLY_H q0
    diff_h1_{iter}: APPLY_H q1
    
    ; Apply X to all
    diff_x0_{iter}: APPLY_X q0
    diff_x1_{iter}: APPLY_X q1
    
    ; Controlled-Z
    diff_h_cz_{iter}: APPLY_H q1
    diff_cnot_{iter}: APPLY_CNOT q0, q1
    diff_h_cz2_{iter}: APPLY_H q1
    
    ; Apply X to all
    diff_x0_2_{iter}: APPLY_X q0
    diff_x1_2_{iter}: APPLY_X q1
    
    ; Apply H to all
    diff_h0_2_{iter}: APPLY_H q0
    diff_h1_2_{iter}: APPLY_H q1
.endfor

; Measure both qubits
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
