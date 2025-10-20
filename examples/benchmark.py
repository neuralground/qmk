#!/usr/bin/env python3
"""
QMK Performance Benchmark

Measures throughput and latency of the QMK system.
"""

import time
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient


def create_simple_circuit(n_qubits: int) -> dict:
    """Create a simple circuit for benchmarking."""
    qubit_ids = [f"q{i}" for i in range(n_qubits)]
    
    nodes = [
        {
            "id": "alloc",
            "op": "ALLOC_LQ",
            "outputs": qubit_ids,
            "profile": "logical:surface_code(d=3)"
        }
    ]
    
    # Add some gates
    for i in range(n_qubits):
        nodes.append({
            "id": f"h{i}",
            "op": "H",
            "qubits": [f"q{i}"],
            "deps": ["alloc"]
        })
    
    # Add measurements
    measure_deps = []
    for i in range(n_qubits):
        nodes.append({
            "id": f"m{i}",
            "op": "MEASURE_Z",
            "qubits": [f"q{i}"],
            "outputs": [f"m{i}"],
            "deps": [f"h{i}"]
        })
        measure_deps.append(f"m{i}")
    
    # Free qubits
    nodes.append({
        "id": "free",
        "op": "FREE_LQ",
        "qubits": qubit_ids,
        "deps": measure_deps
    })
    
    return {
        "version": "0.1",
        "metadata": {"name": f"benchmark_{n_qubits}q"},
        "nodes": nodes,
        "edges": []
    }


def benchmark_submission_latency(client: QSyscallClient, n_iterations: int = 100):
    """Benchmark job submission latency."""
    print(f"\n{'='*60}")
    print("Benchmark 1: Job Submission Latency")
    print(f"{'='*60}")
    print(f"Iterations: {n_iterations}")
    
    graph = create_simple_circuit(2)
    latencies = []
    
    for i in range(n_iterations):
        start = time.time()
        job_id = client.submit_job(graph, seed=i)
        end = time.time()
        latencies.append((end - start) * 1000)  # Convert to ms
        
        # Cancel immediately to avoid queue buildup
        try:
            client.cancel_job(job_id)
        except:
            pass
    
    print(f"\nResults:")
    print(f"  Mean latency: {statistics.mean(latencies):.2f} ms")
    print(f"  Median latency: {statistics.median(latencies):.2f} ms")
    print(f"  Min latency: {min(latencies):.2f} ms")
    print(f"  Max latency: {max(latencies):.2f} ms")
    print(f"  Std dev: {statistics.stdev(latencies):.2f} ms")
    
    return latencies


def benchmark_end_to_end(client: QSyscallClient, n_iterations: int = 20):
    """Benchmark end-to-end job execution."""
    print(f"\n{'='*60}")
    print("Benchmark 2: End-to-End Execution Time")
    print(f"{'='*60}")
    print(f"Iterations: {n_iterations}")
    
    graph = create_simple_circuit(2)
    times = []
    
    for i in range(n_iterations):
        start = time.time()
        result = client.submit_and_wait(graph, timeout_ms=10000, seed=i)
        end = time.time()
        
        if result['state'] == 'COMPLETED':
            times.append((end - start) * 1000)  # Convert to ms
        else:
            print(f"  ⚠ Iteration {i+1} failed")
    
    if times:
        print(f"\nResults:")
        print(f"  Mean time: {statistics.mean(times):.2f} ms")
        print(f"  Median time: {statistics.median(times):.2f} ms")
        print(f"  Min time: {min(times):.2f} ms")
        print(f"  Max time: {max(times):.2f} ms")
        print(f"  Throughput: {1000 / statistics.mean(times):.2f} jobs/sec")
    
    return times


def benchmark_scaling(client: QSyscallClient):
    """Benchmark scaling with number of qubits."""
    print(f"\n{'='*60}")
    print("Benchmark 3: Scaling with Qubit Count")
    print(f"{'='*60}")
    
    qubit_counts = [2, 4, 6, 8, 10]
    results = []
    
    for n_qubits in qubit_counts:
        print(f"\nTesting with {n_qubits} qubits...")
        graph = create_simple_circuit(n_qubits)
        
        times = []
        for i in range(5):
            start = time.time()
            result = client.submit_and_wait(graph, timeout_ms=15000, seed=i)
            end = time.time()
            
            if result['state'] == 'COMPLETED':
                times.append((end - start) * 1000)
        
        if times:
            mean_time = statistics.mean(times)
            results.append((n_qubits, mean_time))
            print(f"  Mean time: {mean_time:.2f} ms")
    
    print(f"\n{'='*60}")
    print("Scaling Summary")
    print(f"{'='*60}")
    print(f"{'Qubits':<10} {'Time (ms)':<15} {'Relative':<10}")
    print(f"{'-'*35}")
    
    baseline = results[0][1] if results else 1.0
    for n_qubits, time_ms in results:
        relative = time_ms / baseline
        print(f"{n_qubits:<10} {time_ms:<15.2f} {relative:<10.2f}x")
    
    return results


def benchmark_concurrent_jobs(client: QSyscallClient, n_jobs: int = 5):
    """Benchmark concurrent job submission."""
    print(f"\n{'='*60}")
    print("Benchmark 4: Concurrent Job Execution")
    print(f"{'='*60}")
    print(f"Submitting {n_jobs} jobs concurrently...")
    
    graph = create_simple_circuit(2)
    
    # Submit all jobs
    start = time.time()
    job_ids = []
    for i in range(n_jobs):
        job_id = client.submit_job(graph, seed=i)
        job_ids.append(job_id)
    submission_time = time.time() - start
    
    print(f"  Submission time: {submission_time*1000:.2f} ms")
    print(f"  Submission rate: {n_jobs/submission_time:.2f} jobs/sec")
    
    # Wait for all to complete
    print(f"\nWaiting for completion...")
    start = time.time()
    completed = 0
    failed = 0
    
    for job_id in job_ids:
        try:
            result = client.wait_for_job(job_id, timeout_ms=10000)
            if result['state'] == 'COMPLETED':
                completed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  ⚠ Job {job_id} failed: {e}")
    
    total_time = time.time() - start
    
    print(f"\nResults:")
    print(f"  Completed: {completed}/{n_jobs}")
    print(f"  Failed: {failed}/{n_jobs}")
    print(f"  Total time: {total_time*1000:.2f} ms")
    print(f"  Throughput: {completed/total_time:.2f} jobs/sec")
    
    return completed, failed, total_time


def main():
    """Run all benchmarks."""
    print("="*60)
    print("QMK Performance Benchmark Suite")
    print("="*60)
    
    # Create client
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    print("\nNegotiating capabilities...")
    caps_result = client.negotiate_capabilities(["CAP_ALLOC"])
    print(f"Session ID: {caps_result['session_id']}")
    
    # Run benchmarks
    try:
        benchmark_submission_latency(client, n_iterations=100)
        benchmark_end_to_end(client, n_iterations=20)
        benchmark_scaling(client)
        benchmark_concurrent_jobs(client, n_jobs=5)
        
        # Final summary
        print(f"\n{'='*60}")
        print("Benchmark Complete")
        print(f"{'='*60}")
        
        telemetry = client.get_telemetry()
        usage = telemetry['resource_usage']
        print(f"\nFinal Resource Usage:")
        print(f"  Logical qubits: {usage['logical_qubits_allocated']}")
        print(f"  Physical qubits: {usage['physical_qubits_used']}")
        print(f"  Utilization: {usage['utilization']:.1%}")
        
        print("\n✅ All benchmarks completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except ConnectionRefusedError:
        print("❌ Error: QMK server not running")
        print("   Start with: python -m kernel.qmk_server")
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
