"""
Unit tests for QIR Bridge
"""

import unittest
from kernel.qir_bridge import (
    QIRParser, QVMGraphGenerator, ResourceEstimator
)
from kernel.simulator.qec_profiles import surface_code, qldpc_code


# Sample QIR programs for testing
SIMPLE_QIR = """
define void @main() {
  %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
  call void @__quantum__qis__h__body(%Qubit* %q0)
  call void @__quantum__qis__x__body(%Qubit* %q0)
  %result = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
  call void @__quantum__rt__qubit_release(%Qubit* %q0)
  ret void
}
"""

BELL_STATE_QIR = """
define void @bell_state() {
  %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
  %q1 = call %Qubit* @__quantum__rt__qubit_allocate()
  call void @__quantum__qis__h__body(%Qubit* %q0)
  call void @__quantum__qis__cnot__body(%Qubit* %q0, %Qubit* %q1)
  %r0 = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
  %r1 = call i1 @__quantum__qis__mz__body(%Qubit* %q1)
  call void @__quantum__rt__qubit_release(%Qubit* %q0)
  call void @__quantum__rt__qubit_release(%Qubit* %q1)
  ret void
}
"""

T_GATE_QIR = """
define void @t_gate_circuit() {
  %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
  call void @__quantum__qis__h__body(%Qubit* %q0)
  call void @__quantum__qis__t__body(%Qubit* %q0)
  call void @__quantum__qis__t__body(%Qubit* %q0)
  call void @__quantum__qis__h__body(%Qubit* %q0)
  %result = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
  call void @__quantum__rt__qubit_release(%Qubit* %q0)
  ret void
}
"""


class TestQIRParser(unittest.TestCase):
    """Test QIR parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = QIRParser()
    
    def test_parse_simple_circuit(self):
        """Test parsing simple circuit."""
        functions = self.parser.parse(SIMPLE_QIR)
        
        self.assertIn("main", functions)
        func = functions["main"]
        self.assertEqual(func.qubit_count, 1)
        self.assertGreater(len(func.instructions), 0)
    
    def test_parse_bell_state(self):
        """Test parsing Bell state circuit."""
        functions = self.parser.parse(BELL_STATE_QIR)
        
        self.assertIn("bell_state", functions)
        func = functions["bell_state"]
        self.assertEqual(func.qubit_count, 2)
    
    def test_parse_t_gates(self):
        """Test parsing T gates."""
        functions = self.parser.parse(T_GATE_QIR)
        
        func = functions["t_gate_circuit"]
        
        # Count T gates
        t_count = sum(
            1 for inst in func.instructions
            if inst.operation == "T"
        )
        self.assertEqual(t_count, 2)
    
    def test_get_statistics(self):
        """Test getting parsing statistics."""
        self.parser.parse(SIMPLE_QIR)
        stats = self.parser.get_statistics()
        
        self.assertIn("total_functions", stats)
        self.assertIn("total_instructions", stats)
        self.assertIn("gate_counts", stats)


class TestQVMGraphGenerator(unittest.TestCase):
    """Test QVM graph generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = QIRParser()
        self.generator = QVMGraphGenerator()
    
    def test_generate_simple_graph(self):
        """Test generating simple QVM graph."""
        functions = self.parser.parse(SIMPLE_QIR)
        func = functions["main"]
        
        graph = self.generator.generate(func)
        
        self.assertIn("nodes", graph)
        self.assertIn("metadata", graph)
        self.assertGreater(len(graph["nodes"]), 0)
    
    def test_generate_bell_state_graph(self):
        """Test generating Bell state graph."""
        functions = self.parser.parse(BELL_STATE_QIR)
        func = functions["bell_state"]
        
        graph = self.generator.generate(func)
        
        # Should have ALLOC, H, CNOT, MEASURE, FREE nodes
        ops = [node["op"] for node in graph["nodes"]]
        self.assertIn("ALLOC_LQ", ops)
        self.assertIn("H", ops)
        self.assertIn("CNOT", ops)
        self.assertIn("MEASURE_Z", ops)
        self.assertIn("FREE_LQ", ops)
    
    def test_teleportation_insertion(self):
        """Test teleportation insertion for T gates."""
        generator = QVMGraphGenerator(insert_teleportation=True)
        functions = self.parser.parse(T_GATE_QIR)
        func = functions["t_gate_circuit"]
        
        graph = generator.generate(func)
        
        # Check that T gates have teleportation marker
        t_nodes = [
            node for node in graph["nodes"]
            if node["op"] == "T"
        ]
        
        for node in t_nodes:
            if "params" in node:
                self.assertTrue(node["params"].get("teleported", False))
    
    def test_generate_multiple(self):
        """Test generating multiple graphs."""
        qir_code = SIMPLE_QIR + "\n" + BELL_STATE_QIR
        functions = self.parser.parse(qir_code)
        
        graphs = self.generator.generate_multiple(functions)
        
        self.assertEqual(len(graphs), 2)
        self.assertIn("main", graphs)
        self.assertIn("bell_state", graphs)


class TestResourceEstimator(unittest.TestCase):
    """Test resource estimator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = QIRParser()
        self.estimator = ResourceEstimator()
    
    def test_estimate_simple_circuit(self):
        """Test estimating simple circuit."""
        functions = self.parser.parse(SIMPLE_QIR)
        func = functions["main"]
        
        estimate = self.estimator.estimate(func)
        
        self.assertEqual(estimate.logical_qubits, 1)
        self.assertGreater(estimate.physical_qubits, 0)
        self.assertGreater(estimate.gate_count, 0)
    
    def test_estimate_bell_state(self):
        """Test estimating Bell state."""
        functions = self.parser.parse(BELL_STATE_QIR)
        func = functions["bell_state"]
        
        estimate = self.estimator.estimate(func)
        
        self.assertEqual(estimate.logical_qubits, 2)
        self.assertIn("H", estimate.gate_breakdown)
        self.assertIn("CNOT", estimate.gate_breakdown)
    
    def test_estimate_t_count(self):
        """Test T-gate counting."""
        functions = self.parser.parse(T_GATE_QIR)
        func = functions["t_gate_circuit"]
        
        estimate = self.estimator.estimate(func)
        
        self.assertEqual(estimate.t_count, 2)
    
    def test_compare_profiles(self):
        """Test comparing QEC profiles."""
        functions = self.parser.parse(SIMPLE_QIR)
        func = functions["main"]
        
        profiles = [
            surface_code(9),
            qldpc_code(9, rate=0.1)
        ]
        
        estimates = self.estimator.compare_profiles(func, profiles)
        
        self.assertEqual(len(estimates), 2)
        self.assertIn("surface_code", estimates)
        self.assertIn("QLDPC", estimates)
    
    def test_magic_state_requirements(self):
        """Test magic state requirement estimation."""
        functions = self.parser.parse(T_GATE_QIR)
        func = functions["t_gate_circuit"]
        
        requirements = self.estimator.estimate_magic_state_requirements(func)
        
        self.assertEqual(requirements["t_states_needed"], 2)
        self.assertGreater(requirements["total_production_time_s"], 0)


if __name__ == "__main__":
    unittest.main()
