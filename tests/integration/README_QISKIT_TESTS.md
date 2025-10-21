# Qiskit Path Equivalence Tests

Automated tests that verify Qiskit circuits produce equivalent results through both execution paths.

## What Gets Tested

### Execution Paths
1. **Native Qiskit Aer** - Direct execution
2. **QMK Stack** - Qiskit → QIR → Optimizer → QVM → QMK (with Aer backend)

### Test Circuits
- ✅ Bell State (2 qubits)
- ✅ GHZ State (3 and 4 qubits)
- ✅ Single Qubit Superposition
- ✅ Deterministic X Gate
- ✅ Deterministic Identity
- ✅ CNOT Gate
- ✅ Multiple Hadamards
- ✅ 2-Qubit Grover Search

### Verification
For each circuit, tests verify:
1. **Correctness** - QMK outcomes are valid (subset of native outcomes)
2. **Determinism** - Deterministic circuits produce expected single outcome
3. **Probability** - Probabilistic circuits produce expected outcome set

## Running Tests

### Prerequisites
```bash
# Install Qiskit
pip install qiskit qiskit-aer

# Start QMK server (in separate terminal)
python -m kernel.qmk_server
```

### Run Tests
```bash
# Run all Qiskit equivalence tests
python run_qiskit_tests.py

# Or run directly
python tests/integration/test_qiskit_path_equivalence.py

# Or with pytest
pytest tests/integration/test_qiskit_path_equivalence.py -v
```

## Test Output

```
======================================================================
Qiskit Path Equivalence Tests
======================================================================

✅ Qiskit available

These tests verify that Qiskit circuits produce equivalent
results through both execution paths:
  1. Native Qiskit Aer simulator
  2. Qiskit → QIR → Optimizer → QVM → QMK

----------------------------------------------------------------------

test_bell_state ... ok
test_ghz_3qubit ... ok
test_ghz_4qubit ... ok
test_superposition_single_qubit ... ok
test_deterministic_x_gate ... ok
test_deterministic_identity ... ok
test_cnot_gate ... ok
test_multiple_hadamards ... ok
test_grover_2qubit ... ok

----------------------------------------------------------------------
Ran 9 tests in 2.345s

OK

======================================================================
✅ ALL QISKIT EQUIVALENCE TESTS PASSED

Both execution paths produce equivalent results!
```

## CI/CD Integration

### GitHub Actions
Tests run automatically on:
- Every push to main
- Every pull request
- Manual trigger via workflow_dispatch

Workflow: `.github/workflows/qiskit_tests.yml`

### Test Matrix
- Python 3.10, 3.11, 3.12
- Installs Qiskit automatically
- Starts QMK server
- Runs equivalence tests
- Reports results

## What Each Test Verifies

### test_bell_state
- Creates Bell state: (|00⟩ + |11⟩)/√2
- Verifies both paths produce only 00 or 11
- Checks QMK results are subset of native results

### test_ghz_3qubit / test_ghz_4qubit
- Creates GHZ state: (|000...⟩ + |111...⟩)/√2
- Verifies only all-0s or all-1s outcomes
- Tests multi-qubit entanglement

### test_superposition_single_qubit
- Creates |+⟩ state with Hadamard
- Verifies both 0 and 1 outcomes possible
- Tests basic superposition

### test_deterministic_x_gate
- Applies X gate to |0⟩
- Verifies always produces |1⟩
- Tests deterministic operations

### test_deterministic_identity
- No gates, just measurement
- Verifies always produces |00⟩
- Tests baseline operation

### test_cnot_gate
- Tests CNOT with control in |1⟩
- Verifies target flips correctly
- Tests two-qubit gates

### test_multiple_hadamards
- Applies H to multiple qubits
- Verifies all outcomes possible
- Tests independent superpositions

### test_grover_2qubit
- Implements Grover search for |11⟩
- Verifies amplitude amplification
- Tests quantum algorithm

## Implementation Details

### Qiskit to QVM Conversion
```python
def convert_qiskit_to_qvm(circuit: QuantumCircuit) -> dict:
    """Convert Qiskit circuit to QVM JSON format."""
    # Supports: H, CNOT, CZ, X, Y, Z, Measure
    # Returns: QVM graph ready for execution
```

### Result Comparison
```python
def assert_equivalent_results(native_counts, qmk_counts):
    """Verify QMK outcomes are subset of native outcomes."""
    # For deterministic circuits: exact match
    # For probabilistic: QMK ⊆ Native
```

### Shot Counts
- Native Qiskit: 1000 shots (statistical distribution)
- QMK Path: 100 shots (faster, still representative)

## Troubleshooting

### "QMK server not running"
```bash
# Start server in separate terminal
python -m kernel.qmk_server
```

### "Qiskit not available"
```bash
pip install qiskit qiskit-aer
```

### Tests fail with unexpected outcomes
- Check QMK server is running properly
- Verify Qiskit version compatibility
- Check for any error messages in server logs

### Timeout errors
- Increase timeout in test: `timeout_ms=30000`
- Check server performance
- Reduce shot count for faster tests

## Adding New Tests

```python
def test_my_circuit(self):
    """Test my custom circuit."""
    # Create circuit
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    
    # Run both paths
    native_counts = self.run_native_qiskit(qc, shots=1000)
    qmk_counts = self.run_qmk_path(qc, shots=100)
    
    # Verify equivalence
    self.assert_equivalent_results(
        native_counts, qmk_counts, "My Circuit"
    )
    
    # Add specific checks
    expected_outcomes = {'00', '11'}
    self.assertTrue(
        get_possible_outcomes(qmk_counts).issubset(expected_outcomes)
    )
```

## Performance Notes

### Test Duration
- Each test: ~0.2-0.5 seconds
- Full suite: ~2-5 seconds
- CI/CD run: ~30 seconds (including setup)

### Optimization
- Tests use fewer shots for QMK (100 vs 1000)
- Still provides good coverage
- Faster CI/CD pipeline

## Success Criteria

Tests pass when:
1. ✅ All QMK outcomes are valid (in native outcome set)
2. ✅ Deterministic circuits produce single expected outcome
3. ✅ Probabilistic circuits produce expected outcome distribution
4. ✅ No errors or timeouts
5. ✅ Both paths complete successfully

## Summary

These automated tests ensure:
- ✅ QMK stack produces correct results
- ✅ Equivalence with native Qiskit
- ✅ All circuit types work correctly
- ✅ Continuous validation via CI/CD
- ✅ Regression protection

The tests provide confidence that the full QMK stack (QIR conversion, optimization, QVM execution) produces results equivalent to native Qiskit execution.
