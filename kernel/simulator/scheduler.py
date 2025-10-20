from collections import defaultdict, deque

def topo_schedule(nodes):
    # event graph schedule (same as validator but returns node list)
    # Also handles guard dependencies
    produces = {}
    indeg = defaultdict(int)
    edges = defaultdict(set)
    nid2node = {n["id"]: n for n in nodes}
    
    # Build produces map
    for n in nodes:
        for ev in n.get("produces",[]):
            produces[ev] = n["id"]
    
    # Add edges from inputs
    for n in nodes:
        for ev in n.get("inputs",[]):
            src = produces.get(ev)
            if src:
                edges[src].add(n["id"])
                indeg[n["id"]] += 1
    
    # Add edges from guards
    for n in nodes:
        guard = n.get("guard")
        if guard:
            # Extract events from guard
            guard_events = _extract_guard_events(guard)
            for ev in guard_events:
                src = produces.get(ev)
                if src:
                    edges[src].add(n["id"])
                    indeg[n["id"]] += 1
    
    q = deque([n["id"] for n in nodes if indeg[n["id"]]==0])
    order = []
    while q:
        nid = q.popleft()
        order.append(nid2node[nid])
        for m in edges[nid]:
            indeg[m] -= 1
            if indeg[m]==0:
                q.append(m)
    if len(order)!=len(nodes):
        raise RuntimeError("Cycle in QVM graph at scheduling time")
    return order


def _extract_guard_events(guard):
    """Extract all event IDs from a guard condition."""
    events = []
    
    guard_type = guard.get("type")
    if guard_type in ("and", "or"):
        # Complex guard with conditions
        for cond in guard.get("conditions", []):
            if "event" in cond:
                events.append(cond["event"])
    elif "event" in guard:
        # Simple guard
        events.append(guard["event"])
    
    return events
