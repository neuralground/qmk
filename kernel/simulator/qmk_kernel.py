import json, random
from .resource_manager import ResourceManager
from .capabilities import DEFAULT_CAPS, has_caps
from .scheduler import topo_schedule

CAP_REQUIRED = {
  "ALLOC_LQ": {"CAP_ALLOC"},
  "OPEN_CHAN": {"CAP_LINK"},
  "TELEPORT_CNOT": {"CAP_TELEPORT"},
  "INJECT_T_STATE": {"CAP_MAGIC"},
}

IRREVERSIBLE = {"MEASURE_Z","MEASURE_X","RESET","CLOSE_CHAN"}

class QMKKernel:
    def __init__(self, num_physical=32, seed=1234, caps=None):
        self.rm = ResourceManager(num_physical=num_physical)
        self.rng = random.Random(seed)
        self.caps = DEFAULT_CAPS.copy()
        if caps:
            self.caps.update(caps)
        self.events = {}

    def _check_caps(self, node, global_caps):
        need = CAP_REQUIRED.get(node["op"], set())
        have = set(node.get("caps",[])) | set([c for c,v in self.caps.items() if v]) | set(global_caps)
        if need and not need.issubset(have):
            missing = ", ".join(sorted(need - have))
            raise RuntimeError(f"Missing capabilities for {node['op']}: {missing}")

    def run(self, eir_json):
        g = eir_json if isinstance(eir_json, dict) else json.loads(eir_json)
        nodes = g["program"]["nodes"]
        order = topo_schedule(nodes)
        global_caps = g.get("caps",[])
        log = []
        for n in order:
            self._check_caps(n, global_caps)
            op = n["op"]
            vqs = n.get("vqs",[])
            # Guard check
            guard = n.get("guard")
            if guard:
                ev = guard["event"]; eq = guard["equals"]
                if self.events.get(ev) != eq:
                    log.append(("SKIP", n["id"], op))
                    continue
            if op == "ALLOC_LQ":
                self.rm.alloc(vqs)
                log.append(("ALLOC", list(self.rm.mapping().items())))
            elif op == "FREE_LQ":
                self.rm.free_vqs(vqs)
                log.append(("FREE", vqs))
            elif op.startswith("APPLY_"):
                # Simulate unitary as a no-op on state; record mapping context
                log.append(("APPLY", op, vqs, self.rm.mapping()))
            elif op.startswith("MEASURE_"):
                # Produce a synthetic bit
                evs = n.get("produces",[])
                bit = self.rng.randint(0,1)
                if evs:
                    self.events[evs[0]] = bit
                log.append(("MEASURE", vqs, evs, bit))
            elif op in ("FENCE_EPOCH","BAR_REGION"):
                log.append(("FENCE", op))
            elif op == "TELEPORT_CNOT":
                # If capability available, treat as composite unit; else raise
                log.append(("TELEPORT_CNOT", vqs, "ok"))
            elif op in ("OPEN_CHAN","USE_CHAN","CLOSE_CHAN","INJECT_T_STATE","RESET","COND_PAULI","SET_POLICY"):
                log.append(("ADMIN", op, vqs))
            else:
                raise RuntimeError(f"Unknown opcode {op}")
        return log
