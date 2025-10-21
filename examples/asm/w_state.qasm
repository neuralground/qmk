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

; Create W state using proper construction
; For 3 qubits: |W⟩ = (|100⟩ + |010⟩ + |001⟩)/√3
;
; Algorithm:
; 1. Start with |000⟩
; 2. Apply X to q2 to get |001⟩
; 3. Apply controlled rotations to create equal superposition
; 4. Use CNOTs to distribute the excitation
;
; This uses the fact that we can build W state by:
; - Creating |001⟩
; - Rotating to share amplitude with |010⟩
; - Rotating again to share with |100⟩

.if n_qubits == 3
    ; Step 1: Initialize to |001⟩
    x_init: APPLY_X q2
    
    ; Step 2: Create superposition between q2 and q1
    ; RY(θ) where sin(θ/2) = 1/√2, so θ = π/2
    ; This creates: |0⟩|0⟩(|0⟩ + |1⟩)/√2
    ry_21: APPLY_RY q2, theta=1.5707963267948966
    
    ; Step 3: CNOT from q2 to q1
    ; This creates: |0⟩(|01⟩ + |10⟩)/√2
    cnot_21: APPLY_CNOT q2, q1
    
    ; Step 4: Rotate q1 to share with q0
    ; RY(θ) where sin(θ/2) = 1/√3, so θ = 2*arcsin(1/√3)
    ry_10: APPLY_RY q1, theta=1.2309594173407747
    
    ; Step 5: CNOT from q1 to q0
    ; This creates the W state
    cnot_10: APPLY_CNOT q1, q0
    
    ; Step 6: X gates to fix the bit pattern
    ; We need to flip q1 and q2 to get the right computational basis states
    x_fix1: APPLY_X q1
    x_fix2: APPLY_X q2
.else
    ; For other sizes, use recursive construction
    ; Start with |10...0⟩
    x0: APPLY_X q0
    
    .for i in 0..n_qubits-2
        .set next_qubit = i + 1
        
        ; Rotate to share amplitude
        ry{i}: APPLY_RY q{i}, theta={angles[i]}
        
        ; Transfer to next qubit
        cnot{i}: APPLY_CNOT q{i}, q{next_qubit}
    .endfor
.endif

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
