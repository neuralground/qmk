# QMK Testing Guide

Comprehensive testing documentation for the QMK quantum computing platform.

## Test Coverage

### Test Suites Overview

| Test Suite | Tests | Coverage | Status |
|------------|-------|----------|--------|
| **Library Components** | 12 | All 9 library components | ✅ Passing |
| **Example Circuits** | 13 | All 13 examples | ✅ Passing |
| **ASM Macros** | 22 | Preprocessor system | ✅ Passing |
| **Classical Helpers** | 10 | Shor's post-processing | ✅ Passing |
| **ASM Runner** | 13 | File assembly utility | ✅ Passing |
| **Total** | **70** | **Complete coverage** | **✅ 100%** |

---

## Test Suites

### 1. Library Component Tests
**File:** `tests/qvm/lib/test_library_components.py`

Tests all reusable quantum circuit components in `qvm/lib/`:

**Components Tested:**
- ✅ QFT (Quantum Fourier Transform)
- ✅ Draper Adder (QFT-based)
- ✅ Cuccaro Adder (Ripple-carry)
- ✅ Comparator (Register comparison)
- ✅ Phase Estimation
- ✅ Amplitude Amplification (Grover operator)
- ✅ Grover Oracle (Search templates)
- ✅ Syndrome Extraction (QEC)
- ✅ Modular Exponentiation
- ✅ Library Integration (Multiple includes)

**What's Tested:**
- Components load without errors
- Parameters substitute correctly
- Different qubit/bit counts work
- Valid QVM graphs generated
- Integration between components

**Run:**
```bash
python tests/qvm/lib/test_library_components.py
```

---

### 2. Example Circuit Tests
**File:** `tests/examples/test_asm_examples.py`

Tests all example circuits in `examples/asm/`:

**Examples Tested:**
- ✅ Bell State
- ✅ GHZ State (multiple qubit counts)
- ✅ W State (with angle calculations)
- ✅ Deutsch-Jozsa (all 5 oracle types)
- ✅ Grover's Search (all 4 target states)
- ✅ VQE Ansatz
- ✅ Adaptive Simple
- ✅ Adaptive Multi-Round
- ✅ Shor's Period Finding
- ✅ Shor's Full Algorithm
- ✅ Measurement Bases (X, Y, Z)
- ✅ Resource Validation
- ✅ Version Validation

**What's Tested:**
- Examples assemble correctly
- Parameter variations work
- Oracle types all functional
- Target states all valid
- Required fields present

**Run:**
```bash
python tests/examples/test_asm_examples.py
```

---

### 3. ASM Macro Tests
**File:** `tests/qvm/test_asm_macros.py`

Tests the macro preprocessor system:

**Features Tested:**
- ✅ `.param` directives (basic, override, arithmetic)
- ✅ `.set` variables (basic, arithmetic, strings)
- ✅ `.for` loops (basic, nested, with variables)
- ✅ `.if/.elif/.else` conditionals
- ✅ String operations (comparison, indexing)
- ✅ `.include` directives
- ✅ Complex macro combinations
- ✅ Error handling

**What's Tested:**
- Parameter substitution works
- Variables evaluate correctly
- Loops expand properly
- Conditionals branch correctly
- Includes resolve
- Nested structures work
- Arithmetic operations correct

**Run:**
```bash
python tests/qvm/test_asm_macros.py
```

---

### 4. Classical Helper Tests
**File:** `tests/examples/test_classical_helpers.py`

Tests classical post-processing functions for Shor's algorithm:

**Functions Tested:**
- ✅ `gcd()` - Greatest common divisor
- ✅ `continued_fraction()` - Continued fraction expansion
- ✅ `convergents()` - Rational approximations
- ✅ `extract_period_from_measurement()` - Period extraction
- ✅ `classical_period_finding()` - Verification
- ✅ `verify_period()` - Period validation
- ✅ `factor_from_period()` - Factor extraction
- ✅ `shors_classical_postprocessing()` - Complete pipeline

**What's Tested:**
- GCD computation correct
- Period extraction works
- Factor extraction successful
- Complete post-processing pipeline
- Edge cases handled

**Run:**
```bash
python tests/examples/test_classical_helpers.py
```

---

### 5. ASM Runner Tests
**File:** `tests/examples/test_asm_runner.py`

Tests the `assemble_file()` utility:

**Features Tested:**
- ✅ File assembly (simple, with params)
- ✅ Parameter substitution (numeric, string, list)
- ✅ File resolution (from asm dir, with includes)
- ✅ Output validation (required fields, nodes, resources)
- ✅ Error handling (nonexistent files, invalid params)

**What's Tested:**
- Files assemble correctly
- Parameters substitute properly
- Paths resolve correctly
- Output structure valid
- Errors handled gracefully

**Run:**
```bash
python tests/examples/test_asm_runner.py
```

---

## Running Tests

### Run Individual Test Suites

```bash
# Library components
python tests/qvm/lib/test_library_components.py

# Example circuits
python tests/examples/test_asm_examples.py

# ASM macros
python tests/qvm/test_asm_macros.py

# Classical helpers
python tests/examples/test_classical_helpers.py

# ASM runner
python tests/examples/test_asm_runner.py
```

### Run All Tests

```bash
# Using test runner
python run_tests.py

# Using pytest (if installed)
pytest tests/

# Using unittest discovery
python -m unittest discover tests/
```

---

## Test Results Summary

### Current Status

```
Library Components:  12/12 tests passed ✅
Example Circuits:    13/13 tests passed ✅
ASM Macros:          22/22 tests passed ✅
Classical Helpers:   10/10 tests passed ✅
ASM Runner:          13/13 tests passed ✅
────────────────────────────────────────
Total:               70/70 tests passed ✅
Success Rate:        100%
```

---

## What's Tested

### Functional Coverage

1. **Assembly & Compilation** ✅
   - ASM files assemble correctly
   - Macros expand properly
   - Parameters substitute
   - Includes resolve

2. **Library Components** ✅
   - All 9 components load
   - Parameters work
   - Different sizes supported
   - Integration tested

3. **Example Circuits** ✅
   - All 13 examples work
   - Parameter variations
   - Oracle types
   - Target states

4. **Classical Processing** ✅
   - Number theory functions
   - Period extraction
   - Factor extraction
   - Complete pipelines

5. **Utilities** ✅
   - File assembly
   - Parameter handling
   - Path resolution
   - Output validation

### Edge Cases

- ✅ Zero/empty inputs
- ✅ Boundary values
- ✅ Invalid parameters
- ✅ Nonexistent files
- ✅ Nested structures
- ✅ Complex combinations

---

## Continuous Integration

### CI/CD Integration

Tests are ready for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python run_tests.py
```

### Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
python run_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## Adding New Tests

### Test Structure

```python
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

class TestNewFeature(unittest.TestCase):
    """Test description."""
    
    def test_basic_functionality(self):
        """Test basic case."""
        # Arrange
        input_data = ...
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        self.assertEqual(result, expected)
```

### Best Practices

1. **One concept per test**
   - Test one thing at a time
   - Clear test names
   - Focused assertions

2. **Arrange-Act-Assert**
   - Set up test data
   - Execute function
   - Verify results

3. **Use subtests for variations**
   ```python
   for param in [1, 2, 3]:
       with self.subTest(param=param):
           result = test_function(param)
           self.assertValid(result)
   ```

4. **Test edge cases**
   - Boundary values
   - Empty inputs
   - Invalid data
   - Error conditions

---

## Test Maintenance

### Updating Tests

When adding new features:
1. Add tests for new functionality
2. Update existing tests if behavior changes
3. Ensure all tests pass
4. Update this documentation

### Regression Testing

All tests serve as regression tests:
- Catch breaking changes
- Ensure examples stay working
- Validate library components
- Verify utilities function

---

## Benefits

### Development Benefits

1. **Confidence** ✅
   - Know code works
   - Catch bugs early
   - Safe refactoring

2. **Documentation** ✅
   - Tests show usage
   - Examples of parameters
   - Expected behavior

3. **Quality** ✅
   - Consistent behavior
   - Edge cases handled
   - Error conditions tested

4. **Speed** ✅
   - Fast feedback
   - Automated validation
   - No manual testing

### User Benefits

1. **Reliability** ✅
   - Tested components
   - Verified examples
   - Known to work

2. **Examples** ✅
   - Tests show usage
   - Parameter examples
   - Integration patterns

3. **Trust** ✅
   - Comprehensive testing
   - 100% pass rate
   - Continuous validation

---

## Summary

**Complete test coverage with 70 automated tests:**

- ✅ All 9 library components tested
- ✅ All 13 example circuits tested
- ✅ Complete macro system tested
- ✅ Classical helpers tested
- ✅ Utilities tested
- ✅ 100% pass rate
- ✅ Ready for CI/CD
- ✅ Regression protection

**Result: Production-ready testing infrastructure!** 🎉
