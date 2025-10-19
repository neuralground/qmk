.version 0.1
.caps CAP_ALLOC

; 3-qubit GHZ state
; |GHZ⟩ = (|000⟩ + |111⟩)/√2

alloc: ALLOC_LQ n=3, profile="logical:surface_code(d=5)" -> q0, q1, q2 [CAP_ALLOC]
h: APPLY_H q0
cnot1: APPLY_CNOT q0, q1
cnot2: APPLY_CNOT q0, q2
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1
m2: MEASURE_Z q2 -> m2
free: FREE_LQ q0, q1, q2
