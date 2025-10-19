"""
QIR Bridge Demonstration

Shows how to use the QIR bridge to:
1. Parse QIR programs
2. Generate QVM graphs
3. Estimate resource requirements
4. Compare QEC profiles
"""

import json
from kernel.qir_bridge import QIRParser, QVMGraphGenerator, ResourceEstimator
from kernel.simulator.qec_profiles import surface_code, qldpc_code, shyps_code


# Sample QIR programs
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

GROVER_ORACLE_QIR = """
define void @grover_oracle() {
  %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
  %q1 = call %Qubit* @__quantum__rt__qubit_allocate()
  %q2 = call %Qubit* @__quantum__rt__qubit_allocate()
  
  ; Oracle for |101⟩
  call void @__quantum__qis__x__body(%Qubit* %q1)
  call void @__quantum__qis__h__body(%Qubit* %q2)
  call void @__quantum__qis__cnot__body(%Qubit* %q0, %Qubit* %q2)
  call void @__quantum__qis__cnot__body(%Qubit* %q1, %Qubit* %q2)
  call void @__quantum__qis__h__body(%Qubit* %q2)
  call void @__quantum__qis__x__body(%Qubit* %q1)
  
  call void @__quantum__rt__qubit_release(%Qubit* %q0)
  call void @__quantum__rt__qubit_release(%Qubit* %q1)
  call void @__quantum__rt__qubit_release(%Qubit* %q2)
  ret void
}
"""

T_CIRCUIT_QIR = """
define void @t_circuit() {
  %q0 = call %Qubit* @__quantum__rt__qubit_allocate()
  %q1 = call %Qubit* @__quantum__rt__qubit_allocate()
  
  call void @__quantum__qis__h__body(%Qubit* %q0)
  call void @__quantum__qis__h__body(%Qubit* %q1)
  call void @__quantum__qis__t__body(%Qubit* %q0)
  call void @__quantum__qis__t__body(%Qubit* %q1)
  call void @__quantum__qis__cnot__body(%Qubit* %q0, %Qubit* %q1)
  call void @__quantum__qis__t__body(%Qubit* %q1)
  call void @__quantum__qis__cnot__body(%Qubit* %q0, %Qubit* %q1)
  
  %r0 = call i1 @__quantum__qis__mz__body(%Qubit* %q0)
  %r1 = call i1 @__quantum__qis__mz__body(%Qubit* %q1)
  
  call void @__quantum__rt__qubit_release(%Qubit* %q0)
  call void @__quantum__rt__qubit_release(%Qubit* %q1)
  ret void
}
"""


def demo_qir_parsing():
    """Demonstrate QIR parsing."""
    print("=" * 70)
    print("1. QIR PARSING")
    print("=" * 70)
    
    parser = QIRParser()
    
    # Parse Bell state
    print("\nParsing Bell state circuit...")
    functions = parser.parse(BELL_STATE_QIR)
    bell_func = functions["bell_state"]
    
    print(f"  Function: {bell_func.name}")
    print(f"  Qubits: {bell_func.qubit_count}")
    print(f"  Instructions: {len(bell_func.instructions)}")
    
    print("\n  Instruction sequence:")
    for i, inst in enumerate(bell_func.instructions[:8], 1):
        print(f"    {i}. {inst}")
    
    # Parse Grover oracle
    print("\nParsing Grover oracle...")
    functions = parser.parse(GROVER_ORACLE_QIR)
    grover_func = functions["grover_oracle"]
    
    print(f"  Function: {grover_func.name}")
    print(f"  Qubits: {grover_func.qubit_count}")
    print(f"  Instructions: {len(grover_func.instructions)}")
    
    # Get statistics
    parser_all = QIRParser()
    parser_all.parse(BELL_STATE_QIR + "\n" + GROVER_ORACLE_QIR + "\n" + T_CIRCUIT_QIR)
    stats = parser_all.get_statistics()
    
    print("\n📊 Parsing Statistics:")
    print(f"  Total functions: {stats['total_functions']}")
    print(f"  Total instructions: {stats['total_instructions']}")
    print(f"  Total qubits: {stats['total_qubits']}")
    print(f"  Gate counts: {stats['gate_counts']}")


def demo_qvm_generation():
    """Demonstrate QVM graph generation."""
    print("\n" + "=" * 70)
    print("2. QVM GRAPH GENERATION")
    print("=" * 70)
    
    parser = QIRParser()
    generator = QVMGraphGenerator()
    
    # Generate Bell state graph
    print("\nGenerating QVM graph for Bell state...")
    functions = parser.parse(BELL_STATE_QIR)
    bell_func = functions["bell_state"]
    
    graph = generator.generate(bell_func)
    
    print(f"  Graph name: {graph['name']}")
    print(f"  Node count: {len(graph['nodes'])}")
    print(f"  Metadata: {graph['metadata']}")
    
    print("\n  Node sequence:")
    for i, node in enumerate(graph['nodes'][:8], 1):
        qubits_str = ', '.join(node['qubits'])
        params_str = f", params={node['params']}" if 'params' in node else ""
        print(f"    {i}. {node['op']}({qubits_str}){params_str}")
    
    # Generate with teleportation
    print("\nGenerating with teleportation insertion...")
    generator_teleport = QVMGraphGenerator(insert_teleportation=True)
    functions = parser.parse(T_CIRCUIT_QIR)
    t_func = functions["t_circuit"]
    
    graph_teleport = generator_teleport.generate(t_func)
    
    # Count teleported gates
    teleported_count = sum(
        1 for node in graph_teleport['nodes']
        if node.get('params', {}).get('teleported', False)
    )
    
    print(f"  Teleported gates: {teleported_count}")
    
    # Show sample QVM graph JSON
    print("\n📄 Sample QVM Graph (first 3 nodes):")
    sample_graph = {
        "name": graph["name"],
        "nodes": graph["nodes"][:3],
        "metadata": graph["metadata"]
    }
    print(json.dumps(sample_graph, indent=2))


def demo_resource_estimation():
    """Demonstrate resource estimation."""
    print("\n" + "=" * 70)
    print("3. RESOURCE ESTIMATION")
    print("=" * 70)
    
    parser = QIRParser()
    estimator = ResourceEstimator()
    
    # Estimate Bell state
    print("\nEstimating Bell state resources...")
    functions = parser.parse(BELL_STATE_QIR)
    bell_func = functions["bell_state"]
    
    estimate = estimator.estimate(bell_func)
    
    print(f"  Logical qubits: {estimate.logical_qubits}")
    print(f"  Physical qubits: {estimate.physical_qubits}")
    print(f"  Gate count: {estimate.gate_count}")
    print(f"  Gate breakdown: {estimate.gate_breakdown}")
    print(f"  Circuit depth: {estimate.depth}")
    print(f"  Execution time: {estimate.execution_time_us:.2f} μs")
    
    # Estimate T circuit
    print("\nEstimating T-gate circuit resources...")
    functions = parser.parse(T_CIRCUIT_QIR)
    t_func = functions["t_circuit"]
    
    estimate_t = estimator.estimate(t_func)
    
    print(f"  Logical qubits: {estimate_t.logical_qubits}")
    print(f"  Physical qubits: {estimate_t.physical_qubits}")
    print(f"  Gate count: {estimate_t.gate_count}")
    print(f"  T-gate count: {estimate_t.t_count}")
    print(f"  Execution time: {estimate_t.execution_time_us:.2f} μs")
    
    # Magic state requirements
    magic_reqs = estimator.estimate_magic_state_requirements(t_func)
    
    print("\n🔮 Magic State Requirements:")
    print(f"  T-states needed: {magic_reqs['t_states_needed']}")
    print(f"  Production time: {magic_reqs['t_production_time_s']:.4f}s")


def demo_qec_comparison():
    """Demonstrate QEC profile comparison."""
    print("\n" + "=" * 70)
    print("4. QEC PROFILE COMPARISON")
    print("=" * 70)
    
    parser = QIRParser()
    estimator = ResourceEstimator()
    
    # Parse Grover oracle
    functions = parser.parse(GROVER_ORACLE_QIR)
    grover_func = functions["grover_oracle"]
    
    # Compare profiles
    profiles = [
        surface_code(9),
        qldpc_code(9, rate=0.1),
        shyps_code(9)
    ]
    
    print("\nComparing QEC profiles for Grover oracle:\n")
    print(f"{'Profile':<20} {'Phys Qubits':<12} {'Exec Time (μs)':<15} {'Depth':<8}")
    print("-" * 70)
    
    estimates = estimator.compare_profiles(grover_func, profiles)
    
    for profile_name, estimate in estimates.items():
        print(f"{profile_name:<20} {estimate.physical_qubits:<12} "
              f"{estimate.execution_time_us:<15.2f} {estimate.depth:<8}")
    
    # Show resource savings
    surface_estimate = estimates["surface_code"]
    
    print("\n💡 Resource Efficiency (vs Surface Code):")
    for profile_name, estimate in estimates.items():
        if profile_name != "surface_code":
            savings = (surface_estimate.physical_qubits - estimate.physical_qubits) / surface_estimate.physical_qubits * 100
            time_diff = (estimate.execution_time_us - surface_estimate.execution_time_us) / surface_estimate.execution_time_us * 100
            
            print(f"  {profile_name}:")
            print(f"    Qubit savings: {savings:+.1f}%")
            print(f"    Time difference: {time_diff:+.1f}%")


def demo_end_to_end_workflow():
    """Demonstrate complete QIR to QVM workflow."""
    print("\n" + "=" * 70)
    print("5. END-TO-END QIR WORKFLOW")
    print("=" * 70)
    
    print("\nComplete workflow: QIR → Parse → Generate → Estimate → Execute")
    
    # Step 1: Parse QIR
    print("\n📥 Step 1: Parse QIR")
    parser = QIRParser()
    functions = parser.parse(BELL_STATE_QIR)
    bell_func = functions["bell_state"]
    print(f"  ✓ Parsed function '{bell_func.name}' with {bell_func.qubit_count} qubits")
    
    # Step 2: Generate QVM graph
    print("\n🔄 Step 2: Generate QVM graph")
    generator = QVMGraphGenerator(insert_teleportation=False)
    graph = generator.generate(bell_func)
    print(f"  ✓ Generated graph with {len(graph['nodes'])} nodes")
    
    # Step 3: Estimate resources
    print("\n📊 Step 3: Estimate resources")
    estimator = ResourceEstimator(qec_profile=surface_code(9))
    estimate = estimator.estimate(bell_func)
    print(f"  ✓ Estimated {estimate.physical_qubits} physical qubits needed")
    print(f"  ✓ Estimated execution time: {estimate.execution_time_us:.2f} μs")
    
    # Step 4: Ready for execution
    print("\n✅ Step 4: Ready for execution")
    print(f"  Graph can now be executed by QMK kernel")
    print(f"  Resource requirements validated")
    
    print("\n" + "=" * 70)
    print("QIR BRIDGE WORKFLOW COMPLETE")
    print("=" * 70)


def main():
    """Run all QIR bridge demonstrations."""
    print("\n" + "=" * 70)
    print("QMK QIR BRIDGE DEMONSTRATION")
    print("=" * 70)
    print("\nDemonstrating:")
    print("  • QIR parsing")
    print("  • QVM graph generation")
    print("  • Resource estimation")
    print("  • QEC profile comparison")
    print("  • End-to-end workflow")
    print()
    
    demo_qir_parsing()
    demo_qvm_generation()
    demo_resource_estimation()
    demo_qec_comparison()
    demo_end_to_end_workflow()
    
    print("\n✅ QIR Bridge enables seamless integration with QIR-based tools!")
    print("\nKey capabilities:")
    print("  • Parse QIR from LLVM-based quantum compilers")
    print("  • Generate executable QVM graphs")
    print("  • Estimate resource requirements")
    print("  • Compare QEC profiles")
    print("  • Insert teleportation for fault tolerance")


if __name__ == "__main__":
    main()
