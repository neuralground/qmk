; Grover Oracle Templates
;
; Provides templates for creating oracles for Grover's search algorithm.
; An oracle marks the target state(s) by flipping their phase.
;
; Oracle types:
; 1. Single state oracle - marks one specific state
; 2. Multiple state oracle - marks several states
; 3. Function oracle - marks states satisfying a condition
;
; Parameters:
;   n_qubits - Number of qubits
;   qubit_prefix - Prefix for qubits
;   target_state - Binary string of target state (e.g., "101")
;   oracle_mode - "single", "multi", or "function"
;
; Usage:
;   .set n_qubits = 3
;   .set qubit_prefix = "q"
;   .set target_state = "101"
;   .set oracle_mode = "single"
;   .include "qvm/lib/grover_oracle.qasm"

.version 0.1

; Parameters (must be set before including)
; .param n_qubits = 3
; .param qubit_prefix = "q"
; .param target_state = "101"
; .param oracle_mode = "single"

; === Single State Oracle ===
; Marks one specific target state
;
; Algorithm:
; 1. Flip qubits where target has 0
; 2. Apply multi-controlled Z
; 3. Flip qubits back

.if oracle_mode == "single"
    ; Step 1: Flip qubits where target_state has '0'
    .for i in 0..n_qubits-1
        .if target_state[i] == '0'
            oracle_flip_{i}: APPLY_X {qubit_prefix}_{i}
        .endif
    .endfor
    
    ; Step 2: Multi-controlled Z (marks |111...1⟩)
    ; For different qubit counts, use appropriate gates
    
    .if n_qubits == 2
        oracle_cz: APPLY_CZ {qubit_prefix}_0, {qubit_prefix}_1
    .elif n_qubits == 3
        ; Use Toffoli with H gates to create CCZ
        oracle_h: APPLY_H {qubit_prefix}_2
        oracle_toffoli: APPLY_TOFFOLI {qubit_prefix}_0, {qubit_prefix}_1, {qubit_prefix}_2
        oracle_h_restore: APPLY_H {qubit_prefix}_2
    .else
        ; For n > 3, use cascaded controls (simplified)
        .for i in 0..n_qubits-2
            oracle_cascade_{i}: APPLY_CNOT {qubit_prefix}_{i}, {qubit_prefix}_{i+1}
        .endfor
        oracle_final_z: APPLY_Z {qubit_prefix}_{n_qubits-1}
        .for i_rev in 0..n_qubits-2
            .set i = n_qubits - 2 - i_rev
            oracle_cascade_restore_{i}: APPLY_CNOT {qubit_prefix}_{i}, {qubit_prefix}_{i+1}
        .endfor
    .endif
    
    ; Step 3: Flip qubits back
    .for i in 0..n_qubits-1
        .if target_state[i] == '0'
            oracle_flip_restore_{i}: APPLY_X {qubit_prefix}_{i}
        .endif
    .endfor

.elif oracle_mode == "multi"
    ; Multiple state oracle
    ; Marks several target states
    ; (Would require multiple single-state oracles)
    ; This is a framework - caller provides specific states
    
    ; Example: Mark states "101" and "110"
    ; Apply single-state oracle for each target
    
.elif oracle_mode == "function"
    ; Function oracle
    ; Marks states satisfying a boolean function
    ; (Requires function-specific implementation)
    
    ; Example: Mark all states with even parity
    ; This would check XOR of all qubits
    
.endif

; Oracle complete!
; Target state(s) now have phase flipped
