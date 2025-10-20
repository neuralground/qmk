; Cuccaro Quantum Adder
;
; Ripple-carry quantum adder with no ancilla qubits.
; Implements in-place addition: |a⟩|b⟩|c⟩ → |a⟩|a+b⟩|c'⟩
;
; Based on: Cuccaro et al., "A new quantum ripple-carry addition circuit"
; arXiv:quant-ph/0410184
;
; Parameters:
;   n_bits - Number of bits in each register
;   a_prefix - Prefix for register a qubits (input, preserved)
;   b_prefix - Prefix for register b qubits (input/output: becomes a+b)
;   carry_qubit - Name of carry qubit (input/output carry)
;
; Complexity: O(n) gates
; Space: 2n + 1 qubits (one carry qubit)
;
; Usage:
;   .set n_bits = 4
;   .set a_prefix = "a"
;   .set b_prefix = "b"
;   .set carry_qubit = "c"
;   .include "qvm/lib/cuccaro_adder.qasm"

.version 0.1

; Parameters (must be set before including)
; .param n_bits = 4
; .param a_prefix = "a"
; .param b_prefix = "b"
; .param carry_qubit = "c"

; === Majority Gate ===
; MAJ(c, b, a) transforms |c⟩|b⟩|a⟩ → |c⟩|c⊕b⟩|carry⟩
; where carry = (a∧b) ⊕ (a∧c) ⊕ (b∧c) = majority(a,b,c)

.macro MAJ(c, b, a)
    maj_cnot1: APPLY_CNOT {a}, {b}
    maj_cnot2: APPLY_CNOT {a}, {c}
    maj_toffoli: APPLY_TOFFOLI {c}, {b}, {a}
.endmacro

; === Unmajority-Add Gate ===
; UMA(c, b, a) transforms |c⟩|c⊕b⟩|carry⟩ → |c⟩|sum⟩|a⟩
; where sum = c ⊕ b ⊕ a

.macro UMA(c, b, a)
    uma_toffoli: APPLY_TOFFOLI {c}, {b}, {a}
    uma_cnot1: APPLY_CNOT {a}, {c}
    uma_cnot2: APPLY_CNOT {c}, {b}
.endmacro

; === Forward Ripple (Compute Carries) ===
; Apply MAJ gates from LSB to MSB

; First MAJ with carry input
MAJ({carry_qubit}, {b_prefix}_0, {a_prefix}_0)

; Ripple through remaining bits
.for i in 1..n_bits-1
    MAJ({a_prefix}_{i-1}, {b_prefix}_{i}, {a_prefix}_{i})
.endfor

; === Final Carry ===
; The MSB of a now contains the output carry
; Copy to carry qubit
cuccaro_final_cnot: APPLY_CNOT {a_prefix}_{n_bits-1}, {carry_qubit}

; === Backward Ripple (Compute Sums and Restore a) ===
; Apply UMA gates from MSB to LSB

.for i_rev in 1..n_bits-1
    .set i = n_bits - i_rev
    UMA({a_prefix}_{i-1}, {b_prefix}_{i}, {a_prefix}_{i})
.endfor

; Last UMA
UMA({carry_qubit}, {b_prefix}_0, {a_prefix}_0)

; Addition complete:
; - Register a is restored to original value
; - Register b contains a + b (mod 2^n)
; - Carry qubit contains the carry-out bit
