# Running QMK Examples

## Fixed Issues ✅

All example scripts have been updated with:
- ✅ Correct import paths (`runtime.client.qsyscall_client`)
- ✅ QVM format support in syscall handler
- ✅ Proper sys.path setup

## Running Examples

### Option 1: Without Server (Import Errors Fixed)

The import errors are now fixed! However, to actually execute quantum circuits, you need the QMK server running.

```bash
# This will now import correctly but fail at connection
python examples/simple_bell_state.py
```

**Expected Output:**
```
❌ Error: QMK server not running
   Start with: python -m kernel.qmk_server
```

### Option 2: With Server (Full Execution)

1. **Start the QMK server** (in one terminal):
```bash
python -m kernel.qmk_server
```

2. **Run examples** (in another terminal):
```bash
python examples/simple_bell_state.py
python examples/adaptive_circuit.py
python examples/vqe_ansatz.py
python examples/multi_qubit_entanglement.py
python examples/deutsch_jozsa.py
python examples/grovers_algorithm.py
python examples/shors_algorithm.py
python examples/benchmark.py
```

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

### 3. Graph Access ✅
**Fixed:** `examples/simple_bell_state.py`

```python
# Correct access to QVM format
print(f"Nodes: {len(graph['program']['nodes'])}")
print(f"Resources: {len(graph['resources']['vqs'])} qubits")
```

## Testing Without Server

You can test that imports work without running the server:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient

print("✅ Import successful!")
client = QSyscallClient()
print(f"✅ Client created: {client}")
```

## Next Steps

To fully test the examples:

1. **Implement or start the QMK server**
2. **Ensure the server uses the updated syscall handler**
3. **Run the examples**

## Summary

✅ **All import errors fixed**  
✅ **QVM format supported**  
✅ **Examples ready to run**  
⏳ **Server needed for full execution**
