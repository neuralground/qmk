#!/usr/bin/env python3
import sys, json, collections

CAP_REQUIRED = {
  "ALLOC_LQ": {"CAP_ALLOC"},
  "OPEN_CHAN": {"CAP_LINK"},
  "TELEPORT_CNOT": {"CAP_TELEPORT"},
  "INJECT_T_STATE": {"CAP_MAGIC"},
}

IRREVERSIBLE = {"MEASURE_Z","MEASURE_X","RESET","CLOSE_CHAN"}

def error(msg):
  print(f"[QVM-ERROR] {msg}", file=sys.stderr)
  sys.exit(1)

def load(path):
  with open(path) as f:
    return json.load(f)

def verify_linear_handles(nodes, declared_vqs, declared_chs):
  live_vq = set()
  seen_vq = set()
  for n in nodes:
    op = n["op"]
    vqs = n.get("vqs",[])
    if op == "ALLOC_LQ":
      for v in vqs:
        if v in seen_vq:
          error(f"VQ '{v}' allocated twice")
        seen_vq.add(v)
        live_vq.add(v)
    elif op == "FREE_LQ":
      for v in vqs:
        if v not in live_vq:
          error(f"FREE of non-live VQ '{v}'")
        live_vq.remove(v)
    else:
      for v in vqs:
        if v not in live_vq:
          error(f"Use of non-live VQ '{v}' in op {op}")
  # All declared must be accounted for
  for v in declared_vqs:
    if v not in seen_vq:
      error(f"Declared VQ '{v}' never allocated in program")

def verify_caps(nodes, global_caps):
  for n in nodes:
    need = CAP_REQUIRED.get(n["op"], set())
    have = set(n.get("caps",[])) | set(global_caps)
    if need and not need.issubset(have):
      missing = ", ".join(sorted(need - have))
      raise SystemExit(f"[QVM-ERROR] Missing capabilities for {n['op']}: {missing}")

def topo_sort(nodes):
  # Build dependency graph via 'inputs' (event dependencies)
  deps = {n["id"]: set(n.get("inputs",[])) for n in nodes}
  # Map events -> producer nodes
  produces = {}
  for n in nodes:
    for ev in n.get("produces",[]):
      produces[ev] = n["id"]
  indeg = {n["id"]: 0 for n in nodes}
  edges = collections.defaultdict(set)
  for n in nodes:
    for ev in n.get("inputs",[]):
      if ev not in produces:
        raise SystemExit(f"[QVM-ERROR] Node {n['id']} depends on unknown event '{ev}'")
      src = produces[ev]
      edges[src].add(n["id"])
      indeg[n["id"]] += 1
  # Kahn's algorithm
  q = [nid for nid,d in indeg.items() if d==0]
  order = []
  while q:
    nid = q.pop()
    order.append(nid)
    for m in edges[nid]:
      indeg[m] -= 1
      if indeg[m]==0:
        q.append(m)
  if len(order) != len(nodes):
    raise SystemExit("[QVM-ERROR] Cycle detected in QVM DAG (check event guards)")
  return order

def verify_irreversibility(nodes):
  # simple pass: identify segments between irreversible ops
  seg = []
  for n in nodes:
    seg.append(n["op"])
    if n["op"] in IRREVERSIBLE:
      seg = []
  # Nothing to do; placeholder for REV segment policy checks

def main():
  if len(sys.argv)<2:
    print("Usage: eir_validate.py <eir.json>")
    sys.exit(2)
  g = load(sys.argv[1])
  if g.get("version") != "0.1":
    error("Unsupported QVM version (expect 0.1)")
  nodes = g["program"]["nodes"]
  # Basic structural checks
  ids = [n["id"] for n in nodes]
  if len(ids) != len(set(ids)):
    error("Duplicate node ids")
  # Declared resources
  declared_vqs = set(g["resources"]["vqs"])
  declared_chs = set(g["resources"]["chs"])
  # Capability checks
  verify_caps(nodes, g.get("caps",[]))
  # Linear handle checks
  verify_linear_handles(nodes, declared_vqs, declared_chs)
  # DAG/topology
  topo = topo_sort(nodes)
  print("[QVM-OK] Validation passed. Topological order:", " -> ".join(topo))

if __name__ == "__main__":
  main()
