"""
Converters between QIR, IR, and QVM formats.

Enables optimization of circuits from various sources.
"""

from typing import Dict, Any
from .ir import QIRCircuit, QIRInstruction, QIRQubit, InstructionType

# QIR parser is in qir.parser module
try:
    from qir.parser.qir_parser import QIRFunction
except ImportError:
    # Fallback for development
    QIRFunction = None


class QIRToIRConverter:
    """Convert QIR function to optimization IR."""
    
    @staticmethod
    def convert(qir_function: QIRFunction) -> QIRCircuit:
        """
        Convert QIR function to IR circuit.
        
        Args:
            qir_function: Parsed QIR function
        
        Returns:
            QIRCircuit for optimization
        """
        circuit = QIRCircuit()
        
        # Map QIR instruction types to IR types
        type_map = {
            'H': InstructionType.H,
            'X': InstructionType.X,
            'Y': InstructionType.Y,
            'Z': InstructionType.Z,
            'S': InstructionType.S,
            'T': InstructionType.T,
            'CNOT': InstructionType.CNOT,
            'CZ': InstructionType.CZ,
            'RX': InstructionType.RX,
            'RY': InstructionType.RY,
            'RZ': InstructionType.RZ,
            'MEASURE': InstructionType.MEASURE,
        }
        
        # Create qubits
        for i in range(qir_function.qubit_count):
            circuit.add_qubit(f'q{i}')
        
        # Convert instructions
        for qir_inst in qir_function.instructions:
            if qir_inst.inst_type.value == 'qubit_alloc':
                # Already handled qubits
                continue
            elif qir_inst.inst_type.value == 'qubit_release':
                # Track but don't add instruction
                continue
            elif qir_inst.inst_type.value == 'gate':
                # Map gate operation
                gate_name = qir_inst.operation.upper()
                if gate_name in type_map:
                    inst_type = type_map[gate_name]
                    qubits = [circuit.get_qubit(q) for q in qir_inst.qubits]
                    
                    ir_inst = QIRInstruction(
                        inst_type=inst_type,
                        qubits=qubits,
                        params={f'param{i}': p for i, p in enumerate(qir_inst.parameters)}
                    )
                    circuit.add_instruction(ir_inst)
            elif qir_inst.inst_type.value == 'measure':
                qubits = [circuit.get_qubit(q) for q in qir_inst.qubits]
                ir_inst = QIRInstruction(
                    inst_type=InstructionType.MEASURE,
                    qubits=qubits,
                    result=qir_inst.result
                )
                circuit.add_instruction(ir_inst)
        
        return circuit


class IRToQVMConverter:
    """Convert optimization IR to QVM format."""
    
    @staticmethod
    def convert(circuit: QIRCircuit) -> Dict[str, Any]:
        """
        Convert IR circuit to QVM format.
        
        Args:
            circuit: Optimized circuit
        
        Returns:
            QVM graph dictionary
        """
        nodes = []
        
        # Add allocation node
        vqs = list(circuit.qubits.keys())
        nodes.append({
            'id': 'alloc',
            'op': 'ALLOC_LQ',
            'args': {'n': len(vqs), 'profile': 'logical:surface_code(d=3)'},
            'vqs': vqs,
            'caps': ['CAP_ALLOC']
        })
        
        # Convert instructions
        op_map = {
            InstructionType.H: 'APPLY_H',
            InstructionType.X: 'APPLY_X',
            InstructionType.Y: 'APPLY_Y',
            InstructionType.Z: 'APPLY_Z',
            InstructionType.S: 'APPLY_S',
            InstructionType.T: 'APPLY_T',
            InstructionType.CNOT: 'APPLY_CNOT',
            InstructionType.CZ: 'APPLY_CZ',
            InstructionType.MEASURE: 'MEASURE_Z',
        }
        
        for i, inst in enumerate(circuit.instructions):
            if inst.inst_type in op_map:
                node = {
                    'id': f'n{i}',
                    'op': op_map[inst.inst_type],
                    'vqs': [q.id for q in inst.qubits]
                }
                
                if inst.result:
                    node['produces'] = [inst.result]
                
                if inst.params:
                    node['args'] = inst.params
                
                nodes.append(node)
        
        # Add deallocation node
        nodes.append({
            'id': 'free',
            'op': 'FREE_LQ',
            'vqs': vqs
        })
        
        # Build QVM graph
        return {
            'version': '0.1',
            'program': {'nodes': nodes},
            'resources': {
                'vqs': vqs,
                'chs': [],
                'events': list(circuit.results)
            },
            'caps': ['CAP_ALLOC']
        }


class QVMToIRConverter:
    """Convert QVM format to optimization IR."""
    
    @staticmethod
    def convert(qvm_graph: Dict[str, Any]) -> QIRCircuit:
        """
        Convert QVM graph to IR circuit.
        
        Args:
            qvm_graph: QVM graph dictionary
        
        Returns:
            QIRCircuit for optimization
        """
        circuit = QIRCircuit()
        
        # Get nodes
        if 'program' in qvm_graph:
            nodes = qvm_graph['program'].get('nodes', [])
        else:
            nodes = qvm_graph.get('nodes', [])
        
        # Create qubits from resources
        resources = qvm_graph.get('resources', {})
        for vq in resources.get('vqs', []):
            circuit.add_qubit(vq)
        
        # Map QVM ops to IR types
        op_map = {
            'APPLY_H': InstructionType.H,
            'APPLY_X': InstructionType.X,
            'APPLY_Y': InstructionType.Y,
            'APPLY_Z': InstructionType.Z,
            'APPLY_S': InstructionType.S,
            'APPLY_T': InstructionType.T,
            'APPLY_CNOT': InstructionType.CNOT,
            'APPLY_CZ': InstructionType.CZ,
            'MEASURE_Z': InstructionType.MEASURE,
        }
        
        # Convert nodes
        for node in nodes:
            op = node.get('op')
            
            if op in ['ALLOC_LQ', 'FREE_LQ']:
                continue  # Skip allocation/deallocation
            
            if op in op_map:
                vqs = node.get('vqs', [])
                qubits = [circuit.get_qubit(vq) for vq in vqs]
                
                inst = QIRInstruction(
                    inst_type=op_map[op],
                    qubits=qubits,
                    params=node.get('args', {}),
                    result=node.get('produces', [None])[0] if node.get('produces') else None
                )
                circuit.add_instruction(inst)
        
        return circuit
