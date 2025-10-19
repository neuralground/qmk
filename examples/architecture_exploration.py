"""
Architecture Exploration Example

Demonstrates how to use QMK for exploring different:
1. QEC code implementations (Surface, QLDPC, SHYPS, Bacon-Shor)
2. Gate implementations (direct vs teleported CNOT)
3. Error models and physical parameters
4. Resource tradeoffs
"""

from kernel.simulator.qec_profiles import (
    surface_code, qldpc_code, shyps_code, bacon_shor_code
)
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.jit import TeleportationPlanner, VariantGenerator, OptimizationStrategy


def compare_qec_codes():
    """Compare different QEC code families."""
    print("=" * 70)
    print("1. QEC CODE COMPARISON")
    print("=" * 70)
    
    distance = 9
    gate_error = 1e-3
    
    codes = {
        "Surface Code": surface_code(distance, gate_error),
        "QLDPC (rate=0.1)": qldpc_code(distance, gate_error, rate=0.1),
        "QLDPC (rate=0.2)": qldpc_code(distance, gate_error, rate=0.2),
        "SHYPS": shyps_code(distance, gate_error),
        "Bacon-Shor": bacon_shor_code(distance, gate_error),
    }
    
    print(f"\nDistance: {distance}, Physical gate error: {gate_error:.0e}\n")
    print(f"{'Code':<20} {'Phys Qubits':<12} {'Cycle Time':<12} {'Logical Error':<15} {'Decoder':<12}")
    print("-" * 70)
    
    for name, profile in codes.items():
        logical_error = profile.logical_error_rate()
        print(f"{name:<20} {profile.physical_qubit_count:<12} "
              f"{profile.logical_cycle_time_us:<12.2f} "
              f"{logical_error:<15.2e} {profile.decoder_type:<12}")
    
    # Resource efficiency analysis
    print("\n📊 Resource Efficiency (normalized to Surface Code):")
    surface_qubits = codes["Surface Code"].physical_qubit_count
    
    for name, profile in codes.items():
        efficiency = surface_qubits / profile.physical_qubit_count
        print(f"  {name:<20} {efficiency:.2f}x "
              f"({'saves' if efficiency > 1 else 'uses'} "
              f"{abs(1-efficiency)*100:.1f}% qubits)")


def compare_gate_implementations():
    """Compare direct vs teleported gate implementations."""
    print("\n" + "=" * 70)
    print("2. GATE IMPLEMENTATION COMPARISON")
    print("=" * 70)
    
    planner = TeleportationPlanner()
    
    # Direct CNOT (lattice surgery)
    direct_cnot = [
        {"node_id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"]}
    ]
    
    # Teleported CNOT using T gates
    teleported_cnot = [
        {"node_id": "t1", "op": "T", "qubits": ["q0"]},
        {"node_id": "h1", "op": "H", "qubits": ["q1"]},
        {"node_id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "t2", "op": "T_DAG", "qubits": ["q0"]},
        {"node_id": "h2", "op": "H", "qubits": ["q1"]},
    ]
    
    # Toffoli decomposition (multiple CNOTs + T gates)
    toffoli_decomp = [
        {"node_id": "h", "op": "H", "qubits": ["q2"]},
        {"node_id": "cnot1", "op": "CNOT", "qubits": ["q1", "q2"]},
        {"node_id": "t1", "op": "T_DAG", "qubits": ["q2"]},
        {"node_id": "cnot2", "op": "CNOT", "qubits": ["q0", "q2"]},
        {"node_id": "t2", "op": "T", "qubits": ["q2"]},
        {"node_id": "cnot3", "op": "CNOT", "qubits": ["q1", "q2"]},
        {"node_id": "t3", "op": "T_DAG", "qubits": ["q2"]},
        {"node_id": "cnot4", "op": "CNOT", "qubits": ["q0", "q2"]},
        {"node_id": "t4", "op": "T", "qubits": ["q1"]},
        {"node_id": "t5", "op": "T", "qubits": ["q2"]},
        {"node_id": "h2", "op": "H", "qubits": ["q2"]},
        {"node_id": "cnot5", "op": "CNOT", "qubits": ["q0", "q1"]},
        {"node_id": "t6", "op": "T", "qubits": ["q0"]},
        {"node_id": "t7", "op": "T_DAG", "qubits": ["q1"]},
        {"node_id": "cnot6", "op": "CNOT", "qubits": ["q0", "q1"]},
    ]
    
    implementations = {
        "Direct CNOT": direct_cnot,
        "Teleported CNOT": teleported_cnot,
        "Toffoli (decomposed)": toffoli_decomp,
    }
    
    print("\n📐 Gate Implementation Analysis:\n")
    print(f"{'Implementation':<25} {'Gates':<8} {'T-states':<10} {'Cost':<10}")
    print("-" * 70)
    
    for name, nodes in implementations.items():
        plan = planner.create_plan(name, nodes)
        t_states = plan.magic_state_requirements.get("T_state", 0)
        
        print(f"{name:<25} {len(nodes):<8} {t_states:<10} {plan.total_cost:<10.1f}")
    
    # Magic state factory throughput analysis
    print("\n🏭 Magic State Factory Throughput:")
    
    for name, nodes in implementations.items():
        plan = planner.create_plan(name, nodes)
        
        if plan.magic_state_requirements:
            throughput = planner.estimate_magic_state_throughput(
                plan,
                factory_throughput={"T_state": 100.0, "rotation_state": 50.0}
            )
            
            print(f"\n  {name}:")
            print(f"    Requirements: {plan.magic_state_requirements}")
            print(f"    Production time: {throughput['total_time']:.4f}s")
            print(f"    Bottleneck: {throughput['bottleneck']}")


def explore_error_regimes():
    """Explore different error rate regimes."""
    print("\n" + "=" * 70)
    print("3. ERROR REGIME EXPLORATION")
    print("=" * 70)
    
    distance = 9
    error_rates = {
        "Current (NISQ)": 1e-3,
        "Near-term": 1e-4,
        "Fault-tolerant": 1e-5,
        "Far future": 1e-6,
    }
    
    print(f"\nLogical error rates for distance {distance}:\n")
    print(f"{'Regime':<20} {'Physical Error':<15} {'Surface':<15} {'QLDPC':<15} {'SHYPS':<15}")
    print("-" * 70)
    
    for regime, gate_error in error_rates.items():
        surface = surface_code(distance, gate_error)
        qldpc = qldpc_code(distance, gate_error, rate=0.1)
        shyps = shyps_code(distance, gate_error)
        
        print(f"{regime:<20} {gate_error:<15.0e} "
              f"{surface.logical_error_rate():<15.2e} "
              f"{qldpc.logical_error_rate():<15.2e} "
              f"{shyps.logical_error_rate():<15.2e}")
    
    # Threshold analysis
    print("\n🎯 Threshold Analysis:")
    print("\nBelow threshold (p < p_th ≈ 0.01):")
    print("  - Logical error decreases exponentially with distance")
    print("  - P_L ≈ (p/p_th)^((d+1)/2)")
    print("\nAbove threshold (p > p_th):")
    print("  - QEC doesn't help, logical error ≈ 1")


def variant_generation_for_architecture():
    """Use variant generator to explore architectural choices."""
    print("\n" + "=" * 70)
    print("4. VARIANT GENERATION FOR ARCHITECTURE EXPLORATION")
    print("=" * 70)
    
    generator = VariantGenerator()
    
    # Generate variants with all QEC codes
    variants = generator.generate_variants(
        graph_id="architecture_test",
        strategies=[OptimizationStrategy.MINIMIZE_RESOURCES],
        qec_profiles=[
            "surface_code_d9",
            "qldpc_d9_r01",
            "qldpc_d9_r02",
            "shyps_d9",
            "bacon_shor_d7"
        ],
        max_variants=10
    )
    
    print(f"\nGenerated {len(variants)} architectural variants\n")
    print(f"{'Variant':<15} {'QEC Profile':<20} {'Resources':<12} {'Latency':<10} {'Score':<8}")
    print("-" * 70)
    
    for variant in variants[:5]:
        print(f"{variant.variant_id:<15} {variant.qec_profile:<20} "
              f"{variant.estimated_resources:<12} "
              f"{variant.estimated_latency:<10.2f} "
              f"{variant.score:<8.4f}")
    
    # Compare best variants
    comparison = generator.compare_variants([v.variant_id for v in variants[:3]])
    
    print("\n📊 Comparison Summary:")
    print(f"  Best for latency: {comparison['best_latency']}")
    print(f"  Best for resources: {comparison['best_resources']}")
    print(f"  Best overall: {comparison['best_overall']}")


def resource_tradeoff_analysis():
    """Analyze resource tradeoffs."""
    print("\n" + "=" * 70)
    print("5. RESOURCE TRADEOFF ANALYSIS")
    print("=" * 70)
    
    # Compare at different distances
    distances = [5, 7, 9, 11, 13]
    
    print("\n📈 Scaling with Distance:\n")
    print(f"{'Distance':<10} {'Surface':<12} {'QLDPC (0.1)':<12} {'SHYPS':<12} {'Improvement':<12}")
    print("-" * 70)
    
    for d in distances:
        surface = surface_code(d)
        qldpc = qldpc_code(d, rate=0.1)
        shyps = shyps_code(d)
        
        improvement = (surface.physical_qubit_count - qldpc.physical_qubit_count) / surface.physical_qubit_count * 100
        
        print(f"{d:<10} {surface.physical_qubit_count:<12} "
              f"{qldpc.physical_qubit_count:<12} "
              f"{shyps.physical_qubit_count:<12} "
              f"{improvement:<12.1f}%")
    
    print("\n💡 Key Insights:")
    print("  - QLDPC codes save 40-60% physical qubits vs Surface codes")
    print("  - SHYPS codes save ~25% physical qubits")
    print("  - Tradeoff: QLDPC has longer cycle times (more complex decoding)")
    print("  - Choice depends on: qubit availability vs time constraints")


def main():
    """Run all architecture exploration demos."""
    print("\n" + "=" * 70)
    print("QMK ARCHITECTURE EXPLORATION DEMONSTRATION")
    print("=" * 70)
    print("\nExploring:")
    print("  • QEC code implementations (Surface, QLDPC, SHYPS, Bacon-Shor)")
    print("  • Gate implementations (direct vs teleported)")
    print("  • Error regimes and thresholds")
    print("  • Resource tradeoffs")
    print()
    
    compare_qec_codes()
    compare_gate_implementations()
    explore_error_regimes()
    variant_generation_for_architecture()
    resource_tradeoff_analysis()
    
    print("\n" + "=" * 70)
    print("ARCHITECTURE EXPLORATION COMPLETE")
    print("=" * 70)
    print("\n✅ QMK enables comprehensive architecture exploration!")
    print("\nKey capabilities:")
    print("  • Compare QEC codes with realistic parameters")
    print("  • Analyze gate implementation tradeoffs")
    print("  • Explore error rate regimes")
    print("  • Optimize resource allocation")
    print("  • Profile-guided variant generation")


if __name__ == "__main__":
    main()
