# Phase 1: Security Hardening - Implementation Plan

**Timeline**: 4-6 weeks  
**Priority**: 🔴 CRITICAL  
**Goal**: Production-ready security system (40% → 80%+)

---

## Executive Summary

This plan addresses the critical security gaps identified in the project assessment. We will implement cryptographic capability tokens, complete capability mediation, add measurement protection, and create comprehensive security tests—all with world-class documentation matching the QIR optimizer standard.

**Current State**: 40% implemented, minimal testing  
**Target State**: 80%+ implemented, 50+ tests, comprehensive documentation

---

## Table of Contents

1. [Implementation Tasks](#implementation-tasks)
2. [Documentation Standard](#documentation-standard)
3. [Testing Requirements](#testing-requirements)
4. [Timeline & Milestones](#timeline--milestones)
5. [Success Criteria](#success-criteria)

---

## Implementation Tasks

### Week 1-2: Cryptographic Capability System

#### Task 1.1: Cryptographic Capability Tokens
**Status**: ❌ Not Started (Currently just dictionaries)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 3-4 days

**Current Implementation**:
```python
# kernel/simulator/capabilities.py (10 lines)
DEFAULT_CAPS = {
    "CAP_ALLOC": True,
    "CAP_LINK": False,
    "CAP_TELEPORT": False,
    "CAP_MAGIC": False,
}
```

**Target Implementation**:
```python
# kernel/security/capability_token.py (300+ lines)
class CapabilityToken:
    """
    Cryptographic capability token with HMAC-SHA256 signing.
    
    Implements object-capability model with:
    - Cryptographic signing (HMAC-SHA256)
    - Expiration timestamps
    - Use count limits
    - Attenuation (subset capabilities)
    - Delegation chains
    - Revocation support
    """
    
    def __init__(self, capabilities: Set[str], ...):
        self.capabilities = capabilities
        self.issued_at = time.time()
        self.expires_at = issued_at + ttl
        self.use_count = 0
        self.max_uses = max_uses
        self.signature = self._sign()
    
    def verify(self, secret_key: bytes) -> bool:
        """Verify token signature and validity."""
        ...
    
    def attenuate(self, subset: Set[str]) -> 'CapabilityToken':
        """Create attenuated token with subset of capabilities."""
        ...
```

**Deliverables**:
- [ ] `kernel/security/capability_token.py` - Token implementation
- [ ] `kernel/security/capability_verifier.py` - Verification logic
- [ ] `tests/security/test_capability_token.py` - 20+ tests
- [ ] `docs/security/capability_tokens.md` - Comprehensive documentation

**Documentation Requirements**:
- Mini-tutorial on object-capability model
- 5+ detailed examples
- Security properties and proofs
- Attack scenarios and mitigations
- Research citations (3+ papers)

---

#### Task 1.2: Complete Capability Mediation
**Status**: ⚠️ Partial (Only 4/20 operations checked)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 days

**Current Coverage**:
```python
CAP_REQUIRED = {
    "ALLOC_LQ": {"CAP_ALLOC"},
    "OPEN_CHAN": {"CAP_LINK"},
    "TELEPORT_CNOT": {"CAP_TELEPORT"},
    "INJECT_T_STATE": {"CAP_MAGIC"},
}
# Only 4 operations! Missing 16 operations!
```

**Target Coverage**:
```python
CAP_REQUIRED = {
    # Qubit operations
    "ALLOC_LQ": {"CAP_ALLOC"},
    "FREE_LQ": {"CAP_ALLOC"},
    "RESET_LQ": {"CAP_ALLOC"},
    
    # Measurements (CRITICAL - currently unprotected!)
    "MEASURE_Z": {"CAP_MEASURE"},
    "MEASURE_X": {"CAP_MEASURE"},
    "MEASURE_Y": {"CAP_MEASURE"},
    "MEASURE_BELL": {"CAP_MEASURE"},
    
    # Single-qubit gates
    "APPLY_H": {"CAP_COMPUTE"},
    "APPLY_X": {"CAP_COMPUTE"},
    "APPLY_Y": {"CAP_COMPUTE"},
    "APPLY_Z": {"CAP_COMPUTE"},
    "APPLY_S": {"CAP_COMPUTE"},
    "APPLY_T": {"CAP_COMPUTE"},
    
    # Two-qubit gates
    "APPLY_CNOT": {"CAP_COMPUTE"},
    "APPLY_CZ": {"CAP_COMPUTE"},
    
    # Channels
    "OPEN_CHAN": {"CAP_LINK"},
    "CLOSE_CHAN": {"CAP_LINK"},
    "SEND_QUBIT": {"CAP_LINK"},
    "RECV_QUBIT": {"CAP_LINK"},
    
    # Advanced operations
    "TELEPORT_CNOT": {"CAP_TELEPORT"},
    "INJECT_T_STATE": {"CAP_MAGIC"},
}
```

**Deliverables**:
- [ ] Update `kernel/simulator/enhanced_executor.py` - Add checks for all operations
- [ ] `tests/security/test_capability_mediation.py` - 20+ tests
- [ ] `docs/security/capability_mediation.md` - Complete reference

---

#### Task 1.3: CAP_MEASURE Enforcement
**Status**: ❌ Not Implemented (CRITICAL SECURITY HOLE!)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 1-2 days

**Problem**: Measurements are currently **unprotected**!
```python
# Anyone can measure any qubit without CAP_MEASURE!
result = executor.execute("MEASURE_Z", [qubit])  # No capability check!
```

**Solution**:
```python
def execute(self, operation: str, qubits: List, token: CapabilityToken):
    """Execute operation with capability checking."""
    
    # Verify token
    if not token.verify(self.secret_key):
        raise SecurityError("Invalid capability token")
    
    # Check required capabilities
    required = CAP_REQUIRED.get(operation, set())
    if not required.issubset(token.capabilities):
        raise SecurityError(f"Missing capabilities: {required - token.capabilities}")
    
    # Check use count
    if token.use_count >= token.max_uses:
        raise SecurityError("Token use limit exceeded")
    
    # Execute operation
    result = self._execute_operation(operation, qubits)
    
    # Update token
    token.use_count += 1
    
    # Audit log
    self.audit_logger.log(AuditEvent(
        event_type=AuditEventType.CAPABILITY_CHECK,
        operation=operation,
        token_id=token.id,
        result="ALLOWED"
    ))
    
    return result
```

**Deliverables**:
- [ ] Add CAP_MEASURE to all measurement operations
- [ ] Update executor to enforce measurement capabilities
- [ ] `tests/security/test_measurement_protection.py` - 15+ tests
- [ ] `docs/security/measurement_protection.md` - Security analysis

---

### Week 2-3: Multi-Tenant Isolation

#### Task 2.1: Physical Qubit Isolation
**Status**: ❌ Not Implemented  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 3-4 days

**Problem**: No enforcement of physical qubit isolation between tenants

**Solution**:
```python
class PhysicalQubitAllocator:
    """
    Manages physical qubit allocation with tenant isolation.
    
    Ensures:
    - Each tenant gets exclusive physical qubits
    - No qubit sharing between tenants
    - Proper cleanup on tenant deletion
    - Resource quota enforcement
    """
    
    def __init__(self, total_qubits: int):
        self.total_qubits = total_qubits
        self.allocations: Dict[str, Set[int]] = {}  # tenant_id -> qubit_ids
        self.free_qubits: Set[int] = set(range(total_qubits))
    
    def allocate(self, tenant_id: str, count: int) -> Set[int]:
        """Allocate physical qubits for tenant."""
        if len(self.free_qubits) < count:
            raise ResourceError("Insufficient physical qubits")
        
        allocated = set(list(self.free_qubits)[:count])
        self.free_qubits -= allocated
        self.allocations[tenant_id] = self.allocations.get(tenant_id, set()) | allocated
        
        return allocated
    
    def verify_access(self, tenant_id: str, qubit_id: int) -> bool:
        """Verify tenant has access to physical qubit."""
        return qubit_id in self.allocations.get(tenant_id, set())
```

**Deliverables**:
- [ ] `kernel/security/physical_qubit_allocator.py` - Allocator implementation
- [ ] Integration with tenant manager
- [ ] `tests/security/test_physical_isolation.py` - 15+ tests
- [ ] `docs/security/physical_isolation.md` - Isolation guarantees

---

#### Task 2.2: Timing Isolation
**Status**: ❌ Not Implemented  
**Priority**: 🟡 HIGH  
**Estimated Time**: 2-3 days

**Problem**: No timing isolation - tenants can infer information via timing

**Solution**:
```python
class TimingIsolator:
    """
    Provides timing isolation between tenants.
    
    Prevents timing side-channels by:
    - Constant-time operations
    - Time slot allocation
    - Execution time padding
    - Timing noise injection
    """
    
    def execute_with_isolation(self, operation: Callable, tenant_id: str):
        """Execute operation with timing isolation."""
        start_time = time.time()
        
        # Execute operation
        result = operation()
        
        # Calculate padding
        elapsed = time.time() - start_time
        target_time = self.get_time_slot_duration(tenant_id)
        padding = max(0, target_time - elapsed)
        
        # Add timing noise
        noise = random.uniform(0, self.timing_noise_ms / 1000)
        time.sleep(padding + noise)
        
        return result
```

**Deliverables**:
- [ ] `kernel/security/timing_isolator.py` - Timing isolation
- [ ] Integration with executor
- [ ] `tests/security/test_timing_isolation.py` - 10+ tests
- [ ] `docs/security/timing_isolation.md` - Side-channel analysis

---

### Week 3-4: Audit & Attestation

#### Task 3.1: Tamper-Evident Audit Log
**Status**: ⚠️ Partial (No Merkle tree)  
**Priority**: 🟡 HIGH  
**Estimated Time**: 2-3 days

**Current**: Basic logging without tamper-evidence

**Target**: Merkle tree-based tamper-evident log
```python
class TamperEvidentAuditLog:
    """
    Audit log with Merkle tree for tamper-evidence.
    
    Features:
    - Merkle tree construction
    - Cryptographic attestation
    - Epoch summaries
    - Tamper detection
    - Persistent storage
    """
    
    def append(self, event: AuditEvent) -> str:
        """Append event and return Merkle root."""
        # Add to log
        self.events.append(event)
        
        # Update Merkle tree
        leaf_hash = self._hash_event(event)
        self.merkle_tree.append(leaf_hash)
        
        # Return new root
        return self.merkle_tree.root()
    
    def verify_integrity(self, start_idx: int, end_idx: int) -> bool:
        """Verify log integrity for range."""
        return self.merkle_tree.verify_range(start_idx, end_idx)
```

**Deliverables**:
- [ ] Update `kernel/security/audit_logger.py` - Add Merkle tree
- [ ] `kernel/security/merkle_tree.py` - Merkle tree implementation
- [ ] `tests/security/test_audit_integrity.py` - 15+ tests
- [ ] `docs/security/audit_logging.md` - Tamper-evidence proofs

---

### Week 4-5: Comprehensive Testing

#### Task 4.1: Security Test Suite
**Status**: ❌ Minimal (2 tests)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 5-7 days

**Target**: 50+ comprehensive security tests

**Test Categories**:

1. **Capability Token Tests** (20 tests)
   - Token creation and signing
   - Signature verification
   - Expiration handling
   - Use count limits
   - Attenuation
   - Delegation chains
   - Revocation
   - Attack scenarios

2. **Capability Mediation Tests** (20 tests)
   - All 20 operations checked
   - Missing capability rejection
   - Expired token rejection
   - Revoked token rejection
   - Use limit enforcement
   - Audit logging
   - Attack scenarios

3. **Isolation Tests** (15 tests)
   - Physical qubit isolation
   - Namespace isolation
   - Timing isolation
   - Cross-tenant access prevention
   - Resource quota enforcement

4. **Audit Log Tests** (10 tests)
   - Event logging
   - Merkle tree integrity
   - Tamper detection
   - Epoch summaries
   - Query functionality

5. **Integration Tests** (10 tests)
   - End-to-end security flows
   - Multi-tenant scenarios
   - Attack simulations
   - Performance impact

**Deliverables**:
- [ ] `tests/security/test_capability_token.py` - 20 tests
- [ ] `tests/security/test_capability_mediation.py` - 20 tests
- [ ] `tests/security/test_isolation.py` - 15 tests
- [ ] `tests/security/test_audit_log.py` - 10 tests
- [ ] `tests/security/test_security_integration.py` - 10 tests

---

### Week 5-6: Documentation

#### Task 5.1: World-Class Security Documentation
**Status**: ⚠️ Spec exists, implementation docs missing  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 5-7 days

**Documentation Standard**: Match QIR optimizer quality
- Mini-tutorials for each feature
- 5+ detailed examples per feature
- Security proofs and analysis
- Attack scenarios and mitigations
- Research citations
- Code examples
- Best practices

**Documents to Create**:

1. **Capability System Documentation** (Similar to optimizer passes)
   - `docs/security/capabilities/README.md` - Overview
   - `docs/security/capabilities/01_capability_tokens.md` - Token system
   - `docs/security/capabilities/02_capability_mediation.md` - Enforcement
   - `docs/security/capabilities/03_attenuation.md` - Delegation
   - `docs/security/capabilities/04_revocation.md` - Lifecycle

2. **Isolation Documentation**
   - `docs/security/isolation/01_physical_isolation.md` - Qubit isolation
   - `docs/security/isolation/02_timing_isolation.md` - Timing channels
   - `docs/security/isolation/03_namespace_isolation.md` - Tenant separation

3. **Audit Documentation**
   - `docs/security/audit/01_audit_logging.md` - Event logging
   - `docs/security/audit/02_tamper_evidence.md` - Merkle trees
   - `docs/security/audit/03_attestation.md` - Cryptographic proofs

4. **Security Guide**
   - `docs/security/SECURITY_GUIDE.md` - Comprehensive guide
   - `docs/security/THREAT_MODEL.md` - Threat analysis
   - `docs/security/ATTACK_SCENARIOS.md` - Attack examples
   - `docs/security/BEST_PRACTICES.md` - Deployment guide

**Each document should include**:
- Overview and motivation
- Mini-tutorial with theory
- 5+ detailed examples
- Security properties and proofs
- Attack scenarios
- Mitigations
- Code examples
- Research citations
- See also links

**Deliverables**:
- [ ] 15+ comprehensive security documents
- [ ] Master security index
- [ ] Security quick reference
- [ ] Deployment checklist

---

## Documentation Standard

### Quality Requirements

To match the QIR optimizer documentation standard, each security document must include:

#### 1. Structure
```markdown
# [Feature Name]

**Category**: Security / Isolation / Audit
**Priority**: CRITICAL / HIGH / MEDIUM
**Complexity**: High / Medium / Low
**Impact**: Critical / High / Medium

## Overview
[High-level description]

## Mini-Tutorial: [Concept]
[Theory and background]

## Examples
[5+ detailed examples with before/after]

## Security Properties
[Formal properties and proofs]

## Attack Scenarios
[Potential attacks and mitigations]

## Implementation
[Code examples and algorithms]

## Research & References
[Citations to papers]

## Usage Example
[Practical code example]

## Best Practices
[Deployment recommendations]

## See Also
[Related documents]
```

#### 2. Content Requirements
- **Mini-Tutorial**: 200+ lines explaining theory
- **Examples**: 5+ detailed scenarios
- **Security Proofs**: Formal analysis
- **Attack Scenarios**: 3+ attack examples
- **Research**: 3+ paper citations
- **Code Examples**: Working implementations
- **Cross-References**: Links to related docs

#### 3. Quality Metrics
- **Length**: 300-600 lines per document
- **Examples**: 5-10 per document
- **Citations**: 3-5 papers per document
- **Code**: 100+ lines of examples
- **Clarity**: Accessible to developers

---

## Testing Requirements

### Test Coverage Targets

| Component | Current | Target | Tests Needed |
|-----------|---------|--------|--------------|
| Capability Tokens | 0% | 100% | 20 tests |
| Capability Mediation | 10% | 100% | 20 tests |
| Physical Isolation | 0% | 100% | 15 tests |
| Timing Isolation | 0% | 80% | 10 tests |
| Audit Logging | 20% | 100% | 10 tests |
| Integration | 0% | 80% | 10 tests |
| **TOTAL** | **~5%** | **~90%** | **85 tests** |

### Test Quality Standards

Each test must:
- ✅ Test one specific behavior
- ✅ Have descriptive name
- ✅ Use Arrange-Act-Assert pattern
- ✅ Include edge cases
- ✅ Be deterministic
- ✅ Run in <1 second
- ✅ Include security assertions

### Test Categories

1. **Unit Tests** (60 tests)
   - Test individual security components
   - Mock dependencies
   - Fast execution

2. **Integration Tests** (15 tests)
   - Test component interactions
   - Real dependencies
   - End-to-end flows

3. **Security Tests** (10 tests)
   - Attack simulations
   - Penetration testing
   - Fuzzing

---

## Timeline & Milestones

### Week 1: Capability Tokens
**Milestone**: Cryptographic capability system working

- [ ] Day 1-2: Implement CapabilityToken class
- [ ] Day 3: Implement verification logic
- [ ] Day 4: Add attenuation and delegation
- [ ] Day 5: Write 20 tests
- [ ] **Deliverable**: Working capability token system

### Week 2: Capability Mediation
**Milestone**: All operations protected

- [ ] Day 1-2: Add CAP_MEASURE enforcement
- [ ] Day 3: Complete mediation for all 20 operations
- [ ] Day 4: Integration with executor
- [ ] Day 5: Write 20 tests
- [ ] **Deliverable**: Complete capability mediation

### Week 3: Isolation
**Milestone**: Multi-tenant isolation working

- [ ] Day 1-2: Physical qubit isolation
- [ ] Day 3-4: Timing isolation
- [ ] Day 5: Write 15 tests
- [ ] **Deliverable**: Tenant isolation complete

### Week 4: Audit & Testing
**Milestone**: Tamper-evident audit + comprehensive tests

- [ ] Day 1-2: Merkle tree audit log
- [ ] Day 3-5: Write remaining tests (30 tests)
- [ ] **Deliverable**: 75+ security tests passing

### Week 5-6: Documentation
**Milestone**: World-class security documentation

- [ ] Week 5: Write capability documentation (5 docs)
- [ ] Week 6 Day 1-2: Write isolation documentation (3 docs)
- [ ] Week 6 Day 3-4: Write audit documentation (3 docs)
- [ ] Week 6 Day 5: Write security guides (4 docs)
- [ ] **Deliverable**: 15+ comprehensive documents

---

## Success Criteria

### Implementation Success
- [x] Cryptographic capability tokens implemented
- [ ] All 20 operations have capability checks
- [ ] CAP_MEASURE protects all measurements
- [ ] Physical qubit isolation enforced
- [ ] Timing isolation implemented
- [ ] Tamper-evident audit log working
- [ ] 75+ security tests passing
- [ ] No critical security vulnerabilities

### Documentation Success
- [ ] 15+ comprehensive security documents
- [ ] Each document 300-600 lines
- [ ] 5+ examples per document
- [ ] 3+ research citations per document
- [ ] Mini-tutorials for all features
- [ ] Attack scenarios documented
- [ ] Best practices guide complete

### Quality Metrics
- [ ] Test coverage ≥90% for security code
- [ ] All tests passing
- [ ] Code review completed
- [ ] Security audit passed
- [ ] Documentation review passed
- [ ] Performance impact <10%

---

## Risk Mitigation

### Technical Risks

**Risk**: Cryptographic implementation errors
- **Mitigation**: Use standard libraries (hmac, hashlib)
- **Mitigation**: Code review by security expert
- **Mitigation**: Penetration testing

**Risk**: Performance impact
- **Mitigation**: Benchmark all changes
- **Mitigation**: Optimize hot paths
- **Mitigation**: Cache capability checks

**Risk**: Breaking existing functionality
- **Mitigation**: Comprehensive regression tests
- **Mitigation**: Feature flags for gradual rollout
- **Mitigation**: Backward compatibility layer

### Schedule Risks

**Risk**: Documentation takes longer than expected
- **Mitigation**: Start documentation early
- **Mitigation**: Parallel documentation and implementation
- **Mitigation**: Reuse optimizer documentation templates

**Risk**: Testing uncovers major issues
- **Mitigation**: Test-driven development
- **Mitigation**: Early integration testing
- **Mitigation**: Buffer time in schedule

---

## Dependencies

### External Dependencies
- ✅ Python 3.9+ (already required)
- ✅ `hmac`, `hashlib` (standard library)
- ✅ `secrets` (standard library)
- ⏳ `pytest` (for testing)
- ⏳ `hypothesis` (for property-based testing)

### Internal Dependencies
- ✅ Existing tenant manager
- ✅ Existing handle signer
- ✅ Existing audit logger
- ⏳ Enhanced executor (needs updates)
- ⏳ Session manager (needs updates)

---

## Deliverables Summary

### Code Deliverables
- [ ] `kernel/security/capability_token.py` (300+ lines)
- [ ] `kernel/security/capability_verifier.py` (200+ lines)
- [ ] `kernel/security/physical_qubit_allocator.py` (250+ lines)
- [ ] `kernel/security/timing_isolator.py` (200+ lines)
- [ ] `kernel/security/merkle_tree.py` (150+ lines)
- [ ] Updates to `kernel/simulator/enhanced_executor.py`
- [ ] Updates to `kernel/security/audit_logger.py`

### Test Deliverables
- [ ] 75+ security tests across 5 test files
- [ ] Integration test suite
- [ ] Security test suite
- [ ] Performance benchmarks

### Documentation Deliverables
- [ ] 15+ comprehensive security documents
- [ ] Security master index
- [ ] Security quick reference
- [ ] Deployment guide
- [ ] Threat model
- [ ] Attack scenarios guide

---

## Next Steps

### Immediate (This Week)
1. ✅ Review and approve this plan
2. ⏳ Set up development branch
3. ⏳ Create documentation templates
4. ⏳ Start implementing CapabilityToken class

### Week 1
1. ⏳ Implement cryptographic capability tokens
2. ⏳ Write capability token tests
3. ⏳ Start capability token documentation

### Week 2
1. ⏳ Add CAP_MEASURE enforcement
2. ⏳ Complete capability mediation
3. ⏳ Write mediation tests

---

**Status**: 📋 PLAN READY FOR EXECUTION  
**Estimated Completion**: 4-6 weeks  
**Documentation Standard**: World-class (matching QIR optimizer)  
**Test Coverage Target**: 90%+

**Ready to begin implementation!** 🚀
