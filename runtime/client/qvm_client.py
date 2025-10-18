import json
from kernel.simulator.qmk_kernel import QMKKernel

class QVMClient:
    def __init__(self, kernel: QMKKernel):
        self.kernel = kernel

    def submit(self, eir_path):
        with open(eir_path) as f:
            g = json.load(f)
        return self.kernel.run(g)
