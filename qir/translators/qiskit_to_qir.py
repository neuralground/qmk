"""
Qiskit to QIR Converter

Converts Qiskit QuantumCircuit to QIR (Quantum Intermediate Representation).
"""

from typing import Dict, List, Any, Optional
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction, Qubit, Clbit


class QiskitToQIRConverter:
    """
    Converts Qiskit circuits to QIR format.
    
    Supports:
    - Single-qubit gates (H, X, Y, Z, S, T, Rx, Ry, Rz)
    - Two-qubit gates (CNOT, CZ, SWAP)
    - Measurements
    - Barriers
    """
    
    def __init__(self):
        self.qubit_map: Dict[Qubit, str] = {}
        self.clbit_map: Dict[Clbit, str] = {}
        self.instruction_count = 0
    
    def convert(self, circuit: QuantumCircuit) -> str:
        """
        Convert Qiskit circuit to QIR string.
        
        Args:
            circuit: Qiskit QuantumCircuit
        
        Returns:
            QIR program as string
        """
        # Build qubit mapping
        for i, qubit in enumerate(circuit.qubits):
            self.qubit_map[qubit] = f"q{i}"
        
        # Build classical bit mapping
        for i, clbit in enumerate(circuit.clbits):
            self.clbit_map[clbit] = f"c{i}"
        
        # Generate QIR
        qir_lines = []
        qir_lines.append("; QIR generated from Qiskit")
        qir_lines.append(f"; Qubits: {circuit.num_qubits}")
        qir_lines.append(f"; Classical bits: {circuit.num_clbits}")
        qir_lines.append("")
        
        # Allocate qubits
        for qubit_name in self.qubit_map.values():
            qir_lines.append(f"%{qubit_name} = call %Qubit* @__quantum__rt__qubit_allocate()")
        
        qir_lines.append("")
        
        # Convert instructions
        for circuit_instruction in circuit.data:
            instruction = circuit_instruction.operation
            qargs = circuit_instruction.qubits
            cargs = circuit_instruction.clbits
            qir_inst = self._convert_instruction(instruction, qargs, cargs)
            if qir_inst:
                qir_lines.append(qir_inst)
        
        qir_lines.append("")
        
        # Release qubits
        for qubit_name in self.qubit_map.values():
            qir_lines.append(f"call void @__quantum__rt__qubit_release(%Qubit* %{qubit_name})")
        
        return "\n".join(qir_lines)
    
    def _convert_instruction(
        self,
        instruction: Instruction,
        qargs: List[Qubit],
        cargs: List[Clbit]
    ) -> Optional[str]:
        """Convert a single instruction to QIR."""
        name = instruction.name.lower()
        
        # Get qubit names
        qubit_names = [self.qubit_map[q] for q in qargs]
        
        # Single-qubit gates
        if name == 'h':
            return f"call void @__quantum__qis__h__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 'x':
            return f"call void @__quantum__qis__x__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 'y':
            return f"call void @__quantum__qis__y__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 'z':
            return f"call void @__quantum__qis__z__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 's':
            return f"call void @__quantum__qis__s__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 'sdg':
            return f"call void @__quantum__qis__s__adj(%Qubit* %{qubit_names[0]})"
        
        elif name == 't':
            return f"call void @__quantum__qis__t__body(%Qubit* %{qubit_names[0]})"
        
        elif name == 'tdg':
            return f"call void @__quantum__qis__t__adj(%Qubit* %{qubit_names[0]})"
        
        # Rotation gates
        elif name == 'rx':
            angle = instruction.params[0]
            return f"call void @__quantum__qis__rx__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        elif name == 'ry':
            angle = instruction.params[0]
            return f"call void @__quantum__qis__ry__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        elif name == 'rz':
            angle = instruction.params[0]
            return f"call void @__quantum__qis__rz__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        # Two-qubit gates
        elif name == 'cx' or name == 'cnot':
            return f"call void @__quantum__qis__cnot__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        elif name == 'cz':
            return f"call void @__quantum__qis__cz__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        elif name == 'swap':
            return f"call void @__quantum__qis__swap__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        # Measurement
        elif name == 'measure':
            clbit_name = self.clbit_map[cargs[0]]
            return f"%{clbit_name} = call %Result* @__quantum__qis__mz__body(%Qubit* %{qubit_names[0]})"
        
        # Barrier (comment in QIR)
        elif name == 'barrier':
            return f"; barrier on {', '.join(qubit_names)}"
        
        else:
            return f"; unsupported instruction: {name}"
    
    def convert_to_qvm(self, circuit: QuantumCircuit) -> Dict[str, Any]:
        """
        Convert Qiskit circuit directly to QVM graph format.
        
        Args:
            circuit: Qiskit QuantumCircuit
        
        Returns:
            QVM graph dictionary
        """
        # Build qubit mapping
        qubit_names = [f"q{i}" for i in range(circuit.num_qubits)]
        
        nodes = []
        
        # Allocate qubits
        nodes.append({
            "id": "alloc1",
            "op": "ALLOC_LQ",
            "args": {"n": circuit.num_qubits, "profile": "logical:Surface(d=7)"},
            "vqs": qubit_names
        })
        
        # Convert instructions
        inst_id = 0
        measurement_results = []
        
        for circuit_instruction in circuit.data:
            instruction = circuit_instruction.operation
            qargs = circuit_instruction.qubits
            cargs = circuit_instruction.clbits
            
            name = instruction.name.lower()
            qubits = [f"q{circuit.qubits.index(q)}" for q in qargs]
            
            if name == 'h':
                nodes.append({"id": f"h{inst_id}", "op": "APPLY_H", "vqs": qubits})
            
            elif name == 'x':
                nodes.append({"id": f"x{inst_id}", "op": "APPLY_X", "vqs": qubits})
            
            elif name == 'y':
                nodes.append({"id": f"y{inst_id}", "op": "APPLY_Y", "vqs": qubits})
            
            elif name == 'z':
                nodes.append({"id": f"z{inst_id}", "op": "APPLY_Z", "vqs": qubits})
            
            elif name == 's':
                nodes.append({"id": f"s{inst_id}", "op": "APPLY_S", "vqs": qubits})
            
            elif name == 'sdg':
                # S-dagger: apply S three times (S^3 = S†)
                nodes.append({"id": f"sdg{inst_id}_1", "op": "APPLY_S", "vqs": qubits})
                nodes.append({"id": f"sdg{inst_id}_2", "op": "APPLY_S", "vqs": qubits})
                nodes.append({"id": f"sdg{inst_id}_3", "op": "APPLY_S", "vqs": qubits})
            
            elif name == 't':
                nodes.append({"id": f"t{inst_id}", "op": "APPLY_T", "vqs": qubits})
            
            elif name == 'tdg':
                # T-dagger: apply T seven times (T^7 = T†)
                for i in range(7):
                    nodes.append({"id": f"tdg{inst_id}_{i}", "op": "APPLY_T", "vqs": qubits})
            
            elif name in ['cx', 'cnot']:
                nodes.append({"id": f"cx{inst_id}", "op": "APPLY_CNOT", "vqs": qubits})
            
            elif name == 'cz':
                nodes.append({"id": f"cz{inst_id}", "op": "APPLY_CZ", "vqs": qubits})
            
            elif name == 'swap':
                nodes.append({"id": f"swap{inst_id}", "op": "APPLY_SWAP", "vqs": qubits})
            
            elif name == 'barrier':
                # Skip barriers
                pass
            
            elif name == 'measure':
                result_name = f"m{circuit.qubits.index(qargs[0])}"
                measurement_results.append(result_name)
                nodes.append({
                    "id": f"m{inst_id}",
                    "op": "MEASURE_Z",
                    "vqs": qubits,
                    "produces": [result_name]
                })
            
            inst_id += 1
        
        return {
            "program": {"nodes": nodes},
            "resources": {
                "vqs": qubit_names,
                "events": measurement_results
            }
        }
