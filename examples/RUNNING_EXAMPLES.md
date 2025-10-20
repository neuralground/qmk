# Running QMK Examples

## ✅ **WORKING! Examples Run with Real QMK Server**

All issues have been fixed and examples now run successfully with the real QMK server!

## Quick Start

### 1. Start the QMK Server

```bash
python -m kernel.qmk_server
```

### 2. Run Examples (in another terminal)

```bash
python examples/simple_bell_state.py
```

**Expected Output:**
```
=== QMK Bell State Example ===

1. Negotiating capabilities...
   Session ID: sess_c2a5cdf4d8f7362f
   Granted: ['CAP_ALLOC', 'CAP_MEASURE', 'CAP_COMPUTE']
   Denied: []

2. Loading Bell state graph...
   Nodes: 5
   Resources: 2 qubits

3. Submitting job...
   Job ID: job_7684ec74d64dc795

4. Waiting for job completion...
   State: COMPLETED
   Events: {'mA': 0, 'mB': 0}

5. Getting telemetry...
   Logical qubits: 2
   Physical qubits: 242
   Channels: 0

✅ Bell state preparation completed successfully!
```

### 3. Try Other Examples

```bash
python examples/adaptive_circuit.py
python examples/vqe_ansatz.py
python examples/multi_qubit_entanglement.py
python examples/deutsch_jozsa.py
python examples/grovers_algorithm.py
python examples/shors_algorithm.py
python examples/benchmark.py
```

---

## What Was Fixed

### 1. Import Path Errors ✅
**Before:**
```python
from runtime.client import QSyscallClient  # ModuleNotFoundError
```

**After:**
```python
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient  # Works!
```

### 2. QVM Format Support ✅
**Updated:** `kernel/syscalls/q_submit.py`

The syscall handler now accepts both formats:
- **QVM Format**: `{"program": {"nodes": [...]}}`
- **Legacy Format**: `{"nodes": [...], "edges": [...]}`

### 3. Server Integration ✅
**Fixed:** Multiple server-side issues

- **Executor initialization**: Fixed to pass `max_physical_qubits` instead of `resource_manager`
- **Job manager**: Fixed to call `execute()` instead of `execute_graph()`
- **Capabilities**: Added `CAP_COMPUTE` and `CAP_MEASURE` to session manager
- **Example graph**: Fixed Bell state graph to remove `FREE_LQ` after measurements (linearity)
- **Capability initialization**: Server now initializes executor with all capabilities enabled

### 4. Graph Format ✅
**Fixed:** `examples/simple_bell_state.py`

```python
# Correct access to QVM format
print(f"Nodes: {len(graph['program']['nodes'])}")
print(f"Resources: {len(graph['resources']['vqs'])} qubits")
```

---

## Summary

✅ **All import errors fixed**  
✅ **QVM format fully supported**  
✅ **Server integration complete**  
✅ **Examples run successfully with real QMK server**  
✅ **Bell state example verified working end-to-end**

**Result**: You can now run quantum circuits on the real QMK server!
