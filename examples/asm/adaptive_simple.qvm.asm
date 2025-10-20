; Simple Adaptive Circuit with Conditional Correction
; 
; Circuit flow:
; 1. Prepare |+⟩ state on q0
; 2. Create entanglement with q1
; 3. Measure q1 (syndrome measurement)
; 4. Conditionally apply correction to q0 based on measurement
; 5. Final measurement of q0

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate qubits
alloc: ALLOC_LQ n=2, profile="logical:Surface(d=3)" -> q0, q1

; Prepare |+⟩ states
h0: APPLY_H q0
h1: APPLY_H q1

; Entangle for syndrome extraction
cnot1: APPLY_CNOT q0, q1

; Syndrome measurement (mid-circuit)
syndrome: MEASURE_Z q1 -> syndrome_bit

; Conditional correction: Apply X to q0 if syndrome_bit == 1
; Note: Guards are handled by the runtime, we just mark the dependency
correction: APPLY_X q0 [syndrome_bit == 1]

; Additional operation
h2: APPLY_H q0

; Final measurement
final_measure: MEASURE_Z q0 -> result
