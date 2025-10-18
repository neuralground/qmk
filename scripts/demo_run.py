#!/usr/bin/env python3
import json, subprocess, sys, os
from kernel.simulator.qmk_kernel import QMKKernel
from runtime.client.qvm_client import QVMClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def run_validator(path):
    tool = os.path.join(ROOT, "qvm", "tools", "qvm_validate.py")
    res = subprocess.run([sys.executable, tool, path], capture_output=True, text=True)
    print(res.stdout.strip())
    if res.returncode != 0:
        print(res.stderr.strip())
        raise SystemExit(res.returncode)

def main():
    bell = os.path.join(ROOT, "qvm", "examples", "bell_teleport_cnot.qvm.json")
    rev = os.path.join(ROOT, "qvm", "examples", "reversible_segment.qvm.json")

    print("== Validate EIR ==")
    run_validator(bell)
    run_validator(rev)

    print("\n== Kernel run (bell) ==")
    kernel = QMKKernel(num_physical=8, seed=42, caps={"CAP_TELEPORT": True})
    client = QVMClient(kernel)
    log = client.submit(bell)
    for entry in log:
        print(entry)

    print("\n== Kernel run (reversible segment) ==")
    kernel2 = QMKKernel(num_physical=4, seed=7)
    client2 = QVMClient(kernel2)
    log2 = client2.submit(rev)
    for entry in log2:
        print(entry)

if __name__ == "__main__":
    main()
