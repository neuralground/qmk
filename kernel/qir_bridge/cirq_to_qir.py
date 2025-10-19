"""
Cirq to QIR Converter

Converts Cirq circuits to QIR (Quantum Intermediate Representation).
"""

from typing import Dict, List, Any, Optional
import cirq


class CirqToQIRConverter:
    """
    Converts Cirq circuits to QIR format.
    
    Supports:
    - Single-qubit gates (H, X, Y, Z, S, T, Rx, Ry, Rz)
    - Two-qubit gates (CNOT, CZ, SWAP)
    - Measurements
    """
    
    def __init__(self):
        self.qubit_map: Dict[cirq.Qid, str] = {}
        self.instruction_count = 0
    
    def convert(self, circuit: cirq.Circuit) -> str:
        """
        Convert Cirq circuit to QIR string.
        
        Args:
            circuit: Cirq Circuit
        
        Returns:
            QIR program as string
        """
        # Build qubit mapping
        qubits = sorted(circuit.all_qubits())
        for i, qubit in enumerate(qubits):
            self.qubit_map[qubit] = f"q{i}"
        
        # Generate QIR
        qir_lines = []
        qir_lines.append("; QIR generated from Cirq")
        qir_lines.append(f"; Qubits: {len(qubits)}")
        qir_lines.append("")
        
        # Allocate qubits
        for qubit_name in self.qubit_map.values():
            qir_lines.append(f"%{qubit_name} = call %Qubit* @__quantum__rt__qubit_allocate()")
        
        qir_lines.append("")
        
        # Convert operations
        for moment in circuit:
            for operation in moment:
                qir_inst = self._convert_operation(operation)
                if qir_inst:
                    qir_lines.append(qir_inst)
        
        qir_lines.append("")
        
        # Release qubits
        for qubit_name in self.qubit_map.values():
            qir_lines.append(f"call void @__quantum__rt__qubit_release(%Qubit* %{qubit_name})")
        
        return "\n".join(qir_lines)
    
    def _convert_operation(self, operation: cirq.Operation) -> Optional[str]:
        """Convert a single operation to QIR."""
        gate = operation.gate
        qubits = operation.qubits
        qubit_names = [self.qubit_map[q] for q in qubits]
        
        # Single-qubit gates
        if isinstance(gate, cirq.HPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__h__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.XPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__x__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.YPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__y__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__z__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 0.5:
            return f"call void @__quantum__qis__s__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.ZPowGate) and gate.exponent == -0.5:
            return f"call void @__quantum__qis__s__adj(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 0.25:
            return f"call void @__quantum__qis__t__body(%Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.ZPowGate) and gate.exponent == -0.25:
            return f"call void @__quantum__qis__t__adj(%Qubit* %{qubit_names[0]})"
        
        # Rotation gates
        elif isinstance(gate, cirq.Rx):
            angle = gate.rads
            return f"call void @__quantum__qis__rx__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.Ry):
            angle = gate.rads
            return f"call void @__quantum__qis__ry__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        elif isinstance(gate, cirq.Rz):
            angle = gate.rads
            return f"call void @__quantum__qis__rz__body(double {angle}, %Qubit* %{qubit_names[0]})"
        
        # Two-qubit gates
        elif isinstance(gate, cirq.CNotPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__cnot__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        elif isinstance(gate, cirq.CZPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__cz__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        elif isinstance(gate, cirq.SwapPowGate) and gate.exponent == 1:
            return f"call void @__quantum__qis__swap__body(%Qubit* %{qubit_names[0]}, %Qubit* %{qubit_names[1]})"
        
        # Measurement
        elif isinstance(gate, cirq.MeasurementGate):
            return f"%m{self.instruction_count} = call %Result* @__quantum__qis__mz__body(%Qubit* %{qubit_names[0]})"
        
        else:
            return f"; unsupported gate: {gate}"
    
    def convert_to_qvm(self, circuit: cirq.Circuit) -> Dict[str, Any]:
        """
        Convert Cirq circuit directly to QVM graph format.
        
        Args:
            circuit: Cirq Circuit
        
        Returns:
            QVM graph dictionary
        """
        # Build qubit mapping
        qubits = sorted(circuit.all_qubits())
        qubit_names = [f"q{i}" for i in range(len(qubits))]
        qubit_map = {q: name for q, name in zip(qubits, qubit_names)}
        
        nodes = []
        
        # Allocate qubits
        nodes.append({
            "id": "alloc1",
            "op": "ALLOC_LQ",
            "args": {"n": len(qubits), "profile": "logical:Surface(d=7)"},
            "vqs": qubit_names
        })
        
        # Convert operations
        inst_id = 0
        measurement_results = []
        
        for moment in circuit:
            for operation in moment:
                gate = operation.gate
                qubits_op = [qubit_map[q] for q in operation.qubits]
                
                if isinstance(gate, cirq.HPowGate) and gate.exponent == 1:
                    nodes.append({"id": f"h{inst_id}", "op": "APPLY_H", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.XPowGate) and gate.exponent == 1:
                    nodes.append({"id": f"x{inst_id}", "op": "APPLY_X", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.YPowGate) and gate.exponent == 1:
                    nodes.append({"id": f"y{inst_id}", "op": "APPLY_Y", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 1:
                    nodes.append({"id": f"z{inst_id}", "op": "APPLY_Z", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 0.5:
                    nodes.append({"id": f"s{inst_id}", "op": "APPLY_S", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.ZPowGate) and gate.exponent == 0.25:
                    nodes.append({"id": f"t{inst_id}", "op": "APPLY_T", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.CNotPowGate) and gate.exponent == 1:
                    nodes.append({"id": f"cx{inst_id}", "op": "APPLY_CNOT", "vqs": qubits_op})
                
                elif isinstance(gate, cirq.MeasurementGate):
                    for i, q in enumerate(qubits_op):
                        result_name = f"m{int(q[1:])}"
                        measurement_results.append(result_name)
                        nodes.append({
                            "id": f"m{inst_id}_{i}",
                            "op": "MEASURE_Z",
                            "vqs": [q],
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
