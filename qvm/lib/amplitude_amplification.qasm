; Amplitude Amplification (Grover Operator)
;
; Implements one iteration of amplitude amplification, which boosts
; the amplitude of marked states. This is the core of Grover's search
; and can be used in many quantum algorithms.
;
; Algorithm:
; 1. Apply oracle (marks target states with phase flip)
; 2. Apply diffusion operator (inversion about average)
;
; The diffusion operator is: D = 2|ψ⟩⟨ψ| - I
; where |ψ⟩ is the uniform superposition
;
; Parameters:
;   n_qubits - Number of qubits
;   qubit_prefix - Prefix for qubits
;   oracle_type - Type of oracle (for documentation)
;
; Complexity: O(n) gates per iteration
; Iterations needed: O(√N) for N items
;
; Usage:
;   .set n_qubits = 3
;   .set qubit_prefix = "q"
;   .set oracle_type = "custom"
;   
;   ; Define oracle before including
;   ; oracle: marks target states
;   
;   .include "qvm/lib/amplitude_amplification.qasm"

.version 0.1

; Parameters (must be set before including)
; .param n_qubits = 3
; .param qubit_prefix = "q"
; .param oracle_type = "custom"

; === Oracle Phase ===
; The oracle must be defined by the caller before including this file
; It should mark target states with a phase flip
; Example:
;   oracle_x0: APPLY_X q0  ; Flip if target has q0=0
;   oracle_cz: APPLY_CZ q0, q1  ; Mark state
;   oracle_x0_restore: APPLY_X q0  ; Restore

; === Diffusion Operator ===
; Implements inversion about average: 2|ψ⟩⟨ψ| - I
; where |ψ⟩ = H^⊗n|0⟩ is uniform superposition

; Step 1: Apply H to all qubits (transform to computational basis)
.for i in 0..n_qubits-1
    amp_amp_h1_{i}: APPLY_H {qubit_prefix}_{i}
.endfor

; Step 2: Apply X to all qubits (flip to |111...1⟩)
.for i in 0..n_qubits-1
    amp_amp_x_{i}: APPLY_X {qubit_prefix}_{i}
.endfor

; Step 3: Multi-controlled Z gate (phase flip |111...1⟩)
; For n qubits, this requires a multi-controlled Z
; We implement this using a cascade of controls

.if n_qubits == 2
    ; For 2 qubits: CZ gate
    amp_amp_cz: APPLY_CZ {qubit_prefix}_0, {qubit_prefix}_1
.elif n_qubits == 3
    ; For 3 qubits: Toffoli + H + Toffoli + H
    amp_amp_h_target: APPLY_H {qubit_prefix}_2
    amp_amp_toffoli: APPLY_TOFFOLI {qubit_prefix}_0, {qubit_prefix}_1, {qubit_prefix}_2
    amp_amp_h_target_restore: APPLY_H {qubit_prefix}_2
.else
    ; For n > 3: Use general multi-controlled Z
    ; (Would require ancilla qubits for efficient implementation)
    ; Here we show the structure for n=4 as example
    
    ; Decompose into Toffoli gates with ancilla
    ; This is a simplified placeholder
    .for i in 0..n_qubits-2
        amp_amp_multi_ctrl_{i}: APPLY_CNOT {qubit_prefix}_{i}, {qubit_prefix}_{i+1}
    .endfor
.endif

; Step 4: Apply X to all qubits (restore)
.for i in 0..n_qubits-1
    amp_amp_x_restore_{i}: APPLY_X {qubit_prefix}_{i}
.endfor

; Step 5: Apply H to all qubits (transform back to superposition)
.for i in 0..n_qubits-1
    amp_amp_h2_{i}: APPLY_H {qubit_prefix}_{i}
.endfor

; Amplitude amplification iteration complete!
; Repeat this (oracle + diffusion) for O(√N) iterations
; to maximize probability of measuring target state
