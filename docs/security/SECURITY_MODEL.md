# QMK Security Model

**Comprehensive Security Architecture for Quantum Computing Infrastructure**

## Table of Contents

1. [Overview](#overview)
2. [Threat Model](#threat-model)
3. [Security Principles](#security-principles)
4. [Capability-Based Security](#capability-based-security)
5. [Linear Type System](#linear-type-system)
6. [Multi-Tenant Isolation](#multi-tenant-isolation)
7. [Entanglement Firewall](#entanglement-firewall)
8. [Audit and Attestation](#audit-and-attestation)
9. [Research Foundations](#research-foundations)
10. [Security Guarantees](#security-guarantees)

---

## Overview

QMK implements a **defense-in-depth** security architecture specifically designed for quantum computing infrastructure. The security model addresses unique challenges in quantum systems:

- **Quantum state fragility**: Unauthorized access can destroy quantum information
- **Entanglement leakage**: Cross-tenant entanglement enables information leakage
- **Resource exhaustion**: Quantum resources are scarce and expensive
- **Non-clonability**: Quantum no-cloning theorem prevents traditional backup strategies
- **Measurement irreversibility**: Measurements destroy quantum states

### Security Goals

1. **Confidentiality**: Prevent unauthorized access to quantum states
2. **Integrity**: Ensure quantum operations execute as intended
3. **Availability**: Protect against resource exhaustion attacks
4. **Isolation**: Prevent cross-tenant interference and entanglement
5. **Accountability**: Maintain complete audit trails

---

## Threat Model

### Adversary Capabilities

We consider adversaries with the following capabilities:

**External Adversaries:**
- Submit malicious quantum circuits
- Attempt resource exhaustion (DoS)
- Try to infer other tenants' quantum states
- Exploit timing side-channels

**Malicious Tenants:**
- Attempt to exceed resource quotas
- Try to create cross-tenant entanglement
- Attempt privilege escalation
- Probe for information leakage

**Compromised Components:**
- Compromised user-mode processes
- Malicious QVM graphs
- Corrupted circuit optimizers

### Out of Scope

- Physical attacks on quantum hardware
- Side-channel attacks on classical control systems
- Compromised microkernel (trusted computing base)
- Quantum algorithm attacks (e.g., Shor's algorithm)

---

## Security Principles

### 1. Principle of Least Privilege

Every operation requires explicit capabilities. No operation is permitted by default.

**Implementation:**
- Capability tokens bound to principals
- Fine-grained permission model
- Explicit capability checks before privileged operations

**Research Foundation:**
- Dennis & Van Horn (1966): "Programming Semantics for Multiprogrammed Computations"
- Miller et al. (2003): "Capability Myths Demolished"

### 2. Defense in Depth

Multiple independent security layers:

```
Layer 1: QIR Optimizer (Static Analysis)
Layer 2: QVM Verifier (Graph Validation)
Layer 3: Capability System (Runtime Checks)
Layer 4: Microkernel (Resource Isolation)
Layer 5: Audit System (Detection & Response)
```

### 3. Fail-Safe Defaults

- Operations fail closed (deny by default)
- Missing capabilities → operation rejected
- Invalid handles → immediate error
- Quota exceeded → graceful degradation

### 4. Complete Mediation

Every access to quantum resources is checked:
- Virtual qubit allocation
- Channel creation
- Gate operations
- Measurements
- Resource deallocation

### 5. Separation of Privilege

Critical operations require multiple independent checks:
- Capability possession
- Quota availability
- Resource validity
- Tenant authorization

---

## Capability-Based Security

### Capability Model

QMK uses **object-capabilities** for access control. A capability is an unforgeable token that grants specific permissions.

**Capability Types:**

```python
CAP_ALLOC      # Allocate virtual qubits
CAP_LINK       # Create entanglement channels
CAP_TELEPORT   # Perform gate teleportation
CAP_MAGIC      # Inject magic states (T-gates)
CAP_MEASURE    # Perform measurements
CAP_ADMIN      # Administrative operations
```

### Capability Properties

1. **Unforgeable**: Cryptographically signed with HMAC-SHA256
2. **Transferable**: Can be delegated with restrictions
3. **Revocable**: Can be revoked by issuer
4. **Attenuable**: Delegated caps have reduced permissions

### Capability Lifecycle

```
1. Grant: Tenant receives initial capabilities
2. Check: Every operation validates required capabilities
3. Delegate: Tenant can delegate subset to sub-processes
4. Attenuate: Delegated caps have time/count limits
5. Revoke: Admin or tenant can revoke capabilities
6. Audit: All capability usage logged
```

### Implementation

```python
class CapabilityToken:
    """
    Unforgeable capability token.
    
    Properties:
    - tenant_id: Owner of capability
    - capabilities: Set of granted permissions
    - expires_at: Expiration timestamp
    - signature: HMAC-SHA256 signature
    - delegation_depth: Number of delegations
    """
    
    def verify(self, secret_key: bytes) -> bool:
        """Verify capability signature."""
        expected = hmac.new(
            secret_key,
            self._canonical_form(),
            hashlib.sha256
        ).digest()
        return hmac.compare_digest(expected, self.signature)
```

### Research Foundation

**Object-Capability Model:**
- Miller, M. (2006): "Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control"
- Shapiro, J. et al. (1999): "EROS: A Fast Capability System"

**Quantum-Specific:**
- Broadbent, A. & Jeffery, S. (2015): "Quantum Homomorphic Encryption for Circuits of Low T-gate Complexity"
  - Discusses capability requirements for quantum operations
- Alagic, G. et al. (2020): "Status Report on the Second Round of the NIST Post-Quantum Cryptography Standardization Process"
  - Cryptographic foundations for capability tokens

---

## Linear Type System

### Motivation

Quantum resources have unique properties:
- **No-cloning**: Cannot duplicate quantum states [Wootters & Zurek, 1982]
- **Single-owner**: Each qubit has exactly one owner
- **Use-once**: Measurement destroys quantum state

Traditional reference counting and garbage collection are **incompatible** with quantum semantics.

### Linear Handles

QMK uses **linear types** to enforce single-ownership:

```python
class VirtualQubitHandle:
    """
    Linear handle to virtual qubit.
    
    Properties:
    - Single-owner: Cannot be copied
    - Must be used exactly once
    - Automatic cleanup on scope exit
    """
    
    def __init__(self, vq_id: str, tenant_id: str):
        self.vq_id = vq_id
        self.tenant_id = tenant_id
        self._consumed = False
    
    def consume(self) -> str:
        """Consume handle (use-once semantics)."""
        if self._consumed:
            raise LinearityViolation("Handle already consumed")
        self._consumed = True
        return self.vq_id
```

### Linearity Enforcement

**Static Checks (QVM Verifier):**
1. Each VQ handle used exactly once
2. No handle aliasing
3. All handles eventually consumed or freed
4. No dangling references

**Runtime Checks (Microkernel):**
1. Handle signature verification
2. Tenant ownership validation
3. Consumption tracking
4. Automatic cleanup

### Benefits

1. **Prevents aliasing**: No accidental sharing of quantum states
2. **Prevents use-after-free**: Consumed handles cannot be reused
3. **Prevents leaks**: All resources explicitly managed
4. **Prevents cross-tenant entanglement**: Handles bound to tenants

### Research Foundation

**Linear Types:**
- Wadler, P. (1990): "Linear Types Can Change the World"
- Walker, D. (2005): "Substructural Type Systems"

**Quantum Linear Logic:**
- Abramsky, S. & Coecke, B. (2004): "A Categorical Semantics of Quantum Protocols"
- Selinger, P. & Valiron, B. (2006): "A Lambda Calculus for Quantum Computation with Classical Control"
- Paykin, J. et al. (2017): "QWIRE: A Core Language for Quantum Circuits"

**Quantum No-Cloning:**
- Wootters, W. & Zurek, W. (1982): "A Single Quantum Cannot be Cloned"
- Dieks, D. (1982): "Communication by EPR Devices"

---

## Multi-Tenant Isolation

### Isolation Mechanisms

QMK provides **strong isolation** between tenants using multiple mechanisms:

#### 1. Namespace Isolation

Each tenant has a unique namespace:
```
tenant_id → namespace → {VQs, channels, jobs, sessions}
```

**Properties:**
- No cross-namespace references
- Namespace-scoped resource IDs
- Cryptographic namespace binding

#### 2. Resource Quotas

Per-tenant limits enforced by microkernel:

```python
class TenantQuota:
    max_sessions: int = 10
    max_jobs_per_session: int = 100
    max_logical_qubits: int = 1000
    max_physical_qubits: int = 10000
    max_channels: int = 100
    max_concurrent_jobs: int = 10
    max_jobs_per_minute: int = 60
    max_api_calls_per_minute: int = 1000
```

**Enforcement:**
- Pre-allocation checks
- Runtime monitoring
- Graceful degradation
- Quota exceeded → operation denied

#### 3. Physical Qubit Isolation

Physical qubits are **never shared** between tenants:
- Dedicated allocation per tenant
- No physical qubit reuse without reset
- Explicit deallocation required

#### 4. Timing Isolation

Prevent timing side-channels:
- Constant-time operations where possible
- Noise injection for timing-sensitive ops
- Randomized scheduling

### Tenant Lifecycle

```
1. Create: Admin creates tenant with quota
2. Authenticate: Tenant proves identity
3. Authorize: Capabilities granted
4. Execute: Jobs run in isolated namespace
5. Monitor: Resource usage tracked
6. Audit: All operations logged
7. Terminate: Resources cleaned up
```

### Research Foundation

**Multi-Tenancy:**
- Ristenpart, T. et al. (2009): "Hey, You, Get Off of My Cloud: Exploring Information Leakage in Third-Party Compute Clouds"
- Varadarajan, V. et al. (2012): "Resource-Freeing Attacks: Improve Your Cloud Performance (at Your Neighbor's Expense)"

**Quantum Multi-Tenancy:**
- Häner, T. et al. (2020): "Quantum Cloud Computing: A Review"
  - Discusses isolation requirements for quantum cloud services
- Pirandola, S. et al. (2020): "Advances in Quantum Cryptography"
  - Security considerations for shared quantum resources

---

## Entanglement Firewall

### Problem

Entanglement between tenants enables **information leakage**:
- Tenant A creates entangled pair
- Shares one qubit with Tenant B
- Tenant A can infer B's measurements

This violates isolation!

### Solution: Entanglement Firewall

QMK prevents unauthorized cross-tenant entanglement:

#### 1. Channel-Based Entanglement

Entanglement only through explicit channels:
```python
# Requires CAP_LINK capability
channel = kernel.create_channel(tenant_a, tenant_b)
kernel.entangle_via_channel(vq_a, vq_b, channel)
```

#### 2. Brokered Capabilities

Cross-tenant channels require **both tenants** to agree:
```
1. Tenant A requests channel to Tenant B
2. Kernel notifies Tenant B
3. Tenant B accepts/rejects
4. If accepted, kernel creates signed channel
5. Both tenants receive channel handles
```

#### 3. Entanglement Tracking

Microkernel tracks all entanglement:
```python
class EntanglementGraph:
    """
    Tracks entanglement relationships.
    
    Invariant: No edges between different tenants
    unless explicit channel exists.
    """
    
    def add_entanglement(self, vq1, vq2, channel=None):
        tenant1 = self.get_tenant(vq1)
        tenant2 = self.get_tenant(vq2)
        
        if tenant1 != tenant2:
            # Cross-tenant entanglement
            if channel is None:
                raise EntanglementFirewallViolation()
            if not self.verify_channel(channel, tenant1, tenant2):
                raise UnauthorizedChannel()
        
        self.graph.add_edge(vq1, vq2)
```

#### 4. Channel Revocation

Channels can be revoked:
- By either tenant
- By administrator
- On quota exceeded
- On security policy violation

### Entanglement Verification

**Static Verification (QVM):**
- Check all two-qubit gates
- Verify channel handles for cross-tenant ops
- Reject graphs with unauthorized entanglement

**Runtime Verification (Kernel):**
- Validate channel signatures
- Check tenant authorization
- Update entanglement graph
- Audit all cross-tenant operations

### Research Foundation

**Quantum Entanglement Security:**
- Ekert, A. (1991): "Quantum Cryptography Based on Bell's Theorem"
  - Foundational work on entanglement-based security
- Scarani, V. et al. (2009): "The Security of Practical Quantum Key Distribution"
  - Security analysis of entanglement-based protocols
- Pirandola, S. et al. (2017): "Theory of Channel Simulation and Bounds for Private Communication"
  - Bounds on information leakage through entanglement

**Quantum Firewalls:**
- Almheiri, A. et al. (2013): "Black Holes: Complementarity or Firewalls?"
  - Theoretical foundations (physics context, but relevant concepts)
- Broadbent, A. et al. (2009): "Universal Blind Quantum Computation"
  - Techniques for preventing information leakage in delegated quantum computation

---

## Audit and Attestation

### Audit System

QMK maintains **comprehensive audit logs** for all security-relevant events:

#### Audit Event Types

```python
class AuditEventType(Enum):
    # Authentication & Authorization
    TENANT_CREATED = "tenant_created"
    TENANT_AUTHENTICATED = "tenant_authenticated"
    CAPABILITY_GRANTED = "capability_granted"
    CAPABILITY_REVOKED = "capability_revoked"
    CAPABILITY_DENIED = "capability_denied"
    
    # Resource Operations
    VQ_ALLOCATED = "vq_allocated"
    VQ_DEALLOCATED = "vq_deallocated"
    CHANNEL_CREATED = "channel_created"
    CHANNEL_CLOSED = "channel_closed"
    
    # Job Execution
    JOB_SUBMITTED = "job_submitted"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    # Security Events
    QUOTA_EXCEEDED = "quota_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    FIREWALL_VIOLATION = "firewall_violation"
    LINEARITY_VIOLATION = "linearity_violation"
    
    # Administrative
    POLICY_UPDATED = "policy_updated"
    TENANT_SUSPENDED = "tenant_suspended"
```

#### Audit Log Format

```json
{
  "timestamp": "2025-10-19T14:34:22.123Z",
  "event_type": "capability_denied",
  "severity": "warning",
  "tenant_id": "tenant_abc123",
  "session_id": "sess_xyz789",
  "job_id": "job_456def",
  "details": {
    "required_capability": "CAP_TELEPORT",
    "granted_capabilities": ["CAP_ALLOC", "CAP_MEASURE"],
    "operation": "TELEPORT_CNOT",
    "reason": "missing_capability"
  },
  "source_ip": "192.168.1.100",
  "user_agent": "qmk-client/1.0"
}
```

### Attestation

QMK provides **cryptographic attestation** of execution:

#### 1. Job Attestation

Each job receives a signed attestation:
```python
class JobAttestation:
    job_id: str
    tenant_id: str
    qvm_graph_hash: str  # SHA-256 of QVM graph
    execution_start: float
    execution_end: float
    resources_used: Dict[str, int]
    measurements: Dict[str, int]
    signature: bytes  # HMAC-SHA256
```

#### 2. Epoch Summaries

Periodic summaries of system state:
```python
class EpochSummary:
    epoch_id: int
    start_time: float
    end_time: float
    total_jobs: int
    total_operations: int
    tenant_summaries: Dict[str, TenantSummary]
    merkle_root: bytes  # Merkle tree of all audit events
    signature: bytes
```

#### 3. Verifiable Logs

Audit logs use **Merkle trees** for tamper-evidence:
- Each event hashed
- Events organized in Merkle tree
- Root hash signed by kernel
- Clients can verify log integrity

### Audit Queries

Administrators can query audit logs:
```python
# Find all capability denials for tenant
events = audit_logger.query(
    event_type=AuditEventType.CAPABILITY_DENIED,
    tenant_id="tenant_abc123",
    time_range=(start, end)
)

# Find all cross-tenant channels
channels = audit_logger.query(
    event_type=AuditEventType.CHANNEL_CREATED,
    filter=lambda e: e.details.get("cross_tenant", False)
)
```

### Research Foundation

**Audit Systems:**
- Schneier, B. & Kelsey, J. (1999): "Secure Audit Logs to Support Computer Forensics"
- Crosby, S. et al. (2009): "Efficient Data Structures for Tamper-Evident Logging"

**Blockchain/Merkle Trees:**
- Merkle, R. (1988): "A Digital Signature Based on a Conventional Encryption Function"
- Naor, M. & Nissim, K. (1998): "Certificate Revocation and Certificate Update"

**Quantum Attestation:**
- Fitzsimons, J. & Kashefi, E. (2017): "Unconditionally Verifiable Blind Quantum Computation"
- Gheorghiu, A. et al. (2019): "Verification of Quantum Computation: An Overview of Existing Approaches"

---

## Research Foundations

### Key Papers

**Capability-Based Security:**
1. Dennis, J. & Van Horn, E. (1966): "Programming Semantics for Multiprogrammed Computations"
   - Original capability model
2. Miller, M. et al. (2003): "Capability Myths Demolished"
   - Modern object-capability model
3. Shapiro, J. et al. (1999): "EROS: A Fast Capability System"
   - Practical capability OS

**Linear Types:**
4. Wadler, P. (1990): "Linear Types Can Change the World"
   - Foundational linear type theory
5. Paykin, J. et al. (2017): "QWIRE: A Core Language for Quantum Circuits"
   - Linear types for quantum computing
6. Selinger, P. & Valiron, B. (2006): "A Lambda Calculus for Quantum Computation"
   - Quantum lambda calculus

**Quantum Security:**
7. Wootters, W. & Zurek, W. (1982): "A Single Quantum Cannot be Cloned"
   - No-cloning theorem
8. Broadbent, A. et al. (2009): "Universal Blind Quantum Computation"
   - Secure delegated quantum computation
9. Alagic, G. et al. (2020): "NIST Post-Quantum Cryptography Standardization"
   - Cryptographic foundations

**Multi-Tenancy:**
10. Ristenpart, T. et al. (2009): "Hey, You, Get Off of My Cloud"
    - Cloud security and isolation
11. Varadarajan, V. et al. (2012): "Resource-Freeing Attacks"
    - Multi-tenant resource attacks

**Quantum Information:**
12. Nielsen, M. & Chuang, I. (2010): "Quantum Computation and Quantum Information"
    - Comprehensive quantum computing textbook
13. Preskill, J. (2018): "Quantum Computing in the NISQ Era and Beyond"
    - Modern quantum computing overview

---

## Security Guarantees

### Formal Guarantees

QMK provides the following **provable** security guarantees:

#### 1. Tenant Isolation

**Guarantee**: No tenant can access another tenant's quantum states without explicit authorization.

**Mechanism**:
- Namespace isolation
- Cryptographic handle signing
- Entanglement firewall
- Capability-based access control

**Proof Sketch**:
- All VQ handles signed with tenant-specific key
- Kernel verifies signature on every operation
- Cross-tenant operations require channel with both signatures
- Entanglement graph enforces firewall invariant

#### 2. Linearity

**Guarantee**: Each quantum resource is used exactly once (no aliasing, no double-free).

**Mechanism**:
- Linear type system
- Static verification in QVM
- Runtime consumption tracking

**Proof Sketch**:
- QVM verifier checks each handle used exactly once
- Kernel tracks handle consumption
- Consumed handles cannot be reused
- All handles eventually freed or consumed

#### 3. Capability Enforcement

**Guarantee**: No operation succeeds without required capabilities.

**Mechanism**:
- Capability tokens with HMAC signatures
- Complete mediation
- Fail-safe defaults

**Proof Sketch**:
- Every privileged operation checks capabilities
- Capability tokens cryptographically verified
- Missing capability → operation denied
- No bypass mechanisms

#### 4. Resource Bounds

**Guarantee**: No tenant can exceed quota limits.

**Mechanism**:
- Pre-allocation quota checks
- Runtime resource tracking
- Graceful degradation

**Proof Sketch**:
- Allocation checks quota before proceeding
- Kernel maintains accurate resource counts
- Quota exceeded → allocation fails
- No resource leaks (linearity guarantee)

#### 5. Audit Completeness

**Guarantee**: All security-relevant events are logged.

**Mechanism**:
- Comprehensive audit points
- Tamper-evident logs (Merkle trees)
- Cryptographic attestation

**Proof Sketch**:
- Every security check logs result
- Logs stored in Merkle tree
- Root hash signed by kernel
- Clients can verify log integrity

### Limitations

**What QMK Does NOT Guarantee:**

1. **Physical Security**: Hardware attacks out of scope
2. **Side-Channels**: Timing/power analysis not fully mitigated
3. **Quantum Algorithm Attacks**: Cannot prevent Shor's algorithm
4. **Compromised Kernel**: TCB must be trusted
5. **Perfect Isolation**: Covert channels may exist

### Threat Mitigation Summary

| Threat | Mitigation | Strength |
|--------|-----------|----------|
| Unauthorized access | Capabilities + Signatures | Strong |
| Resource exhaustion | Quotas + Rate limiting | Strong |
| Cross-tenant entanglement | Entanglement firewall | Strong |
| Handle aliasing | Linear types | Strong |
| Privilege escalation | Capability attenuation | Strong |
| Information leakage | Namespace isolation | Moderate |
| Timing side-channels | Noise injection | Weak |
| Covert channels | Monitoring | Weak |

---

## Security Best Practices

### For Administrators

1. **Principle of Least Privilege**: Grant minimum required capabilities
2. **Regular Audits**: Review audit logs for anomalies
3. **Quota Tuning**: Set appropriate resource limits
4. **Capability Rotation**: Periodically rotate capability keys
5. **Incident Response**: Have plan for security incidents

### For Tenants

1. **Protect Capabilities**: Never share capability tokens
2. **Validate Inputs**: Check all QVM graphs before submission
3. **Monitor Usage**: Track resource consumption
4. **Report Anomalies**: Report suspicious behavior
5. **Clean Up Resources**: Explicitly free unused resources

### For Developers

1. **Defense in Depth**: Multiple independent checks
2. **Fail Securely**: Default to deny
3. **Complete Mediation**: Check every access
4. **Audit Everything**: Log all security events
5. **Test Security**: Regular security testing

---

## Conclusion

QMK's security model provides **strong, multi-layered protection** for quantum computing infrastructure. The combination of capability-based security, linear types, multi-tenant isolation, and comprehensive auditing creates a robust defense against a wide range of threats.

The security architecture is grounded in **decades of research** in capability systems, linear types, and quantum information theory, adapted specifically for the unique challenges of quantum computing.

**Key Strengths:**
- ✅ Strong tenant isolation
- ✅ Unforgeable capabilities
- ✅ Provable linearity guarantees
- ✅ Entanglement firewall
- ✅ Comprehensive audit trail
- ✅ Research-backed design

**Areas for Future Work:**
- Side-channel mitigation
- Formal verification
- Quantum-safe cryptography
- Advanced covert channel detection

---

## References

See inline citations throughout document. Key references:

1. Dennis & Van Horn (1966) - Capability model
2. Wadler (1990) - Linear types
3. Wootters & Zurek (1982) - No-cloning theorem
4. Miller et al. (2003) - Object-capabilities
5. Paykin et al. (2017) - Quantum linear types
6. Broadbent et al. (2009) - Blind quantum computation
7. Alagic et al. (2020) - Post-quantum cryptography
8. Ristenpart et al. (2009) - Cloud multi-tenancy
9. Schneier & Kelsey (1999) - Secure audit logs
10. Gheorghiu et al. (2019) - Quantum verification

---

**Document Version**: 1.0  
**Last Updated**: October 19, 2025  
**Status**: Production  
**Maintainer**: QMK Security Team
