"""
QIR Parser

Parses Quantum Intermediate Representation (QIR) into an intermediate format
that can be lowered to QVM graphs.

QIR is based on LLVM IR with quantum-specific intrinsics.
This parser handles a simplified subset of QIR for demonstration.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class QIRInstructionType(Enum):
    """Types of QIR instructions."""
    # Quantum operations
    QUBIT_ALLOC = "qubit_alloc"
    QUBIT_RELEASE = "qubit_release"
    GATE = "gate"
    MEASURE = "measure"
    RESET = "reset"
    
    # Classical operations
    BRANCH = "branch"
    CALL = "call"
    RETURN = "return"
    
    # Metadata
    FUNCTION_DEF = "function_def"
    LABEL = "label"


@dataclass
class QIRInstruction:
    """
    Represents a single QIR instruction.
    
    Attributes:
        inst_type: Instruction type
        operation: Operation name (for gates)
        qubits: Qubit operands
        parameters: Gate parameters (angles, etc.)
        result: Result register
        metadata: Additional metadata
    """
    inst_type: QIRInstructionType
    operation: Optional[str] = None
    qubits: List[str] = field(default_factory=list)
    parameters: List[float] = field(default_factory=list)
    result: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __repr__(self):
        parts = [f"{self.inst_type.value}"]
        if self.operation:
            parts.append(f"op={self.operation}")
        if self.qubits:
            parts.append(f"qubits={self.qubits}")
        if self.parameters:
            parts.append(f"params={self.parameters}")
        return f"QIRInstruction({', '.join(parts)})"


@dataclass
class QIRFunction:
    """
    Represents a QIR function.
    
    Attributes:
        name: Function name
        parameters: Function parameters
        instructions: List of instructions
        qubit_count: Number of qubits used
    """
    name: str
    parameters: List[str] = field(default_factory=list)
    instructions: List[QIRInstruction] = field(default_factory=list)
    qubit_count: int = 0


class QIRParser:
    """
    Parser for simplified QIR format.
    
    Supports:
    - Basic quantum gates (H, X, Y, Z, S, T, CNOT, RZ, RY, RX)
    - Qubit allocation and release
    - Measurements
    - Function definitions
    """
    
    # QIR intrinsic patterns
    GATE_PATTERNS = {
        r'__quantum__qis__h__body\(%Qubit\* (.+)\)': ('H', 1),
        r'__quantum__qis__x__body\(%Qubit\* (.+)\)': ('X', 1),
        r'__quantum__qis__y__body\(%Qubit\* (.+)\)': ('Y', 1),
        r'__quantum__qis__z__body\(%Qubit\* (.+)\)': ('Z', 1),
        r'__quantum__qis__s__body\(%Qubit\* (.+)\)': ('S', 1),
        r'__quantum__qis__t__body\(%Qubit\* (.+)\)': ('T', 1),
        r'__quantum__qis__cnot__body\(%Qubit\* (.+), %Qubit\* (.+)\)': ('CNOT', 2),
        r'__quantum__qis__rz__body\(double (.+), %Qubit\* (.+)\)': ('RZ', 1),
        r'__quantum__qis__ry__body\(double (.+), %Qubit\* (.+)\)': ('RY', 1),
        r'__quantum__qis__rx__body\(double (.+), %Qubit\* (.+)\)': ('RX', 1),
    }
    
    def __init__(self):
        """Initialize QIR parser."""
        self.functions: Dict[str, QIRFunction] = {}
        self.current_function: Optional[QIRFunction] = None
    
    def parse(self, qir_text: str) -> Dict[str, QIRFunction]:
        """
        Parse QIR text into functions.
        
        Args:
            qir_text: QIR source code
        
        Returns:
            Dictionary of function name -> QIRFunction
        """
        lines = qir_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            self._parse_line(line)
        
        return self.functions
    
    def _parse_line(self, line: str):
        """Parse a single line of QIR."""
        # Function definition
        if line.startswith('define'):
            self._parse_function_def(line)
        
        # Qubit allocation
        elif '__quantum__rt__qubit_allocate' in line:
            self._parse_qubit_alloc(line)
        
        # Qubit release
        elif '__quantum__rt__qubit_release' in line:
            self._parse_qubit_release(line)
        
        # Measurement
        elif '__quantum__qis__mz__body' in line or '__quantum__qis__m__body' in line:
            self._parse_measure(line)
        
        # Reset
        elif '__quantum__qis__reset__body' in line:
            self._parse_reset(line)
        
        # Gates
        else:
            self._parse_gate(line)
    
    def _parse_function_def(self, line: str):
        """Parse function definition."""
        # Example: define void @main() #0 {
        match = re.search(r'define\s+\w+\s+@(\w+)\((.*?)\)', line)
        if match:
            func_name = match.group(1)
            params = match.group(2)
            
            self.current_function = QIRFunction(
                name=func_name,
                parameters=params.split(',') if params else []
            )
            self.functions[func_name] = self.current_function
    
    def _parse_qubit_alloc(self, line: str):
        """Parse qubit allocation."""
        # Example: %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
        match = re.search(r'(%\w+)\s*=\s*call.*__quantum__rt__qubit_allocate', line)
        if match and self.current_function:
            qubit_id = match.group(1)
            
            inst = QIRInstruction(
                inst_type=QIRInstructionType.QUBIT_ALLOC,
                result=qubit_id
            )
            self.current_function.instructions.append(inst)
            self.current_function.qubit_count += 1
    
    def _parse_qubit_release(self, line: str):
        """Parse qubit release."""
        # Example: call void @__quantum__rt__qubit_release(%Qubit* %q0)
        match = re.search(r'__quantum__rt__qubit_release\(%Qubit\*\s+(.+?)\)', line)
        if match and self.current_function:
            qubit_id = match.group(1)
            
            inst = QIRInstruction(
                inst_type=QIRInstructionType.QUBIT_RELEASE,
                qubits=[qubit_id]
            )
            self.current_function.instructions.append(inst)
    
    def _parse_measure(self, line: str):
        """Parse measurement."""
        # Example: %result = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
        match = re.search(r'(%\w+)\s*=\s*call.*__quantum__qis__m[z]?__body\(%Qubit\*\s+(.+?)\)', line)
        if match and self.current_function:
            result = match.group(1)
            qubit_id = match.group(2)
            
            inst = QIRInstruction(
                inst_type=QIRInstructionType.MEASURE,
                operation="MEASURE_Z",
                qubits=[qubit_id],
                result=result
            )
            self.current_function.instructions.append(inst)
    
    def _parse_reset(self, line: str):
        """Parse reset."""
        # Example: call void @__quantum__qis__reset__body(%Qubit* %q0)
        match = re.search(r'__quantum__qis__reset__body\(%Qubit\*\s+(.+?)\)', line)
        if match and self.current_function:
            qubit_id = match.group(1)
            
            inst = QIRInstruction(
                inst_type=QIRInstructionType.RESET,
                operation="RESET",
                qubits=[qubit_id]
            )
            self.current_function.instructions.append(inst)
    
    def _parse_gate(self, line: str):
        """Parse quantum gate."""
        if not self.current_function:
            return
        
        for pattern, (gate_name, qubit_count) in self.GATE_PATTERNS.items():
            match = re.search(pattern, line)
            if match:
                if qubit_count == 1:
                    # Single-qubit gate
                    if gate_name in ['RZ', 'RY', 'RX']:
                        # Rotation gate with parameter
                        angle_str = match.group(1)
                        qubit_id = match.group(2)
                        
                        # Parse angle (could be constant or variable)
                        try:
                            angle = float(angle_str)
                        except ValueError:
                            angle = 0.0  # Placeholder for variable
                        
                        inst = QIRInstruction(
                            inst_type=QIRInstructionType.GATE,
                            operation=gate_name,
                            qubits=[qubit_id],
                            parameters=[angle]
                        )
                    else:
                        # Non-parameterized single-qubit gate
                        qubit_id = match.group(1)
                        inst = QIRInstruction(
                            inst_type=QIRInstructionType.GATE,
                            operation=gate_name,
                            qubits=[qubit_id]
                        )
                elif qubit_count == 2:
                    # Two-qubit gate
                    control = match.group(1)
                    target = match.group(2)
                    inst = QIRInstruction(
                        inst_type=QIRInstructionType.GATE,
                        operation=gate_name,
                        qubits=[control, target]
                    )
                else:
                    continue
                
                self.current_function.instructions.append(inst)
                break
    
    def get_function(self, name: str) -> Optional[QIRFunction]:
        """
        Get a parsed function by name.
        
        Args:
            name: Function name
        
        Returns:
            QIRFunction or None if not found
        """
        return self.functions.get(name)
    
    def get_statistics(self) -> Dict:
        """
        Get parsing statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_functions = len(self.functions)
        total_instructions = sum(len(f.instructions) for f in self.functions.values())
        total_qubits = sum(f.qubit_count for f in self.functions.values())
        
        gate_counts = {}
        for func in self.functions.values():
            for inst in func.instructions:
                if inst.inst_type == QIRInstructionType.GATE:
                    gate_counts[inst.operation] = gate_counts.get(inst.operation, 0) + 1
        
        return {
            "total_functions": total_functions,
            "total_instructions": total_instructions,
            "total_qubits": total_qubits,
            "gate_counts": gate_counts
        }
