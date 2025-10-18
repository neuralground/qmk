#!/usr/bin/env python3
"""QVM Graph Validator

Validates QVM graphs against the JSON schema and performs semantic checks:
- JSON schema conformance
- DAG acyclicity (no cycles)
- Node ID uniqueness
- Linear handle semantics (single producer/consumer)
- Capability coverage
- Event dependencies
- Resource lifetime tracking
"""
import sys, json, collections, os

CAP_REQUIRED = {
  "ALLOC_LQ": {"CAP_ALLOC"},
  "OPEN_CHAN": {"CAP_LINK"},
  "TELEPORT_CNOT": {"CAP_TELEPORT"},
  "INJECT_T_STATE": {"CAP_MAGIC"},
}

IRREVERSIBLE = {"MEASURE_Z","MEASURE_X","RESET","CLOSE_CHAN"}

def error(msg):
  print(f"❌ [QVM-ERROR] {msg}", file=sys.stderr)
  sys.exit(1)

def warn(msg):
  print(f"⚠️  [QVM-WARN] {msg}", file=sys.stderr)

def info(msg):
  print(f"ℹ️  [QVM-INFO] {msg}")

def load(path):
  with open(path) as f:
    return json.load(f)

def verify_linear_handles(nodes, declared_vqs, declared_chs):
  """Verify linear resource semantics for VQ and CH handles.
  
  In QVM, operations 'thread' VQs through - they consume and produce the same handle.
  Linearity means: each VQ flows through a single path in the DAG (no branching/aliasing).
  """
  allocated_vqs = set()
  freed_vqs = set()
  
  for n in nodes:
    op = n["op"]
    node_id = n["id"]
    vqs = n.get("vqs",[])
    
    if op == "ALLOC_LQ":
      # ALLOC produces VQs
      for v in vqs:
        if v in allocated_vqs:
          error(f"VQ '{v}' allocated twice (node {node_id})")
        allocated_vqs.add(v)
    elif op == "FREE_LQ":
      # FREE consumes VQs
      for v in vqs:
        if v not in allocated_vqs:
          error(f"FREE of non-allocated VQ '{v}' in node {node_id}")
        if v in freed_vqs:
          error(f"VQ '{v}' freed twice (node {node_id})")
        freed_vqs.add(v)
    else:
      # Other ops use VQs (must be allocated, not yet freed)
      for v in vqs:
        if v not in allocated_vqs:
          error(f"Use of non-allocated VQ '{v}' in op {op} (node {node_id})")
        if v in freed_vqs:
          error(f"Use of already-freed VQ '{v}' in op {op} (node {node_id})")
  
  # All declared VQs must be allocated
  for v in declared_vqs:
    if v not in allocated_vqs:
      error(f"Declared VQ '{v}' never allocated in program")
  
  # Warn about VQs that are never freed
  for v in allocated_vqs:
    if v not in freed_vqs:
      warn(f"VQ '{v}' allocated but never freed (potential resource leak)")
  
  # Similar checks for channels (simplified for now)
  live_ch = set()
  for n in nodes:
    op = n["op"]
    chs = n.get("chs",[])
    if op == "OPEN_CHAN":
      for c in chs:
        if c in live_ch:
          error(f"Channel '{c}' opened twice")
        live_ch.add(c)
    elif op == "CLOSE_CHAN":
      for c in chs:
        if c not in live_ch:
          error(f"CLOSE of non-open channel '{c}'")
        live_ch.remove(c)
  
  for c in live_ch:
    warn(f"Channel '{c}' opened but never closed")

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
  """Identify reversible (REV) segments between irreversible operations."""
  seg = []
  rev_segments = []
  
  for n in nodes:
    if n["op"] not in IRREVERSIBLE:
      seg.append(n["id"])
    else:
      if seg:
        rev_segments.append(seg)
      seg = []
  
  if seg:
    rev_segments.append(seg)
  
  if rev_segments:
    info(f"Found {len(rev_segments)} reversible (REV) segments:")
    for i, s in enumerate(rev_segments):
      info(f"  REV-{i+1}: {' -> '.join(s)}")
  
  return rev_segments

def validate_schema(graph_path):
  """Validate against JSON schema if jsonschema is available."""
  try:
    import jsonschema
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qvm_schema.json")
    if os.path.exists(schema_path):
      with open(schema_path) as f:
        schema = json.load(f)
      with open(graph_path) as f:
        graph = json.load(f)
      jsonschema.validate(graph, schema)
      info("JSON schema validation passed")
      return graph
    else:
      warn("Schema file not found, skipping schema validation")
      return load(graph_path)
  except ImportError:
    warn("jsonschema module not installed, skipping schema validation")
    return load(graph_path)
  except jsonschema.ValidationError as e:
    error(f"Schema validation failed: {e.message}")

def verify_handle_declarations(nodes, resources):
  """Verify all handles used in nodes are declared in resources."""
  declared_vqs = set(resources["vqs"])
  declared_chs = set(resources["chs"])
  declared_events = set(resources["events"])
  
  for n in nodes:
    # Check VQs
    for v in n.get("vqs", []):
      if v not in declared_vqs:
        error(f"Node {n['id']} uses undeclared VQ '{v}'")
    
    # Check CHs
    for c in n.get("chs", []):
      if c not in declared_chs:
        error(f"Node {n['id']} uses undeclared channel '{c}'")
    
    # Check events in inputs
    for e in n.get("inputs", []):
      if e not in declared_events:
        error(f"Node {n['id']} uses undeclared event '{e}'")
    
    # Check events in produces
    for e in n.get("produces", []):
      if e not in declared_events:
        error(f"Node {n['id']} produces undeclared event '{e}'")
    
    # Check guard events
    if "guard" in n:
      ev = n["guard"]["event"]
      if ev not in declared_events:
        error(f"Node {n['id']} guard references undeclared event '{ev}'")

def main():
  if len(sys.argv) < 2:
    print("Usage: qvm_validate.py <graph.qvm.json>")
    print("\nValidates QVM graphs for:")
    print("  - JSON schema conformance")
    print("  - DAG structure (no cycles)")
    print("  - Linear resource semantics")
    print("  - Capability requirements")
    print("  - Handle declarations")
    sys.exit(2)
  
  graph_path = sys.argv[1]
  info(f"Validating QVM graph: {graph_path}")
  
  # Schema validation
  g = validate_schema(graph_path)
  
  # Version check
  if g.get("version") != "0.1":
    error("Unsupported QVM version (expect 0.1)")
  
  nodes = g["program"]["nodes"]
  info(f"Graph contains {len(nodes)} nodes")
  
  # Basic structural checks
  ids = [n["id"] for n in nodes]
  if len(ids) != len(set(ids)):
    duplicates = [x for x in ids if ids.count(x) > 1]
    error(f"Duplicate node IDs: {set(duplicates)}")
  
  # Declared resources
  resources = g["resources"]
  declared_vqs = set(resources["vqs"])
  declared_chs = set(resources["chs"])
  declared_events = set(resources["events"])
  
  info(f"Declared resources: {len(declared_vqs)} VQs, {len(declared_chs)} CHs, {len(declared_events)} events")
  
  # Handle declaration checks
  verify_handle_declarations(nodes, resources)
  
  # Capability checks
  verify_caps(nodes, g.get("caps", []))
  
  # Linear handle checks
  verify_linear_handles(nodes, declared_vqs, declared_chs)
  
  # DAG/topology
  topo = topo_sort(nodes)
  info(f"Topological order: {' → '.join(topo)}")
  
  # Reversibility analysis
  rev_segs = verify_irreversibility(nodes)
  
  print("\n✅ [QVM-OK] Validation passed successfully!")
  print(f"   Graph: {len(nodes)} nodes, {len(declared_vqs)} VQs, {len(rev_segs)} REV segments")

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\n⚠️  Validation interrupted by user", file=sys.stderr)
    sys.exit(130)
  except Exception as e:
    print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
