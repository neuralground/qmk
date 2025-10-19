"""
QVM Graph Generator

Converts parsed QIR functions into QVM graphs that can be executed by QMK.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from .qir_parser import QIRFunction, QIRInstruction, QIRInstructionType


@dataclass
class QVMNode:
    """Represents a node in the QVM graph."""
    node_id: str
    op: str
    qubits: List[str]
    params: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        node = {
            "node_id": self.node_id,
            "op": self.op,
            "qubits": self.qubits
        }
        if self.params:
            node["params"] = self.params
        return node


class QVMGraphGenerator:
    """
    Generates QVM graphs from QIR functions.
    
    Handles:
    - Qubit allocation/release
    - Gate operations
    - Measurements
    - Teleportation insertion for non-Clifford gates
    """
    
    def __init__(self, insert_teleportation: bool = False):
        """
        Initialize QVM graph generator.
        
        Args:
            insert_teleportation: Whether to insert teleportation for non-Clifford gates
        """
        self.insert_teleportation = insert_teleportation
        self.node_counter = 0
    
    def generate(self, qir_function: QIRFunction) -> Dict:
        """
        Generate QVM graph from QIR function.
        
        Args:
            qir_function: Parsed QIR function
        
        Returns:
            QVM graph dictionary
        """
        nodes = []
        qubit_map = {}  # QIR qubit ID -> QVM qubit ID
        
        for inst in qir_function.instructions:
            if inst.inst_type == QIRInstructionType.QUBIT_ALLOC:
                # Allocate qubit
                qir_qubit = inst.result
                qvm_qubit = f"q{len(qubit_map)}"
                qubit_map[qir_qubit] = qvm_qubit
                
                node = self._create_alloc_node(qvm_qubit)
                nodes.append(node)
            
            elif inst.inst_type == QIRInstructionType.QUBIT_RELEASE:
                # Release qubit
                qir_qubit = inst.qubits[0]
                if qir_qubit in qubit_map:
                    qvm_qubit = qubit_map[qir_qubit]
                    node = self._create_free_node(qvm_qubit)
                    nodes.append(node)
            
            elif inst.inst_type == QIRInstructionType.GATE:
                # Gate operation
                qvm_qubits = [qubit_map.get(q, q) for q in inst.qubits]
                
                if self.insert_teleportation and inst.operation in ['T', 'RZ', 'RY', 'RX']:
                    # Insert teleportation for non-Clifford gates
                    teleport_nodes = self._create_teleportation_nodes(
                        inst.operation, qvm_qubits, inst.parameters
                    )
                    nodes.extend(teleport_nodes)
                else:
                    # Direct gate
                    node = self._create_gate_node(
                        inst.operation, qvm_qubits, inst.parameters
                    )
                    nodes.append(node)
            
            elif inst.inst_type == QIRInstructionType.MEASURE:
                # Measurement
                qir_qubit = inst.qubits[0]
                if qir_qubit in qubit_map:
                    qvm_qubit = qubit_map[qir_qubit]
                    node = self._create_measure_node(qvm_qubit, inst.result)
                    nodes.append(node)
            
            elif inst.inst_type == QIRInstructionType.RESET:
                # Reset
                qir_qubit = inst.qubits[0]
                if qir_qubit in qubit_map:
                    qvm_qubit = qubit_map[qir_qubit]
                    node = self._create_reset_node(qvm_qubit)
                    nodes.append(node)
        
        # Build QVM graph
        graph = {
            "name": qir_function.name,
            "nodes": [node.to_dict() for node in nodes],
            "metadata": {
                "source": "QIR",
                "qubit_count": len(qubit_map),
                "instruction_count": len(qir_function.instructions)
            }
        }
        
        return graph
    
    def _create_alloc_node(self, qubit: str) -> QVMNode:
        """Create qubit allocation node."""
        node_id = self._next_node_id()
        return QVMNode(
            node_id=node_id,
            op="ALLOC_LQ",
            qubits=[qubit],
            params={"profile": "logical:surface_code(d=9)"}
        )
    
    def _create_free_node(self, qubit: str) -> QVMNode:
        """Create qubit release node."""
        node_id = self._next_node_id()
        return QVMNode(
            node_id=node_id,
            op="FREE_LQ",
            qubits=[qubit]
        )
    
    def _create_gate_node(
        self,
        operation: str,
        qubits: List[str],
        parameters: Optional[List[float]] = None
    ) -> QVMNode:
        """Create gate operation node."""
        node_id = self._next_node_id()
        params = None
        
        if parameters:
            if operation in ['RZ', 'RY', 'RX']:
                params = {"angle": parameters[0]}
        
        return QVMNode(
            node_id=node_id,
            op=operation,
            qubits=qubits,
            params=params
        )
    
    def _create_measure_node(self, qubit: str, result: Optional[str] = None) -> QVMNode:
        """Create measurement node."""
        node_id = self._next_node_id()
        params = {"basis": "Z"}
        if result:
            params["result"] = result
        
        return QVMNode(
            node_id=node_id,
            op="MEASURE_Z",
            qubits=[qubit],
            params=params
        )
    
    def _create_reset_node(self, qubit: str) -> QVMNode:
        """Create reset node."""
        node_id = self._next_node_id()
        return QVMNode(
            node_id=node_id,
            op="RESET",
            qubits=[qubit]
        )
    
    def _create_teleportation_nodes(
        self,
        operation: str,
        qubits: List[str],
        parameters: Optional[List[float]] = None
    ) -> List[QVMNode]:
        """
        Create teleportation sequence for non-Clifford gate.
        
        For T gate: uses magic state teleportation
        For rotation gates: uses rotation state teleportation
        """
        nodes = []
        qubit = qubits[0]
        
        # Simplified teleportation: just mark it as teleported
        node_id = self._next_node_id()
        params = {"teleported": True}
        
        if parameters:
            params["angle"] = parameters[0]
        
        nodes.append(QVMNode(
            node_id=node_id,
            op=operation,
            qubits=qubits,
            params=params
        ))
        
        return nodes
    
    def _next_node_id(self) -> str:
        """Generate next node ID."""
        node_id = f"n{self.node_counter}"
        self.node_counter += 1
        return node_id
    
    def generate_multiple(
        self,
        qir_functions: Dict[str, QIRFunction]
    ) -> Dict[str, Dict]:
        """
        Generate QVM graphs for multiple functions.
        
        Args:
            qir_functions: Dictionary of function name -> QIRFunction
        
        Returns:
            Dictionary of function name -> QVM graph
        """
        graphs = {}
        
        for name, func in qir_functions.items():
            self.node_counter = 0  # Reset for each function
            graphs[name] = self.generate(func)
        
        return graphs
