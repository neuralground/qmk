; Multi-Round Adaptive Circuit: 3-Qubit Repetition Code
;
; Implements a 3-qubit repetition code with syndrome measurements
; and conditional corrections based on AND guards.
;
; Circuit structure:
; 1. Encode logical |0⟩ as |000⟩ (already in this state after allocation)
; 2. Syndrome extraction:
;    - Check d0 ⊕ d1 (parity of first two qubits)
;    - Check d1 ⊕ d2 (parity of last two qubits)
; 3. Conditional corrections based on syndrome pattern:
;    - s01=1, s12=0 → error on d0
;    - s01=1, s12=1 → error on d1
;    - s01=0, s12=1 → error on d2
; 4. Final measurements
;
; This demonstrates complex AND guards for quantum error correction.

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Allocate 3 data qubits + 2 ancilla qubits
alloc: ALLOC_LQ n=5, profile="logical:Surface(d=3)" -> d0, d1, d2, a0, a1

; === Optional: Inject Error for Testing ===
; Uncomment one of these to test error correction:
; inject_error_d0: APPLY_X d0  ; Error on first qubit
; inject_error_d1: APPLY_X d1  ; Error on middle qubit
; inject_error_d2: APPLY_X d2  ; Error on last qubit

; === Syndrome Extraction Round ===

; Check d0 ⊕ d1 (parity check between first two data qubits)
; For Z-basis repetition code, use CNOT with ancilla as target
cnot_d0_a0: APPLY_CNOT d0, a0
cnot_d1_a0: APPLY_CNOT d1, a0
syndrome_01: MEASURE_Z a0 -> s01

; Check d1 ⊕ d2 (parity check between last two data qubits)
; For Z-basis repetition code, use CNOT with ancilla as target
cnot_d1_a1: APPLY_CNOT d1, a1
cnot_d2_a1: APPLY_CNOT d2, a1
syndrome_12: MEASURE_Z a1 -> s12

; === Conditional Corrections ===

; If s01=1 AND s12=0: error on d0
correct_d0: APPLY_X d0 if s01==1 && s12==0

; If s01=1 AND s12=1: error on d1
correct_d1: APPLY_X d1 if s01==1 && s12==1

; If s01=0 AND s12=1: error on d2
correct_d2: APPLY_X d2 if s01==0 && s12==1

; === Final Measurements ===

m_d0: MEASURE_Z d0 -> m_d0
m_d1: MEASURE_Z d1 -> m_d1
m_d2: MEASURE_Z d2 -> m_d2
