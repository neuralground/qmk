"""
Enhanced QVM Graph Executor with Logical Qubit Simulation

Executes QVM graphs using the logical qubit simulator with full error modeling.
"""

from typing import Dict, List, Any, Optional
import json

from .enhanced_resource_manager import EnhancedResourceManager
from .qec_profiles import parse_profile_string
from .logical_qubit import TwoQubitGate
from .capabilities import DEFAULT_CAPS, has_caps
from .scheduler import topo_schedule


# Capability requirements for operations
CAP_REQUIRED = {
    "ALLOC_LQ": {"CAP_ALLOC"},
    "OPEN_CHAN": {"CAP_LINK"},
    "TELEPORT_CNOT": {"CAP_TELEPORT"},
    "INJECT_T_STATE": {"CAP_MAGIC"},
}

# Operations that are irreversible (break REV segments)
IRREVERSIBLE = {"MEASURE_Z", "MEASURE_X", "RESET", "CLOSE_CHAN"}


class EnhancedExecutor:
    """
    Enhanced QVM graph executor with logical qubit simulation.
    
    Features:
    - Full logical qubit simulation with error models
    - QEC profile support (Surface, SHYPS, Bacon-Shor)
    - Azure QRE compatibility
    - Comprehensive telemetry
    - Deterministic execution with seeds
    """
    
    def __init__(self, max_physical_qubits: int = 10000, 
                 seed: Optional[int] = None,
                 caps: Optional[Dict[str, bool]] = None):
        """
        Initialize executor.
        
        Args:
            max_physical_qubits: Maximum physical qubits available
            seed: Random seed for deterministic execution
            caps: Capability overrides
        """
        self.resource_manager = EnhancedResourceManager(max_physical_qubits, seed)
        self.caps = DEFAULT_CAPS.copy()
        if caps:
            self.caps.update(caps)
        
        # Event storage (measurement outcomes)
        self.events: Dict[str, int] = {}
        
        # Execution log
        self.execution_log: List[Tuple[str, ...]] = []
    
    def execute(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a QVM graph.
        
        Args:
            qvm_graph: QVM graph in JSON format
        
        Returns:
            Execution result with telemetry
        """
        # Parse graph
        if isinstance(qvm_graph, str):
            graph = json.loads(qvm_graph)
        else:
            graph = qvm_graph
        
        nodes = graph["program"]["nodes"]
        global_caps = graph.get("caps", [])
        
        # Topological sort for execution order
        execution_order = topo_schedule(nodes)
        
        # Execute nodes in order
        for node in execution_order:
            self._execute_node(node, global_caps)
        
        # Collect results
        result = {
            "status": "COMPLETED",
            "events": dict(self.events),
            "telemetry": self.resource_manager.get_telemetry(),
            "execution_log": self.execution_log,
        }
        
        return result
    
    def _execute_node(self, node: Dict[str, Any], global_caps: List[str]):
        """Execute a single node in the graph."""
        node_id = node["id"]
        op = node["op"]
        
        # Check capabilities
        self._check_capabilities(node, global_caps)
        
        # Check guard condition
        if not self._check_guard(node):
            self.execution_log.append(("SKIP", node_id, op, "guard_failed"))
            return
        
        # Execute operation
        if op == "ALLOC_LQ":
            self._exec_alloc(node)
        elif op == "FREE_LQ":
            self._exec_free(node)
        elif op == "FENCE_EPOCH":
            self._exec_fence(node)
        elif op == "BAR_REGION":
            self._exec_barrier(node)
        elif op.startswith("APPLY_"):
            self._exec_gate(node)
        elif op.startswith("MEASURE_"):
            self._exec_measurement(node)
        elif op == "RESET":
            self._exec_reset(node)
        elif op == "COND_PAULI":
            self._exec_cond_pauli(node)
        elif op == "OPEN_CHAN":
            self._exec_open_chan(node)
        elif op == "CLOSE_CHAN":
            self._exec_close_chan(node)
        elif op == "TELEPORT_CNOT":
            self._exec_teleport_cnot(node)
        elif op == "INJECT_T_STATE":
            self._exec_inject_t(node)
        elif op == "SET_POLICY":
            self._exec_set_policy(node)
        else:
            raise RuntimeError(f"Unknown operation: {op}")
    
    def _check_capabilities(self, node: Dict[str, Any], global_caps: List[str]):
        """Check if required capabilities are available."""
        op = node["op"]
        required = CAP_REQUIRED.get(op, set())
        
        if not required:
            return
        
        # Collect available capabilities
        node_caps = set(node.get("caps", []))
        available = node_caps | set(global_caps) | {c for c, v in self.caps.items() if v}
        
        if not required.issubset(available):
            missing = required - available
            raise RuntimeError(
                f"Missing capabilities for {op}: {', '.join(sorted(missing))}"
            )
    
    def _check_guard(self, node: Dict[str, Any]) -> bool:
        """Check if guard condition is satisfied."""
        guard = node.get("guard")
        if not guard:
            return True
        
        # Handle complex guards (AND/OR)
        guard_type = guard.get("type")
        
        if guard_type == "and":
            # All conditions must be true
            conditions = guard.get("conditions", [])
            for cond in conditions:
                if not self._check_single_condition(cond):
                    return False
            return True
        
        elif guard_type == "or":
            # At least one condition must be true
            conditions = guard.get("conditions", [])
            for cond in conditions:
                if self._check_single_condition(cond):
                    return True
            return False
        
        else:
            # Simple guard
            return self._check_single_condition(guard)
    
    def _check_single_condition(self, condition: Dict[str, Any]) -> bool:
        """Check a single guard condition."""
        event_id = condition["event"]
        expected = condition.get("equals", condition.get("value", 0))
        
        if event_id not in self.events:
            # Event not yet produced - this shouldn't happen in valid graphs
            return False
        
        return self.events[event_id] == expected
    
    def _exec_alloc(self, node: Dict[str, Any]):
        """Execute ALLOC_LQ operation."""
        args = node.get("args", {})
        vq_ids = node.get("vqs", [])
        profile_str = args.get("profile", "logical:surface_code(d=9)")
        
        # Parse QEC profile
        profile = parse_profile_string(profile_str)
        
        # Allocate logical qubits
        allocated = self.resource_manager.alloc_logical_qubits(vq_ids, profile)
        
        self.execution_log.append(("ALLOC", node["id"], vq_ids, profile.code_family, allocated))
    
    def _exec_free(self, node: Dict[str, Any]):
        """Execute FREE_LQ operation."""
        vq_ids = node.get("vqs", [])
        self.resource_manager.free_logical_qubits(vq_ids)
        
        self.execution_log.append(("FREE", node["id"], vq_ids))
    
    def _exec_fence(self, node: Dict[str, Any]):
        """Execute FENCE_EPOCH operation."""
        # Fence is a scheduling hint - just log it
        self.execution_log.append(("FENCE", node["id"]))
    
    def _exec_barrier(self, node: Dict[str, Any]):
        """Execute BAR_REGION operation."""
        args = node.get("args", {})
        tag = args.get("tag", "")
        self.execution_log.append(("BARRIER", node["id"], tag))
    
    def _exec_gate(self, node: Dict[str, Any]):
        """Execute gate operation (APPLY_H, APPLY_X, etc.)."""
        op = node["op"]
        gate_type = op.replace("APPLY_", "")
        vq_ids = node.get("vqs", [])
        
        if len(vq_ids) == 1:
            # Single-qubit gate
            qubit = self.resource_manager.get_logical_qubit(vq_ids[0])
            qubit.apply_gate(gate_type, self.resource_manager.current_time_us)
            
            # Advance time by logical cycle time
            self.resource_manager.advance_time(qubit.profile.logical_cycle_time_us)
            
            self.execution_log.append(("GATE", node["id"], gate_type, vq_ids[0]))
        
        elif len(vq_ids) == 2:
            # Two-qubit gate
            qubit1 = self.resource_manager.get_logical_qubit(vq_ids[0])
            qubit2 = self.resource_manager.get_logical_qubit(vq_ids[1])
            
            if gate_type == "CNOT":
                TwoQubitGate.apply_cnot(qubit1, qubit2, self.resource_manager.current_time_us)
            elif gate_type == "CZ":
                TwoQubitGate.apply_cz(qubit1, qubit2, self.resource_manager.current_time_us)
            elif gate_type == "SWAP":
                TwoQubitGate.apply_swap(qubit1, qubit2, self.resource_manager.current_time_us)
            else:
                raise RuntimeError(f"Unsupported two-qubit gate: {gate_type}")
            
            # Advance time
            cycle_time = max(qubit1.profile.logical_cycle_time_us, 
                           qubit2.profile.logical_cycle_time_us)
            self.resource_manager.advance_time(cycle_time)
            
            self.execution_log.append(("GATE", node["id"], gate_type, vq_ids))
        
        else:
            raise RuntimeError(f"Invalid number of qubits for {op}: {len(vq_ids)}")
    
    def _exec_measurement(self, node: Dict[str, Any]):
        """Execute measurement operation."""
        op = node["op"]
        vq_ids = node.get("vqs", [])
        event_ids = node.get("produces", [])
        
        # Check if this is a Bell basis measurement (2 qubits)
        if op == "MEASURE_BELL" or len(vq_ids) == 2:
            # Bell basis measurement on two qubits
            if len(vq_ids) != 2:
                raise RuntimeError(f"Bell measurement requires exactly 2 qubits, got {len(vq_ids)}")
            
            qubit1 = self.resource_manager.get_logical_qubit(vq_ids[0])
            qubit2 = self.resource_manager.get_logical_qubit(vq_ids[1])
            
            # Perform Bell measurement
            from .logical_qubit import LogicalQubit
            outcome1, outcome2, bell_index = LogicalQubit.measure_bell_basis(
                qubit1, qubit2, self.resource_manager.current_time_us
            )
            
            # Store events
            if len(event_ids) >= 2:
                self.events[event_ids[0]] = outcome1
                self.events[event_ids[1]] = outcome2
            elif len(event_ids) == 1:
                # Store combined outcome as bell_index
                self.events[event_ids[0]] = bell_index
            
            # Advance time
            cycle_time = max(qubit1.profile.logical_cycle_time_us,
                           qubit2.profile.logical_cycle_time_us)
            self.resource_manager.advance_time(cycle_time)
            
            self.execution_log.append(("MEASURE_BELL", node["id"], vq_ids, 
                                      (outcome1, outcome2, bell_index), event_ids))
            return
        
        # Single-qubit measurement
        if len(vq_ids) != 1:
            raise RuntimeError(f"Single-qubit measurement requires exactly 1 qubit, got {len(vq_ids)}")
        
        # Determine measurement basis
        if op == "MEASURE_Z":
            basis = "Z"
        elif op == "MEASURE_X":
            basis = "X"
        elif op == "MEASURE_Y":
            basis = "Y"
        else:
            # Default to Z-basis for unknown measurement types
            basis = "Z"
        
        qubit = self.resource_manager.get_logical_qubit(vq_ids[0])
        outcome = qubit.measure(basis, self.resource_manager.current_time_us)
        
        # If this qubit is entangled, propagate the outcome to its partner
        if qubit.entangled_with is not None:
            try:
                partner = self.resource_manager.get_logical_qubit(qubit.entangled_with)
                # For Bell state |00⟩ + |11⟩, both measurements should match
                partner.measurement_outcome = outcome
            except:
                pass  # Partner may not exist or already measured
        
        # Store event
        if event_ids:
            self.events[event_ids[0]] = outcome
        
        # Advance time
        self.resource_manager.advance_time(qubit.profile.logical_cycle_time_us)
        
        self.execution_log.append(("MEASURE", node["id"], vq_ids[0], basis, outcome, event_ids))
    
    def _exec_reset(self, node: Dict[str, Any]):
        """Execute RESET operation."""
        vq_ids = node.get("vqs", [])
        
        for vq_id in vq_ids:
            qubit = self.resource_manager.get_logical_qubit(vq_id)
            qubit.reset(self.resource_manager.current_time_us)
            self.resource_manager.advance_time(qubit.profile.logical_cycle_time_us)
        
        self.execution_log.append(("RESET", node["id"], vq_ids))
    
    def _exec_cond_pauli(self, node: Dict[str, Any]):
        """Execute COND_PAULI operation."""
        args = node.get("args", {})
        mask = args.get("mask", "X")
        vq_ids = node.get("vqs", [])
        event_ids = node.get("inputs", [])
        
        if not event_ids:
            return
        
        # Check event value
        event_value = self.events.get(event_ids[0], 0)
        
        if event_value == 1:
            # Apply Pauli correction
            for vq_id in vq_ids:
                qubit = self.resource_manager.get_logical_qubit(vq_id)
                qubit.apply_gate(mask, self.resource_manager.current_time_us)
                self.resource_manager.advance_time(qubit.profile.logical_cycle_time_us)
        
        self.execution_log.append(("COND_PAULI", node["id"], mask, vq_ids, event_value))
    
    def _exec_open_chan(self, node: Dict[str, Any]):
        """Execute OPEN_CHAN operation."""
        args = node.get("args", {})
        ch_ids = node.get("chs", [])
        vq_ids = node.get("vqs", [])
        fidelity = args.get("fidelity", 0.99)
        
        if len(ch_ids) != 1 or len(vq_ids) != 2:
            raise RuntimeError("OPEN_CHAN requires 1 channel and 2 qubits")
        
        self.resource_manager.open_channel(ch_ids[0], vq_ids[0], vq_ids[1], fidelity)
        
        self.execution_log.append(("OPEN_CHAN", node["id"], ch_ids[0], vq_ids))
    
    def _exec_close_chan(self, node: Dict[str, Any]):
        """Execute CLOSE_CHAN operation."""
        ch_ids = node.get("chs", [])
        
        for ch_id in ch_ids:
            self.resource_manager.close_channel(ch_id)
        
        self.execution_log.append(("CLOSE_CHAN", node["id"], ch_ids))
    
    def _exec_teleport_cnot(self, node: Dict[str, Any]):
        """Execute TELEPORT_CNOT operation."""
        vq_ids = node.get("vqs", [])
        
        # Simplified: treat as regular CNOT for now
        if len(vq_ids) == 2:
            control = self.resource_manager.get_logical_qubit(vq_ids[0])
            target = self.resource_manager.get_logical_qubit(vq_ids[1])
            
            TwoQubitGate.apply_cnot(control, target, self.resource_manager.current_time_us)
            
            cycle_time = max(control.profile.logical_cycle_time_us,
                           target.profile.logical_cycle_time_us)
            self.resource_manager.advance_time(cycle_time)
        
        self.execution_log.append(("TELEPORT_CNOT", node["id"], vq_ids))
    
    def _exec_inject_t(self, node: Dict[str, Any]):
        """Execute INJECT_T_STATE operation."""
        # Simplified: log the operation
        self.execution_log.append(("INJECT_T", node["id"]))
    
    def _exec_set_policy(self, node: Dict[str, Any]):
        """Execute SET_POLICY operation."""
        args = node.get("args", {})
        self.execution_log.append(("SET_POLICY", node["id"], args))
