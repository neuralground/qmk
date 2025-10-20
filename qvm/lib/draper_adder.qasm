; Draper Quantum Adder
;
; QFT-based quantum adder that adds two n-bit numbers.
; Uses the Draper addition algorithm which leverages the QFT.
;
; Algorithm:
; 1. Apply QFT to register b
; 2. Apply controlled phase rotations based on register a
; 3. Apply inverse QFT to register b
; Result: b = a + b (mod 2^n)
;
; Parameters:
;   n_bits - Number of bits in each register
;   a_prefix - Prefix for register a qubits (e.g., "a" for a0, a1, ...)
;   b_prefix - Prefix for register b qubits (e.g., "b" for b0, b1, ...)
;
; Complexity: O(n²) gates
; Space: 2n qubits (no ancilla needed)
;
; Usage:
;   .set n_bits = 4
;   .set a_prefix = "a"
;   .set b_prefix = "b"
;   .include "qvm/lib/draper_adder.qasm"

.version 0.1

; Parameters (must be set before including)
; .param n_bits = 4
; .param a_prefix = "a"
; .param b_prefix = "b"

; === Phase 1: Apply QFT to register b ===
.for i in 0..n_bits-1
    ; Hadamard on b_i
    draper_qft_h_{i}: APPLY_H {b_prefix}_{i}
    
    ; Controlled phase rotations
    .for j in i+1..n_bits-1
        .set k = j - i + 1
        .set angle = 3.14159265359 / (2 ** (k - 1))
        
        ; Controlled-RZ from b_j to b_i
        draper_qft_rz1_{i}_{j}: APPLY_RZ {b_prefix}_{i}, theta={angle}/2
        draper_qft_cnot1_{i}_{j}: APPLY_CNOT {b_prefix}_{j}, {b_prefix}_{i}
        draper_qft_rz2_{i}_{j}: APPLY_RZ {b_prefix}_{i}, theta=-{angle}/2
        draper_qft_cnot2_{i}_{j}: APPLY_CNOT {b_prefix}_{j}, {b_prefix}_{i}
    .endfor
.endfor

; === Phase 2: Add register a to register b (in Fourier space) ===
; For each bit in a, apply controlled phase rotations to b
.for i in 0..n_bits-1
    .for j in 0..n_bits-1-i
        ; Phase rotation angle depends on bit positions
        .set k = j + 1
        .set angle = 3.14159265359 / (2 ** k)
        
        ; Controlled phase rotation: if a_i is |1⟩, rotate b_{i+j}
        draper_add_rz1_{i}_{j}: APPLY_RZ {b_prefix}_{i+j}, theta={angle}/2
        draper_add_cnot1_{i}_{j}: APPLY_CNOT {a_prefix}_{i}, {b_prefix}_{i+j}
        draper_add_rz2_{i}_{j}: APPLY_RZ {b_prefix}_{i+j}, theta=-{angle}/2
        draper_add_cnot2_{i}_{j}: APPLY_CNOT {a_prefix}_{i}, {b_prefix}_{i+j}
    .endfor
.endfor

; === Phase 3: Apply inverse QFT to register b ===
; Swap qubits first (QFT reverses order)
.set n_swaps = n_bits / 2
.for i in 0..n_swaps-1
    .set j = n_bits - 1 - i
    
    draper_iqft_swap_{i}_{j}_cnot1: APPLY_CNOT {b_prefix}_{i}, {b_prefix}_{j}
    draper_iqft_swap_{i}_{j}_cnot2: APPLY_CNOT {b_prefix}_{j}, {b_prefix}_{i}
    draper_iqft_swap_{i}_{j}_cnot3: APPLY_CNOT {b_prefix}_{i}, {b_prefix}_{j}
.endfor

; Inverse QFT (reverse order of QFT)
.for i_rev in 0..n_bits-1
    .set i = n_bits - 1 - i_rev
    
    ; Inverse controlled rotations
    .for j_rev in 0..i-1
        .set j = i - 1 - j_rev
        .set k = i - j + 1
        .set angle = -3.14159265359 / (2 ** (k - 1))
        
        draper_iqft_rz1_{i}_{j}: APPLY_RZ {b_prefix}_{i}, theta={angle}/2
        draper_iqft_cnot1_{i}_{j}: APPLY_CNOT {b_prefix}_{j}, {b_prefix}_{i}
        draper_iqft_rz2_{i}_{j}: APPLY_RZ {b_prefix}_{i}, theta=-{angle}/2
        draper_iqft_cnot2_{i}_{j}: APPLY_CNOT {b_prefix}_{j}, {b_prefix}_{i}
    .endfor
    
    ; Hadamard
    draper_iqft_h_{i}: APPLY_H {b_prefix}_{i}
.endfor

; Addition complete: register b now contains a + b (mod 2^n)
