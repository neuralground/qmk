# qSyscall ABI Specification

**Version 0.1**

## Table of Contents

1. [Introduction](#introduction)
2. [Design Principles](#design-principles)
3. [Syscall Categories](#syscall-categories)
4. [Syscall Reference](#syscall-reference)
5. [Error Handling](#error-handling)
6. [Usage Patterns](#usage-patterns)
7. [Security Considerations](#security-considerations)

---

## 1. Introduction

The **qSyscall ABI** defines the interface between user-mode applications and the QMK supervisor kernel. All quantum operations are mediated through capability-checked syscalls that enforce:

- **Capability security**: Privileged operations require explicit capability tokens
- **Handle isolation**: Resource handles are kernel-issued and unforgeable
- **Tenant isolation**: Cross-tenant operations require brokered capabilities
- **Deterministic execution**: Syscalls are deterministic given the same inputs and seed

### 1.1 Calling Convention

**Transport**: JSON-RPC 2.0 over Unix domain sockets (primary) or gRPC (future)

**Request Format**:
```json
{
  "jsonrpc": "2.0",
  "method": "q_submit",
  "params": { ... },
  "id": 1
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 1
}
```

**Error Format**:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Insufficient capabilities",
    "data": { "required": ["CAP_ALLOC"], "missing": ["CAP_ALLOC"] }
  },
  "id": 1
}
```

---

## 2. Design Principles

### 2.1 Capability-Based Security

All syscalls that allocate resources or perform privileged operations require capabilities:
- Capabilities are granted by the kernel during tenant authentication
- Capabilities cannot be forged or transferred without kernel mediation
- Missing capabilities result in immediate syscall rejection

### 2.2 Kernel-Issued Handles

All resource identifiers (VQ, CH, job IDs) are:
- **Opaque**: User mode cannot inspect internal structure
- **Unforgeable**: Cryptographically signed or validated by kernel
- **Scoped**: Bound to the issuing tenant namespace

### 2.3 Asynchronous Execution

Long-running operations (graph execution) are asynchronous:
- `q_submit` returns immediately with a job ID
- `q_status` polls for completion and results
- `q_wait` blocks until completion (with timeout)

---

## 3. Syscall Categories

### 3.1 Resource Management
- `q_negotiate_caps` — Capability negotiation
- `q_alloc` — Allocate logical qubits
- `q_release` — Release logical qubits

### 3.2 Graph Submission & Control
- `q_submit` — Submit QVM graph for execution
- `q_cancel` — Cancel running job
- `q_status` — Query job status
- `q_wait` — Block until job completion

### 3.3 Channel Management
- `q_open_chan` — Open entanglement channel
- `q_close_chan` — Close entanglement channel
- `q_chan_status` — Query channel fidelity

### 3.4 Checkpoint & Migration
- `q_checkpoint` — Create checkpoint of running job
- `q_restore` — Restore from checkpoint
- `q_migrate` — Migrate job to different physical resources

### 3.5 Telemetry & Debugging
- `q_get_telemetry` — Retrieve job telemetry
- `q_get_mapping` — Get virtual→physical mapping (debug only)
- `q_replay` — Replay job with same seed

---

## 4. Syscall Reference

### 4.1 q_negotiate_caps

**Purpose**: Negotiate capabilities with the kernel during session establishment.

**Required Capability**: None (authentication-level operation)

**Parameters**:
```json
{
  "requested": ["CAP_ALLOC", "CAP_TELEPORT", "CAP_MAGIC", "CAP_LINK"]
}
```

**Returns**:
```json
{
  "granted": ["CAP_ALLOC", "CAP_TELEPORT"],
  "denied": ["CAP_MAGIC", "CAP_LINK"],
  "session_id": "sess_a1b2c3d4",
  "quota": {
    "max_logical_qubits": 100,
    "max_channels": 10,
    "max_jobs": 5
  }
}
```

**Errors**:
- `AUTH_FAILED` (-32100): Authentication failure
- `TENANT_SUSPENDED` (-32101): Tenant account suspended

**Usage Pattern**:
```python
# Establish session and negotiate capabilities
response = qsyscall("q_negotiate_caps", {
    "requested": ["CAP_ALLOC", "CAP_TELEPORT"]
})
session_id = response["session_id"]
granted_caps = response["granted"]
```

---

### 4.2 q_submit

**Purpose**: Submit a QVM graph for asynchronous execution.

**Required Capability**: Depends on graph contents (e.g., `CAP_ALLOC` if graph allocates qubits)

**Parameters**:
```json
{
  "graph": { /* QVM graph JSON */ },
  "policy": {
    "priority": 10,
    "deadline_epochs": 1000,
    "seed": 42,
    "debug": false
  },
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "job_id": "job_x7y8z9",
  "state": "QUEUED",
  "estimated_epochs": 50
}
```

**Errors**:
- `INVALID_GRAPH` (-32200): Graph validation failed
- `INSUFFICIENT_CAPS` (-32001): Missing required capabilities
- `QUOTA_EXCEEDED` (-32201): Tenant quota exceeded
- `RESOURCE_EXHAUSTED` (-32202): Insufficient physical resources

**Usage Pattern**:
```python
# Submit Bell state preparation
with open("bell_state.qvm.json") as f:
    graph = json.load(f)

result = qsyscall("q_submit", {
    "graph": graph,
    "policy": {"priority": 5, "seed": 42},
    "session_id": session_id
})
job_id = result["job_id"]
```

---

### 4.3 q_status

**Purpose**: Query the status of a submitted job.

**Required Capability**: None (tenant can only query own jobs)

**Parameters**:
```json
{
  "job_id": "job_x7y8z9",
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "job_id": "job_x7y8z9",
  "state": "COMPLETED",
  "progress": {
    "current_epoch": 50,
    "total_epochs": 50,
    "nodes_executed": 6,
    "nodes_total": 6
  },
  "events": {
    "mA": 0,
    "mB": 0
  },
  "telemetry": {
    "start_time": "2024-10-17T23:00:00Z",
    "end_time": "2024-10-17T23:00:05Z",
    "physical_qubits_used": 18
  }
}
```

**Job States**:
- `QUEUED`: Waiting for resources
- `VALIDATING`: Graph validation in progress
- `RUNNING`: Executing on quantum hardware
- `COMPLETED`: Successfully completed
- `FAILED`: Execution failed (see error field)
- `CANCELLED`: Cancelled by user

**Errors**:
- `JOB_NOT_FOUND` (-32300): Invalid job ID
- `ACCESS_DENIED` (-32301): Job belongs to different tenant

**Usage Pattern**:
```python
# Poll for completion
while True:
    status = qsyscall("q_status", {
        "job_id": job_id,
        "session_id": session_id
    })
    if status["state"] in ["COMPLETED", "FAILED", "CANCELLED"]:
        break
    time.sleep(0.1)

# Extract measurement results
events = status["events"]
print(f"Measurement outcomes: mA={events['mA']}, mB={events['mB']}")
```

---

### 4.4 q_wait

**Purpose**: Block until job completion or timeout.

**Required Capability**: None

**Parameters**:
```json
{
  "job_id": "job_x7y8z9",
  "timeout_ms": 5000,
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**: Same as `q_status` when job completes

**Errors**:
- `TIMEOUT` (-32302): Job did not complete within timeout
- `JOB_NOT_FOUND` (-32300): Invalid job ID

**Usage Pattern**:
```python
# Submit and wait for completion
job_id = qsyscall("q_submit", {...})["job_id"]
result = qsyscall("q_wait", {
    "job_id": job_id,
    "timeout_ms": 10000,
    "session_id": session_id
})
```

---

### 4.5 q_cancel

**Purpose**: Cancel a queued or running job.

**Required Capability**: None (tenant can only cancel own jobs)

**Parameters**:
```json
{
  "job_id": "job_x7y8z9",
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "job_id": "job_x7y8z9",
  "state": "CANCELLED",
  "cancelled_at_epoch": 25
}
```

**Errors**:
- `JOB_NOT_FOUND` (-32300): Invalid job ID
- `ALREADY_COMPLETED` (-32303): Job already completed

---

### 4.6 q_checkpoint

**Purpose**: Create a checkpoint of a running job at the next fence.

**Required Capability**: `CAP_CHECKPOINT` (optional feature)

**Parameters**:
```json
{
  "job_id": "job_x7y8z9",
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "checkpoint_id": "ckpt_abc123",
  "epoch": 25,
  "size_bytes": 4096
}
```

---

### 4.7 q_open_chan

**Purpose**: Open an entanglement channel between qubits.

**Required Capability**: `CAP_LINK`

**Parameters**:
```json
{
  "vq_a": "vq_handle_1",
  "vq_b": "vq_handle_2",
  "options": {
    "fidelity": 0.99,
    "type": "bell_pair"
  },
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "channel_id": "ch_handle_abc",
  "actual_fidelity": 0.995,
  "purification_rounds": 2
}
```

---

### 4.8 q_get_telemetry

**Purpose**: Retrieve detailed telemetry for a completed job.

**Required Capability**: None

**Parameters**:
```json
{
  "job_id": "job_x7y8z9",
  "session_id": "sess_a1b2c3d4"
}
```

**Returns**:
```json
{
  "job_id": "job_x7y8z9",
  "telemetry": {
    "total_epochs": 50,
    "total_gates": 150,
    "physical_qubits_used": 18,
    "decoder_cycles": 500,
    "execution_time_ms": 5000
  }
}
```

---

## 5. Error Handling

### 5.1 Error Code Ranges

| Range | Category | Examples |
|-------|----------|----------|
| -32000 to -32099 | General | Invalid params, method not found |
| -32100 to -32199 | Authentication | Auth failed, session expired |
| -32200 to -32299 | Graph Validation | Invalid graph, missing caps |
| -32300 to -32399 | Job Control | Job not found, timeout |
| -32400 to -32499 | Checkpoint | No fence, checkpoint failed |
| -32500 to -32599 | Channel | Fidelity unavailable |
| -32600 to -32699 | Resource | Quota exceeded, resource exhausted |

### 5.2 Retry Strategy

**Transient Errors** (retry with exponential backoff):
- `RESOURCE_EXHAUSTED` (-32202)
- `TIMEOUT` (-32302)

**Permanent Errors** (do not retry):
- `INVALID_GRAPH` (-32200)
- `INSUFFICIENT_CAPS` (-32001)
- `AUTH_FAILED` (-32100)

---

## 6. Usage Patterns

### 6.1 Basic Graph Submission

```python
# 1. Establish session
session = qsyscall("q_negotiate_caps", {
    "requested": ["CAP_ALLOC"]
})
session_id = session["session_id"]

# 2. Load and submit graph
with open("bell_state.qvm.json") as f:
    graph = json.load(f)

job = qsyscall("q_submit", {
    "graph": graph,
    "policy": {"seed": 42},
    "session_id": session_id
})
job_id = job["job_id"]

# 3. Wait for completion
result = qsyscall("q_wait", {
    "job_id": job_id,
    "timeout_ms": 10000,
    "session_id": session_id
})

# 4. Extract results
events = result["events"]
print(f"Measurement: {events}")
```

### 6.2 Polling with Backoff

```python
def wait_for_job(job_id, max_wait_s=60):
    start = time.time()
    backoff = 0.1
    
    while time.time() - start < max_wait_s:
        status = qsyscall("q_status", {
            "job_id": job_id,
            "session_id": session_id
        })
        
        if status["state"] == "COMPLETED":
            return status
        elif status["state"] == "FAILED":
            raise JobFailedError(status.get("error"))
        
        time.sleep(backoff)
        backoff = min(backoff * 1.5, 2.0)
    
    raise TimeoutError(f"Job did not complete")
```

### 6.3 Batch Submission

```python
# Submit multiple independent jobs
job_ids = []
for graph_file in ["bell.qvm.json", "ghz.qvm.json"]:
    with open(graph_file) as f:
        graph = json.load(f)
    job = qsyscall("q_submit", {
        "graph": graph,
        "session_id": session_id
    })
    job_ids.append(job["job_id"])

# Wait for all to complete
results = [qsyscall("q_wait", {"job_id": jid, ...}) for jid in job_ids]
```

---

## 7. Security Considerations

### 7.1 Handle Forgery Prevention

All handles are:
- **Cryptographically signed** with tenant-specific keys
- **Validated** on every syscall
- **Scoped** to tenant namespace

### 7.2 Capability Enforcement

- Checked at submission time and execution time
- Missing capabilities result in immediate rejection

### 7.3 Resource Quotas

Per-tenant quotas prevent DoS:
- Max logical qubits
- Max channels
- Max concurrent jobs
- Execution time limits

### 7.4 Audit Logging

All syscalls logged with tenant ID, timestamp, and resource usage for security audits and billing.

---

## Appendix: Complete Example

```python
#!/usr/bin/env python3
"""Bell state preparation via qSyscall"""

import json
from qsyscall_client import QSyscallClient

def main():
    client = QSyscallClient("/var/run/qmk/qsyscall.sock")
    
    # Negotiate capabilities
    session = client.call("q_negotiate_caps", {
        "requested": ["CAP_ALLOC"]
    })
    session_id = session["session_id"]
    
    # Load and submit graph
    with open("bell_state.qvm.json") as f:
        graph = json.load(f)
    
    job = client.call("q_submit", {
        "graph": graph,
        "policy": {"seed": 42},
        "session_id": session_id
    })
    
    # Wait for completion
    result = client.call("q_wait", {
        "job_id": job["job_id"],
        "timeout_ms": 10000,
        "session_id": session_id
    })
    
    print(f"Results: {result['events']}")
    print(f"Telemetry: {result['telemetry']}")

if __name__ == "__main__":
    main()
```

---

**End of qSyscall ABI Specification v0.1**
