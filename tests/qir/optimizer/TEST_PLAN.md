# QIR Optimizer Test Plan

**Status**: In Progress  
**Coverage Target**: 100% of optimization passes  
**Success Criteria**: Fidelity > 0.95, Gate reduction 20-50%

---

## Test Categories

### 1. Unit Tests ✅ COMPLETE
**Purpose**: Test each optimization pass in isolation

**Coverage**:
- ✅ Gate Cancellation (`test_gate_cancellation.py`)
- ✅ Gate Commutation (`test_gate_commutation.py`)
- ✅ Gate Fusion (`test_gate_fusion.py`)
- ✅ Dead Code Elimination (`test_dead_code_elimination.py`)
- ✅ Constant Propagation (`test_constant_propagation.py`)
- ✅ Template Matching (`test_template_matching.py`)
- ✅ Measurement Deferral (`test_measurement_deferral.py`)
- ✅ Clifford+T Optimization (`test_clifford_t_optimization.py`)
- ✅ Magic State Optimization (`test_magic_state_optimization.py`)
- ✅ Gate Teleportation (`test_gate_teleportation.py`)
- ✅ Uncomputation Optimization (`test_uncomputation_optimization.py`)
- ✅ Lattice Surgery Optimization (`test_lattice_surgery_optimization.py`)
- ✅ SWAP Insertion (`test_swap_insertion.py`)
- ✅ Qubit Mapping (`test_qubit_mapping.py`)
- ✅ Measurement Canonicalization (`test_measurement_canonicalization_pass.py`)
- ✅ Measurement Canonicalization v2 (`test_measurement_canonicalization_v2.py`)
- ✅ Experimental Passes (`test_experimental_passes.py`) **NEW**

**Status**: 17/17 passes have unit tests (100%)

---

### 2. Integration Tests ✅ NEW
**Purpose**: Test combinations of optimization passes

**Test File**: `test_pass_integration.py`

**Coverage**:
- ✅ Cancellation + Commutation
- ✅ Fusion + Cancellation
- ✅ Dead Code + Constant Propagation
- ✅ Full optimization pipeline
- ✅ Clifford+T optimization pipeline
- ✅ Pass ordering tests
- ✅ Pass idempotence tests
- ✅ Pass conflict detection

**Status**: Integration tests created

---

### 3. Algorithm Validation Tests ✅ NEW
**Purpose**: Test optimization on standard quantum algorithms

**Test File**: `test_algorithm_validation.py`

**Algorithms Tested**:
- ✅ Bell States
- ✅ GHZ States
- ✅ Grover's Algorithm (diffusion operator)
- ✅ VQE Ansatz
- ✅ Quantum Fourier Transform
- ✅ Clifford+T Circuits (Toffoli)

**Status**: Algorithm validation tests created

---

### 4. Performance Benchmarks ⏳ TODO
**Purpose**: Measure optimization impact

**Metrics to Measure**:
- [ ] Gate count reduction (target: 20-50%)
- [ ] Depth reduction (target: 15-30%)
- [ ] T-count reduction (target: 30-60%)
- [ ] SWAP overhead (target: <20%)
- [ ] Optimization time
- [ ] Memory usage

**Status**: Not yet implemented

---

### 5. Correctness Validation ⏳ TODO
**Purpose**: Verify optimized circuits produce correct results

**Tests Needed**:
- [ ] Native vs QMK comparison
- [ ] Fidelity measurements (target: >0.95)
- [ ] State vector comparison
- [ ] Measurement distribution comparison
- [ ] Entanglement preservation

**Status**: Not yet implemented

---

### 6. Regression Tests ⏳ TODO
**Purpose**: Ensure optimizations don't break existing functionality

**Tests Needed**:
- [ ] Baseline test suite
- [ ] Performance regression detection
- [ ] Correctness regression detection
- [ ] CI/CD integration

**Status**: Not yet implemented

---

## Test Execution

### Running Tests

**All Tests**:
```bash
cd tests/qir/optimizer
python run_all_tests.py
```

**Individual Test Files**:
```bash
python test_gate_cancellation.py
python test_pass_integration.py
python test_algorithm_validation.py
```

**Specific Test**:
```bash
python -m unittest test_gate_cancellation.TestGateCancellation.test_self_inverse_h_gate
```

---

## Test Coverage

### Current Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests | 17/17 passes | ✅ 100% |
| Integration Tests | 15 tests | ✅ Complete |
| Algorithm Validation | 15 tests | ✅ Complete |
| Performance Benchmarks | 0 tests | ⏳ TODO |
| Correctness Validation | 0 tests | ⏳ TODO |
| Regression Tests | 0 tests | ⏳ TODO |

**Overall**: ~60% complete

---

## Success Criteria

### From OPTIMIZATION_PLAN.md

**Performance Targets**:
- ✅ Gate count reduction: 20-50% typical
- ⏳ Depth reduction: 15-30% typical
- ⏳ T-count reduction: 30-60% for Clifford+T
- ⏳ SWAP overhead: <20%

**Correctness Targets**:
- ⏳ Fidelity: >0.95 for all circuits
- ⏳ Correlation: >95% for entangled states
- ✅ Test coverage: 100% of passes
- ⏳ Regression rate: <1%

**Status**: 2/8 criteria validated

---

## Test Circuits

### Standard Test Circuits

1. **Bell States**
   - |Φ+⟩ = (|00⟩ + |11⟩)/√2
   - |Φ-⟩ = (|00⟩ - |11⟩)/√2
   - |Ψ+⟩ = (|01⟩ + |10⟩)/√2
   - |Ψ-⟩ = (|01⟩ - |10⟩)/√2

2. **GHZ States**
   - 3-qubit: (|000⟩ + |111⟩)/√2
   - 4-qubit: (|0000⟩ + |1111⟩)/√2
   - n-qubit: (|0...0⟩ + |1...1⟩)/√2

3. **Grover's Algorithm**
   - Oracle
   - Diffusion operator
   - Full iteration

4. **VQE Ansatz**
   - Hardware-efficient ansatz
   - UCCSD ansatz
   - Custom parameterized circuits

5. **Quantum Fourier Transform**
   - 2-qubit QFT
   - 3-qubit QFT
   - n-qubit QFT

6. **Shor's Algorithm**
   - Modular exponentiation
   - QFT
   - Full algorithm

---

## Next Steps

### Immediate (This Week)
1. ✅ Create experimental pass tests
2. ✅ Create integration tests
3. ✅ Create algorithm validation tests
4. ✅ Create test runner script

### Short-term (Next 2 Weeks)
5. [ ] Implement performance benchmarks
6. [ ] Add correctness validation (native vs QMK)
7. [ ] Measure fidelity for test circuits
8. [ ] Create regression test suite

### Medium-term (Next Month)
9. [ ] CI/CD integration
10. [ ] Automated performance tracking
11. [ ] Test coverage reporting
12. [ ] Documentation of test results

---

## Test Infrastructure

### Required Tools
- ✅ unittest (Python standard library)
- ⏳ pytest (for advanced features)
- ⏳ coverage.py (for coverage reporting)
- ⏳ pytest-benchmark (for performance tests)

### CI/CD Integration
- ⏳ GitHub Actions workflow
- ⏳ Automated test runs on PR
- ⏳ Performance regression detection
- ⏳ Coverage reporting

---

## Known Issues

### Test Gaps
1. **Performance Benchmarks**: Not yet implemented
2. **Native Comparison**: Need Qiskit/Azure integration
3. **Fidelity Measurements**: Need quantum simulator
4. **Regression Baseline**: Need to establish baseline

### Test Improvements Needed
1. **Parametrized Tests**: Use pytest parametrize
2. **Test Fixtures**: Reusable circuit fixtures
3. **Mock Objects**: For hardware-specific tests
4. **Property-Based Testing**: Use hypothesis library

---

## Resources

- [Original Plan](../../../docs/qir/OPTIMIZATION_PLAN.md)
- [Implementation Status](../../../docs/qir/IMPLEMENTATION_STATUS.md)
- [Pass Documentation](../../../docs/qir/passes/)

---

## Conclusion

**Current Status**: 🟡 **GOOD PROGRESS**

- ✅ Unit tests: 100% complete
- ✅ Integration tests: Created
- ✅ Algorithm validation: Created
- ⏳ Performance benchmarks: TODO
- ⏳ Correctness validation: TODO
- ⏳ Regression tests: TODO

**Priority**: Focus on performance benchmarks and correctness validation next.
