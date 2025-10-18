from collections import defaultdict, deque

def topo_schedule(nodes):
    # event graph schedule (same as validator but returns node list)
    produces = {}
    indeg = defaultdict(int)
    edges = defaultdict(set)
    nid2node = {n["id"]: n for n in nodes}
    for n in nodes:
        for ev in n.get("produces",[]):
            produces[ev] = n["id"]
    for n in nodes:
        for ev in n.get("inputs",[]):
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
