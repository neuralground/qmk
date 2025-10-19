.version 0.1
.caps CAP_ALLOC

; Simple Bell state preparation
; Creates maximally entangled pair |Φ+⟩ = (|00⟩ + |11⟩)/√2

alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> qA, qB [CAP_ALLOC]
h: APPLY_H qA
cnot: APPLY_CNOT qA, qB
mA: MEASURE_Z qA -> mA
mB: MEASURE_Z qB -> mB
free: FREE_LQ qA, qB
