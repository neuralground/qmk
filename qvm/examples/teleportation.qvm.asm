.version 0.1
.caps CAP_ALLOC

; Quantum teleportation protocol
; Teleports state of q0 to q2 using entangled pair (q1, q2)

; Allocate qubits
alloc: ALLOC_LQ n=3, profile="logical:surface_code(d=3)" -> q0, q1, q2 [CAP_ALLOC]

; Prepare state to teleport on q0 (example: |+⟩)
prep: APPLY_H q0

; Create Bell pair between q1 and q2
bell_h: APPLY_H q1
bell_cnot: APPLY_CNOT q1, q2

; Bell measurement on q0 and q1
cnot_meas: APPLY_CNOT q0, q1
h_meas: APPLY_H q0
m0: MEASURE_Z q0 -> m0
m1: MEASURE_Z q1 -> m1

; Conditional corrections on q2 based on measurement results
fence: FENCE_EPOCH
corr_x: APPLY_X q2 if m1==1
corr_z: APPLY_Z q2 if m0==1

; Verify teleportation
m2: MEASURE_Z q2 -> m2

; Cleanup
free: FREE_LQ q0, q1, q2
