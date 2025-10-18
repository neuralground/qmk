# QMK Test Suite

Comprehensive automated test suite for the Quantum Microkernel.

## Running Tests

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Module

```bash
python -m unittest tests.unit.test_qec_profiles
python -m unittest tests.unit.test_azure_qre_compat
python -m unittest tests.unit.test_error_models
python -m unittest tests.unit.test_logical_qubit
```

### Run Specific Test Class

```bash
python -m unittest tests.unit.test_qec_profiles.TestSurfaceCode
```

### Run Specific Test Method

```bash
python -m unittest tests.unit.test_qec_profiles.TestSurfaceCode.test_default_surface_code
```

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_qec_profiles.py        # QEC profile tests (14 tests)
│   ├── test_azure_qre_compat.py    # Azure QRE compatibility (25 tests)
│   ├── test_error_models.py        # Error model tests (14 tests)
│   └── test_logical_qubit.py       # Logical qubit tests (14 tests)
└── integration/             # Integration tests (future)
```

## Test Coverage

### QEC Profiles (14 tests)
- ✅ Profile creation and parameters
- ✅ Logical error rate calculation
- ✅ Surface code scaling with distance
- ✅ SHYPS code efficiency
- ✅ Bacon-Shor code parameters
- ✅ Profile string parsing
- ✅ Standard profile library

### Azure QRE Compatibility (25 tests)
- ✅ Qubit parameter schemas (gate-based and Majorana)
- ✅ QEC scheme formulas
- ✅ Time string parsing (ns, µs, ms, s)
- ✅ Formula evaluation engine
- ✅ All 6 predefined qubit parameters
- ✅ All 3 predefined QEC schemes
- ✅ Resource computation accuracy
- ✅ Distance scaling

### Error Models (14 tests)
- ✅ Depolarizing noise (X, Y, Z errors)
- ✅ Coherence noise (T1, T2)
- ✅ Measurement errors
- ✅ Composite error model
- ✅ Error tracking and telemetry
- ✅ Probability scaling with time/duration

### Logical Qubits (14 tests)
- ✅ Qubit initialization
- ✅ Single-qubit gates (H, X, Y, Z, S)
- ✅ Two-qubit gates (CNOT)
- ✅ Measurements (Z and X basis)
- ✅ State transformations
- ✅ Decoder cycle tracking
- ✅ Telemetry collection
- ✅ Deterministic behavior with seeds
- ✅ Logical error rate scaling

## Test Statistics

**Total Tests**: 67  
**Pass Rate**: 100%  
**Coverage**: Core simulator components

## Continuous Integration

Tests run automatically on:
- Every push to `main`
- Every pull request
- Python versions: 3.9, 3.10, 3.11, 3.12

See `.github/workflows/tests.yml` for CI configuration.

## Writing New Tests

### Test Template

```python
import unittest
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.simulator.your_module import YourClass


class TestYourClass(unittest.TestCase):
    """Test YourClass functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.method()
        self.assertEqual(result, expected_value)


if __name__ == "__main__":
    unittest.main()
```

### Best Practices

1. **One test per behavior**: Each test should verify one specific behavior
2. **Descriptive names**: Use `test_<what>_<condition>_<expected>` format
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use fixtures**: Set up common test data in `setUp()`
5. **Test edge cases**: Include boundary conditions and error cases
6. **Deterministic**: Use fixed seeds for reproducibility
7. **Fast**: Keep unit tests under 1 second each

### Test Categories

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test component interactions
- **Regression tests**: Prevent bugs from reoccurring
- **Property tests**: Verify invariants hold

## Debugging Failed Tests

### Run with verbose output

```bash
python run_tests.py -v
```

### Run single test with debugging

```bash
python -m pdb -m unittest tests.unit.test_qec_profiles.TestSurfaceCode.test_default_surface_code
```

### Check test output

```bash
python -m unittest tests.unit.test_qec_profiles -v 2>&1 | tee test_output.txt
```

## Future Test Additions

- [ ] Integration tests for full QVM graph execution
- [ ] Performance benchmarks
- [ ] Stress tests for large graphs
- [ ] Fuzz testing for validator
- [ ] Property-based tests with Hypothesis
- [ ] Coverage reporting with pytest-cov

---

**Last Updated**: Phase 2 - Logical Qubit Simulator  
**Test Count**: 67 tests, 100% passing
