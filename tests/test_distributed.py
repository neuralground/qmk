"""
Unit tests for Distributed Execution
"""

import unittest
import time
from kernel.distributed import (
    GraphPartitioner, NodeManager, DistributedExecutor,
    LoadBalancer, NodeCapabilities, BalancingStrategy, WorkloadMetrics
)


# Sample graph for testing
SAMPLE_GRAPH = {
    "name": "test_circuit",
    "nodes": [
        {"node_id": "n0", "op": "ALLOC_LQ", "qubits": ["q0"]},
        {"node_id": "n1", "op": "ALLOC_LQ", "qubits": ["q1"]},
        {"node_id": "n2", "op": "H", "qubits": ["q0"]},
        {"node_id": "n3", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n4", "op": "H", "qubits": ["q1"]},
        {"node_id": "n5", "op": "MEASURE_Z", "qubits": ["q0"]},
        {"node_id": "n6", "op": "MEASURE_Z", "qubits": ["q1"]},
    ]
}


class TestGraphPartitioner(unittest.TestCase):
    """Test graph partitioner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.partitioner = GraphPartitioner(num_partitions=2)
    
    def test_initialization(self):
        """Test partitioner initialization."""
        self.assertEqual(self.partitioner.num_partitions, 2)
    
    def test_partition_by_qubits(self):
        """Test qubit-based partitioning."""
        plan = self.partitioner.partition_by_qubits(SAMPLE_GRAPH)
        
        self.assertGreater(len(plan.partitions), 0)
        self.assertIsNotNone(plan.plan_id)
    
    def test_partition_by_time(self):
        """Test time-based partitioning."""
        plan = self.partitioner.partition_by_time(SAMPLE_GRAPH)
        
        self.assertGreater(len(plan.partitions), 0)
        self.assertGreater(plan.parallelism, 0)
    
    def test_partition_balanced(self):
        """Test balanced partitioning."""
        plan = self.partitioner.partition_balanced(SAMPLE_GRAPH)
        
        self.assertGreater(len(plan.partitions), 0)
        
        # Check balance
        node_counts = [len(p.nodes) for p in plan.partitions]
        self.assertLessEqual(max(node_counts) - min(node_counts), 2)
    
    def test_get_partition_stats(self):
        """Test getting partition statistics."""
        plan = self.partitioner.partition_balanced(SAMPLE_GRAPH)
        stats = self.partitioner.get_partition_stats(plan)
        
        self.assertIn("num_partitions", stats)
        self.assertIn("total_nodes", stats)
        self.assertIn("parallelism", stats)


class TestNodeManager(unittest.TestCase):
    """Test node manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = NodeManager()
    
    def test_register_node(self):
        """Test node registration."""
        caps = NodeCapabilities(
            max_qubits=20,
            max_memory_mb=8192,
            cpu_cores=8
        )
        
        node = self.manager.register_node(
            "node1",
            "localhost",
            8000,
            caps
        )
        
        self.assertEqual(node.node_id, "node1")
        self.assertIn("node1", self.manager.nodes)
    
    def test_unregister_node(self):
        """Test node unregistration."""
        caps = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        self.manager.register_node("node1", "localhost", 8000, caps)
        
        self.manager.unregister_node("node1")
        
        self.assertNotIn("node1", self.manager.nodes)
    
    def test_heartbeat(self):
        """Test node heartbeat."""
        caps = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        self.manager.register_node("node1", "localhost", 8000, caps)
        
        initial_time = self.manager.nodes["node1"].last_heartbeat
        time.sleep(0.01)
        
        self.manager.heartbeat("node1", 0.5)
        
        self.assertGreater(
            self.manager.nodes["node1"].last_heartbeat,
            initial_time
        )
        self.assertEqual(self.manager.nodes["node1"].current_load, 0.5)
    
    def test_get_available_nodes(self):
        """Test getting available nodes."""
        caps1 = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        caps2 = NodeCapabilities(max_qubits=20, max_memory_mb=8192, cpu_cores=8)
        
        self.manager.register_node("node1", "localhost", 8000, caps1)
        self.manager.register_node("node2", "localhost", 8001, caps2)
        
        # Get all available
        available = self.manager.get_available_nodes()
        self.assertEqual(len(available), 2)
        
        # Get with requirements
        available = self.manager.get_available_nodes(min_qubits=15)
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].node_id, "node2")
    
    def test_select_best_node(self):
        """Test selecting best node."""
        caps1 = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        caps2 = NodeCapabilities(max_qubits=20, max_memory_mb=8192, cpu_cores=8)
        
        self.manager.register_node("node1", "localhost", 8000, caps1)
        self.manager.register_node("node2", "localhost", 8001, caps2)
        
        # Set different loads
        self.manager.heartbeat("node1", 0.8)
        self.manager.heartbeat("node2", 0.3)
        
        best = self.manager.select_best_node()
        
        self.assertEqual(best.node_id, "node2")  # Lower load
    
    def test_get_cluster_stats(self):
        """Test getting cluster statistics."""
        caps = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        self.manager.register_node("node1", "localhost", 8000, caps)
        self.manager.register_node("node2", "localhost", 8001, caps)
        
        stats = self.manager.get_cluster_stats()
        
        self.assertEqual(stats["total_nodes"], 2)
        self.assertEqual(stats["online_nodes"], 2)


class TestDistributedExecutor(unittest.TestCase):
    """Test distributed executor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = NodeManager()
        
        # Register nodes
        for i in range(3):
            caps = NodeCapabilities(
                max_qubits=20,
                max_memory_mb=8192,
                cpu_cores=8
            )
            self.manager.register_node(
                f"node{i}",
                "localhost",
                8000 + i,
                caps
            )
        
        self.executor = DistributedExecutor(self.manager, num_partitions=3)
    
    def test_initialization(self):
        """Test executor initialization."""
        self.assertIsNotNone(self.executor.node_manager)
        self.assertIsNotNone(self.executor.partitioner)
    
    def test_execute_distributed(self):
        """Test distributed execution."""
        result = self.executor.execute_distributed(
            "job1",
            SAMPLE_GRAPH,
            partition_strategy="balanced"
        )
        
        self.assertEqual(result["job_id"], "job1")
        self.assertEqual(result["status"], "completed")
        self.assertGreater(result["num_partitions"], 0)
    
    def test_get_execution_status(self):
        """Test getting execution status."""
        # Execute and then check status
        self.executor.execute_distributed("job2", SAMPLE_GRAPH)
        
        status = self.executor.get_execution_status("job2")
        
        self.assertIsNotNone(status)
        self.assertEqual(status["job_id"], "job2")
    
    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        self.executor.execute_distributed("job3", SAMPLE_GRAPH)
        
        stats = self.executor.get_execution_stats()
        
        self.assertGreaterEqual(stats["total_executions"], 1)


class TestLoadBalancer(unittest.TestCase):
    """Test load balancer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = NodeManager()
        
        # Register nodes with different capabilities
        caps1 = NodeCapabilities(max_qubits=10, max_memory_mb=4096, cpu_cores=4)
        caps2 = NodeCapabilities(max_qubits=20, max_memory_mb=8192, cpu_cores=8)
        
        self.manager.register_node("node1", "localhost", 8000, caps1)
        self.manager.register_node("node2", "localhost", 8001, caps2)
        
        self.balancer = LoadBalancer(self.manager, BalancingStrategy.LEAST_LOADED)
    
    def test_initialization(self):
        """Test balancer initialization."""
        self.assertEqual(self.balancer.strategy, BalancingStrategy.LEAST_LOADED)
    
    def test_select_node_least_loaded(self):
        """Test least-loaded selection."""
        # Set different loads
        self.manager.heartbeat("node1", 0.8)
        self.manager.heartbeat("node2", 0.3)
        
        workload = WorkloadMetrics(estimated_qubits=5)
        node = self.balancer.select_node(workload)
        
        self.assertEqual(node.node_id, "node2")
    
    def test_select_node_round_robin(self):
        """Test round-robin selection."""
        balancer = LoadBalancer(self.manager, BalancingStrategy.ROUND_ROBIN)
        
        workload = WorkloadMetrics(estimated_qubits=5)
        
        node1 = balancer.select_node(workload)
        node2 = balancer.select_node(workload)
        
        # Should alternate
        self.assertNotEqual(node1.node_id, node2.node_id)
    
    def test_balance_workload(self):
        """Test balancing multiple workloads."""
        workloads = [
            WorkloadMetrics(estimated_qubits=5),
            WorkloadMetrics(estimated_qubits=10),
            WorkloadMetrics(estimated_qubits=15)
        ]
        
        assignments = self.balancer.balance_workload(workloads)
        
        self.assertGreater(len(assignments), 0)
        self.assertEqual(sum(len(v) for v in assignments.values()), 3)
    
    def test_get_balance_stats(self):
        """Test getting balance statistics."""
        stats = self.balancer.get_balance_stats()
        
        self.assertIn("strategy", stats)
        self.assertIn("average_load", stats)
        self.assertIn("balance_quality", stats)


if __name__ == "__main__":
    unittest.main()
