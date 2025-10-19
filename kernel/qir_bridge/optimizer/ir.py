"""
Intermediate Representation for QIR Optimization

Provides a mutable IR for circuit optimization that can be converted
to/from QIR and QVM formats.
"""

from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


class InstructionType(Enum):
    """Types of quantum instructions."""
    # Allocation
    ALLOC = "alloc"
    RELEASE = "release"
    
    # Single-qubit gates
    H = "h"
    X = "x"
    Y = "y"
    Z = "z"
    S = "s"
    SDG = "sdg"
    T = "t"
    TDG = "tdg"
    
    # Rotation gates
    RX = "rx"
    RY = "ry"
    RZ = "rz"
    
    # Two-qubit gates
    CNOT = "cnot"
    CZ = "cz"
    SWAP = "swap"
    
    # Measurements
    MEASURE = "measure"
    
    # Control flow
    BARRIER = "barrier"
    RESET = "reset"


@dataclass
class QIRQubit:
    """Represents a qubit in the IR."""
    id: str
    index: int
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, QIRQubit):
            return self.id == other.id
        return False
    
    def __repr__(self):
        return f"Qubit({self.id})"


@dataclass
class QIRInstruction:
    """
    Represents a quantum instruction in the IR.
    
    Attributes:
        inst_type: Type of instruction
        qubits: Qubits this instruction operates on
        params: Parameters (e.g., rotation angles)
        result: Result register (for measurements)
        metadata: Additional metadata
    """
    inst_type: InstructionType
    qubits: List[QIRQubit] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_gate(self) -> bool:
        """Check if this is a gate operation."""
        return self.inst_type not in [
            InstructionType.ALLOC,
            InstructionType.RELEASE,
            InstructionType.MEASURE,
            InstructionType.BARRIER
        ]
    
    def is_single_qubit_gate(self) -> bool:
        """Check if this is a single-qubit gate."""
        return self.is_gate() and len(self.qubits) == 1
    
    def is_two_qubit_gate(self) -> bool:
        """Check if this is a two-qubit gate."""
        return self.is_gate() and len(self.qubits) == 2
    
    def is_measurement(self) -> bool:
        """Check if this is a measurement."""
        return self.inst_type == InstructionType.MEASURE
    
    def commutes_with(self, other: 'QIRInstruction') -> bool:
        """
        Check if this instruction commutes with another.
        
        Commutation rules:
        - Gates on different qubits commute
        - Same gate on same qubit may not commute
        - Measurements don't commute with gates on same qubit
        """
        # Different qubits always commute
        self_qubits = set(self.qubits)
        other_qubits = set(other.qubits)
        
        if not self_qubits.intersection(other_qubits):
            return True
        
        # Same qubits - need to check gate types
        # For now, conservative: only commute if both are single-qubit Pauli gates
        if (self.inst_type in [InstructionType.X, InstructionType.Y, InstructionType.Z] and
            other.inst_type in [InstructionType.X, InstructionType.Y, InstructionType.Z] and
            self.inst_type != other.inst_type):
            return False  # Different Paulis don't commute
        
        return False  # Conservative: don't commute by default
    
    def inverse(self) -> Optional['QIRInstruction']:
        """
        Get the inverse of this instruction.
        
        Returns None if the instruction is not invertible or is self-inverse.
        """
        # Self-inverse gates
        if self.inst_type in [InstructionType.H, InstructionType.X, 
                              InstructionType.Y, InstructionType.Z,
                              InstructionType.CNOT, InstructionType.SWAP]:
            return QIRInstruction(
                inst_type=self.inst_type,
                qubits=self.qubits.copy(),
                params=self.params.copy()
            )
        
        # S and S†
        if self.inst_type == InstructionType.S:
            return QIRInstruction(
                inst_type=InstructionType.SDG,
                qubits=self.qubits.copy()
            )
        elif self.inst_type == InstructionType.SDG:
            return QIRInstruction(
                inst_type=InstructionType.S,
                qubits=self.qubits.copy()
            )
        
        # T and T†
        if self.inst_type == InstructionType.T:
            return QIRInstruction(
                inst_type=InstructionType.TDG,
                qubits=self.qubits.copy()
            )
        elif self.inst_type == InstructionType.TDG:
            return QIRInstruction(
                inst_type=InstructionType.T,
                qubits=self.qubits.copy()
            )
        
        # Rotation gates (negate angle)
        if self.inst_type in [InstructionType.RX, InstructionType.RY, InstructionType.RZ]:
            return QIRInstruction(
                inst_type=self.inst_type,
                qubits=self.qubits.copy(),
                params={'theta': -self.params.get('theta', 0)}
            )
        
        return None
    
    def __repr__(self):
        qubits_str = ', '.join(str(q) for q in self.qubits)
        if self.params:
            params_str = f", params={self.params}"
        else:
            params_str = ""
        return f"{self.inst_type.value}({qubits_str}{params_str})"


class QIRCircuit:
    """
    Mutable intermediate representation of a quantum circuit.
    
    Provides methods for circuit manipulation and optimization.
    """
    
    def __init__(self):
        self.instructions: List[QIRInstruction] = []
        self.qubits: Dict[str, QIRQubit] = {}
        self.results: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    def add_qubit(self, qubit_id: str) -> QIRQubit:
        """Add a qubit to the circuit."""
        if qubit_id not in self.qubits:
            qubit = QIRQubit(qubit_id, len(self.qubits))
            self.qubits[qubit_id] = qubit
        return self.qubits[qubit_id]
    
    def get_qubit(self, qubit_id: str) -> Optional[QIRQubit]:
        """Get a qubit by ID."""
        return self.qubits.get(qubit_id)
    
    def add_instruction(self, instruction: QIRInstruction):
        """Add an instruction to the circuit."""
        self.instructions.append(instruction)
        
        # Track result registers
        if instruction.result:
            self.results.add(instruction.result)
    
    def remove_instruction(self, index: int):
        """Remove an instruction by index."""
        if 0 <= index < len(self.instructions):
            inst = self.instructions.pop(index)
            # Clean up result if it was the only use
            if inst.result and not any(i.result == inst.result for i in self.instructions):
                self.results.discard(inst.result)
    
    def insert_instruction(self, index: int, instruction: QIRInstruction):
        """Insert an instruction at a specific index."""
        self.instructions.insert(index, instruction)
        if instruction.result:
            self.results.add(instruction.result)
    
    def get_qubit_last_use(self, qubit: QIRQubit) -> Optional[int]:
        """Get the index of the last instruction using this qubit."""
        for i in range(len(self.instructions) - 1, -1, -1):
            if qubit in self.instructions[i].qubits:
                return i
        return None
    
    def get_qubit_uses(self, qubit: QIRQubit) -> List[int]:
        """Get all instruction indices that use this qubit."""
        return [i for i, inst in enumerate(self.instructions) 
                if qubit in inst.qubits]
    
    def is_qubit_measured(self, qubit: QIRQubit) -> bool:
        """Check if a qubit is ever measured."""
        return any(inst.is_measurement() and qubit in inst.qubits 
                  for inst in self.instructions)
    
    def get_gate_count(self) -> int:
        """Count the number of gate operations."""
        return sum(1 for inst in self.instructions if inst.is_gate())
    
    def get_depth(self) -> int:
        """
        Calculate circuit depth (longest path through gates).
        
        Simplified: assumes all gates on different qubits can be parallel.
        """
        if not self.instructions:
            return 0
        
        # Track depth for each qubit
        qubit_depths = {q: 0 for q in self.qubits.values()}
        
        for inst in self.instructions:
            if inst.is_gate():
                # Depth is max of all qubits involved + 1
                max_depth = max(qubit_depths[q] for q in inst.qubits)
                for q in inst.qubits:
                    qubit_depths[q] = max_depth + 1
        
        return max(qubit_depths.values()) if qubit_depths else 0
    
    def get_t_count(self) -> int:
        """Count the number of T gates."""
        return sum(1 for inst in self.instructions 
                  if inst.inst_type in [InstructionType.T, InstructionType.TDG])
    
    def get_cnot_count(self) -> int:
        """Count the number of CNOT gates."""
        return sum(1 for inst in self.instructions 
                  if inst.inst_type == InstructionType.CNOT)
    
    def clone(self) -> 'QIRCircuit':
        """Create a deep copy of this circuit."""
        new_circuit = QIRCircuit()
        new_circuit.qubits = {qid: QIRQubit(q.id, q.index) 
                             for qid, q in self.qubits.items()}
        
        # Map old qubits to new qubits
        qubit_map = {old_q: new_circuit.qubits[old_q.id] 
                    for old_q in self.qubits.values()}
        
        # Copy instructions with new qubit references
        for inst in self.instructions:
            new_inst = QIRInstruction(
                inst_type=inst.inst_type,
                qubits=[qubit_map[q] for q in inst.qubits],
                params=inst.params.copy(),
                result=inst.result,
                metadata=inst.metadata.copy()
            )
            new_circuit.add_instruction(new_inst)
        
        new_circuit.metadata = self.metadata.copy()
        return new_circuit
    
    def __repr__(self):
        return f"QIRCircuit({len(self.qubits)} qubits, {len(self.instructions)} instructions)"
    
    def to_string(self) -> str:
        """Convert circuit to human-readable string."""
        lines = [f"Circuit: {len(self.qubits)} qubits, {len(self.instructions)} instructions"]
        lines.append(f"Qubits: {', '.join(self.qubits.keys())}")
        lines.append("Instructions:")
        for i, inst in enumerate(self.instructions):
            lines.append(f"  {i:3d}: {inst}")
        return '\n'.join(lines)
