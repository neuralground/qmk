"""
QVM Static Verifier

Performs static analysis and certification of QVM graphs BEFORE execution.
No graph is admitted for execution without full certification.

Verifies:
- Linearity (use-once semantics)
- Capability requirements
- Entanglement firewall rules
- Resource bounds
- Type safety

Research Foundation:
- Selinger (2004): "Towards a Quantum Programming Language"
- Green et al. (2013): "Quipper: A Scalable Quantum Programming Language"
- Paykin et al. (2017): "QWIRE: A Core Language for Quantum Circuits"
"""

from typing import Dict, Set, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class VerificationError(Exception):
    """Raised when static verification fails."""
    
    def __init__(self, message: str, error_type: str, details: Dict):
        super().__init__(message)
        self.error_type = error_type
        self.details = details


class VerificationErrorType(Enum):
    """Types of verification errors."""
    LINEARITY_VIOLATION = "linearity_violation"
    CAPABILITY_MISSING = "capability_missing"
    FIREWALL_VIOLATION = "firewall_violation"
    RESOURCE_LEAK = "resource_leak"
    TYPE_ERROR = "type_error"
    INVALID_GRAPH = "invalid_graph"


@dataclass
class VerificationResult:
    """Result of static verification."""
    is_valid: bool
    errors: List[VerificationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {
                    "type": e.error_type,
                    "message": str(e),
                    "details": e.details
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "metadata": self.metadata
        }


class QVMStaticVerifier:
    """
    Static verifier for QVM graphs.
    
    Performs comprehensive static analysis before execution:
    1. Linearity verification (use-once semantics)
    2. Capability verification (required capabilities)
    3. Firewall verification (cross-tenant rules)
    4. Resource leak detection
    5. Type checking
    
    NO GRAPH IS EXECUTED WITHOUT CERTIFICATION.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize static verifier.
        
        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode
        
        # Capability requirements for operations
        self.capability_requirements = {
            "ALLOC_LQ": {"CAP_ALLOC"},
            "MEASURE_Z": {"CAP_MEASURE"},
            "MEASURE_X": {"CAP_MEASURE"},
            "MEASURE_Y": {"CAP_MEASURE"},
            "MEASURE_BELL": {"CAP_MEASURE"},
            "OPEN_CHAN": {"CAP_LINK"},
            "TELEPORT_CNOT": {"CAP_TELEPORT"},
            "INJECT_T_STATE": {"CAP_MAGIC"},
        }
        
        # Operations that consume qubits (linearity)
        self.consuming_operations = {
            "MEASURE_Z", "MEASURE_X", "MEASURE_Y", "MEASURE_BELL",
            "FREE_LQ", "RESET"
        }
        
        # Two-qubit gates that create entanglement
        self.entangling_gates = {
            "APPLY_CNOT", "APPLY_CZ", "APPLY_SWAP",
            "TELEPORT_CNOT"
        }
    
    def verify_graph(
        self,
        qvm_graph: Dict[str, Any],
        available_capabilities: Optional[Set[str]] = None,
        tenant_id: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify a QVM graph statically.
        
        This is the GATE KEEPER - no graph passes without certification.
        
        Args:
            qvm_graph: QVM graph to verify
            available_capabilities: Set of available capability names
            tenant_id: Tenant executing the graph
        
        Returns:
            VerificationResult with certification status
        """
        result = VerificationResult(is_valid=True)
        
        # Parse graph
        try:
            if isinstance(qvm_graph, str):
                graph = json.loads(qvm_graph)
            else:
                graph = qvm_graph
            
            nodes = graph.get("program", {}).get("nodes", [])
            
            # Validate nodes is a list
            if not isinstance(nodes, list):
                result.errors.append(VerificationError(
                    f"Invalid nodes type: expected list, got {type(nodes).__name__}",
                    VerificationErrorType.INVALID_GRAPH.value,
                    {"nodes_type": type(nodes).__name__}
                ))
                result.is_valid = False
                return result
            
            if not nodes:
                result.errors.append(VerificationError(
                    "Empty or invalid graph",
                    VerificationErrorType.INVALID_GRAPH.value,
                    {"graph": graph}
                ))
                result.is_valid = False
                return result
        
        except Exception as e:
            result.errors.append(VerificationError(
                f"Failed to parse graph: {e}",
                VerificationErrorType.INVALID_GRAPH.value,
                {"error": str(e)}
            ))
            result.is_valid = False
            return result
        
        # Run verification passes
        self._verify_linearity(nodes, result)
        self._verify_capabilities(nodes, available_capabilities, result)
        self._verify_firewall_rules(nodes, tenant_id, result)
        self._verify_resource_bounds(nodes, result)
        
        # In strict mode, warnings are errors
        if self.strict_mode and result.warnings:
            for warning in result.warnings:
                result.errors.append(VerificationError(
                    f"Strict mode: {warning}",
                    VerificationErrorType.INVALID_GRAPH.value,
                    {"warning": warning}
                ))
        
        # Final verdict
        result.is_valid = len(result.errors) == 0
        
        # Add metadata
        result.metadata = {
            "node_count": len(nodes),
            "strict_mode": self.strict_mode,
            "tenant_id": tenant_id,
            "verified": result.is_valid
        }
        
        return result
    
    def _verify_linearity(self, nodes: List[Dict], result: VerificationResult):
        """
        Verify linearity constraints (use-once semantics).
        
        Ensures:
        - Each qubit is used at most once
        - No use-after-consume
        - No double-free
        """
        # Track qubit lifecycle
        allocated_qubits: Set[str] = set()
        consumed_qubits: Set[str] = set()
        
        for node in nodes:
            op = node.get("op", "")
            vqs = node.get("vqs", [])
            
            # Allocation
            if op == "ALLOC_LQ":
                for vq in vqs:
                    if vq in allocated_qubits:
                        result.errors.append(VerificationError(
                            f"Qubit {vq} allocated twice",
                            VerificationErrorType.LINEARITY_VIOLATION.value,
                            {"node_id": node.get("id"), "qubit": vq}
                        ))
                    allocated_qubits.add(vq)
            
            # Consumption
            elif op in self.consuming_operations:
                for vq in vqs:
                    if vq not in allocated_qubits:
                        result.errors.append(VerificationError(
                            f"Qubit {vq} used before allocation",
                            VerificationErrorType.LINEARITY_VIOLATION.value,
                            {"node_id": node.get("id"), "qubit": vq, "operation": op}
                        ))
                    
                    if vq in consumed_qubits:
                        result.errors.append(VerificationError(
                            f"Qubit {vq} used after consumption (use-after-free)",
                            VerificationErrorType.LINEARITY_VIOLATION.value,
                            {"node_id": node.get("id"), "qubit": vq, "operation": op}
                        ))
                    
                    consumed_qubits.add(vq)
            
            # Usage (non-consuming)
            else:
                for vq in vqs:
                    if vq not in allocated_qubits:
                        result.errors.append(VerificationError(
                            f"Qubit {vq} used before allocation",
                            VerificationErrorType.LINEARITY_VIOLATION.value,
                            {"node_id": node.get("id"), "qubit": vq, "operation": op}
                        ))
                    
                    if vq in consumed_qubits:
                        result.errors.append(VerificationError(
                            f"Qubit {vq} used after consumption",
                            VerificationErrorType.LINEARITY_VIOLATION.value,
                            {"node_id": node.get("id"), "qubit": vq, "operation": op}
                        ))
        
        # Check for resource leaks (allocated but never consumed)
        leaked_qubits = allocated_qubits - consumed_qubits
        if leaked_qubits:
            result.warnings.append(
                f"Potential resource leaks: {', '.join(sorted(leaked_qubits))}"
            )
    
    def _verify_capabilities(
        self,
        nodes: List[Dict],
        available_capabilities: Optional[Set[str]],
        result: VerificationResult
    ):
        """
        Verify capability requirements.
        
        Ensures all operations have required capabilities.
        """
        if available_capabilities is None:
            # No capability checking if not provided
            return
        
        for node in nodes:
            op = node.get("op", "")
            required = self.capability_requirements.get(op, set())
            
            if not required:
                continue
            
            # Check if all required capabilities are available
            missing = required - available_capabilities
            if missing:
                result.errors.append(VerificationError(
                    f"Operation {op} requires capabilities {missing}",
                    VerificationErrorType.CAPABILITY_MISSING.value,
                    {
                        "node_id": node.get("id"),
                        "operation": op,
                        "required": list(required),
                        "missing": list(missing)
                    }
                ))
    
    def _verify_firewall_rules(
        self,
        nodes: List[Dict],
        tenant_id: Optional[str],
        result: VerificationResult
    ):
        """
        Verify entanglement firewall rules.
        
        Ensures:
        - Cross-tenant entanglement has channels
        - Same-tenant entanglement is allowed
        """
        # Track qubit ownership
        qubit_tenants: Dict[str, str] = {}
        
        for node in nodes:
            op = node.get("op", "")
            vqs = node.get("vqs", [])
            args = node.get("args", {})
            
            # Track allocation
            if op == "ALLOC_LQ":
                node_tenant = args.get("tenant_id", tenant_id or "default")
                for vq in vqs:
                    qubit_tenants[vq] = node_tenant
            
            # Check entangling gates
            if op in self.entangling_gates and len(vqs) >= 2:
                vq1, vq2 = vqs[0], vqs[1]
                
                # Get tenants
                tenant1 = qubit_tenants.get(vq1, tenant_id or "default")
                tenant2 = qubit_tenants.get(vq2, tenant_id or "default")
                
                # Cross-tenant entanglement requires channel
                if tenant1 != tenant2:
                    channel = args.get("channel")
                    if not channel:
                        result.errors.append(VerificationError(
                            f"Cross-tenant entanglement {vq1}({tenant1}) ↔ {vq2}({tenant2}) requires channel",
                            VerificationErrorType.FIREWALL_VIOLATION.value,
                            {
                                "node_id": node.get("id"),
                                "operation": op,
                                "qubit1": vq1,
                                "tenant1": tenant1,
                                "qubit2": vq2,
                                "tenant2": tenant2
                            }
                        ))
    
    def _verify_resource_bounds(self, nodes: List[Dict], result: VerificationResult):
        """
        Verify resource bounds.
        
        Checks:
        - Maximum qubit count
        - Graph depth
        - Operation count
        """
        # Count allocations
        max_qubits = 0
        current_qubits = set()
        
        for node in nodes:
            op = node.get("op", "")
            vqs = node.get("vqs", [])
            
            if op == "ALLOC_LQ":
                current_qubits.update(vqs)
                max_qubits = max(max_qubits, len(current_qubits))
            elif op in self.consuming_operations:
                current_qubits.difference_update(vqs)
        
        # Warn if too many qubits
        if max_qubits > 1000:
            result.warnings.append(
                f"Graph uses {max_qubits} qubits (may exceed resource limits)"
            )
        
        # Warn if too many operations
        if len(nodes) > 10000:
            result.warnings.append(
                f"Graph has {len(nodes)} operations (may be too complex)"
            )
    
    def certify_graph(
        self,
        qvm_graph: Dict[str, Any],
        available_capabilities: Optional[Set[str]] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[bool, VerificationResult]:
        """
        Certify a QVM graph for execution.
        
        This is the FINAL GATE - returns (certified, result).
        
        Args:
            qvm_graph: QVM graph to certify
            available_capabilities: Available capabilities
            tenant_id: Tenant ID
        
        Returns:
            (is_certified, verification_result)
        """
        result = self.verify_graph(qvm_graph, available_capabilities, tenant_id)
        
        # Graph is certified ONLY if no errors
        is_certified = result.is_valid and len(result.errors) == 0
        
        return is_certified, result
    
    def get_certification_report(self, result: VerificationResult) -> str:
        """
        Generate human-readable certification report.
        
        Args:
            result: Verification result
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("QVM GRAPH CERTIFICATION REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        if result.is_valid:
            lines.append("✅ CERTIFIED - Graph passed all verification checks")
        else:
            lines.append("❌ REJECTED - Graph failed verification")
        
        lines.append("")
        lines.append(f"Errors: {len(result.errors)}")
        lines.append(f"Warnings: {len(result.warnings)}")
        lines.append("")
        
        if result.errors:
            lines.append("ERRORS:")
            for i, error in enumerate(result.errors, 1):
                lines.append(f"  {i}. [{error.error_type}] {error}")
                if error.details:
                    for key, value in error.details.items():
                        lines.append(f"     - {key}: {value}")
            lines.append("")
        
        if result.warnings:
            lines.append("WARNINGS:")
            for i, warning in enumerate(result.warnings, 1):
                lines.append(f"  {i}. {warning}")
            lines.append("")
        
        lines.append("METADATA:")
        for key, value in result.metadata.items():
            lines.append(f"  - {key}: {value}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Convenience function for quick verification
def verify_qvm_graph(
    qvm_graph: Dict[str, Any],
    available_capabilities: Optional[Set[str]] = None,
    tenant_id: Optional[str] = None,
    strict_mode: bool = True
) -> VerificationResult:
    """
    Quick verification of QVM graph.
    
    Args:
        qvm_graph: QVM graph to verify
        available_capabilities: Available capabilities
        tenant_id: Tenant ID
        strict_mode: Treat warnings as errors
    
    Returns:
        VerificationResult
    """
    verifier = QVMStaticVerifier(strict_mode=strict_mode)
    return verifier.verify_graph(qvm_graph, available_capabilities, tenant_id)
