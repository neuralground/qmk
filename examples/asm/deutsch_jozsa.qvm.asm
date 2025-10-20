; Deutsch-Jozsa Algorithm
; Determines if a function is constant or balanced
;
; Parameters:
;   oracle_type - Type of oracle function (can be overridden from Python)
;     - "constant_0": f(x) = 0 for all x
;     - "constant_1": f(x) = 1 for all x
;     - "balanced_x0": f(x) = x0
;     - "balanced_x1": f(x) = x1
;     - "balanced_xor": f(x) = x0 ⊕ x1

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Parameter with default value
.param oracle_type = "balanced_x0"

; Deutsch-Jozsa for 2-bit function
; Input qubits: x0, x1
; Output qubit: y

alloc: ALLOC_LQ n=3, profile="logical:Surface(d=3)" -> x0, x1, y

; Initialize output qubit to |1⟩
x_init: APPLY_X y

; Apply Hadamard to all qubits
h_x0: APPLY_H x0
h_x1: APPLY_H x1
h_y: APPLY_H y

; === Oracle (selected via .elif chain) ===
.if oracle_type == "constant_0"
    ; Oracle: f(x) = 0 for all x (identity - do nothing)
.elif oracle_type == "constant_1"
    ; Oracle: f(x) = 1 for all x (flip output)
    oracle_x: APPLY_X y
.elif oracle_type == "balanced_x0"
    ; Oracle: f(x) = x0
    oracle_cnot: APPLY_CNOT x0, y
.elif oracle_type == "balanced_x1"
    ; Oracle: f(x) = x1
    oracle_cnot: APPLY_CNOT x1, y
.elif oracle_type == "balanced_xor"
    ; Oracle: f(x) = x0 ⊕ x1
    oracle_cnot0: APPLY_CNOT x0, y
    oracle_cnot1: APPLY_CNOT x1, y
.endif

; Apply Hadamard to input qubits
h_x0_final: APPLY_H x0
h_x1_final: APPLY_H x1

; Measure input qubits
m0: MEASURE_Z x0 -> m0
m1: MEASURE_Z x1 -> m1
m_y: MEASURE_Z y -> m_y
