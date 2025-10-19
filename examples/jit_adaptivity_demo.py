"""
JIT and Adaptivity Demonstration

Demonstrates profile-guided optimization, variant generation, teleportation planning,
and adaptive execution strategies.
"""

from kernel.jit import (
    ProfileCollector, VariantGenerator, TeleportationPlanner,
    AdaptivePolicyEngine, OptimizationStrategy
)


def demo_profile_collection():
    """Demonstrate execution profiling."""
    print("=" * 60)
    print("1. EXECUTION PROFILING")
    print("=" * 60)
    
    collector = ProfileCollector()
    
    # Start profiling a job
    profile_id = collector.start_profiling("job_1", "graph_1", metadata={"algorithm": "grover"})
    print(f"Started profiling: {profile_id}")
    
    # Simulate execution and record metrics
    collector.record_node_execution(profile_id, "node_1", duration=0.5, gate_type="H")
    collector.record_node_execution(profile_id, "node_2", duration=2.0, gate_type="CNOT")
    collector.record_node_execution(profile_id, "node_3", duration=0.3, gate_type="T")
    collector.record_node_execution(profile_id, "node_4", duration=1.5, gate_type="RZ")
    
    # Record qubit usage
    collector.record_qubit_usage(profile_id, "q0", usage_count=4)
    collector.record_qubit_usage(profile_id, "q1", usage_count=3)
    
    # Record error rates
    collector.record_error_rate(profile_id, "CNOT", error_rate=0.015)
    collector.record_error_rate(profile_id, "T", error_rate=0.001)
    
    # End profiling
    profile = collector.end_profiling(profile_id)
    
    print(f"\nProfile Summary:")
    print(f"  Job ID: {profile.job_id}")
    print(f"  Total Duration: {profile.total_duration:.3f}s")
    print(f"  Gate Counts: {profile.gate_counts}")
    print(f"  Qubit Usage: {profile.qubit_usage}")
    print(f"  Error Rates: {profile.error_rates}")
    
    # Identify hotspots
    hotspots = profile.get_hotspots(top_n=3)
    print(f"\nTop 3 Hotspots:")
    for node_id, duration in hotspots:
        print(f"  {node_id}: {duration:.3f}s")
    
    # Identify optimization opportunities
    opportunities = collector.identify_optimization_opportunities(profile_id)
    print(f"\nOptimization Opportunities:")
    for opp in opportunities:
        print(f"  Type: {opp['type']}")
        print(f"  Description: {opp['description']}")
    
    return profile, collector


def demo_variant_generation(profile_data):
    """Demonstrate variant generation."""
    print("\n" + "=" * 60)
    print("2. VARIANT GENERATION")
    print("=" * 60)
    
    generator = VariantGenerator()
    
    # Generate variants with different strategies
    print("\nGenerating execution variants...")
    variants = generator.generate_variants(
        graph_id="graph_1",
        strategies=[
            OptimizationStrategy.MINIMIZE_LATENCY,
            OptimizationStrategy.MINIMIZE_ERROR,
            OptimizationStrategy.BALANCED
        ],
        qec_profiles=["surface_code_d3", "surface_code_d5", "surface_code_d7"],
        max_variants=9
    )
    
    print(f"Generated {len(variants)} variants")
    
    # Display top 3 variants
    print("\nTop 3 Variants:")
    for i, variant in enumerate(variants[:3], 1):
        print(f"\n  Variant {i}: {variant.variant_id}")
        print(f"    QEC Profile: {variant.qec_profile}")
        print(f"    Strategy: {variant.optimization_strategy.value}")
        print(f"    Estimated Latency: {variant.estimated_latency:.2f}s")
        print(f"    Estimated Error Rate: {variant.estimated_error_rate:.6f}")
        print(f"    Estimated Resources: {variant.estimated_resources}")
        print(f"    Score: {variant.score:.4f}")
    
    # Select best variant with custom weights
    print("\nSelecting best variant (prioritizing error minimization)...")
    best = generator.select_best_variant(
        variants,
        weights={"latency": 0.2, "error": 0.6, "resources": 0.2}
    )
    print(f"Best Variant: {best.variant_id}")
    print(f"  QEC Profile: {best.qec_profile}")
    print(f"  Strategy: {best.optimization_strategy.value}")
    print(f"  Score: {best.score:.4f}")
    
    # Profile-guided generation
    print("\nGenerating profile-guided variants...")
    profile_guided = generator.generate_profile_guided_variants(
        "graph_1",
        profile_data,
        max_variants=5
    )
    print(f"Generated {len(profile_guided)} profile-guided variants")
    
    # Compare variants
    variant_ids = [v.variant_id for v in variants[:3]]
    comparison = generator.compare_variants(variant_ids)
    print(f"\nVariant Comparison:")
    print(f"  Best for Latency: {comparison['best_latency']}")
    print(f"  Best for Error: {comparison['best_error']}")
    print(f"  Best for Resources: {comparison['best_resources']}")
    print(f"  Best Overall: {comparison['best_overall']}")
    
    return variants


def demo_teleportation_planning():
    """Demonstrate teleportation planning."""
    print("\n" + "=" * 60)
    print("3. TELEPORTATION PLANNING")
    print("=" * 60)
    
    planner = TeleportationPlanner()
    
    # Create a graph with non-Clifford gates
    nodes = [
        {"node_id": "n1", "op": "H", "qubits": ["q0"]},
        {"node_id": "n2", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n3", "op": "T", "qubits": ["q0"]},
        {"node_id": "n4", "op": "T", "qubits": ["q1"]},
        {"node_id": "n5", "op": "RZ", "qubits": ["q0"], "angle": 0.785},
        {"node_id": "n6", "op": "T_DAG", "qubits": ["q1"]},
        {"node_id": "n7", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "n8", "op": "RY", "qubits": ["q1"], "angle": 1.57}
    ]
    
    print(f"\nCreating teleportation plan for {len(nodes)} nodes...")
    plan = planner.create_plan("graph_1", nodes)
    
    print(f"\nTeleportation Plan: {plan.plan_id}")
    print(f"  Total Sites: {len(plan.sites)}")
    print(f"  Total Cost: {plan.total_cost:.2f}")
    print(f"  Magic State Requirements:")
    for state_type, count in plan.magic_state_requirements.items():
        print(f"    {state_type}: {count}")
    
    # Show teleportation sites
    print(f"\nTeleportation Sites:")
    for site in plan.sites[:5]:  # Show first 5
        print(f"  {site.site_id}:")
        print(f"    Node: {site.node_id}")
        print(f"    Gate: {site.gate_type}")
        print(f"    Magic State: {site.magic_state_type}")
        print(f"    Cost: {site.cost:.2f}")
    
    # Estimate magic state throughput
    print(f"\nEstimating magic state factory throughput...")
    throughput = planner.estimate_magic_state_throughput(
        plan,
        factory_throughput={"T_state": 100.0, "rotation_state": 50.0}
    )
    print(f"  Production Times:")
    for state_type, time in throughput["production_times"].items():
        print(f"    {state_type}: {time:.4f}s")
    print(f"  Total Time: {throughput['total_time']:.4f}s")
    print(f"  Bottleneck: {throughput['bottleneck']}")
    
    # Optimize plan
    print(f"\nOptimizing plan for minimum cost...")
    optimized = planner.optimize_plan(plan.plan_id, "minimize_cost")
    print(f"  Optimized Cost: {optimized.total_cost:.2f}")
    
    # Get statistics
    stats = planner.get_plan_statistics(plan.plan_id)
    print(f"\nPlan Statistics:")
    print(f"  Total Sites: {stats['total_sites']}")
    print(f"  By Gate Type: {stats['by_gate_type']}")
    
    return plan


def demo_adaptive_policy(profile_data, variants):
    """Demonstrate adaptive policy engine."""
    print("\n" + "=" * 60)
    print("4. ADAPTIVE POLICY ENGINE")
    print("=" * 60)
    
    engine = AdaptivePolicyEngine()
    
    # Analyze profile and make decisions
    print("\nAnalyzing execution profile...")
    decisions = engine.analyze_and_decide(
        profile_data,
        system_state={"load": 0.75}
    )
    
    print(f"\nAdaptive Decisions ({len(decisions)}):")
    for decision in decisions:
        print(f"\n  Decision: {decision.decision_type.value}")
        print(f"  Reason: {decision.reason}")
        print(f"  Parameters: {decision.parameters}")
        print(f"  Confidence: {decision.confidence:.2f}")
    
    # Recommend variant
    print("\nRecommending best variant...")
    variant_list = [
        {
            "variant_id": v.variant_id,
            "estimated_error_rate": v.estimated_error_rate,
            "estimated_latency": v.estimated_latency,
            "score": v.score
        }
        for v in variants[:5]
    ]
    
    recommended = engine.recommend_variant(profile_data, variant_list)
    print(f"  Recommended Variant: {recommended}")
    
    # Check if checkpointing should be enabled
    should_checkpoint = engine.should_enable_checkpointing(
        profile_data,
        job_metadata={"priority": "high"}
    )
    print(f"\nCheckpointing Recommendation: {'Enabled' if should_checkpoint else 'Disabled'}")
    
    # Get decision statistics
    stats = engine.get_decision_statistics()
    print(f"\nDecision Statistics:")
    print(f"  Total Decisions: {stats['total_decisions']}")
    print(f"  By Type: {stats['by_type']}")
    print(f"  Average Confidence: {stats['avg_confidence']:.2f}")
    
    return engine


def demo_integrated_workflow():
    """Demonstrate integrated JIT workflow."""
    print("\n" + "=" * 60)
    print("5. INTEGRATED JIT WORKFLOW")
    print("=" * 60)
    
    print("\nSimulating complete JIT optimization workflow...")
    
    # Step 1: Profile execution
    print("\nStep 1: Profiling initial execution...")
    profile, collector = demo_profile_collection()
    
    # Aggregate profile data
    profile_data = collector.aggregate_profiles([profile.profile_id])
    
    # Step 2: Generate variants
    print("\n\nStep 2: Generating optimized variants...")
    variants = demo_variant_generation(profile_data)
    
    # Step 3: Plan teleportation
    print("\n\nStep 3: Planning teleportation...")
    plan = demo_teleportation_planning()
    
    # Step 4: Make adaptive decisions
    print("\n\nStep 4: Making adaptive decisions...")
    engine = demo_adaptive_policy(profile_data, variants)
    
    print("\n" + "=" * 60)
    print("JIT WORKFLOW COMPLETE")
    print("=" * 60)
    print("\nSummary:")
    print(f"  Profiles Collected: 1")
    print(f"  Variants Generated: {len(variants)}")
    print(f"  Teleportation Sites: {len(plan.sites)}")
    print(f"  Adaptive Decisions: {len(engine.decision_history)}")
    print("\nThe system is now optimized for future executions!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("QMK JIT & ADAPTIVITY DEMONSTRATION")
    print("=" * 60)
    
    # Run individual demos
    profile, collector = demo_profile_collection()
    profile_data = collector.aggregate_profiles([profile.profile_id])
    
    variants = demo_variant_generation(profile_data)
    plan = demo_teleportation_planning()
    engine = demo_adaptive_policy(profile_data, variants)
    
    # Run integrated workflow
    print("\n\n")
    demo_integrated_workflow()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
