from kernel.simulator.qmk_kernel import QMKKernel
from runtime.client.qvm_client import QVMClient
import json, os

ROOT = os.path.dirname(os.path.dirname(__file__))

def test_rev_segment_runs():
    kernel = QMKKernel(num_physical=4, seed=1)
    client = QVMClient(kernel)
    path = os.path.join(ROOT, "qvm", "examples", "reversible_segment.qvm.json")
    with open(path) as f:
        g = json.load(f)
    log = kernel.run(g)
    assert any(x[0]=="MEASURE" for x in log)
