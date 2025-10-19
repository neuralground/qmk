"""
Distributed Execution Demonstration

Shows how to execute quantum programs across multiple compute nodes:
1. Graph partitioning strategies
2. Node management and clustering
3. Distributed execution
4. Load balancing
5. Performance analysis
"""

from kernel.distributed import (
    GraphPartitioner, NodeManager, DistributedExecutor,
    LoadBalancer, NodeCapabilities, BalancingStrategy, WorkloadMetrics
)


# Sample quantum circuit
BELL_STATE_GRAPH = {
    "name": "bell_state",
    "nodes": [
        {"node_id": "n0", "op": "ALLOC_LQ", "qubits": ["q0"]},
        {"node_id": "n1", "op": "ALLOC_LQ", "qubits": ["q1"]},
        {"node_id": "n2", "op": "H", "qubits": ["q0"]},
        {"node_id": "n3", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n4", "op": "MEASURE_Z", "qubits": ["q0"]},
        {"node_id": "n5", "op": "MEASURE_Z", "qubits": ["q1"]},
    ]
}

# Larger circuit for better demonstration
LARGE_CIRCUIT_GRAPH = {
    "name": "large_circuit",
    "nodes": [
        {"node_id": f"alloc_{i}", "op": "ALLOC_LQ", "qubits": [f"q{i}"]}
        for i in range(10)
    ] + [
        {"node_id": f"h_{i}", "op": "H", "qubits": [f"q{i}"]}
        for i in range(10)
    ] + [
        {"node_id": f"cnot_{i}", "op": "CNOT", "qubits": [f"q{i}", f"q{(i+1)%10}"]}
        for i in range(10)
    ] + [
        {"node_id": f"measure_{i}", "op": "MEASURE_Z", "qubits": [f"q{i}"]}
        for i in range(10)
    ]
}


def demo_graph_partitioning():
    """Demonstrate graph partitioning strategies."""
    print("=" * 70)
    print("1. GRAPH PARTITIONING STRATEGIES")
    print("=" * 70)
    
    partitioner = GraphPartitioner(num_partitions=4)
    
    print(f"\n📊 Partitioning large circuit ({len(LARGE_CIRCUIT_GRAPH['nodes'])} nodes)...")
    
    # Try different strategies
    strategies = {
        "Qubit-based": partitioner.partition_by_qubits,
        "Time-based": partitioner.partition_by_time,
        "Load-balanced": partitioner.partition_balanced
    }
    
    for strategy_name, strategy_func in strategies.items():
        print(f"\n🔹 {strategy_name} Partitioning:")
        plan = strategy_func(LARGE_CIRCUIT_GRAPH)
        stats = partitioner.get_partition_stats(plan)
        
        print(f"  Partitions: {stats['num_partitions']}")
        print(f"  Avg nodes/partition: {stats['avg_nodes_per_partition']:.1f}")
        print(f"  Parallelism: {stats['parallelism']}x")
        print(f"  Communication cost: {stats['communication_cost']:.3f}s")
        print(f"  Estimated speedup: {stats['estimated_speedup']:.2f}x")


def demo_node_management():
    """Demonstrate node management."""
    print("\n" + "=" * 70)
    print("2. NODE MANAGEMENT & CLUSTERING")
    print("=" * 70)
    
    manager = NodeManager()
    
    print(f"\n🖥️  Registering compute nodes...")
    
    # Register different types of nodes
    nodes_config = [
        ("node1", "10.0.0.1", 8000, NodeCapabilities(20, 8192, 8, has_gpu=False)),
        ("node2", "10.0.0.2", 8000, NodeCapabilities(50, 16384, 16, has_gpu=True)),
        ("node3", "10.0.0.3", 8000, NodeCapabilities(20, 8192, 8, has_gpu=False)),
        ("node4", "10.0.0.4", 8000, NodeCapabilities(100, 32768, 32, has_gpu=True)),
    ]
    
    for node_id, hostname, port, caps in nodes_config:
        manager.register_node(node_id, hostname, port, caps)
        print(f"  ✓ {node_id}: {caps.max_qubits} qubits, {caps.max_memory_mb}MB"
              f"{' (GPU)' if caps.has_gpu else ''}")
    
    # Simulate heartbeats with different loads
    manager.heartbeat("node1", 0.3)
    manager.heartbeat("node2", 0.7)
    manager.heartbeat("node3", 0.2)
    manager.heartbeat("node4", 0.9)
    
    print(f"\n📊 Cluster Statistics:")
    stats = manager.get_cluster_stats()
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Online nodes: {stats['online_nodes']}")
    print(f"  Total qubits: {stats['total_qubits']}")
    print(f"  Average load: {stats['average_load']:.1%}")
    
    print(f"\n🔍 Node Selection:")
    best = manager.select_best_node({"qubits": 30, "memory_mb": 10000})
    if best:
        print(f"  Best node for 30 qubits: {best.node_id}")
        print(f"    Load: {best.current_load:.1%}")
        print(f"    Capacity: {best.capabilities.max_qubits} qubits")


def demo_distributed_execution():
    """Demonstrate distributed execution."""
    print("\n" + "=" * 70)
    print("3. DISTRIBUTED EXECUTION")
    print("=" * 70)
    
    # Setup cluster
    manager = NodeManager()
    for i in range(4):
        caps = NodeCapabilities(
            max_qubits=20,
            max_memory_mb=8192,
            cpu_cores=8
        )
        manager.register_node(f"node{i}", f"10.0.0.{i+1}", 8000, caps)
    
    # Create executor
    executor = DistributedExecutor(manager, num_partitions=4)
    
    print(f"\n🚀 Executing circuit across {len(manager.nodes)} nodes...")
    
    # Execute with different strategies
    strategies = ["balanced", "qubit", "time"]
    
    for strategy in strategies:
        print(f"\n  Strategy: {strategy}")
        result = executor.execute_distributed(
            f"job_{strategy}",
            LARGE_CIRCUIT_GRAPH,
            partition_strategy=strategy
        )
        
        print(f"    Status: {result['status']}")
        print(f"    Partitions: {result['num_partitions']}")
        print(f"    Parallelism: {result['parallelism']}x")
        print(f"    Execution time: {result['execution_time']:.3f}s")
        print(f"    Communication cost: {result['communication_cost']:.3f}s")
    
    # Get execution stats
    print(f"\n📈 Execution Statistics:")
    stats = executor.get_execution_stats()
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Completed: {stats['completed_executions']}")


def demo_load_balancing():
    """Demonstrate load balancing."""
    print("\n" + "=" * 70)
    print("4. LOAD BALANCING")
    print("=" * 70)
    
    # Setup cluster with varied capabilities
    manager = NodeManager()
    
    configs = [
        ("small1", NodeCapabilities(10, 4096, 4)),
        ("small2", NodeCapabilities(10, 4096, 4)),
        ("medium1", NodeCapabilities(20, 8192, 8)),
        ("large1", NodeCapabilities(50, 16384, 16)),
    ]
    
    for node_id, caps in configs:
        manager.register_node(node_id, "localhost", 8000, caps)
    
    # Set different loads
    manager.heartbeat("small1", 0.8)
    manager.heartbeat("small2", 0.2)
    manager.heartbeat("medium1", 0.5)
    manager.heartbeat("large1", 0.3)
    
    print(f"\n⚖️  Testing load balancing strategies...")
    
    # Test different strategies
    strategies = [
        BalancingStrategy.LEAST_LOADED,
        BalancingStrategy.ROUND_ROBIN,
        BalancingStrategy.CAPABILITY_BASED
    ]
    
    workloads = [
        WorkloadMetrics(estimated_qubits=5, estimated_memory_mb=2000),
        WorkloadMetrics(estimated_qubits=15, estimated_memory_mb=6000),
        WorkloadMetrics(estimated_qubits=30, estimated_memory_mb=12000),
        WorkloadMetrics(estimated_qubits=8, estimated_memory_mb=3000),
    ]
    
    for strategy in strategies:
        balancer = LoadBalancer(manager, strategy)
        
        print(f"\n  🔹 {strategy.value.replace('_', ' ').title()}:")
        assignments = balancer.balance_workload(workloads)
        
        for node_id, workload_indices in assignments.items():
            print(f"    {node_id}: {len(workload_indices)} workloads")
        
        stats = balancer.get_balance_stats()
        print(f"    Balance quality: {stats['balance_quality']:.2%}")


def demo_performance_analysis():
    """Demonstrate performance analysis."""
    print("\n" + "=" * 70)
    print("5. PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    # Setup cluster
    manager = NodeManager()
    num_nodes = 8
    
    for i in range(num_nodes):
        caps = NodeCapabilities(max_qubits=20, max_memory_mb=8192, cpu_cores=8)
        manager.register_node(f"node{i}", f"10.0.0.{i+1}", 8000, caps)
    
    print(f"\n📊 Analyzing scalability with {num_nodes} nodes...")
    
    # Test with different partition counts
    partition_counts = [1, 2, 4, 8]
    
    print(f"\n{'Partitions':<12} {'Time (s)':<12} {'Speedup':<12} {'Efficiency':<12}")
    print("-" * 70)
    
    baseline_time = None
    
    for num_partitions in partition_counts:
        executor = DistributedExecutor(manager, num_partitions=num_partitions)
        
        result = executor.execute_distributed(
            f"perf_test_{num_partitions}",
            LARGE_CIRCUIT_GRAPH,
            partition_strategy="balanced"
        )
        
        exec_time = result['execution_time']
        
        if baseline_time is None:
            baseline_time = exec_time
            speedup = 1.0
        else:
            speedup = baseline_time / exec_time
        
        efficiency = speedup / num_partitions
        
        print(f"{num_partitions:<12} {exec_time:<12.4f} {speedup:<12.2f} {efficiency:<12.1%}")
    
    print(f"\n💡 Insights:")
    print(f"  • Parallelism improves with more partitions")
    print(f"  • Efficiency decreases due to communication overhead")
    print(f"  • Optimal partition count depends on circuit structure")


def demo_fault_tolerance():
    """Demonstrate fault tolerance."""
    print("\n" + "=" * 70)
    print("6. FAULT TOLERANCE & RECOVERY")
    print("=" * 70)
    
    manager = NodeManager()
    
    # Register nodes
    for i in range(4):
        caps = NodeCapabilities(max_qubits=20, max_memory_mb=8192, cpu_cores=8)
        manager.register_node(f"node{i}", f"10.0.0.{i+1}", 8000, caps)
    
    print(f"\n🔧 Initial cluster state:")
    stats = manager.get_cluster_stats()
    print(f"  Online nodes: {stats['online_nodes']}")
    
    # Simulate node failure
    print(f"\n⚠️  Simulating node failure...")
    manager.nodes["node1"].status = manager.nodes["node1"].status.__class__.OFFLINE
    
    stats = manager.get_cluster_stats()
    print(f"  Online nodes: {stats['online_nodes']}")
    print(f"  Offline nodes: {stats['offline_nodes']}")
    
    # Show that execution continues with remaining nodes
    executor = DistributedExecutor(manager, num_partitions=3)
    result = executor.execute_distributed(
        "fault_tolerant_job",
        BELL_STATE_GRAPH,
        partition_strategy="balanced"
    )
    
    print(f"\n✅ Execution completed despite node failure:")
    print(f"  Status: {result['status']}")
    print(f"  Used {result['num_partitions']} partitions on remaining nodes")


def main():
    """Run all distributed execution demonstrations."""
    print("\n" + "=" * 70)
    print("DISTRIBUTED EXECUTION DEMONSTRATION")
    print("=" * 70)
    print("\nDemonstrating:")
    print("  • Graph partitioning strategies")
    print("  • Node management and clustering")
    print("  • Distributed execution")
    print("  • Load balancing")
    print("  • Performance analysis")
    print("  • Fault tolerance")
    print()
    
    demo_graph_partitioning()
    demo_node_management()
    demo_distributed_execution()
    demo_load_balancing()
    demo_performance_analysis()
    demo_fault_tolerance()
    
    print("\n" + "=" * 70)
    print("DISTRIBUTED EXECUTION COMPLETE")
    print("=" * 70)
    print("\n✅ QMK supports distributed quantum computing!")
    print("\nKey capabilities:")
    print("  • Multiple partitioning strategies")
    print("  • Automatic load balancing")
    print("  • Fault tolerance")
    print("  • Performance optimization")
    print("  • Scalable to large clusters")


if __name__ == "__main__":
    main()
