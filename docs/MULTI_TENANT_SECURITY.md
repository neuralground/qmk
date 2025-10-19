# Multi-Tenant Security in QMK

**Isolation, Resource Management, and Cross-Tenant Protection**

## Table of Contents

1. [Overview](#overview)
2. [Isolation Architecture](#isolation-architecture)
3. [Resource Quotas](#resource-quotas)
4. [Entanglement Firewall](#entanglement-firewall)
5. [Cross-Tenant Channels](#cross-tenant-channels)
6. [Attack Scenarios](#attack-scenarios)
7. [Performance Isolation](#performance-isolation)
8. [Monitoring and Detection](#monitoring-and-detection)

---

## Overview

QMK supports **secure multi-tenancy** where multiple independent users share the same quantum computing infrastructure while maintaining strong isolation guarantees.

### Multi-Tenancy Challenges in Quantum Computing

Quantum systems present unique multi-tenancy challenges:

1. **Entanglement Leakage**: Shared entanglement enables information flow
2. **State Fragility**: Unauthorized access destroys quantum information
3. **Resource Scarcity**: Quantum resources are limited and expensive
4. **Non-Clonability**: Cannot backup quantum states
5. **Measurement Irreversibility**: Measurements are destructive

### Isolation Goals

1. **Confidentiality**: Tenant A cannot read Tenant B's quantum states
2. **Integrity**: Tenant A cannot modify Tenant B's qubits
3. **Availability**: Tenant A cannot exhaust resources for Tenant B
4. **Isolation**: No unintended entanglement between tenants
5. **Accountability**: All cross-tenant interactions audited

---

## Isolation Architecture

### Layered Isolation

QMK implements **defense-in-depth** isolation:

```
┌─────────────────────────────────────────┐
│         Layer 1: Namespace              │
│  Logical separation of tenant resources │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      Layer 2: Handle Signing            │
│  Cryptographic binding to tenant        │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│    Layer 3: Entanglement Firewall       │
│  Prevent unauthorized cross-tenant      │
│  entanglement                           │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      Layer 4: Resource Quotas           │
│  Limit resource consumption per tenant  │
└─────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│    Layer 5: Physical Isolation          │
│  Dedicated physical qubits per tenant   │
└─────────────────────────────────────────┘
```

### Tenant Model

```python
@dataclass
class Tenant:
    """
    Represents an isolated tenant.
    
    Each tenant has:
    - Unique identifier
    - Isolated namespace
    - Resource quotas
    - Capability grants
    - Usage tracking
    """
    tenant_id: str              # Unique identifier
    name: str                   # Human-readable name
    namespace: str              # Isolated namespace
    quota: TenantQuota          # Resource limits
    capabilities: Set[str]      # Granted capabilities
    
    # Usage tracking
    active_sessions: int        # Current sessions
    active_jobs: int            # Running jobs
    total_jobs_run: int         # Historical job count
    
    # Security
    created_at: float           # Creation timestamp
    is_active: bool             # Active/suspended
    metadata: Dict              # Additional metadata
```

### Namespace Isolation

Each tenant operates in an isolated namespace:

```python
class TenantNamespace:
    """
    Isolated namespace for tenant resources.
    
    All resource IDs are scoped to namespace.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.namespace = f"ns_{tenant_id}"
        
        # Namespace-scoped resources
        self.virtual_qubits: Dict[str, VirtualQubit] = {}
        self.channels: Dict[str, Channel] = {}
        self.sessions: Dict[str, Session] = {}
        self.jobs: Dict[str, Job] = {}
    
    def scoped_id(self, resource_id: str) -> str:
        """Create namespace-scoped resource ID."""
        return f"{self.namespace}:{resource_id}"
    
    def verify_ownership(self, resource_id: str) -> bool:
        """Verify resource belongs to this namespace."""
        return resource_id.startswith(f"{self.namespace}:")
```

**Properties:**
- No cross-namespace references
- Resource IDs include namespace prefix
- Kernel enforces namespace boundaries

---

## Resource Quotas

### Quota Types

QMK enforces multiple types of quotas:

#### 1. Capacity Quotas

Limits on total resources:

```python
@dataclass
class TenantQuota:
    # Quantum resources
    max_logical_qubits: int = 1000      # Max VQs
    max_physical_qubits: int = 10000    # Max PQs
    max_channels: int = 100             # Max entanglement channels
    
    # Classical resources
    max_sessions: int = 10              # Max concurrent sessions
    max_jobs_per_session: int = 100     # Max jobs per session
    max_concurrent_jobs: int = 10       # Max parallel jobs
    
    # Storage
    max_circuit_size: int = 100000      # Max gates per circuit
    max_qvm_graph_size: int = 50000     # Max QVM nodes
```

#### 2. Rate Limits

Limits on operation frequency:

```python
@dataclass
class RateLimits:
    max_jobs_per_minute: int = 60           # Job submission rate
    max_api_calls_per_minute: int = 1000    # API call rate
    max_allocations_per_minute: int = 100   # Qubit allocation rate
    max_measurements_per_second: int = 1000 # Measurement rate
```

#### 3. Time Limits

Limits on resource duration:

```python
@dataclass
class TimeLimits:
    max_session_duration_hours: int = 24    # Max session lifetime
    max_job_duration_minutes: int = 60      # Max job runtime
    max_qubit_lifetime_hours: int = 12      # Max VQ lifetime
```

### Quota Enforcement

Quotas are enforced at multiple points:

```python
class QuotaEnforcer:
    """
    Enforces tenant resource quotas.
    
    Checks quotas before allocation and during execution.
    """
    
    def check_allocation_quota(
        self,
        tenant: Tenant,
        resource_type: str,
        count: int
    ) -> bool:
        """
        Check if allocation would exceed quota.
        
        Returns:
            True if within quota, False otherwise
        """
        current = self.get_current_usage(tenant, resource_type)
        limit = self.get_quota_limit(tenant, resource_type)
        
        if current + count > limit:
            audit_logger.log(
                AuditEventType.QUOTA_EXCEEDED,
                tenant_id=tenant.tenant_id,
                details={
                    "resource_type": resource_type,
                    "current": current,
                    "requested": count,
                    "limit": limit
                }
            )
            return False
        
        return True
    
    def check_rate_limit(
        self,
        tenant: Tenant,
        operation: str
    ) -> bool:
        """
        Check if operation would exceed rate limit.
        
        Uses token bucket algorithm.
        """
        bucket = self.get_rate_bucket(tenant, operation)
        
        if not bucket.consume(1):
            audit_logger.log(
                AuditEventType.RATE_LIMIT_EXCEEDED,
                tenant_id=tenant.tenant_id,
                details={"operation": operation}
            )
            return False
        
        return True
```

### Quota Violations

When quotas are exceeded:

1. **Soft Limits**: Warning logged, operation proceeds
2. **Hard Limits**: Operation denied, error returned
3. **Grace Period**: Brief overage allowed
4. **Throttling**: Rate limited for repeated violations

---

## Entanglement Firewall

### Problem Statement

**Threat**: Unauthorized cross-tenant entanglement enables information leakage.

**Example Attack:**
```
1. Attacker (Tenant A) creates Bell pair: |Φ+⟩ = (|00⟩ + |11⟩)/√2
2. Attacker shares one qubit with Victim (Tenant B)
3. Victim performs computation on shared qubit
4. Attacker measures their qubit
5. Attacker infers information about Victim's operations
```

**Research**: Pirandola et al. (2017) - "Theory of Channel Simulation and Bounds for Private Communication"

### Firewall Architecture

QMK prevents unauthorized entanglement through multiple mechanisms:

#### 1. Entanglement Tracking

Kernel maintains global entanglement graph:

```python
class EntanglementGraph:
    """
    Tracks all entanglement relationships.
    
    Invariant: No edges between tenants without explicit channel.
    """
    
    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.tenant_map: Dict[str, str] = {}  # VQ → tenant
        self.channels: Dict[Tuple[str, str], Channel] = {}
    
    def add_entanglement(
        self,
        vq1: str,
        vq2: str,
        channel: Optional[Channel] = None
    ) -> None:
        """
        Add entanglement between two qubits.
        
        Raises:
            EntanglementFirewallViolation: If cross-tenant without channel
        """
        tenant1 = self.tenant_map[vq1]
        tenant2 = self.tenant_map[vq2]
        
        # Check if cross-tenant
        if tenant1 != tenant2:
            # Requires explicit channel
            if channel is None:
                raise EntanglementFirewallViolation(
                    f"Cross-tenant entanglement requires channel: "
                    f"{vq1} ({tenant1}) ↔ {vq2} ({tenant2})"
                )
            
            # Verify channel authorization
            if not self.verify_channel(channel, tenant1, tenant2):
                raise UnauthorizedChannel(
                    f"Invalid channel for {tenant1} ↔ {tenant2}"
                )
            
            # Log cross-tenant entanglement
            audit_logger.log(
                AuditEventType.CROSS_TENANT_ENTANGLEMENT,
                details={
                    "tenant1": tenant1,
                    "tenant2": tenant2,
                    "vq1": vq1,
                    "vq2": vq2,
                    "channel_id": channel.channel_id
                }
            )
        
        # Add edge
        self.graph[vq1].add(vq2)
        self.graph[vq2].add(vq1)
```

#### 2. Static Verification

QVM verifier checks circuits before execution:

```python
def verify_entanglement_firewall(qvm_graph: QVMGraph) -> bool:
    """
    Verify no unauthorized cross-tenant entanglement.
    
    Checks:
    - All two-qubit gates
    - Channel handles for cross-tenant ops
    - Tenant ownership of qubits
    """
    for node in qvm_graph.nodes:
        if node.op_type in TWO_QUBIT_GATES:
            vq1, vq2 = node.qubits
            tenant1 = get_tenant(vq1)
            tenant2 = get_tenant(vq2)
            
            if tenant1 != tenant2:
                # Cross-tenant operation
                if "channel" not in node.args:
                    return False  # Missing channel
                
                channel = node.args["channel"]
                if not verify_channel_signature(channel):
                    return False  # Invalid channel
    
    return True
```

#### 3. Runtime Enforcement

Kernel validates every two-qubit operation:

```python
def apply_two_qubit_gate(
    vq1: VirtualQubit,
    vq2: VirtualQubit,
    gate: str,
    channel: Optional[Channel] = None
) -> None:
    """
    Apply two-qubit gate with firewall check.
    """
    # Check tenant ownership
    tenant1 = vq1.tenant_id
    tenant2 = vq2.tenant_id
    
    if tenant1 != tenant2:
        # Cross-tenant gate requires channel
        if channel is None:
            raise EntanglementFirewallViolation(
                "Cross-tenant gate requires channel"
            )
        
        # Verify channel
        if not channel.authorizes(tenant1, tenant2):
            raise UnauthorizedChannel()
        
        # Check channel not revoked
        if channel.is_revoked():
            raise RevokedChannel()
    
    # Apply gate
    _apply_gate_internal(vq1, vq2, gate)
    
    # Update entanglement graph
    entanglement_graph.add_entanglement(vq1.vq_id, vq2.vq_id, channel)
```

### Firewall Guarantees

**Theorem**: No cross-tenant entanglement without explicit channel.

**Proof Sketch**:
1. All two-qubit gates checked (static + runtime)
2. Cross-tenant gates require channel
3. Channels cryptographically signed
4. Entanglement graph enforces invariant
5. No bypass mechanisms

---

## Cross-Tenant Channels

### Channel Model

Channels enable **authorized** cross-tenant entanglement:

```python
@dataclass
class Channel:
    """
    Authorized channel for cross-tenant entanglement.
    
    Requires agreement from both tenants.
    """
    channel_id: str             # Unique identifier
    tenant_a: str               # First tenant
    tenant_b: str               # Second tenant
    
    # Authorization
    authorized_by_a: bool       # Tenant A approved
    authorized_by_b: bool       # Tenant B approved
    
    # Constraints
    max_entanglements: int      # Max entangled pairs
    entanglements_used: int     # Current count
    expires_at: Optional[float] # Expiration time
    
    # Cryptographic
    signature_a: bytes          # Tenant A signature
    signature_b: bytes          # Tenant B signature
    created_at: float           # Creation time
    
    # State
    is_active: bool             # Active/closed
    is_revoked: bool            # Revoked flag
```

### Channel Lifecycle

#### 1. Request

Tenant A requests channel to Tenant B:

```python
def request_channel(
    requester_tenant: str,
    target_tenant: str,
    max_entanglements: int,
    expires_at: Optional[float] = None
) -> ChannelRequest:
    """
    Request cross-tenant channel.
    
    Returns pending request awaiting target approval.
    """
    request = ChannelRequest(
        request_id=generate_id(),
        requester=requester_tenant,
        target=target_tenant,
        max_entanglements=max_entanglements,
        expires_at=expires_at,
        status="pending"
    )
    
    # Notify target tenant
    notify_tenant(
        target_tenant,
        NotificationType.CHANNEL_REQUEST,
        details=request.to_dict()
    )
    
    # Log request
    audit_logger.log(
        AuditEventType.CHANNEL_REQUESTED,
        tenant_id=requester_tenant,
        details={"target": target_tenant}
    )
    
    return request
```

#### 2. Approval

Tenant B approves or rejects:

```python
def approve_channel_request(
    request_id: str,
    approver_tenant: str,
    approved: bool
) -> Optional[Channel]:
    """
    Approve or reject channel request.
    
    Returns:
        Channel if approved, None if rejected
    """
    request = get_channel_request(request_id)
    
    if request.target != approver_tenant:
        raise UnauthorizedApproval()
    
    if not approved:
        # Rejected
        audit_logger.log(
            AuditEventType.CHANNEL_REJECTED,
            tenant_id=approver_tenant,
            details={"request_id": request_id}
        )
        return None
    
    # Create channel
    channel = Channel(
        channel_id=generate_id(),
        tenant_a=request.requester,
        tenant_b=request.target,
        authorized_by_a=True,
        authorized_by_b=True,
        max_entanglements=request.max_entanglements,
        entanglements_used=0,
        expires_at=request.expires_at,
        created_at=time.time(),
        is_active=True,
        is_revoked=False
    )
    
    # Sign channel
    channel.signature_a = sign_channel(channel, request.requester)
    channel.signature_b = sign_channel(channel, request.target)
    
    # Store channel
    channel_store.add(channel)
    
    # Log creation
    audit_logger.log(
        AuditEventType.CHANNEL_CREATED,
        details={
            "channel_id": channel.channel_id,
            "tenant_a": channel.tenant_a,
            "tenant_b": channel.tenant_b
        }
    )
    
    return channel
```

#### 3. Usage

Channel used for entanglement:

```python
def use_channel(channel: Channel) -> bool:
    """
    Use channel for one entanglement.
    
    Returns:
        True if successful, False if exhausted
    """
    # Check active
    if not channel.is_active or channel.is_revoked:
        return False
    
    # Check expiration
    if channel.expires_at and time.time() > channel.expires_at:
        return False
    
    # Check quota
    if channel.entanglements_used >= channel.max_entanglements:
        return False
    
    # Increment usage
    channel.entanglements_used += 1
    
    # Log usage
    audit_logger.log(
        AuditEventType.CHANNEL_USED,
        details={
            "channel_id": channel.channel_id,
            "usage": channel.entanglements_used,
            "limit": channel.max_entanglements
        }
    )
    
    return True
```

#### 4. Revocation

Either tenant can revoke:

```python
def revoke_channel(
    channel_id: str,
    revoking_tenant: str
) -> None:
    """
    Revoke channel.
    
    Either tenant can revoke at any time.
    """
    channel = channel_store.get(channel_id)
    
    # Verify authority
    if revoking_tenant not in [channel.tenant_a, channel.tenant_b]:
        raise UnauthorizedRevocation()
    
    # Mark revoked
    channel.is_revoked = True
    channel.is_active = False
    
    # Log revocation
    audit_logger.log(
        AuditEventType.CHANNEL_REVOKED,
        tenant_id=revoking_tenant,
        details={"channel_id": channel_id}
    )
```

---

## Attack Scenarios

### Attack 1: Resource Exhaustion

**Attack**: Tenant A tries to exhaust resources for Tenant B.

**Mitigation**:
- Per-tenant quotas
- Rate limiting
- Fair scheduling
- Resource isolation

**Detection**:
- Monitor quota usage
- Alert on rapid allocation
- Track failed allocations

### Attack 2: Entanglement Leakage

**Attack**: Tenant A tries to entangle with Tenant B's qubits.

**Mitigation**:
- Entanglement firewall
- Channel requirement
- Cryptographic verification
- Static + runtime checks

**Detection**:
- Monitor cross-tenant operations
- Alert on firewall violations
- Track channel usage

### Attack 3: Timing Side-Channel

**Attack**: Tenant A infers Tenant B's operations from timing.

**Mitigation**:
- Constant-time operations (where possible)
- Noise injection
- Randomized scheduling
- Timing obfuscation

**Detection**:
- Statistical analysis
- Correlation detection
- Anomaly detection

### Attack 4: Covert Channel

**Attack**: Tenants communicate through shared resources.

**Mitigation**:
- Resource isolation
- Noise injection
- Monitoring
- Rate limiting

**Detection**:
- Information flow analysis
- Correlation detection
- Behavioral analysis

---

## Performance Isolation

### Fair Scheduling

QMK uses **fair scheduling** to prevent performance interference:

```python
class FairScheduler:
    """
    Fair scheduler for multi-tenant workloads.
    
    Ensures each tenant gets fair share of resources.
    """
    
    def __init__(self):
        self.tenant_queues: Dict[str, Queue[Job]] = {}
        self.tenant_weights: Dict[str, float] = {}
        self.last_scheduled: Dict[str, float] = {}
    
    def schedule_next(self) -> Optional[Job]:
        """
        Select next job to execute using weighted fair queuing.
        
        Returns:
            Next job to execute
        """
        # Calculate virtual finish times
        candidates = []
        for tenant_id, queue in self.tenant_queues.items():
            if queue.empty():
                continue
            
            weight = self.tenant_weights.get(tenant_id, 1.0)
            last_time = self.last_scheduled.get(tenant_id, 0.0)
            
            # Virtual finish time
            vft = last_time + (1.0 / weight)
            candidates.append((vft, tenant_id, queue))
        
        if not candidates:
            return None
        
        # Select tenant with earliest virtual finish time
        vft, tenant_id, queue = min(candidates, key=lambda x: x[0])
        
        # Dequeue job
        job = queue.get()
        self.last_scheduled[tenant_id] = vft
        
        return job
```

### Resource Reservation

Tenants can reserve resources:

```python
class ResourceReservation:
    """
    Reserve resources for guaranteed availability.
    """
    
    def reserve(
        self,
        tenant_id: str,
        resource_type: str,
        count: int,
        duration: float
    ) -> Reservation:
        """
        Reserve resources for tenant.
        
        Guarantees availability during reservation period.
        """
        # Check quota
        if not self.check_quota(tenant_id, resource_type, count):
            raise QuotaExceeded()
        
        # Create reservation
        reservation = Reservation(
            reservation_id=generate_id(),
            tenant_id=tenant_id,
            resource_type=resource_type,
            count=count,
            start_time=time.time(),
            end_time=time.time() + duration
        )
        
        # Reserve resources
        self.reserved_resources[tenant_id][resource_type] += count
        
        return reservation
```

---

## Monitoring and Detection

### Metrics Collection

Per-tenant metrics:

```python
class TenantMetrics:
    """
    Collect per-tenant metrics for monitoring.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
        # Resource usage
        self.vqs_allocated = 0
        self.pqs_allocated = 0
        self.channels_created = 0
        
        # Operation counts
        self.jobs_submitted = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        
        # Performance
        self.avg_job_duration = 0.0
        self.total_gate_count = 0
        
        # Security
        self.quota_violations = 0
        self.firewall_violations = 0
        self.capability_denials = 0
```

### Anomaly Detection

Detect suspicious behavior:

```python
class AnomalyDetector:
    """
    Detect anomalous tenant behavior.
    """
    
    def detect_anomalies(self, tenant_id: str) -> List[Anomaly]:
        """
        Detect anomalies in tenant behavior.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        metrics = self.get_metrics(tenant_id)
        
        # Check for resource exhaustion attempts
        if metrics.quota_violations > THRESHOLD:
            anomalies.append(Anomaly(
                type="resource_exhaustion",
                severity="high",
                details={"violations": metrics.quota_violations}
            ))
        
        # Check for firewall probing
        if metrics.firewall_violations > THRESHOLD:
            anomalies.append(Anomaly(
                type="firewall_probing",
                severity="critical",
                details={"violations": metrics.firewall_violations}
            ))
        
        # Check for unusual patterns
        if self.is_unusual_pattern(metrics):
            anomalies.append(Anomaly(
                type="unusual_pattern",
                severity="medium",
                details=self.get_pattern_details(metrics)
            ))
        
        return anomalies
```

---

## Research References

1. **Ristenpart, T. et al. (2009)**: "Hey, You, Get Off of My Cloud: Exploring Information Leakage in Third-Party Compute Clouds"
   - Cloud multi-tenancy security

2. **Varadarajan, V. et al. (2012)**: "Resource-Freeing Attacks: Improve Your Cloud Performance (at Your Neighbor's Expense)"
   - Resource exhaustion attacks

3. **Pirandola, S. et al. (2017)**: "Theory of Channel Simulation and Bounds for Private Communication"
   - Information leakage bounds through entanglement

4. **Häner, T. et al. (2020)**: "Quantum Cloud Computing: A Review"
   - Quantum cloud security considerations

5. **Broadbent, A. et al. (2009)**: "Universal Blind Quantum Computation"
   - Secure delegated quantum computation

---

**Document Version**: 1.0  
**Last Updated**: October 19, 2025  
**Status**: Production  
**Maintainer**: QMK Security Team
