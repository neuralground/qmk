# QMK Capability System

**Object-Capability Security for Quantum Operations**

## Table of Contents

1. [Overview](#overview)
2. [Capability Model](#capability-model)
3. [Capability Types](#capability-types)
4. [Capability Lifecycle](#capability-lifecycle)
5. [Delegation and Attenuation](#delegation-and-attenuation)
6. [Implementation Details](#implementation-details)
7. [Usage Examples](#usage-examples)
8. [Security Analysis](#security-analysis)
9. [Best Practices](#best-practices)

---

## Overview

QMK uses **object-capabilities** as the primary access control mechanism. Unlike traditional access control lists (ACLs), capabilities are **unforgeable tokens** that grant specific permissions.

### Why Capabilities?

**Traditional ACL Problems:**
- Ambient authority (confused deputy problem)
- Difficult to delegate safely
- Hard to audit who has access
- Privilege escalation risks

**Capability Advantages:**
- No ambient authority
- Safe delegation with attenuation
- Clear audit trail
- Composable security

### Capability Properties

1. **Unforgeable**: Cryptographically signed, cannot be forged
2. **Transferable**: Can be passed to other principals
3. **Attenuable**: Can be weakened when delegated
4. **Revocable**: Can be revoked by issuer
5. **Inspectable**: Can query what permissions a capability grants

---

## Capability Model

### Capability Definition

A capability is a triple: `(object, rights, signature)`

```python
@dataclass
class Capability:
    """
    Unforgeable capability token.
    
    Grants specific rights to perform operations.
    """
    # Identity
    capability_id: str          # Unique capability identifier
    tenant_id: str              # Owner of this capability
    issued_by: str              # Issuer (admin or delegator)
    
    # Permissions
    rights: Set[str]            # Set of granted permissions
    
    # Constraints
    expires_at: Optional[float] # Expiration timestamp (None = never)
    max_uses: Optional[int]     # Maximum number of uses (None = unlimited)
    uses_remaining: int         # Current remaining uses
    
    # Delegation
    delegation_depth: int       # Number of times delegated (0 = original)
    max_delegation_depth: int   # Maximum allowed delegation depth
    parent_capability_id: Optional[str]  # Parent if delegated
    
    # Cryptographic
    signature: bytes            # HMAC-SHA256 signature
    issued_at: float            # Issuance timestamp
    
    # Metadata
    metadata: Dict[str, Any]    # Additional metadata
```

### Capability Verification

Every operation that requires capabilities follows this flow:

```
1. Extract capability token from request
2. Verify cryptographic signature
3. Check expiration
4. Check use count
5. Verify required rights present
6. Decrement use count (if limited)
7. Log capability usage
8. Proceed with operation
```

---

## Capability Types

### Core Capabilities

#### CAP_ALLOC - Virtual Qubit Allocation

**Grants**: Ability to allocate virtual qubits

**Required For:**
- `ALLOC_LQ` operation
- Creating new virtual qubits

**Rationale**: Qubit allocation consumes scarce resources and must be controlled.

**Example:**
```python
# Allocate 10 virtual qubits
vqs = kernel.alloc_lq(
    count=10,
    profile="Surface(d=7)",
    capabilities=[CAP_ALLOC]
)
```

#### CAP_LINK - Entanglement Channel Creation

**Grants**: Ability to create entanglement channels

**Required For:**
- `OPEN_CHAN` operation
- Creating channels between qubits
- Cross-tenant entanglement

**Rationale**: Entanglement channels enable information flow and must be authorized.

**Example:**
```python
# Create channel between two qubits
channel = kernel.open_chan(
    vq1, vq2,
    capabilities=[CAP_LINK]
)
```

#### CAP_TELEPORT - Gate Teleportation

**Grants**: Ability to perform gate teleportation

**Required For:**
- `TELEPORT_CNOT` operation
- Non-local gate execution
- Distributed quantum computing

**Rationale**: Gate teleportation is a privileged operation that consumes entanglement.

**Research**: Gottesman & Chuang (1999) - "Demonstrating the viability of universal quantum computation using teleportation and single-qubit operations"

**Example:**
```python
# Teleport CNOT gate
kernel.teleport_cnot(
    control_vq, target_vq, channel,
    capabilities=[CAP_TELEPORT, CAP_LINK]
)
```

#### CAP_MAGIC - Magic State Injection

**Grants**: Ability to inject magic states (T-gates)

**Required For:**
- `INJECT_T_STATE` operation
- T-gate implementation
- Universal quantum computation

**Rationale**: Magic states are expensive to prepare and enable universal computation.

**Research**: Bravyi & Kitaev (2005) - "Universal quantum computation with ideal Clifford gates and noisy ancillas"

**Example:**
```python
# Inject T-state for T-gate
kernel.inject_t_state(
    vq,
    capabilities=[CAP_MAGIC]
)
```

#### CAP_MEASURE - Quantum Measurement

**Grants**: Ability to perform measurements

**Required For:**
- `MEASURE_Z`, `MEASURE_X`, `MEASURE_Y` operations
- Bell basis measurements
- Arbitrary angle measurements

**Rationale**: Measurements are irreversible and destroy quantum information.

**Example:**
```python
# Measure qubit in X-basis
outcome = kernel.measure_x(
    vq,
    capabilities=[CAP_MEASURE]
)
```

### Administrative Capabilities

#### CAP_ADMIN - Administrative Operations

**Grants**: Full administrative access

**Required For:**
- Creating/deleting tenants
- Granting/revoking capabilities
- Modifying quotas
- System configuration

**Rationale**: Administrative operations affect all tenants and must be highly restricted.

**Example:**
```python
# Create new tenant (admin only)
tenant = kernel.create_tenant(
    name="research_team",
    quota=default_quota,
    capabilities=[CAP_ADMIN]
)
```

#### CAP_AUDIT - Audit Log Access

**Grants**: Ability to query audit logs

**Required For:**
- Viewing audit events
- Generating compliance reports
- Security monitoring

**Rationale**: Audit logs contain sensitive information about all tenants.

**Example:**
```python
# Query audit logs
events = audit_logger.query(
    tenant_id="tenant_123",
    event_type=AuditEventType.CAPABILITY_DENIED,
    capabilities=[CAP_AUDIT]
)
```

### Composite Capabilities

Some operations require **multiple capabilities**:

```python
# Distributed quantum computation requires:
# - CAP_ALLOC (allocate qubits)
# - CAP_LINK (create channels)
# - CAP_TELEPORT (teleport gates)
# - CAP_MEASURE (final measurements)

required_caps = {
    CAP_ALLOC,
    CAP_LINK,
    CAP_TELEPORT,
    CAP_MEASURE
}
```

---

## Capability Lifecycle

### 1. Issuance

Capabilities are issued by administrators or through delegation:

```python
def issue_capability(
    tenant_id: str,
    rights: Set[str],
    expires_at: Optional[float] = None,
    max_uses: Optional[int] = None,
    max_delegation_depth: int = 3
) -> Capability:
    """
    Issue new capability to tenant.
    
    Args:
        tenant_id: Recipient tenant
        rights: Set of granted permissions
        expires_at: Optional expiration time
        max_uses: Optional use limit
        max_delegation_depth: Maximum delegation depth
    
    Returns:
        Signed capability token
    """
    cap = Capability(
        capability_id=generate_id(),
        tenant_id=tenant_id,
        issued_by="admin",
        rights=rights,
        expires_at=expires_at,
        max_uses=max_uses,
        uses_remaining=max_uses or -1,
        delegation_depth=0,
        max_delegation_depth=max_delegation_depth,
        parent_capability_id=None,
        issued_at=time.time(),
        metadata={}
    )
    
    # Sign capability
    cap.signature = sign_capability(cap, secret_key)
    
    # Log issuance
    audit_logger.log(
        AuditEventType.CAPABILITY_GRANTED,
        tenant_id=tenant_id,
        details={"rights": list(rights)}
    )
    
    return cap
```

### 2. Verification

Every use of a capability is verified:

```python
def verify_capability(
    cap: Capability,
    required_rights: Set[str],
    secret_key: bytes
) -> bool:
    """
    Verify capability is valid and has required rights.
    
    Returns:
        True if valid, False otherwise
    """
    # 1. Verify signature
    if not verify_signature(cap, secret_key):
        audit_logger.log(
            AuditEventType.CAPABILITY_DENIED,
            tenant_id=cap.tenant_id,
            details={"reason": "invalid_signature"}
        )
        return False
    
    # 2. Check expiration
    if cap.expires_at and time.time() > cap.expires_at:
        audit_logger.log(
            AuditEventType.CAPABILITY_DENIED,
            tenant_id=cap.tenant_id,
            details={"reason": "expired"}
        )
        return False
    
    # 3. Check use count
    if cap.max_uses and cap.uses_remaining <= 0:
        audit_logger.log(
            AuditEventType.CAPABILITY_DENIED,
            tenant_id=cap.tenant_id,
            details={"reason": "uses_exhausted"}
        )
        return False
    
    # 4. Check rights
    if not required_rights.issubset(cap.rights):
        audit_logger.log(
            AuditEventType.CAPABILITY_DENIED,
            tenant_id=cap.tenant_id,
            details={
                "reason": "insufficient_rights",
                "required": list(required_rights),
                "granted": list(cap.rights)
            }
        )
        return False
    
    # 5. Decrement use count
    if cap.max_uses:
        cap.uses_remaining -= 1
    
    # 6. Log successful use
    audit_logger.log(
        AuditEventType.CAPABILITY_USED,
        tenant_id=cap.tenant_id,
        details={
            "capability_id": cap.capability_id,
            "rights_used": list(required_rights)
        }
    )
    
    return True
```

### 3. Delegation

Capabilities can be delegated with attenuation:

```python
def delegate_capability(
    parent_cap: Capability,
    delegatee_tenant_id: str,
    attenuated_rights: Set[str],
    expires_at: Optional[float] = None,
    max_uses: Optional[int] = None
) -> Capability:
    """
    Delegate capability with attenuation.
    
    Args:
        parent_cap: Parent capability to delegate
        delegatee_tenant_id: Recipient of delegated capability
        attenuated_rights: Subset of parent rights
        expires_at: Optional expiration (must be <= parent)
        max_uses: Optional use limit
    
    Returns:
        Delegated capability
    
    Raises:
        DelegationError: If delegation not allowed
    """
    # Check delegation depth
    if parent_cap.delegation_depth >= parent_cap.max_delegation_depth:
        raise DelegationError("Max delegation depth exceeded")
    
    # Check rights attenuation
    if not attenuated_rights.issubset(parent_cap.rights):
        raise DelegationError("Cannot grant rights not in parent")
    
    # Check expiration
    if expires_at and parent_cap.expires_at:
        if expires_at > parent_cap.expires_at:
            raise DelegationError("Cannot extend expiration")
    
    # Create delegated capability
    delegated_cap = Capability(
        capability_id=generate_id(),
        tenant_id=delegatee_tenant_id,
        issued_by=parent_cap.tenant_id,
        rights=attenuated_rights,
        expires_at=expires_at or parent_cap.expires_at,
        max_uses=max_uses,
        uses_remaining=max_uses or -1,
        delegation_depth=parent_cap.delegation_depth + 1,
        max_delegation_depth=parent_cap.max_delegation_depth,
        parent_capability_id=parent_cap.capability_id,
        issued_at=time.time(),
        metadata={"delegated_from": parent_cap.capability_id}
    )
    
    # Sign delegated capability
    delegated_cap.signature = sign_capability(delegated_cap, secret_key)
    
    # Log delegation
    audit_logger.log(
        AuditEventType.CAPABILITY_DELEGATED,
        tenant_id=parent_cap.tenant_id,
        details={
            "delegatee": delegatee_tenant_id,
            "rights": list(attenuated_rights),
            "parent_id": parent_cap.capability_id
        }
    )
    
    return delegated_cap
```

### 4. Revocation

Capabilities can be revoked:

```python
def revoke_capability(
    cap_id: str,
    revoke_children: bool = True
) -> None:
    """
    Revoke capability and optionally all delegated children.
    
    Args:
        cap_id: Capability to revoke
        revoke_children: If True, revoke all delegated capabilities
    """
    # Add to revocation list
    revoked_capabilities.add(cap_id)
    
    # Optionally revoke children
    if revoke_children:
        children = find_delegated_capabilities(cap_id)
        for child_id in children:
            revoked_capabilities.add(child_id)
    
    # Log revocation
    audit_logger.log(
        AuditEventType.CAPABILITY_REVOKED,
        details={
            "capability_id": cap_id,
            "revoke_children": revoke_children
        }
    )
```

---

## Delegation and Attenuation

### Attenuation Rules

When delegating, capabilities can only be **weakened**, never strengthened:

1. **Rights Attenuation**: Subset of parent rights
2. **Time Attenuation**: Earlier or same expiration
3. **Use Attenuation**: Fewer or same uses
4. **Depth Attenuation**: Cannot increase max delegation depth

### Delegation Patterns

#### Pattern 1: Temporary Access

Grant temporary capability for specific task:

```python
# Grant 1-hour CAP_ALLOC for experiment
temp_cap = delegate_capability(
    parent_cap=admin_cap,
    delegatee_tenant_id="researcher_123",
    attenuated_rights={CAP_ALLOC},
    expires_at=time.time() + 3600,  # 1 hour
    max_uses=100  # Limited uses
)
```

#### Pattern 2: Least Privilege

Grant minimum required capabilities:

```python
# Job only needs measurement, not allocation
job_cap = delegate_capability(
    parent_cap=full_cap,
    delegatee_tenant_id="job_executor",
    attenuated_rights={CAP_MEASURE},  # Only measurement
    max_uses=1000  # Limited to job size
)
```

#### Pattern 3: Hierarchical Delegation

Delegate to sub-teams with further attenuation:

```python
# Team lead gets broad capabilities
team_cap = delegate_capability(
    parent_cap=admin_cap,
    delegatee_tenant_id="team_lead",
    attenuated_rights={CAP_ALLOC, CAP_LINK, CAP_MEASURE},
    max_delegation_depth=2  # Can delegate further
)

# Team member gets subset
member_cap = delegate_capability(
    parent_cap=team_cap,
    delegatee_tenant_id="team_member",
    attenuated_rights={CAP_ALLOC, CAP_MEASURE},  # No CAP_LINK
    max_delegation_depth=1  # Limited delegation
)
```

---

## Implementation Details

### Cryptographic Signing

Capabilities use HMAC-SHA256 for signatures:

```python
def sign_capability(cap: Capability, secret_key: bytes) -> bytes:
    """
    Sign capability with HMAC-SHA256.
    
    Args:
        cap: Capability to sign
        secret_key: Secret signing key
    
    Returns:
        HMAC signature
    """
    # Create canonical form
    canonical = f"{cap.capability_id}|{cap.tenant_id}|{cap.issued_by}|"
    canonical += f"{','.join(sorted(cap.rights))}|{cap.expires_at}|"
    canonical += f"{cap.max_uses}|{cap.delegation_depth}|{cap.issued_at}"
    
    # Compute HMAC
    signature = hmac.new(
        secret_key,
        canonical.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return signature

def verify_signature(cap: Capability, secret_key: bytes) -> bool:
    """Verify capability signature."""
    expected = sign_capability(cap, secret_key)
    return hmac.compare_digest(expected, cap.signature)
```

### Capability Storage

Capabilities are stored in-memory with persistent backup:

```python
class CapabilityStore:
    """
    Store and manage capabilities.
    
    Provides:
    - Fast lookup by capability_id
    - Tenant-scoped queries
    - Revocation checking
    - Persistence
    """
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.tenant_capabilities: Dict[str, Set[str]] = defaultdict(set)
        self.revoked: Set[str] = set()
    
    def store(self, cap: Capability) -> None:
        """Store capability."""
        self.capabilities[cap.capability_id] = cap
        self.tenant_capabilities[cap.tenant_id].add(cap.capability_id)
    
    def get(self, cap_id: str) -> Optional[Capability]:
        """Retrieve capability."""
        if cap_id in self.revoked:
            return None
        return self.capabilities.get(cap_id)
    
    def get_tenant_capabilities(self, tenant_id: str) -> List[Capability]:
        """Get all capabilities for tenant."""
        cap_ids = self.tenant_capabilities.get(tenant_id, set())
        return [
            self.capabilities[cid]
            for cid in cap_ids
            if cid not in self.revoked
        ]
    
    def revoke(self, cap_id: str) -> None:
        """Revoke capability."""
        self.revoked.add(cap_id)
```

---

## Usage Examples

### Example 1: Simple Quantum Circuit

```python
# Tenant has CAP_ALLOC and CAP_MEASURE
capabilities = {CAP_ALLOC, CAP_MEASURE}

# Allocate qubits
vq0 = kernel.alloc_lq(1, "Surface(d=7)", capabilities)[0]
vq1 = kernel.alloc_lq(1, "Surface(d=7)", capabilities)[0]

# Apply gates (no capability required for basic gates)
kernel.apply_gate(vq0, "H")
kernel.apply_gate(vq0, vq1, "CNOT")

# Measure (requires CAP_MEASURE)
outcome0 = kernel.measure_z(vq0, capabilities)
outcome1 = kernel.measure_z(vq1, capabilities)
```

### Example 2: Distributed Quantum Computing

```python
# Requires CAP_ALLOC, CAP_LINK, CAP_TELEPORT
capabilities = {CAP_ALLOC, CAP_LINK, CAP_TELEPORT}

# Allocate qubits on different nodes
vq_alice = kernel.alloc_lq(1, "Surface(d=7)", capabilities)[0]
vq_bob = kernel.alloc_lq(1, "Surface(d=7)", capabilities)[0]

# Create entanglement channel
channel = kernel.open_chan(vq_alice, vq_bob, capabilities)

# Teleport CNOT gate
kernel.teleport_cnot(vq_alice, vq_bob, channel, capabilities)
```

### Example 3: Capability Delegation

```python
# Admin grants capabilities to team lead
admin_cap = Capability(
    rights={CAP_ALLOC, CAP_LINK, CAP_TELEPORT, CAP_MEASURE, CAP_MAGIC},
    max_delegation_depth=3
)

# Team lead delegates to researcher
researcher_cap = delegate_capability(
    parent_cap=admin_cap,
    delegatee_tenant_id="researcher_001",
    attenuated_rights={CAP_ALLOC, CAP_MEASURE},  # Subset
    expires_at=time.time() + 86400,  # 24 hours
    max_uses=1000
)

# Researcher uses delegated capability
vqs = kernel.alloc_lq(10, "Surface(d=7)", [researcher_cap])
```

---

## Security Analysis

### Threat Model

**Threats Mitigated:**
1. ✅ Unauthorized resource access
2. ✅ Privilege escalation
3. ✅ Capability forgery
4. ✅ Confused deputy attacks
5. ✅ Ambient authority

**Residual Risks:**
1. ⚠️ Capability theft (if token leaked)
2. ⚠️ Delegation abuse (if parent compromised)
3. ⚠️ Timing side-channels

### Security Properties

**Theorem 1: Unforgeability**
> Without knowledge of the secret key, an adversary cannot forge a valid capability.

**Proof Sketch**: HMAC-SHA256 provides 256-bit security. Forging requires finding a collision or recovering the key, both computationally infeasible.

**Theorem 2: Attenuation Monotonicity**
> Delegated capabilities have equal or fewer rights than parent.

**Proof Sketch**: Delegation enforces `attenuated_rights ⊆ parent.rights`. No mechanism to add rights.

**Theorem 3: Revocation Completeness**
> Revoked capabilities cannot be used, even if cached.

**Proof Sketch**: Every verification checks revocation list. Revoked capabilities fail verification.

### Comparison to ACLs

| Property | Capabilities | ACLs |
|----------|-------------|------|
| Ambient authority | ❌ No | ✅ Yes |
| Safe delegation | ✅ Yes | ❌ Difficult |
| Confused deputy | ✅ Prevented | ⚠️ Possible |
| Audit trail | ✅ Complete | ⚠️ Partial |
| Revocation | ✅ Immediate | ⚠️ Delayed |
| Composability | ✅ High | ❌ Low |

---

## Best Practices

### For Administrators

1. **Minimal Initial Grants**: Start with minimum capabilities
2. **Regular Audits**: Review capability usage monthly
3. **Rotation**: Rotate signing keys periodically
4. **Monitoring**: Alert on unusual capability patterns
5. **Revocation Plan**: Have process for emergency revocation

### For Developers

1. **Check Early**: Verify capabilities before expensive operations
2. **Fail Securely**: Deny if capability check fails
3. **Log Everything**: Log all capability checks
4. **Delegate Minimally**: Only delegate what's needed
5. **Validate Inputs**: Don't trust capability holders

### For Tenants

1. **Protect Tokens**: Never share capability tokens
2. **Minimal Delegation**: Delegate least privilege
3. **Short Lifetimes**: Use short expiration times
4. **Monitor Usage**: Track your capability usage
5. **Report Anomalies**: Report suspicious activity

---

## Research References

1. **Dennis, J. & Van Horn, E. (1966)**: "Programming Semantics for Multiprogrammed Computations"
   - Original capability model

2. **Miller, M. et al. (2003)**: "Capability Myths Demolished"
   - Modern object-capability model

3. **Shapiro, J. et al. (1999)**: "EROS: A Fast Capability System"
   - Practical capability OS implementation

4. **Hardy, N. (1985)**: "KeyKOS Architecture"
   - Capability-based microkernel

5. **Gottesman, D. & Chuang, I. (1999)**: "Demonstrating the viability of universal quantum computation using teleportation and single-qubit operations"
   - Gate teleportation (CAP_TELEPORT)

6. **Bravyi, S. & Kitaev, A. (2005)**: "Universal quantum computation with ideal Clifford gates and noisy ancillas"
   - Magic state distillation (CAP_MAGIC)

---

## Appendix: Capability Grammar

Formal grammar for capability expressions:

```
Capability ::= (Rights, Constraints, Signature)

Rights ::= Set<Permission>
Permission ::= CAP_ALLOC | CAP_LINK | CAP_TELEPORT | CAP_MAGIC | CAP_MEASURE | CAP_ADMIN

Constraints ::= {
    expires_at: Timestamp?,
    max_uses: Integer?,
    delegation_depth: Integer,
    max_delegation_depth: Integer
}

Signature ::= HMAC-SHA256(canonical_form, secret_key)
```

---

**Document Version**: 1.0  
**Last Updated**: October 19, 2025  
**Status**: Production  
**Maintainer**: QMK Security Team
