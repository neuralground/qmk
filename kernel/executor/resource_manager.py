class ResourceManager:
    def __init__(self, num_physical=32):
        self.num_physical = num_physical
        self.free = set(range(num_physical))
        self.bindings = {}  # VQ -> physical id

    def alloc(self, vqs):
        assigned = []
        for v in vqs:
            if not self.free:
                raise RuntimeError("Out of physical qubits")
            p = self.free.pop()
            self.bindings[v] = p
            assigned.append((v,p))
        return assigned

    def free_vqs(self, vqs):
        for v in vqs:
            p = self.bindings.pop(v, None)
            if p is not None:
                self.free.add(p)

    def mapping(self):
        return dict(self.bindings)
