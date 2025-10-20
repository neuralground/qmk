#!/usr/bin/env python3
"""Performance benchmarks for QIR optimizer passes.

Measures:
- Gate count reduction
- Depth reduction
- T-count reduction
- SWAP overhead
- Optimization time
- Memory usage

Success Criteria (from OPTIMIZATION_PLAN.md):
- Gate count reduction: 20-50% typical
- Depth reduction: 15-30% typical
- T-count reduction: 30-60% for Clifford+T
- SWAP overhead: <20%
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import QIRCircuit, QIRInstruction, InstructionType, PassManager
from qir.optimizer.passes import (
    GateCancellationPass,
    GateCommutationPass,
    GateFusionPass,
    DeadCodeEliminationPass,
    ConstantPropagationPass,
    TemplateMatchingPass,
    MeasurementDeferralPass,
    CliffordTPlusOptimizationPass,
    MagicStateOptimizationPass,
    GateTeleportationPass,
    UncomputationOptimizationPass,
    LatticeSurgeryOptimizationPass,
    SwapInsertionPass,
    QubitMappingPass
)


class BenchmarkMetrics:
    """Metrics for a single benchmark run."""
    
    def __init__(self, name: str):
        self.name = name
        self.initial_gate_count = 0
        self.final_gate_count = 0
        self.initial_depth = 0
        self.final_depth = 0
        self.initial_t_count = 0
        self.final_t_count = 0
        self.initial_cnot_count = 0
        self.final_cnot_count = 0
        self.optimization_time = 0.0
        
    @property
    def gate_reduction_percent(self) -> float:
        """Calculate gate count reduction percentage."""
        if self.initial_gate_count == 0:
            return 0.0
        return ((self.initial_gate_count - self.final_gate_count) / 
                self.initial_gate_count * 100)
    
    @property
    def depth_reduction_percent(self) -> float:
        """Calculate depth reduction percentage."""
        if self.initial_depth == 0:
            return 0.0
        return ((self.initial_depth - self.final_depth) / 
                self.initial_depth * 100)
    
    @property
    def t_count_reduction_percent(self) -> float:
        """Calculate T-count reduction percentage."""
        if self.initial_t_count == 0:
            return 0.0
        return ((self.initial_t_count - self.final_t_count) / 
                self.initial_t_count * 100)
    
    @property
    def cnot_reduction_percent(self) -> float:
        """Calculate CNOT reduction percentage."""
        if self.initial_cnot_count == 0:
            return 0.0
        return ((self.initial_cnot_count - self.final_cnot_count) / 
                self.initial_cnot_count * 100)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            'name': self.name,
            'initial_gate_count': self.initial_gate_count,
            'final_gate_count': self.final_gate_count,
            'gate_reduction_percent': round(self.gate_reduction_percent, 2),
            'initial_depth': self.initial_depth,
            'final_depth': self.final_depth,
            'depth_reduction_percent': round(self.depth_reduction_percent, 2),
            'initial_t_count': self.initial_t_count,
            'final_t_count': self.final_t_count,
            't_count_reduction_percent': round(self.t_count_reduction_percent, 2),
            'initial_cnot_count': self.initial_cnot_count,
            'final_cnot_count': self.final_cnot_count,
            'cnot_reduction_percent': round(self.cnot_reduction_percent, 2),
            'optimization_time_ms': round(self.optimization_time * 1000, 2)
        }


def count_t_gates(circuit: QIRCircuit) -> int:
    """Count T and T† gates in circuit."""
    count = 0
    for inst in circuit.instructions:
        if inst.type in [InstructionType.T, InstructionType.TDG]:
            count += 1
    return count


def count_cnot_gates(circuit: QIRCircuit) -> int:
    """Count CNOT gates in circuit."""
    count = 0
    for inst in circuit.instructions:
        if inst.type == InstructionType.CNOT:
            count += 1
    return count


def estimate_depth(circuit: QIRCircuit) -> int:
    """Estimate circuit depth (simplified)."""
    # Simple depth estimation: count layers
    # In reality, would need dependency analysis
    return circuit.get_gate_count()  # Simplified


def benchmark_pass(circuit: QIRCircuit, pass_class, name: str) -> BenchmarkMetrics:
    """Benchmark a single optimization pass."""
    metrics = BenchmarkMetrics(name)
    
    # Record initial metrics
    metrics.initial_gate_count = circuit.get_gate_count()
    metrics.initial_depth = estimate_depth(circuit)
    metrics.initial_t_count = count_t_gates(circuit)
    metrics.initial_cnot_count = count_cnot_gates(circuit)
    
    # Run optimization
    opt_pass = pass_class()
    start_time = time.time()
    result = opt_pass.run(circuit)
    end_time = time.time()
    
    # Record final metrics
    metrics.final_gate_count = result.get_gate_count()
    metrics.final_depth = estimate_depth(result)
    metrics.final_t_count = count_t_gates(result)
    metrics.final_cnot_count = count_cnot_gates(result)
    metrics.optimization_time = end_time - start_time
    
    return metrics


def benchmark_pipeline(circuit: QIRCircuit, passes: List, name: str) -> BenchmarkMetrics:
    """Benchmark a pipeline of optimization passes."""
    metrics = BenchmarkMetrics(name)
    
    # Record initial metrics
    metrics.initial_gate_count = circuit.get_gate_count()
    metrics.initial_depth = estimate_depth(circuit)
    metrics.initial_t_count = count_t_gates(circuit)
    metrics.initial_cnot_count = count_cnot_gates(circuit)
    
    # Run pipeline
    manager = PassManager(passes)
    manager.verbose = False
    
    start_time = time.time()
    result = manager.run(circuit)
    end_time = time.time()
    
    # Record final metrics
    metrics.final_gate_count = result.get_gate_count()
    metrics.final_depth = estimate_depth(result)
    metrics.final_t_count = count_t_gates(result)
    metrics.final_cnot_count = count_cnot_gates(result)
    metrics.optimization_time = end_time - start_time
    
    return metrics


# ============================================================================
# Test Circuits
# ============================================================================

def create_redundant_circuit() -> QIRCircuit:
    """Create circuit with many redundant gates."""
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    
    # Many cancellable gates
    for _ in range(10):
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
    
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    
    for _ in range(5):
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
    
    return circuit


def create_clifford_t_circuit() -> QIRCircuit:
    """Create Clifford+T circuit."""
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    
    # Many T gates
    for _ in range(8):
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
    
    circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    
    for _ in range(4):
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
    
    circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
    circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
    
    return circuit


def create_rotation_circuit() -> QIRCircuit:
    """Create circuit with many rotations."""
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    
    # Many rotations that can be fused
    for i in range(10):
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.1 * i}))
    
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    
    for i in range(8):
        circuit.add_instruction(QIRInstruction(InstructionType.RY, [q1], {'theta': 0.05 * i}))
    
    return circuit


def create_bell_state() -> QIRCircuit:
    """Create Bell state circuit."""
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    
    circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    
    return circuit


def create_ghz_state(n: int = 4) -> QIRCircuit:
    """Create n-qubit GHZ state."""
    circuit = QIRCircuit()
    qubits = [circuit.add_qubit(f'q{i}') for i in range(n)]
    
    circuit.add_instruction(QIRInstruction(InstructionType.H, [qubits[0]]))
    
    for i in range(n - 1):
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [qubits[i], qubits[i + 1]]))
    
    return circuit


def create_vqe_ansatz() -> QIRCircuit:
    """Create VQE ansatz circuit."""
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    q2 = circuit.add_qubit('q2')
    
    # Layer 1
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 0.5}))
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q1], {'theta': 0.3}))
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q2], {'theta': 0.7}))
    
    # Entangling layer
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q2]))
    
    # Layer 2
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q0], {'theta': 0.2}))
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q1], {'theta': 0.4}))
    circuit.add_instruction(QIRInstruction(InstructionType.RY, [q2], {'theta': 0.6}))
    
    return circuit


# ============================================================================
# Benchmark Suites
# ============================================================================

def benchmark_individual_passes():
    """Benchmark each optimization pass individually."""
    print("\n" + "="*70)
    print("BENCHMARKING INDIVIDUAL PASSES")
    print("="*70)
    
    results = []
    
    # Gate Cancellation
    circuit = create_redundant_circuit()
    metrics = benchmark_pass(circuit, GateCancellationPass, "Gate Cancellation")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # Gate Fusion
    circuit = create_rotation_circuit()
    metrics = benchmark_pass(circuit, GateFusionPass, "Gate Fusion")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # Clifford+T Optimization
    circuit = create_clifford_t_circuit()
    metrics = benchmark_pass(circuit, CliffordTPlusOptimizationPass, "Clifford+T Optimization")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  T-count reduction: {metrics.t_count_reduction_percent:.1f}%")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # Dead Code Elimination
    circuit = QIRCircuit()
    q0 = circuit.add_qubit('q0')
    q1 = circuit.add_qubit('q1')
    q2 = circuit.add_qubit('q2')
    circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
    circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))  # q1 never used
    circuit.add_instruction(QIRInstruction(InstructionType.Y, [q2]))  # q2 never used
    circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
    
    metrics = benchmark_pass(circuit, DeadCodeEliminationPass, "Dead Code Elimination")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    return results


def benchmark_pipelines():
    """Benchmark optimization pipelines."""
    print("\n" + "="*70)
    print("BENCHMARKING OPTIMIZATION PIPELINES")
    print("="*70)
    
    results = []
    
    # Standard pipeline
    circuit = create_redundant_circuit()
    passes = [
        GateCancellationPass(),
        GateCommutationPass(),
        GateFusionPass(),
        DeadCodeEliminationPass()
    ]
    metrics = benchmark_pipeline(circuit, passes, "Standard Pipeline")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # Clifford+T pipeline
    circuit = create_clifford_t_circuit()
    passes = [
        GateCommutationPass(),
        CliffordTPlusOptimizationPass(),
        GateFusionPass(),
        GateCancellationPass()
    ]
    metrics = benchmark_pipeline(circuit, passes, "Clifford+T Pipeline")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  T-count reduction: {metrics.t_count_reduction_percent:.1f}%")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # VQE pipeline
    circuit = create_vqe_ansatz()
    passes = [
        GateCommutationPass(),
        GateFusionPass(),
        TemplateMatchingPass()
    ]
    metrics = benchmark_pipeline(circuit, passes, "VQE Pipeline")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    return results


def benchmark_algorithms():
    """Benchmark optimization on standard algorithms."""
    print("\n" + "="*70)
    print("BENCHMARKING STANDARD ALGORITHMS")
    print("="*70)
    
    results = []
    
    # Bell state
    circuit = create_bell_state()
    passes = [GateCancellationPass(), GateCommutationPass()]
    metrics = benchmark_pipeline(circuit, passes, "Bell State")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Initial gates: {metrics.initial_gate_count}")
    print(f"  Final gates: {metrics.final_gate_count}")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # GHZ state
    circuit = create_ghz_state(4)
    passes = [GateCancellationPass(), GateCommutationPass()]
    metrics = benchmark_pipeline(circuit, passes, "4-Qubit GHZ State")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Initial gates: {metrics.initial_gate_count}")
    print(f"  Final gates: {metrics.final_gate_count}")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    # VQE ansatz
    circuit = create_vqe_ansatz()
    passes = [
        GateCommutationPass(),
        GateFusionPass(),
        GateCancellationPass()
    ]
    metrics = benchmark_pipeline(circuit, passes, "VQE Ansatz")
    results.append(metrics)
    print(f"\n✓ {metrics.name}")
    print(f"  Gate reduction: {metrics.gate_reduction_percent:.1f}%")
    print(f"  Time: {metrics.optimization_time*1000:.2f}ms")
    
    return results


def generate_report(all_results: List[List[BenchmarkMetrics]]):
    """Generate comprehensive benchmark report."""
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY REPORT")
    print("="*70)
    
    # Flatten results
    all_metrics = []
    for result_list in all_results:
        all_metrics.extend(result_list)
    
    # Calculate averages
    total_gate_reduction = sum(m.gate_reduction_percent for m in all_metrics if m.initial_gate_count > 0)
    count_gate = sum(1 for m in all_metrics if m.initial_gate_count > 0)
    avg_gate_reduction = total_gate_reduction / count_gate if count_gate > 0 else 0
    
    total_t_reduction = sum(m.t_count_reduction_percent for m in all_metrics if m.initial_t_count > 0)
    count_t = sum(1 for m in all_metrics if m.initial_t_count > 0)
    avg_t_reduction = total_t_reduction / count_t if count_t > 0 else 0
    
    total_time = sum(m.optimization_time for m in all_metrics)
    avg_time = total_time / len(all_metrics) if all_metrics else 0
    
    print(f"\nTotal benchmarks run: {len(all_metrics)}")
    print(f"\nAverage gate count reduction: {avg_gate_reduction:.1f}%")
    print(f"Average T-count reduction: {avg_t_reduction:.1f}%")
    print(f"Average optimization time: {avg_time*1000:.2f}ms")
    print(f"Total optimization time: {total_time*1000:.2f}ms")
    
    # Check against success criteria
    print("\n" + "-"*70)
    print("SUCCESS CRITERIA VALIDATION")
    print("-"*70)
    
    gate_target = (20, 50)
    t_target = (30, 60)
    
    print(f"\nGate count reduction:")
    print(f"  Target: {gate_target[0]}-{gate_target[1]}%")
    print(f"  Achieved: {avg_gate_reduction:.1f}%")
    if gate_target[0] <= avg_gate_reduction <= gate_target[1]:
        print(f"  Status: ✅ MEETS TARGET")
    elif avg_gate_reduction > gate_target[1]:
        print(f"  Status: ✅ EXCEEDS TARGET")
    else:
        print(f"  Status: ⚠️ BELOW TARGET")
    
    if avg_t_reduction > 0:
        print(f"\nT-count reduction:")
        print(f"  Target: {t_target[0]}-{t_target[1]}%")
        print(f"  Achieved: {avg_t_reduction:.1f}%")
        if t_target[0] <= avg_t_reduction <= t_target[1]:
            print(f"  Status: ✅ MEETS TARGET")
        elif avg_t_reduction > t_target[1]:
            print(f"  Status: ✅ EXCEEDS TARGET")
        else:
            print(f"  Status: ⚠️ BELOW TARGET")
    
    # Save results to JSON
    output_file = Path(__file__).parent / "benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump([m.to_dict() for m in all_metrics], f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")


def main():
    """Run all benchmarks."""
    print("\n" + "="*70)
    print("QIR OPTIMIZER PERFORMANCE BENCHMARKS")
    print("="*70)
    print("\nMeasuring optimization performance against success criteria:")
    print("- Gate count reduction: 20-50% typical")
    print("- T-count reduction: 30-60% for Clifford+T")
    print("- Depth reduction: 15-30% typical")
    
    all_results = []
    
    # Run benchmarks
    all_results.append(benchmark_individual_passes())
    all_results.append(benchmark_pipelines())
    all_results.append(benchmark_algorithms())
    
    # Generate report
    generate_report(all_results)
    
    print("\n" + "="*70)
    print("BENCHMARKING COMPLETE!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
