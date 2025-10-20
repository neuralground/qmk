; Measurement in Different Bases
;
; Demonstrates measuring a qubit in X, Y, or Z basis.
; The basis is selected via parameter and appropriate rotations are applied.
;
; Parameters:
;   basis - Measurement basis: "X", "Y", or "Z" (default "Z")

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Parameter with default value
.param basis = "Z"

; Allocate single qubit
alloc: ALLOC_LQ n=1, profile="logical:Surface(d=3)" -> q0

; Prepare |+⟩ state
h_prep: APPLY_H q0

; === Basis Rotation Before Measurement ===
.if basis == "X"
    ; X basis: rotate from Z to X
    h_before: APPLY_H q0
.elif basis == "Y"
    ; Y basis: rotate from Z to Y
    sdg: APPLY_SDG q0
    h_before: APPLY_H q0
.endif
; Z basis: no rotation needed

; Measure in Z basis (hardware always measures in Z)
measure: MEASURE_Z q0 -> result

; === Basis Rotation After Measurement (if needed) ===
.if basis == "X"
    ; Rotate back from X to Z
    h_after: APPLY_H q0
.elif basis == "Y"
    ; Rotate back from Y to Z
    h_after: APPLY_H q0
    s: APPLY_S q0
.endif
