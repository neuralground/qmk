# QMK Resource Lifecycle Management

## Overview

QMK implements systematic resource lifecycle management with automatic cleanup, ensuring resources are properly allocated and released for every job execution, regardless of success or failure.

## Architecture

### Three-Phase Execution Model

```
┌─────────────────────────────────────────────────────────┐
│                    JOB EXECUTION                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ PHASE 1: LOAD                                    │  │
│  │ - Verify graph (certification)                   │  │
│  │ - Prepare fresh execution context                │  │
│  │ - Reset resource manager                         │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ PHASE 2: EXECUTE                                 │  │
│  │ - Run graph operations                           │  │
│  │ - Track allocated resources                      │  │
│  │ - Execute quantum operations                     │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ PHASE 3: UNLOAD (automatic)                      │  │
│  │ - Free allocated qubits                          │  │
│  │ - Clean up resources                             │  │
│  │ - Happens on success OR error                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### Executor: `EnhancedExecutor.execute()`

```python
def execute(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Execute with automatic resource lifecycle management."""
    allocated_qubits = []
    
    try:
        # PHASE 1: LOAD
        self._load_graph(qvm_graph)
        
        # PHASE 2: EXECUTE
        for node in execution_order:
            self._execute_node(node, global_caps)
            if node.get("op") == "ALLOC_LQ":
                allocated_qubits.extend(node.get("vqs", []))
        
        # Return results
        return result
        
    except Exception as e:
        # Log error
        self.execution_log.append(("ERROR", str(e)))
        raise
        
    finally:
        # PHASE 3: UNLOAD (ALWAYS runs)
        self._unload_graph(allocated_qubits)
```

### Key Methods

#### `_load_graph(qvm_graph)`
**Purpose**: Prepare execution context

**Actions**:
1. Verify graph through static certification
2. Reset resource manager to clean state
3. Clear execution logs and tracking
4. Log successful load

**Errors**: Raises `VerificationError` if graph invalid

#### `_unload_graph(allocated_qubits)`
**Purpose**: Clean up resources

**Actions**:
1. Free any qubits still allocated
2. Release all resources
3. Log cleanup completion
4. Never raises exceptions (logs errors instead)

**Guarantee**: Always runs via `finally` block

## Benefits

### 1. Automatic Cleanup ✅
Resources are **automatically** released after each job:
- No manual cleanup needed by callers
- Works for both success and error cases
- Guaranteed by Python's `try/finally` semantics

### 2. Server-Managed Lifecycle ✅
The **server** manages resources, not the test/caller:
- Tests just submit jobs
- Server handles load/unload
- Proper separation of concerns

### 3. Error Safety ✅
Resources cleaned up even on errors:
- Verification failures
- Execution errors
- Unexpected exceptions
- All trigger cleanup

### 4. Observable State ✅
Telemetry confirms cleanup:
```python
# After job completion
telemetry = {
    "logical_qubits": 0,      # All freed
    "physical_qubits": 0,     # All released
    "channels": 0             # All closed
}
```

## Usage

### From Test/Client Perspective

```python
# Submit job
job_id = client.submit_job(graph)

# Wait for completion
result = client.wait_for_job(job_id)

# Resources automatically cleaned up!
# No manual cleanup needed
```

### Multiple Jobs

```python
# Run multiple jobs - no conflicts!
for i in range(10):
    job_id = client.submit_job(graph)
    result = client.wait_for_job(job_id)
    # Each job gets fresh resources
    # Previous job's resources are freed
```

## Resource Manager

### `EnhancedResourceManager.reset()`

Called during LOAD phase to prepare fresh state:

```python
def reset(self):
    """Reset to initial state."""
    self.logical_qubits.clear()
    self.physical_qubits_used = 0
    self.channels.clear()
    self.current_time_us = 0.0
    self.seed_counter = 0
```

### `EnhancedResourceManager.free_logical_qubits(vq_ids)`

Called during UNLOAD phase to release resources:

```python
def free_logical_qubits(self, vq_ids: List[str]):
    """Free logical qubits and reclaim physical resources."""
    for vq_id in vq_ids:
        if vq_id in self.logical_qubits:
            lq = self.logical_qubits[vq_id]
            self.physical_qubits_used -= lq.physical_qubit_count
            del self.logical_qubits[vq_id]
```

## Execution Log

The execution log tracks lifecycle phases:

```python
execution_log = [
    ("CERTIFIED", "static_verification_passed"),
    ("LOAD", "graph_loaded_and_verified"),
    ("EXECUTE", "node_n1_completed"),
    ("EXECUTE", "node_n2_completed"),
    # ... more execution steps ...
    ("UNLOAD", "freed_2_qubits"),
    ("UNLOAD", "resources_released")
]
```

On error:
```python
execution_log = [
    ("CERTIFIED", "static_verification_passed"),
    ("LOAD", "graph_loaded_and_verified"),
    ("EXECUTE", "node_n1_completed"),
    ("ERROR", "Missing capabilities for MEASURE_Z"),
    ("UNLOAD", "freed_2_qubits"),
    ("UNLOAD", "resources_released")
]
```

## Design Principles

### 1. Fail-Safe Design
- Cleanup **always** happens (via `finally`)
- Cleanup errors are logged but don't fail the job
- Resources never leak

### 2. Separation of Concerns
- **Caller**: Submits job, waits for result
- **Server**: Manages lifecycle, handles cleanup
- **Executor**: Implements phases, tracks resources

### 3. Idempotent Operations
- Multiple resets are safe
- Freeing already-freed qubits is safe
- Cleanup can be called multiple times

### 4. Observable Behavior
- Execution log shows all phases
- Telemetry confirms cleanup
- Errors are logged and visible

## Testing

### Verify Cleanup

```python
# Run job
result = executor.execute(graph)

# Check telemetry
telemetry = result["telemetry"]
assert telemetry["logical_qubits"] == 0
assert telemetry["physical_qubits"] == 0

# Check execution log
log = result["execution_log"]
assert ("LOAD", "graph_loaded_and_verified") in log
assert ("UNLOAD", "resources_released") in log
```

### Verify Multiple Jobs

```python
# Run multiple jobs
for i in range(10):
    result = executor.execute(graph)
    assert result["status"] == "COMPLETED"
    
# All should succeed without conflicts
```

### Verify Error Cleanup

```python
# Submit invalid graph
try:
    result = executor.execute(invalid_graph)
except VerificationError:
    pass

# Resources still cleaned up
telemetry = executor.resource_manager.get_telemetry()
assert telemetry["logical_qubits"] == 0
```

## Comparison: Before vs After

### Before (Manual Cleanup)
```python
# Test had to manage cleanup
executor.execute(graph1)
executor.resource_manager.reset()  # Manual!

executor.execute(graph2)
executor.resource_manager.reset()  # Manual!

# Easy to forget, causes conflicts
```

### After (Automatic Cleanup)
```python
# Server manages everything
executor.execute(graph1)  # Auto cleanup
executor.execute(graph2)  # Auto cleanup

# No manual intervention needed
# No conflicts possible
```

## Future Enhancements

### 1. Resource Pooling
- Reuse allocated qubits across jobs
- Reduce allocation overhead
- Maintain isolation between tenants

### 2. Partial Cleanup
- Free resources incrementally during execution
- Reduce peak resource usage
- Enable longer-running jobs

### 3. Resource Limits
- Enforce per-job resource limits
- Prevent resource exhaustion
- Fair scheduling across tenants

### 4. Cleanup Metrics
- Track cleanup time
- Monitor resource leaks
- Alert on cleanup failures

## Summary

QMK's resource lifecycle management provides:

✅ **Automatic cleanup** - No manual intervention needed  
✅ **Error safety** - Resources freed even on errors  
✅ **Server-managed** - Proper separation of concerns  
✅ **Observable** - Telemetry and logs confirm cleanup  
✅ **Reliable** - Guaranteed by `try/finally` semantics  

**Result**: Tests and clients can focus on quantum operations, not resource management!
