import json, subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
def test_validator_ok():
    path = os.path.join(ROOT, "qvm", "examples", "bell_teleport_cnot.qvm.json")
    tool = os.path.join(ROOT, "qvm", "tools", "qvm_validate.py")
    res = subprocess.run([sys.executable, tool, path], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
