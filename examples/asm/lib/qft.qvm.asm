; Quantum Fourier Transform (QFT) Library
;
; Implements the full QFT with controlled phase rotations.
; The QFT is a key component in many quantum algorithms including
; Shor's algorithm, phase estimation, and quantum simulation.
;
; QFT transforms |x⟩ → (1/√N) Σ exp(2πixy/N)|y⟩
;
; Parameters:
;   n_qubits - Number of qubits to transform
;   qubit_prefix - Prefix for qubit names (e.g., "q" for q0, q1, q2...)
;
; Usage:
;   .include "lib/qft.qvm.asm"
;   .set n_qubits = 4
;   .set qubit_prefix = "count"
;
; This will generate QFT on count_0, count_1, count_2, count_3

.version 0.1

; Parameters (must be set before including)
; .param n_qubits = 4
; .param qubit_prefix = "q"

; === QFT Implementation ===
; For each qubit i from 0 to n-1:
;   1. Apply Hadamard to qubit i
;   2. Apply controlled phase rotations from qubits j > i
;
; Phase rotation: R_k = diag(1, exp(2πi/2^k))

.for i in 0..n_qubits-1
    ; Hadamard on qubit i
    qft_h_{i}: APPLY_H {qubit_prefix}_{i}
    
    ; Controlled phase rotations
    .for j in i+1..n_qubits-1
        ; R_k where k = j - i + 1
        ; Implemented as: RZ(π/2^(k-1)) controlled by qubit j
        .set k = j - i + 1
        .set angle = 3.14159265359 / (2 ** (k - 1))
        
        ; Controlled-RZ decomposition:
        ; Control qubit: {qubit_prefix}_{j}
        ; Target qubit: {qubit_prefix}_{i}
        
        ; RZ(θ/2) on target
        qft_cr_{i}_{j}_rz1: APPLY_RZ {qubit_prefix}_{i}, theta={angle}/2
        
        ; CNOT (control → target)
        qft_cr_{i}_{j}_cnot1: APPLY_CNOT {qubit_prefix}_{j}, {qubit_prefix}_{i}
        
        ; RZ(-θ/2) on target
        qft_cr_{i}_{j}_rz2: APPLY_RZ {qubit_prefix}_{i}, theta=-{angle}/2
        
        ; CNOT (control → target)
        qft_cr_{i}_{j}_cnot2: APPLY_CNOT {qubit_prefix}_{j}, {qubit_prefix}_{i}
    .endfor
.endfor

; === Swap qubits to reverse order ===
; QFT naturally produces output in reversed order
; Swap qubit i with qubit (n-1-i) for i < n/2

.set n_swaps = n_qubits / 2
.for i in 0..n_swaps-1
    .set j = n_qubits - 1 - i
    
    ; SWAP using 3 CNOTs
    qft_swap_{i}_{j}_cnot1: APPLY_CNOT {qubit_prefix}_{i}, {qubit_prefix}_{j}
    qft_swap_{i}_{j}_cnot2: APPLY_CNOT {qubit_prefix}_{j}, {qubit_prefix}_{i}
    qft_swap_{i}_{j}_cnot3: APPLY_CNOT {qubit_prefix}_{i}, {qubit_prefix}_{j}
.endfor

; QFT complete!
; Output qubits are now in Fourier basis
