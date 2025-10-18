#!/usr/bin/env python3
import sys, json
def main():
  if len(sys.argv)<2:
    print("Usage: qvm_pretty.py <qvm.json>")
    sys.exit(2)
  with open(sys.argv[1]) as f:
    g = json.load(f)
  for n in g["program"]["nodes"]:
    vqs = ",".join(n.get("vqs",[]))
    ins = ",".join(n.get("inputs",[]))
    outs = ",".join(n.get("produces",[]))
    print(f"{n['id']:>4} | {n['op']:<14} vqs=[{vqs}] in=[{ins}] out=[{outs}]")
if __name__ == "__main__":
  main()
