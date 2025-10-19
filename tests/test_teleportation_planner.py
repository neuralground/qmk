"""
Unit tests for Teleportation Planner
"""

import unittest
from kernel.jit.teleportation_planner import TeleportationPlanner


class TestTeleportationPlanner(unittest.TestCase):
    """Test teleportation planning."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.planner = TeleportationPlanner()
    
    def test_create_plan_with_non_clifford_gates(self):
        """Test creating plan with non-Clifford gates."""
        nodes = [
            {"node_id": "n1", "op": "H", "qubits": ["q0"]},
            {"node_id": "n2", "op": "T", "qubits": ["q0"]},
            {"node_id": "n3", "op": "RZ", "qubits": ["q1"], "angle": 0.5},
            {"node_id": "n4", "op": "CNOT", "qubits": ["q0", "q1"]}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        self.assertEqual(len(plan.sites), 2)  # T and RZ
        self.assertIn("T_state", plan.magic_state_requirements)
        self.assertIn("rotation_state", plan.magic_state_requirements)
    
    def test_create_plan_clifford_only(self):
        """Test creating plan with only Clifford gates."""
        nodes = [
            {"node_id": "n1", "op": "H", "qubits": ["q0"]},
            {"node_id": "n2", "op": "CNOT", "qubits": ["q0", "q1"]},
            {"node_id": "n3", "op": "S", "qubits": ["q1"]}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        self.assertEqual(len(plan.sites), 0)
        self.assertEqual(len(plan.magic_state_requirements), 0)
    
    def test_magic_state_requirements(self):
        """Test magic state requirement calculation."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "T", "qubits": ["q1"]},
            {"node_id": "n3", "op": "T_DAG", "qubits": ["q2"]}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        self.assertEqual(plan.magic_state_requirements["T_state"], 3)
    
    def test_optimize_plan_minimize_cost(self):
        """Test optimizing plan to minimize cost."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "RZ", "qubits": ["q1"], "angle": 0.5}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        optimized = self.planner.optimize_plan(plan.plan_id, "minimize_cost")
        
        self.assertIsNotNone(optimized)
        self.assertEqual(len(optimized.sites), 2)
    
    def test_estimate_magic_state_throughput(self):
        """Test estimating magic state throughput."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "T", "qubits": ["q1"]}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        throughput = self.planner.estimate_magic_state_throughput(
            plan,
            factory_throughput={"T_state": 100.0, "rotation_state": 50.0}
        )
        
        self.assertIn("requirements", throughput)
        self.assertIn("production_times", throughput)
        self.assertIn("total_time", throughput)
        self.assertGreater(throughput["total_time"], 0)
    
    def test_merge_plans(self):
        """Test merging multiple plans."""
        nodes1 = [{"node_id": "n1", "op": "T", "qubits": ["q0"]}]
        nodes2 = [{"node_id": "n2", "op": "RZ", "qubits": ["q1"], "angle": 0.5}]
        
        plan1 = self.planner.create_plan("graph_1", nodes1)
        plan2 = self.planner.create_plan("graph_2", nodes2)
        
        merged = self.planner.merge_plans([plan1.plan_id, plan2.plan_id])
        
        self.assertEqual(len(merged.sites), 2)
        self.assertIn("T_state", merged.magic_state_requirements)
        self.assertIn("rotation_state", merged.magic_state_requirements)
    
    def test_get_plan_statistics(self):
        """Test getting plan statistics."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "T", "qubits": ["q1"]},
            {"node_id": "n3", "op": "RZ", "qubits": ["q2"], "angle": 0.5}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        stats = self.planner.get_plan_statistics(plan.plan_id)
        
        self.assertEqual(stats["total_sites"], 3)
        self.assertGreater(stats["total_cost"], 0)
        self.assertIn("by_gate_type", stats)
    
    def test_execution_order(self):
        """Test execution order generation."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "T", "qubits": ["q1"]}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        self.assertEqual(len(plan.execution_order), 2)
        self.assertTrue(all(isinstance(sid, str) for sid in plan.execution_order))
    
    def test_cost_calculation(self):
        """Test cost calculation for different gates."""
        nodes = [
            {"node_id": "n1", "op": "T", "qubits": ["q0"]},
            {"node_id": "n2", "op": "RZ", "qubits": ["q1"], "angle": 0.5}
        ]
        
        plan = self.planner.create_plan("graph_1", nodes)
        
        # T gates should have lower cost than rotation gates
        t_site = next(s for s in plan.sites if s.gate_type == "T")
        rz_site = next(s for s in plan.sites if s.gate_type == "RZ")
        
        self.assertLess(t_site.cost, rz_site.cost)


if __name__ == "__main__":
    unittest.main()
