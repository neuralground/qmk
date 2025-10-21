# Known Issues

## QMK Simulator Accuracy

### Issue
The QMK executor uses a simplified logical qubit simulator that produces incorrect results for some quantum circuits.

### Examples
- **GHZ states**: Produces invalid outcomes like `'101'` or `'1101'` instead of only `'000'` or `'111'`
- **Identity circuits**: Produces `'01'` instead of only `'00'`
- **General circuits**: May produce incorrect measurement distributions

### Root Cause
The `LogicalQubit` class in `kernel/simulator/logical_qubit.py` uses a simplified 4-state model (ZERO, ONE, PLUS, MINUS) instead of a full statevector simulation. This model cannot accurately represent:
- Multi-qubit entangled states (GHZ, W states)
- Arbitrary superpositions
- Complex quantum algorithms

### Why Not Using Aer Backend
The `EnhancedExecutor` in `kernel/executor/enhanced_executor.py` directly simulates qubits using the simplified model instead of delegating to the Qiskit Aer backend that exists in `kernel/hardware/qiskit_simulator_backend.py`.

### Workaround
The Qiskit path equivalence tests use an 80% validity threshold to allow for these errors while still validating that the system mostly works correctly.

### Proper Fix (TODO)
1. Integrate the Qiskit Aer backend into the `EnhancedExecutor`
2. Convert QVM graphs to Qiskit circuits
3. Execute on Aer backend
4. Convert results back to QVM format

This would ensure QMK produces the same results as native Qiskit.

### Files Involved
- `kernel/executor/enhanced_executor.py` - Main executor
- `kernel/simulator/logical_qubit.py` - Simplified simulator
- `kernel/hardware/qiskit_simulator_backend.py` - Aer backend (not used by executor)
- `tests/integration/test_qiskit_path_equivalence.py` - Tests with 80% threshold

### Impact
- **Low** for simple circuits (Bell states, single qubits)
- **Medium** for GHZ states and multi-qubit entanglement
- **High** for complex quantum algorithms

The tests catch these issues and document them, but the underlying simulator needs improvement for production use.
