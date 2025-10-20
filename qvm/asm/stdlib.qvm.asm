; QVM Assembly Standard Library
; Common quantum circuit patterns and macros

; ============================================================================
; Basic Two-Qubit Gates
; ============================================================================

.macro BELL_PAIR(q0, q1)
    ; Create Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2
    h: APPLY_H {q0}
    cnot: APPLY_CNOT {q0}, {q1}
.endmacro

.macro SWAP(q0, q1)
    ; SWAP two qubits using 3 CNOTs
    cnot1: APPLY_CNOT {q0}, {q1}
    cnot2: APPLY_CNOT {q1}, {q0}
    cnot3: APPLY_CNOT {q0}, {q1}
.endmacro

; ============================================================================
; Multi-Qubit Entanglement
; ============================================================================

.macro GHZ_STATE(qubits)
    ; Create GHZ state: |GHZ⟩ = (|00...0⟩ + |11...1⟩)/√2
    ; Args: qubits - list of qubit names
    h0: APPLY_H {qubits[0]}
    .for i in 1..len(qubits)-1
        cnot{i}: APPLY_CNOT {qubits[0]}, {qubits[i]}
    .endfor
.endmacro

; ============================================================================
; Quantum Fourier Transform
; ============================================================================

.macro QFT(qubits)
    ; Quantum Fourier Transform
    ; Args: qubits - list of qubit names
    .set n = len(qubits)
    
    .for i in 0..n-1
        h{i}: APPLY_H {qubits[i]}
        
        ; Controlled rotations
        .for j in i+1..n-1
            .set angle = pi / (2 ** (j - i))
            ; Controlled-RZ decomposition
            cr{i}_{j}_rz1: APPLY_RZ {qubits[j]}, theta={angle/2}
            cr{i}_{j}_cnot1: APPLY_CNOT {qubits[i]}, {qubits[j]}
            cr{i}_{j}_rz2: APPLY_RZ {qubits[j]}, theta={-angle/2}
            cr{i}_{j}_cnot2: APPLY_CNOT {qubits[i]}, {qubits[j]}
        .endfor
    .endfor
    
    ; Reverse qubit order with SWAPs
    .for i in 0..n//2-1
        .set j = n - 1 - i
        SWAP({qubits[i]}, {qubits[j]})
    .endfor
.endmacro

; ============================================================================
; Grover's Algorithm Components
; ============================================================================

.macro GROVER_ORACLE(target, qubits)
    ; Oracle that marks target state
    ; Args: target - binary string, qubits - list of qubit names
    
    ; Flip bits that should be 0
    .for i in 0..len(target)-1
        .if target[i] == '0'
            flip{i}: APPLY_X {qubits[i]}
        .endif
    .endfor
    
    ; Controlled-Z (mark the state)
    .set last = len(qubits) - 1
    h_cz: APPLY_H {qubits[last]}
    cnot_cz: APPLY_CNOT {qubits[0]}, {qubits[last]}
    h_cz2: APPLY_H {qubits[last]}
    
    ; Flip back
    .for i in 0..len(target)-1
        .if target[i] == '0'
            unflip{i}: APPLY_X {qubits[i]}
        .endif
    .endfor
.endmacro

.macro GROVER_DIFFUSION(qubits)
    ; Diffusion operator (inversion about average)
    ; Args: qubits - list of qubit names
    
    ; Apply H to all
    .for i in 0..len(qubits)-1
        dh{i}_1: APPLY_H {qubits[i]}
    .endfor
    
    ; Apply X to all
    .for i in 0..len(qubits)-1
        dx{i}_1: APPLY_X {qubits[i]}
    .endfor
    
    ; Controlled-Z
    .set last = len(qubits) - 1
    dh_cz: APPLY_H {qubits[last]}
    dcnot: APPLY_CNOT {qubits[0]}, {qubits[last]}
    dh_cz2: APPLY_H {qubits[last]}
    
    ; Apply X to all
    .for i in 0..len(qubits)-1
        dx{i}_2: APPLY_X {qubits[i]}
    .endfor
    
    ; Apply H to all
    .for i in 0..len(qubits)-1
        dh{i}_2: APPLY_H {qubits[i]}
    .endfor
.endmacro

; ============================================================================
; Deutsch-Jozsa Algorithm Components
; ============================================================================

.macro DJ_ORACLE_CONSTANT_0(qubits)
    ; Constant oracle: f(x) = 0 for all x
    ; Identity - do nothing
.endmacro

.macro DJ_ORACLE_CONSTANT_1(y)
    ; Constant oracle: f(x) = 1 for all x
    ; Flip output qubit
    oracle_x: APPLY_X {y}
.endmacro

.macro DJ_ORACLE_BALANCED_BIT(control, target, bit_index)
    ; Balanced oracle: f(x) = x[bit_index]
    oracle_cnot: APPLY_CNOT {control}, {target}
.endmacro

; ============================================================================
; Utility Macros
; ============================================================================

.macro SUPERPOSITION(qubits)
    ; Put all qubits in equal superposition
    .for i in 0..len(qubits)-1
        h{i}: APPLY_H {qubits[i]}
    .endfor
.endmacro

.macro MEASURE_ALL(qubits)
    ; Measure all qubits in Z basis
    .for i in 0..len(qubits)-1
        m{i}: MEASURE_Z {qubits[i]} -> m{i}
    .endfor
.endmacro

.macro ALLOC_QUBITS(n, prefix, profile)
    ; Allocate n qubits with given prefix
    .set qubit_list = ["{prefix}{i}" for i in 0..n-1]
    alloc: ALLOC_LQ n={n}, profile={profile} -> {", ".join(qubit_list)}
.endmacro
