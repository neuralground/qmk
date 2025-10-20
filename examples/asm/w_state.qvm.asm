; W State Generation
; Creates |W⟩ = (|100...0⟩ + |010...0⟩ + ... + |00...01⟩)/√n
;
; Parameters (set via Python):
;   n_qubits - number of qubits

.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Generate qubit list
.set qubit_list = [f"q{i}" for i in range(n_qubits)]

; Allocate qubits
alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> {", ".join(qubit_list)}

; Create W state (simplified construction)
; Initialize first qubit to |1⟩
x0: APPLY_X q0

; Distribute excitation across all qubits
.for i in 0..n_qubits-2
    .set angle = 2 * math.asin(1 / math.sqrt(n_qubits - i))
    ry{i}: APPLY_RY q{i}, theta={angle}
    cnot{i}: APPLY_CNOT q{i}, q{i+1}
.endfor

; Measure all qubits
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
