# Example Update Plan - Convert to ASM Format

## Why ASM Format?
- **Concise**: Much shorter than JSON
- **Readable**: Easy to understand circuit structure
- **Commentable**: Can add inline comments
- **Maintainable**: Easier to modify and debug
- **Abstraction**: Hides JSON representation details

## Examples to Update

### ✅ Already Using QVM Files
- `simple_bell_state.py` - Uses `bell_teleport_cnot.qvm.json`

### ✅ Already Updated
- `vqe_ansatz.py` - Now uses ASM format

### 🔧 Need ASM Conversion

#### Simple (No Guards)
1. `multi_qubit_entanglement.py` - GHZ state
2. `deutsch_jozsa.py` - DJ algorithm
3. `grovers_algorithm.py` - Grover's search
4. `shors_algorithm.py` - Shor's factoring
5. `benchmark.py` - Performance testing

#### Complex (With Guards/Conditionals)
6. `adaptive_circuit.py` - Mid-circuit measurements with guards

### 📦 Framework-Specific (Keep As-Is)
- `qiskit_algorithms.py` - Uses Qiskit
- `cirq_algorithms.py` - Uses Cirq
- `qsharp_algorithms.py` - Uses Q#
- `azure_qre_example.py` - Azure integration

### 🔬 Advanced Demos (Review Later)
- `advanced_qec_demo.py`
- `architecture_exploration.py`
- `compare_execution_paths.py`
- `distributed_execution_demo.py`
- `hardware_adapters_demo.py`
- `jit_adaptivity_demo.py`
- `measurement_bases_demo.py`
- `qir_bridge_demo.py`
- `reversibility_demo.py`

## Update Strategy

For each example:
1. Convert graph creation to ASM format
2. Add proper capabilities (CAP_ALLOC, CAP_COMPUTE, CAP_MEASURE)
3. Remove FREE_LQ after measurements (linearity)
4. Add comments explaining circuit structure
5. Test execution

## ASM Template

```python
from qvm.tools.qvm_asm import assemble

def create_circuit() -> dict:
    asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

; Circuit description
; Visual diagram

alloc: ALLOC_LQ n=X, profile="logical:Surface(d=3)" -> q0, q1, ... [CAP_ALLOC]
; ... operations ...
m0: MEASURE_Z q0 -> m0
"""
    return assemble(asm)
```
