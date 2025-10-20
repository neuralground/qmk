; VQE Ansatz Circuit
; Variational Quantum Eigensolver ansatz with parameterized rotations
;
; Parameters (set via Python):
;   theta1, theta2, theta3 - rotation angles

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; VQE ansatz with θ=({theta1:.3f}, {theta2:.3f}, {theta3:.3f})
; Circuit: q0: ─H─Rz(θ1)─●─Rz(θ3)─M
;                        │
;         q1: ─H─Rz(θ2)─X────────M

alloc: ALLOC_LQ n=2, profile="logical:Surface(d=3)" -> q0, q1

; Initialize in superposition
h0: APPLY_H q0
h1: APPLY_H q1

; Parameterized rotations
rz0: APPLY_RZ q0, theta={theta1}
rz1: APPLY_RZ q1, theta={theta2}

; Entanglement
cnot: APPLY_CNOT q0, q1

; Final rotation
rz2: APPLY_RZ q0, theta={theta3}

; Measurements
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
