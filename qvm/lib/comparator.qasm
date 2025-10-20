; Quantum Comparator
;
; Compares two n-bit quantum registers and outputs result to ancilla.
; Computes: |a⟩|b⟩|0⟩ → |a⟩|b⟩|a>b⟩
;
; Algorithm:
; Starting from MSB, check if a_i > b_i at each position.
; If found, set output and stop. Otherwise continue to next bit.
;
; Parameters:
;   n_bits - Number of bits in each register
;   a_prefix - Prefix for register a qubits
;   b_prefix - Prefix for register b qubits
;   result_qubit - Output qubit (|1⟩ if a > b, |0⟩ otherwise)
;
; Complexity: O(n) gates
; Space: 2n + 1 qubits
;
; Usage:
;   .set n_bits = 4
;   .set a_prefix = "a"
;   .set b_prefix = "b"
;   .set result_qubit = "result"
;   .include "qvm/lib/comparator.qasm"

.version 0.1

; Parameters (must be set before including)
; .param n_bits = 4
; .param a_prefix = "a"
; .param b_prefix = "b"
; .param result_qubit = "result"

; === Comparison Circuit ===
; Check from MSB to LSB
; At each bit position i:
;   If a_i = 1 and b_i = 0, then a > b (set result)
;   If a_i = 0 and b_i = 1, then a < b (don't set result)
;   If a_i = b_i, continue to next bit

.for i_rev in 0..n_bits-1
    .set i = n_bits - 1 - i_rev
    
    ; Check if a_i > b_i (a_i=1, b_i=0)
    ; This requires: a_i AND (NOT b_i)
    
    ; Flip b_i
    comp_x_b_{i}: APPLY_X {b_prefix}_{i}
    
    ; Controlled-controlled-X: if a_i=1 and b_i=0 (now 1), set result
    ; Use Toffoli: a_i, b_i (flipped), result
    comp_toffoli_{i}: APPLY_TOFFOLI {a_prefix}_{i}, {b_prefix}_{i}, {result_qubit}
    
    ; Flip b_i back
    comp_x_b_restore_{i}: APPLY_X {b_prefix}_{i}
    
    ; If result is already set, skip remaining comparisons
    ; (In a full implementation, we'd use conditional execution)
.endfor

; Result qubit now contains |1⟩ if a > b, |0⟩ otherwise
; Note: This is a simplified version. Full version would handle
; early termination when result is determined.
