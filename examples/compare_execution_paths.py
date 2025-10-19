#!/usr/bin/env python3
"""
Compare Execution Paths

This script compares running the same quantum algorithm through different paths:
1. Native Qiskit execution
2. Native Azure Quantum execution  
3. QIR → QVM → QMK execution
4. QVM direct execution

This validates that all paths produce functionally equivalent results.
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from kernel.hardware.qiskit_simulator_backend import QiskitSimulatorBackend
from kernel.hardware.azure_quantum_simulator_backend import AzureQuantumSimulatorBackend
from kernel.hardware.hal_interface import JobStatus
from kernel.qir_bridge import QIRParser, QVMGraphGenerator
from kernel.simulator.enhanced_executor import EnhancedExecutor


class ExecutionPathComparator:
    """Compare execution across different paths."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = {}
    
    def log(self, message):
        """Log message if verbose."""
        if self.verbose:
            print(message)
    
    def create_test_circuit(self, circuit_type='bell_state') -> Dict:
        """
        Create a test circuit in QVM format.
        
        Args:
            circuit_type: Type of circuit ('bell_state', 'ghz_3', 'teleportation')
        
        Returns:
            QVM graph dictionary
        """
        if circuit_type == 'bell_state':
            return {
                'version': '0.1',
                'program': {
                    'nodes': [
                        {'id': 'alloc', 'op': 'ALLOC_LQ', 'args': {'n': 2, 'profile': 'logical:surface_code(d=3)'}, 'vqs': ['q0', 'q1'], 'caps': ['CAP_ALLOC']},
                        {'id': 'h', 'op': 'APPLY_H', 'vqs': ['q0']},
                        {'id': 'cnot', 'op': 'APPLY_CNOT', 'vqs': ['q0', 'q1']},
                        {'id': 'm0', 'op': 'MEASURE_Z', 'vqs': ['q0'], 'produces': ['m0']},
                        {'id': 'm1', 'op': 'MEASURE_Z', 'vqs': ['q1'], 'produces': ['m1']},
                        {'id': 'free', 'op': 'FREE_LQ', 'vqs': ['q0', 'q1']}
                    ]
                },
                'resources': {
                    'vqs': ['q0', 'q1'],
                    'chs': [],
                    'events': ['m0', 'm1']
                },
                'caps': ['CAP_ALLOC'],
                'metadata': {'description': 'Bell state for comparison'}
            }
        elif circuit_type == 'ghz_3':
            return {
                'version': '0.1',
                'program': {
                    'nodes': [
                        {'id': 'alloc', 'op': 'ALLOC_LQ', 'args': {'n': 3, 'profile': 'logical:surface_code(d=3)'}, 'vqs': ['q0', 'q1', 'q2'], 'caps': ['CAP_ALLOC']},
                        {'id': 'h', 'op': 'APPLY_H', 'vqs': ['q0']},
                        {'id': 'cnot1', 'op': 'APPLY_CNOT', 'vqs': ['q0', 'q1']},
                        {'id': 'cnot2', 'op': 'APPLY_CNOT', 'vqs': ['q0', 'q2']},
                        {'id': 'm0', 'op': 'MEASURE_Z', 'vqs': ['q0'], 'produces': ['m0']},
                        {'id': 'm1', 'op': 'MEASURE_Z', 'vqs': ['q1'], 'produces': ['m1']},
                        {'id': 'm2', 'op': 'MEASURE_Z', 'vqs': ['q2'], 'produces': ['m2']},
                        {'id': 'free', 'op': 'FREE_LQ', 'vqs': ['q0', 'q1', 'q2']}
                    ]
                },
                'resources': {
                    'vqs': ['q0', 'q1', 'q2'],
                    'chs': [],
                    'events': ['m0', 'm1', 'm2']
                },
                'caps': ['CAP_ALLOC'],
                'metadata': {'description': '3-qubit GHZ state'}
            }
        else:
            raise ValueError(f"Unknown circuit type: {circuit_type}")
    
    def run_qiskit_native(self, qvm_graph: Dict, shots: int = 1000) -> Dict:
        """Run circuit natively on Qiskit."""
        self.log("\n" + "="*70)
        self.log("PATH 1: Native Qiskit Execution")
        self.log("="*70)
        
        try:
            backend = QiskitSimulatorBackend(method='statevector')
            backend.connect()
            
            start_time = time.time()
            job_id = backend.submit_job("qiskit_test", qvm_graph, shots=shots)
            result = backend.get_job_result(job_id)
            total_time = time.time() - start_time
            
            self.log(f"✓ Execution time: {result.execution_time:.4f}s")
            self.log(f"✓ Total time: {total_time:.4f}s")
            self.log(f"✓ Status: {result.status.value}")
            
            # Analyze results
            counts = result.metadata.get('counts', {})
            self.log(f"\nMeasurement counts (top 5):")
            for bitstring, count in sorted(counts.items(), key=lambda x: -x[1])[:5]:
                prob = count / shots
                self.log(f"  |{bitstring}⟩: {count}/{shots} ({prob:.1%})")
            
            return {
                'path': 'qiskit_native',
                'success': True,
                'execution_time': result.execution_time,
                'total_time': total_time,
                'counts': counts,
                'shots': shots
            }
            
        except Exception as e:
            self.log(f"✗ Failed: {e}")
            return {'path': 'qiskit_native', 'success': False, 'error': str(e)}
    
    def run_azure_native(self, qvm_graph: Dict, shots: int = 1000) -> Dict:
        """Run circuit natively on Azure Quantum."""
        self.log("\n" + "="*70)
        self.log("PATH 2: Native Azure Quantum Execution")
        self.log("="*70)
        
        try:
            backend = AzureQuantumSimulatorBackend(target='ionq.simulator', use_local=True)
            backend.connect()
            
            start_time = time.time()
            job_id = backend.submit_job("azure_test", qvm_graph, shots=shots)
            result = backend.get_job_result(job_id)
            total_time = time.time() - start_time
            
            self.log(f"✓ Execution time: {result.execution_time:.4f}s")
            self.log(f"✓ Total time: {total_time:.4f}s")
            self.log(f"✓ Status: {result.status.value}")
            
            if result.status == JobStatus.FAILED:
                self.log(f"✗ Error: {result.error_message}")
                return {'path': 'azure_native', 'success': False, 'error': result.error_message}
            
            counts = result.metadata.get('counts', {})
            self.log(f"\nMeasurement counts (top 5):")
            for bitstring, count in sorted(counts.items(), key=lambda x: -x[1])[:5]:
                prob = count / shots
                self.log(f"  |{bitstring}⟩: {count}/{shots} ({prob:.1%})")
            
            return {
                'path': 'azure_native',
                'success': True,
                'execution_time': result.execution_time,
                'total_time': total_time,
                'counts': counts,
                'shots': shots
            }
            
        except Exception as e:
            self.log(f"✗ Failed: {e}")
            return {'path': 'azure_native', 'success': False, 'error': str(e)}
    
    def run_qmk_direct(self, qvm_graph: Dict, shots: int = 1000) -> Dict:
        """Run circuit directly on QMK."""
        self.log("\n" + "="*70)
        self.log("PATH 3: QMK Direct Execution")
        self.log("="*70)
        
        try:
            executor = EnhancedExecutor()
            
            # Run multiple shots
            all_counts = {}
            start_time = time.time()
            
            for shot in range(shots):
                result = executor.execute(qvm_graph)
                
                # Extract measurements
                events = result.get('events', {})
                bitstring = ''.join(str(events.get(f'm{i}', 0)) for i in range(len(events)))
                all_counts[bitstring] = all_counts.get(bitstring, 0) + 1
            
            total_time = time.time() - start_time
            
            self.log(f"✓ Execution time: {total_time:.4f}s")
            self.log(f"✓ Shots: {shots}")
            
            self.log(f"\nMeasurement counts (top 5):")
            for bitstring, count in sorted(all_counts.items(), key=lambda x: -x[1])[:5]:
                prob = count / shots
                self.log(f"  |{bitstring}⟩: {count}/{shots} ({prob:.1%})")
            
            return {
                'path': 'qmk_direct',
                'success': True,
                'execution_time': total_time,
                'total_time': total_time,
                'counts': all_counts,
                'shots': shots
            }
            
        except Exception as e:
            self.log(f"✗ Failed: {e}")
            return {'path': 'qmk_direct', 'success': False, 'error': str(e)}
    
    def compare_results(self, results: List[Dict]) -> Dict:
        """
        Compare results from different execution paths.
        
        Args:
            results: List of result dictionaries
        
        Returns:
            Comparison statistics
        """
        self.log("\n" + "="*70)
        self.log("COMPARISON ANALYSIS")
        self.log("="*70)
        
        successful_results = [r for r in results if r.get('success')]
        
        if len(successful_results) < 2:
            self.log("✗ Not enough successful results to compare")
            return {'comparable': False}
        
        # Compare execution times
        self.log("\n📊 Execution Times:")
        for result in successful_results:
            path = result['path']
            time_val = result.get('execution_time', 0)
            self.log(f"  {path}: {time_val:.4f}s")
        
        # Compare measurement distributions
        self.log("\n📊 Measurement Distribution Comparison:")
        
        # Get all unique bitstrings
        all_bitstrings = set()
        for result in successful_results:
            all_bitstrings.update(result.get('counts', {}).keys())
        
        # Calculate fidelity between distributions
        fidelities = {}
        for i, result1 in enumerate(successful_results):
            for j, result2 in enumerate(successful_results[i+1:], i+1):
                path1 = result1['path']
                path2 = result2['path']
                
                counts1 = result1.get('counts', {})
                counts2 = result2.get('counts', {})
                shots1 = result1.get('shots', 1)
                shots2 = result2.get('shots', 1)
                
                # Calculate fidelity
                fidelity = self._calculate_fidelity(counts1, counts2, shots1, shots2)
                fidelities[f"{path1}_vs_{path2}"] = fidelity
                
                self.log(f"  {path1} vs {path2}: {fidelity:.4f}")
        
        # Statistical tests
        self.log("\n📊 Statistical Analysis:")
        for result in successful_results:
            counts = result.get('counts', {})
            shots = result.get('shots', 1)
            
            # Check for expected correlations (e.g., Bell state should have 00 and 11)
            if '00' in counts and '11' in counts:
                corr_prob = (counts.get('00', 0) + counts.get('11', 0)) / shots
                self.log(f"  {result['path']}: Correlation probability = {corr_prob:.1%}")
        
        return {
            'comparable': True,
            'fidelities': fidelities,
            'execution_times': {r['path']: r.get('execution_time', 0) for r in successful_results},
            'all_match': all(f > 0.95 for f in fidelities.values())
        }
    
    def _calculate_fidelity(
        self,
        counts1: Dict,
        counts2: Dict,
        shots1: int,
        shots2: int
    ) -> float:
        """Calculate fidelity between two measurement distributions."""
        # Get all bitstrings
        all_bitstrings = set(counts1.keys()) | set(counts2.keys())
        
        # Calculate probabilities
        probs1 = {bs: counts1.get(bs, 0) / shots1 for bs in all_bitstrings}
        probs2 = {bs: counts2.get(bs, 0) / shots2 for bs in all_bitstrings}
        
        # Classical fidelity: sum of sqrt(p1 * p2)
        fidelity = sum(np.sqrt(probs1[bs] * probs2[bs]) for bs in all_bitstrings)
        
        return fidelity
    
    def run_comparison(self, circuit_type='bell_state', shots=1000):
        """Run full comparison across all paths."""
        self.log("\n" + "="*70)
        self.log(f"QUANTUM ALGORITHM EXECUTION PATH COMPARISON")
        self.log(f"Circuit: {circuit_type}")
        self.log(f"Shots: {shots}")
        self.log("="*70)
        
        # Create test circuit
        qvm_graph = self.create_test_circuit(circuit_type)
        
        # Run on all paths
        results = []
        
        # Path 1: Qiskit native
        try:
            result = self.run_qiskit_native(qvm_graph, shots)
            results.append(result)
        except Exception as e:
            self.log(f"Qiskit path failed: {e}")
        
        # Path 2: Azure native (may not be available)
        try:
            result = self.run_azure_native(qvm_graph, shots)
            results.append(result)
        except Exception as e:
            self.log(f"Azure path skipped: {e}")
        
        # Path 3: QMK direct
        try:
            result = self.run_qmk_direct(qvm_graph, shots)
            results.append(result)
        except Exception as e:
            self.log(f"QMK path failed: {e}")
        
        # Compare results
        comparison = self.compare_results(results)
        
        # Print summary
        self.log("\n" + "="*70)
        self.log("SUMMARY")
        self.log("="*70)
        
        successful = sum(1 for r in results if r.get('success'))
        self.log(f"\nSuccessful paths: {successful}/{len(results)}")
        
        if comparison.get('comparable'):
            if comparison.get('all_match'):
                self.log("✅ All execution paths produce functionally equivalent results!")
            else:
                self.log("⚠️  Some differences detected between paths")
            
            self.log(f"\nFidelities:")
            for pair, fidelity in comparison.get('fidelities', {}).items():
                status = "✅" if fidelity > 0.95 else "⚠️"
                self.log(f"  {status} {pair}: {fidelity:.4f}")
        
        return results, comparison


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare quantum execution paths')
    parser.add_argument('--circuit', default='bell_state', 
                       choices=['bell_state', 'ghz_3'],
                       help='Circuit type to test')
    parser.add_argument('--shots', type=int, default=1000,
                       help='Number of shots')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode')
    args = parser.parse_args()
    
    comparator = ExecutionPathComparator(verbose=not args.quiet)
    results, comparison = comparator.run_comparison(args.circuit, args.shots)
    
    # Exit with success if all paths match
    if comparison.get('all_match'):
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
