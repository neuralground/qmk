#!/usr/bin/env python3
"""
Performance benchmarks and baselines for QMK.

Establishes performance baselines for key operations.
"""

import unittest
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer.ir import QIRCircuit, QIRInstruction, InstructionType
from kernel.qir_bridge.optimizer.converters import IRToQVMConverter
from qvm.static_verifier import verify_qvm_graph
from kernel.security.capability_mediator import CapabilityMediator
from kernel.security.physical_qubit_allocator import PhysicalQubitAllocator


class TestPerformanceBaselines(unittest.TestCase):
    """Performance baseline tests."""
    
    def test_circuit_creation_performance(self):
        """Benchmark circuit creation."""
        start = time.time()
        
        for _ in range(100):
            circuit = QIRCircuit()
            q0 = circuit.add_qubit('q0')
            q1 = circuit.add_qubit('q1')
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
            circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        elapsed = time.time() - start
        per_circuit = elapsed / 100 * 1000  # ms per circuit
        
        print(f"\nCircuit creation: {per_circuit:.2f}ms per circuit")
        self.assertLess(per_circuit, 10, "Circuit creation should be < 10ms")
    
    def test_qvm_conversion_performance(self):
        """Benchmark QIR to QVM conversion."""
        # Create circuit
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        for _ in range(10):
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
            circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        converter = IRToQVMConverter()
        
        start = time.time()
        for _ in range(100):
            qvm = converter.convert(circuit)
        elapsed = time.time() - start
        per_conversion = elapsed / 100 * 1000  # ms
        
        print(f"\nQVM conversion: {per_conversion:.2f}ms per conversion")
        self.assertLess(per_conversion, 50, "QVM conversion should be < 50ms")
    
    def test_verification_performance(self):
        """Benchmark static verification."""
        # Create QVM graph
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(10)]
        
        for q in qubits:
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        converter = IRToQVMConverter()
        qvm = converter.convert(circuit)
        
        start = time.time()
        for _ in range(100):
            result = verify_qvm_graph(qvm)
        elapsed = time.time() - start
        per_verification = elapsed / 100 * 1000  # ms
        
        print(f"\nVerification: {per_verification:.2f}ms per verification")
        self.assertLess(per_verification, 20, "Verification should be < 20ms")
    
    def test_capability_check_performance(self):
        """Benchmark capability checking."""
        mediator = CapabilityMediator(secret_key=b'test_key')
        token = mediator.create_token(
            capabilities={'CAP_COMPUTE', 'CAP_MEASURE'},
            tenant_id='tenant1'
        )
        
        start = time.time()
        for _ in range(10000):
            result = mediator.check_capability(token, 'APPLY_H')
        elapsed = time.time() - start
        per_check = elapsed / 10000 * 1000  # ms
        
        print(f"\nCapability check: {per_check:.3f}ms per check")
        self.assertLess(per_check, 0.1, "Capability check should be < 0.1ms")
    
    def test_qubit_allocation_performance(self):
        """Benchmark qubit allocation."""
        allocator = PhysicalQubitAllocator(total_qubits=1000)
        
        start = time.time()
        for i in range(100):
            qubits = allocator.allocate(f'tenant{i}', count=10)
        elapsed = time.time() - start
        per_allocation = elapsed / 100 * 1000  # ms
        
        print(f"\nQubit allocation: {per_allocation:.2f}ms per allocation")
        self.assertLess(per_allocation, 5, "Qubit allocation should be < 5ms")
    
    def test_large_circuit_performance(self):
        """Benchmark large circuit handling."""
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(100)]
        
        start = time.time()
        
        # Add 1000 gates
        for i in range(1000):
            q = qubits[i % 100]
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        elapsed = time.time() - start
        print(f"\nLarge circuit (1000 gates): {elapsed*1000:.2f}ms")
        self.assertLess(elapsed, 1.0, "Large circuit creation should be < 1s")
    
    def test_verification_scaling(self):
        """Test verification performance scaling."""
        sizes = [10, 50, 100, 200]
        times = []
        
        for size in sizes:
            circuit = QIRCircuit()
            qubits = [circuit.add_qubit(f'q{i}') for i in range(size)]
            
            for q in qubits:
                circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
            
            converter = IRToQVMConverter()
            qvm = converter.convert(circuit)
            
            start = time.time()
            result = verify_qvm_graph(qvm)
            elapsed = time.time() - start
            times.append(elapsed * 1000)
        
        print(f"\nVerification scaling:")
        for size, t in zip(sizes, times):
            print(f"  {size} qubits: {t:.2f}ms")
        
        # Should scale roughly linearly
        self.assertLess(times[-1] / times[0], 30, "Verification should scale reasonably")


class TestMemoryBaselines(unittest.TestCase):
    """Memory usage baselines."""
    
    def test_circuit_memory_usage(self):
        """Test circuit memory footprint."""
        import sys
        
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(100)]
        
        for i in range(1000):
            q = qubits[i % 100]
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        size = sys.getsizeof(circuit)
        print(f"\nCircuit memory (100q, 1000g): {size/1024:.2f} KB")
        self.assertLess(size, 10_000_000, "Circuit should use < 10MB")
    
    def test_qvm_graph_memory_usage(self):
        """Test QVM graph memory footprint."""
        import sys
        import json
        
        circuit = QIRCircuit()
        qubits = [circuit.add_qubit(f'q{i}') for i in range(50)]
        
        for i in range(500):
            q = qubits[i % 50]
            circuit.add_instruction(QIRInstruction(InstructionType.H, [q]))
        
        converter = IRToQVMConverter()
        qvm = converter.convert(circuit)
        
        # Serialize to JSON to get realistic size
        json_str = json.dumps(qvm)
        size = len(json_str)
        
        print(f"\nQVM graph size (50q, 500g): {size/1024:.2f} KB")
        self.assertLess(size, 5_000_000, "QVM graph should be < 5MB")


class TestThroughputBaselines(unittest.TestCase):
    """Throughput baselines."""
    
    def test_operations_per_second(self):
        """Measure operations per second."""
        mediator = CapabilityMediator(secret_key=b'test_key')
        token = mediator.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant1'
        )
        
        operations = 0
        start = time.time()
        duration = 1.0  # 1 second
        
        while time.time() - start < duration:
            mediator.check_capability(token, 'APPLY_H')
            operations += 1
        
        ops_per_sec = operations / duration
        print(f"\nCapability checks: {ops_per_sec:.0f} ops/sec")
        self.assertGreater(ops_per_sec, 10000, "Should handle > 10k ops/sec")
    
    def test_verification_throughput(self):
        """Measure verification throughput."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        converter = IRToQVMConverter()
        qvm = converter.convert(circuit)
        
        verifications = 0
        start = time.time()
        duration = 1.0
        
        while time.time() - start < duration:
            verify_qvm_graph(qvm)
            verifications += 1
        
        ver_per_sec = verifications / duration
        print(f"\nVerifications: {ver_per_sec:.0f} per second")
        self.assertGreater(ver_per_sec, 100, "Should handle > 100 verifications/sec")


if __name__ == '__main__':
    unittest.main(verbosity=2)
