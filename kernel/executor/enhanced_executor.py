"""
Enhanced QVM Graph Executor with Logical Qubit Simulation

Executes QVM graphs using the logical qubit simulator with full error modeling.
"""

from typing import Dict, List, Any, Optional
import json

from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.qec_profiles import parse_profile_string
from kernel.simulator.logical_qubit import TwoQubitGate
from kernel.simulator.capabilities import DEFAULT_CAPS, has_caps
from kernel.simulator.scheduler import topo_schedule
from kernel.security.entanglement_firewall import (
    EntanglementGraph,
    EntanglementFirewallViolation
)
from kernel.types.linear_types import (
    LinearTypeSystem,
    LinearityViolation
)
from kernel.security.capability_system import (
    CapabilitySystem,
    CapabilityToken,
    CapabilityType
)
from qvm.static_verifier import QVMStaticVerifier, VerificationError


# Capability requirements for operations
CAP_REQUIRED = {
    "ALLOC_LQ": {CapabilityType.CAP_ALLOC},
    "OPEN_CHAN": {CapabilityType.CAP_LINK},
    "TELEPORT_CNOT": {CapabilityType.CAP_TELEPORT},
    "INJECT_T_STATE": {CapabilityType.CAP_MAGIC},
    "MEASURE_Z": {CapabilityType.CAP_MEASURE},
    "MEASURE_X": {CapabilityType.CAP_MEASURE},
    "MEASURE_BELL": {CapabilityType.CAP_MEASURE},
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
                 caps: Optional[Dict[str, bool]] = None,
                 entanglement_firewall: Optional[EntanglementGraph] = None,
                 linear_type_system: Optional[LinearTypeSystem] = None,
                 capability_system: Optional[CapabilitySystem] = None,
                 capability_token: Optional[CapabilityToken] = None,
                 require_certification: bool = True,
                 strict_verification: bool = True):
        """
        Initialize executor.
        
        Args:
            max_physical_qubits: Maximum physical qubits available
            seed: Random seed for deterministic execution
            caps: Capability overrides (deprecated, use capability_token)
            entanglement_firewall: Optional entanglement firewall for multi-tenant security
            linear_type_system: Optional linear type system for use-once semantics
            capability_system: Optional capability system for operation authorization
            capability_token: Optional capability token for this execution
            require_certification: If True, graphs must be certified before execution (RECOMMENDED)
            strict_verification: If True, warnings are treated as errors in verification
        """
        self.resource_manager = EnhancedResourceManager(
            max_physical_qubits=max_physical_qubits,
            seed=seed
        )
        self.caps = caps or DEFAULT_CAPS.copy()
        self.execution_log: List = []
        self.events: Dict[str, Any] = {}
        
        # Entanglement firewall for multi-tenant security
        self.entanglement_firewall = entanglement_firewall
        
        # Linear type system for use-once semantics
        self.linear_type_system = linear_type_system
        
        # Capability system for operation authorization
        self.capability_system = capability_system
        self.capability_token = capability_token
        
        # Static verifier for graph certification
        self.require_certification = require_certification
        self.static_verifier = QVMStaticVerifier(strict_mode=strict_verification)
        
        # Track qubit tenant ownership for firewall
        self.qubit_tenants: Dict[str, str] = {}
        
        # Track linear handles for qubits
        self.qubit_handles: Dict[str, str] = {}  # vq_id -> handle_id
        
        # Event storage (measurement outcomes)
        self.events: Dict[str, int] = {}
        
        # Execution log
        self.execution_log: List = []
        
        # Store configuration for execution context
        self.max_physical_qubits = max_physical_qubits
        self.seed = seed
        self.strict_verification = strict_verification
    
    def get_execution_context(self) -> Dict[str, Any]:
        """
        Get execution context information.
        
        Returns:
            Dictionary with backend and configuration details
        """
        return {
            "backend": "QMK Enhanced Executor",
            "backend_version": "1.0.0",
            "simulator": "Logical Qubit Simulator",
            "qec_enabled": True,
            "configuration": {
                "max_physical_qubits": self.max_physical_qubits,
                "deterministic": self.seed is not None,
                "seed": self.seed,
                "certification_required": self.require_certification,
                "strict_verification": self.strict_verification,
            },
            "security_features": {
                "entanglement_firewall": self.entanglement_firewall is not None,
                "linear_type_system": self.linear_type_system is not None,
                "capability_system": self.capability_system is not None,
            },
            "capabilities": list(self.caps.keys()) if self.caps else []
        }
    
    def execute(self, qvm_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a QVM graph with automatic resource lifecycle management.
        
        CRITICAL: Graph must pass static verification before execution.
        NO GRAPH IS EXECUTED WITHOUT CERTIFICATION.
        
        Resource Lifecycle:
        1. LOAD: Verify graph and prepare execution context
        2. EXECUTE: Run graph operations
        3. UNLOAD: Clean up resources (automatic, even on error)
        
        Args:
            qvm_graph: QVM graph in JSON format
        
        Returns:
            Execution result with telemetry
        
        Raises:
            VerificationError: If graph fails static verification
        """
        # Track allocated resources for cleanup
        allocated_qubits = []
        
        try:
            # === PHASE 1: LOAD ===
            # Verify and prepare execution context
            self._load_graph(qvm_graph)
            
            # Parse graph
            if isinstance(qvm_graph, str):
                graph = json.loads(qvm_graph)
            else:
                graph = qvm_graph
            
            nodes = graph["program"]["nodes"]
            global_caps = graph.get("caps", [])
            
            # Topological sort for execution order
            execution_order = topo_schedule(nodes)
            
            # === PHASE 2: EXECUTE ===
            # Execute nodes in order
            for node in execution_order:
                self._execute_node(node, global_caps)
                
                # Track allocations for cleanup
                if node.get("op") == "ALLOC_LQ":
                    allocated_qubits.extend(node.get("vqs", []))
            
            # === PHASE 3: UNLOAD (Success) ===
            # Capture telemetry BEFORE cleanup to show peak resource usage
            peak_telemetry = self.resource_manager.get_telemetry()
            peak_usage = self.resource_manager.get_resource_usage()
            
            result = {
                "status": "COMPLETED",
                "events": dict(self.events),
                "telemetry": peak_telemetry,
                "peak_resources": {
                    "logical_qubits": peak_usage["logical_qubits_allocated"],
                    "physical_qubits": peak_usage["physical_qubits_used"],
                    "channels": peak_usage["channels_open"]
                },
                "execution_context": self.get_execution_context(),
                "execution_log": self.execution_log,
            }
            
            return result
            
        except Exception as e:
            # === PHASE 3: UNLOAD (Error) ===
            # Log the error
            self.execution_log.append(("ERROR", str(e)))
            
            # Re-raise the exception after cleanup
            raise
            
        finally:
            # ALWAYS clean up resources, success or failure
            self._unload_graph(allocated_qubits)
    
    def _load_graph(self, qvm_graph: Dict[str, Any]):
        """
        LOAD phase: Verify graph and prepare execution context.
        
        Args:
            qvm_graph: QVM graph to load
        
        Raises:
            VerificationError: If graph fails verification
        """
        # GATE KEEPER: Static verification BEFORE execution
        if self.require_certification:
            # Get available capabilities
            available_caps = None
            if self.capability_token:
                available_caps = {cap.value for cap in self.capability_token.capabilities}
            
            # Get tenant ID
            tenant_id = self.capability_token.tenant_id if self.capability_token else None
            
            # CERTIFY THE GRAPH
            is_certified, verification_result = self.static_verifier.certify_graph(
                qvm_graph,
                available_capabilities=available_caps,
                tenant_id=tenant_id
            )
            
            # REJECT if not certified
            if not is_certified:
                # Log rejection
                self.execution_log.append(("REJECTED", "static_verification_failed"))
                
                # Generate report
                report = self.static_verifier.get_certification_report(verification_result)
                
                # Raise error with full details
                raise VerificationError(
                    f"Graph failed static verification with {len(verification_result.errors)} errors",
                    "certification_failed",
                    {
                        "errors": [str(e) for e in verification_result.errors],
                        "report": report,
                        "verification_result": verification_result.to_dict()
                    }
                )
            
            # Log successful certification
            self.execution_log.append(("CERTIFIED", "static_verification_passed"))
        
        # Prepare fresh execution context
        self.resource_manager.reset()
        self.events.clear()
        self.execution_log.clear()
        self.qubit_tenants.clear()
        self.qubit_handles.clear()
        
        self.execution_log.append(("LOAD", "graph_loaded_and_verified"))
    
    def _unload_graph(self, allocated_qubits: List[str]):
        """
        UNLOAD phase: Clean up all allocated resources.
        
        This is called automatically after execution (success or failure)
        to ensure resources are properly released.
        
        Args:
            allocated_qubits: List of qubit IDs that were allocated
        """
        # Free any allocated qubits that weren't explicitly freed
        if allocated_qubits:
            try:
                # Only free qubits that are still allocated
                still_allocated = [
                    qid for qid in allocated_qubits 
                    if qid in self.resource_manager.logical_qubits
                ]
                
                if still_allocated:
                    self.resource_manager.free_logical_qubits(still_allocated)
                    self.execution_log.append(("UNLOAD", f"freed_{len(still_allocated)}_qubits"))
            except Exception as e:
                # Log cleanup errors but don't fail
                self.execution_log.append(("UNLOAD_ERROR", f"cleanup_failed: {e}"))
        
        self.execution_log.append(("UNLOAD", "resources_released"))
    
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
        
        # If capability system is enabled, use cryptographic tokens
        if self.capability_system and self.capability_token:
            for cap in required:
                if not self.capability_system.check_capability(
                    self.capability_token, cap, use_token=False
                ):
                    raise RuntimeError(
                        f"Capability {cap.value} required for {op} but not granted"
                    )
        else:
            # Fallback to old system (deprecated)
            node_caps = set(node.get("caps", []))
            available = node_caps | set(global_caps) | {c for c, v in self.caps.items() if v}
            
            # Convert required CapabilityType to strings for comparison
            required_str = {cap.value if hasattr(cap, 'value') else str(cap) for cap in required}
            
            if not required_str.issubset(available):
                missing = required_str - available
                missing_str = ', '.join(sorted(missing))
                raise RuntimeError(
                    f"Missing capabilities for {op}: {missing_str}"
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
        
        # Register qubits with entanglement firewall
        if self.entanglement_firewall is not None:
            tenant_id = args.get("tenant_id", "default")
            for vq_id in vq_ids:
                self.entanglement_firewall.register_qubit(vq_id, tenant_id)
                self.qubit_tenants[vq_id] = tenant_id
        
        # Create linear handles for use-once semantics
        if self.linear_type_system is not None:
            tenant_id = args.get("tenant_id", "default")
            for vq_id in vq_ids:
                handle = self.linear_type_system.create_handle(
                    resource_type="VQ",
                    resource_id=vq_id,
                    tenant_id=tenant_id,
                    metadata={"profile": profile_str}
                )
                self.qubit_handles[vq_id] = handle.handle_id
        
        self.execution_log.append(("ALLOC", node["id"], vq_ids, profile.code_family, allocated))
    
    def _exec_free(self, node: Dict[str, Any]):
        """Execute FREE_LQ operation."""
        vq_ids = node.get("vqs", [])
        self.resource_manager.free_logical_qubits(vq_ids)
        
        # Consume linear handles (use-once semantics)
        if self.linear_type_system is not None:
            for vq_id in vq_ids:
                if vq_id in self.qubit_handles:
                    handle_id = self.qubit_handles[vq_id]
                    try:
                        self.linear_type_system.consume_handle(handle_id, "FREE_LQ")
                    except LinearityViolation as e:
                        self.execution_log.append(("LINEARITY_VIOLATION", node["id"], str(e)))
                        raise
                    del self.qubit_handles[vq_id]
        
        # Unregister qubits from entanglement firewall
        if self.entanglement_firewall is not None:
            for vq_id in vq_ids:
                self.entanglement_firewall.unregister_qubit(vq_id)
                if vq_id in self.qubit_tenants:
                    del self.qubit_tenants[vq_id]
        
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
            # Two-qubit gate - check entanglement firewall
            vq1_id, vq2_id = vq_ids[0], vq_ids[1]
            
            # Firewall check for cross-tenant entanglement
            if self.entanglement_firewall is not None:
                # Get channel if provided in node args
                channel = node.get("args", {}).get("channel")
                
                # Add entanglement (firewall will check authorization)
                try:
                    self.entanglement_firewall.add_entanglement(
                        vq1_id, vq2_id, gate_type, channel
                    )
                except EntanglementFirewallViolation as e:
                    # Log violation and re-raise
                    self.execution_log.append(("FIREWALL_VIOLATION", node["id"], str(e)))
                    raise
            
            # Execute gate
            qubit1 = self.resource_manager.get_logical_qubit(vq1_id)
            qubit2 = self.resource_manager.get_logical_qubit(vq2_id)
            
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
            from kernel.simulator.logical_qubit import LogicalQubit
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
        
        # Consume linear handle (measurement consumes the qubit)
        if self.linear_type_system is not None:
            vq_id = vq_ids[0]
            if vq_id in self.qubit_handles:
                handle_id = self.qubit_handles[vq_id]
                try:
                    self.linear_type_system.consume_handle(handle_id, f"MEASURE_{basis}")
                except LinearityViolation as e:
                    self.execution_log.append(("LINEARITY_VIOLATION", node["id"], str(e)))
                    raise
                del self.qubit_handles[vq_id]
        
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
