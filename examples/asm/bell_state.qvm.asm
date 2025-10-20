; Simple Bell State Circuit
; 
; Creates a maximally entangled Bell pair: |Φ+⟩ = (|00⟩ + |11⟩)/√2
;
; Circuit:
; q0: ─H─●─M
;         │
; q1: ───X─M
;
; This is the simplest example of quantum entanglement.
; After measurement, both qubits will always show the same value.

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate 2 qubits
alloc: ALLOC_LQ n=2, profile="logical:Surface(d=3)" -> q0, q1

; Create superposition on q0
h: APPLY_H q0

; Entangle q0 and q1
cnot: APPLY_CNOT q0, q1

; Measure both qubits
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
