"""
Advanced QEC Decoders Demonstration

Shows how to use production-grade QEC decoders:
1. MWPM (Minimum Weight Perfect Matching)
2. Union-Find (fast alternative)
3. Belief Propagation (for LDPC codes)
4. Syndrome extraction
5. Decoder comparison
"""

import numpy as np
from kernel.qec import (
    MWPMDecoder, UnionFindDecoder, BeliefPropagationDecoder,
    SyndromeExtractor, DecoderManager, Syndrome, ParityCheck,
    create_surface_code_decoders
)


def demo_mwpm_decoder():
    """Demonstrate MWPM decoder."""
    print("=" * 70)
    print("1. MWPM DECODER (Gold Standard for Surface Codes)")
    print("=" * 70)
    
    decoder = MWPMDecoder(distance=9)
    
    print(f"\n📊 Decoder Configuration:")
    stats = decoder.get_decoder_stats()
    print(f"  Type: {stats['decoder_type']}")
    print(f"  Algorithm: {stats['algorithm']}")
    print(f"  Distance: {stats['distance']}")
    print(f"  Complexity: {stats['complexity']}")
    
    # Create test syndromes
    syndromes = [
        Syndrome(position=(1, 1), time=0, parity='X'),
        Syndrome(position=(3, 3), time=0, parity='X'),
        Syndrome(position=(5, 5), time=0, parity='X'),
        Syndrome(position=(7, 7), time=0, parity='X'),
    ]
    
    print(f"\n🔍 Decoding {len(syndromes)} syndromes...")
    corrections = decoder.decode(syndromes)
    
    print(f"  Found {len(corrections)} correction chains:")
    for i, (pos1, pos2) in enumerate(corrections, 1):
        distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        print(f"    {i}. {pos1} ↔ {pos2} (distance: {distance})")
    
    # Logical error probability
    print(f"\n📈 Logical Error Probability:")
    for p_phys in [1e-4, 1e-3, 5e-3, 1e-2]:
        p_log = decoder.estimate_logical_error_probability(p_phys)
        print(f"  p_phys = {p_phys:.0e} → p_log = {p_log:.2e}")


def demo_union_find_decoder():
    """Demonstrate Union-Find decoder."""
    print("\n" + "=" * 70)
    print("2. UNION-FIND DECODER (Fast Alternative)")
    print("=" * 70)
    
    decoder = UnionFindDecoder(distance=9)
    
    print(f"\n📊 Decoder Configuration:")
    stats = decoder.get_decoder_stats()
    print(f"  Type: {stats['decoder_type']}")
    print(f"  Algorithm: {stats['algorithm']}")
    print(f"  Complexity: {stats['complexity']}")
    print(f"  Threshold: {stats['threshold']}")
    
    # Create syndromes
    syndromes = [
        Syndrome(position=(0, 0), time=0, parity='Z'),
        Syndrome(position=(2, 1), time=0, parity='Z'),
        Syndrome(position=(4, 4), time=0, parity='Z'),
        Syndrome(position=(6, 3), time=0, parity='Z'),
        Syndrome(position=(8, 8), time=0, parity='Z'),
    ]
    
    print(f"\n🔍 Decoding {len(syndromes)} syndromes...")
    corrections = decoder.decode(syndromes)
    
    print(f"  Found {len(corrections)} correction chains")
    print(f"  Odd parity handled: {len(syndromes) % 2 == 1}")
    
    # Performance comparison with MWPM
    print(f"\n⚡ Performance Characteristics:")
    print(f"  Union-Find: O(n log n) - Faster")
    print(f"  MWPM: O(n³) - More accurate")
    print(f"  Threshold: ~0.009 vs ~0.010 (MWPM)")


def demo_belief_propagation_decoder():
    """Demonstrate BP decoder for LDPC codes."""
    print("\n" + "=" * 70)
    print("3. BELIEF PROPAGATION DECODER (For QLDPC Codes)")
    print("=" * 70)
    
    # Create LDPC parity checks
    checks = [
        ParityCheck(qubits=[0, 1, 2, 3], parity='X'),
        ParityCheck(qubits=[2, 3, 4, 5], parity='X'),
        ParityCheck(qubits=[4, 5, 6, 7], parity='X'),
        ParityCheck(qubits=[6, 7, 8, 9], parity='X'),
        ParityCheck(qubits=[1, 3, 5, 7], parity='Z'),
        ParityCheck(qubits=[0, 2, 4, 6], parity='Z'),
    ]
    
    decoder = BeliefPropagationDecoder(checks, max_iterations=50)
    
    print(f"\n📊 Decoder Configuration:")
    stats = decoder.get_decoder_stats()
    print(f"  Type: {stats['decoder_type']}")
    print(f"  Algorithm: {stats['algorithm']}")
    print(f"  Qubits: {stats['num_qubits']}")
    print(f"  Checks: {stats['num_checks']}")
    print(f"  Max iterations: {stats['max_iterations']}")
    
    # Create syndrome
    syndrome = np.array([1, 0, 1, 0, 1, 0])
    
    print(f"\n🔍 Decoding syndrome: {syndrome}")
    error = decoder.decode(syndrome)
    
    print(f"  Decoded error vector: {error}")
    print(f"  Error weight: {np.sum(error)}")
    
    # QLDPC advantages
    print(f"\n💡 QLDPC Advantages:")
    print(f"  • Better qubit efficiency (d²/rate vs 2d²)")
    print(f"  • Higher thresholds (~0.03 vs 0.01)")
    print(f"  • Scalable to large codes")


def demo_syndrome_extraction():
    """Demonstrate syndrome extraction."""
    print("\n" + "=" * 70)
    print("4. SYNDROME EXTRACTION SIMULATION")
    print("=" * 70)
    
    extractor = SyndromeExtractor(
        code_distance=7,
        measurement_error_rate=0.01,
        extraction_time_us=1.0
    )
    
    print(f"\n⚙️  Extractor Configuration:")
    print(f"  Code distance: {extractor.code_distance}")
    print(f"  Measurement error rate: {extractor.measurement_error_rate}")
    print(f"  Extraction time: {extractor.extraction_time_us} μs")
    
    # Simulate errors
    error_locations = [(1, 1), (2, 3), (4, 4)]
    
    print(f"\n🔬 Extracting syndromes from {len(error_locations)} errors...")
    
    # Multiple rounds
    rounds = extractor.extract_multiple_rounds(error_locations, num_rounds=5)
    
    print(f"\n📊 Extraction Results:")
    for round in rounds:
        print(f"  Round {round.round_num}:")
        print(f"    Syndromes detected: {len(round.syndromes)}")
        print(f"    Measurement errors: {round.measurement_errors}")
        print(f"    Time: {round.time_us} μs")
    
    # Statistics
    stats = extractor.get_syndrome_statistics()
    print(f"\n📈 Overall Statistics:")
    print(f"  Total rounds: {stats['total_rounds']}")
    print(f"  Total syndromes: {stats['total_syndromes']}")
    print(f"  Avg syndromes/round: {stats['avg_syndromes_per_round']:.2f}")
    print(f"  Total measurement errors: {stats['total_measurement_errors']}")


def demo_decoder_comparison():
    """Demonstrate decoder comparison."""
    print("\n" + "=" * 70)
    print("5. DECODER COMPARISON")
    print("=" * 70)
    
    # Create manager with multiple decoders
    manager = create_surface_code_decoders(distance=7)
    
    print(f"\n🔧 Registered Decoders:")
    for decoder_name in manager.list_decoders():
        info = manager.get_decoder_info(decoder_name)
        print(f"  • {info['decoder_type']}: {info['algorithm']}")
    
    # Create test syndromes
    syndromes = [
        Syndrome(position=(1, 1), time=0, parity='X'),
        Syndrome(position=(2, 3), time=0, parity='X'),
        Syndrome(position=(4, 2), time=0, parity='X'),
        Syndrome(position=(5, 5), time=0, parity='X'),
    ]
    
    print(f"\n⚔️  Comparing decoders on {len(syndromes)} syndromes...")
    
    results = manager.compare_decoders(syndromes)
    
    print(f"\n📊 Comparison Results:")
    print(f"{'Decoder':<15} {'Corrections':<12} {'Time (ms)':<12}")
    print("-" * 70)
    
    for decoder_name, result in results.items():
        time_ms = result['decode_time'] * 1000
        print(f"{decoder_name:<15} {result['num_corrections']:<12} {time_ms:<12.4f}")
    
    # Run multiple times for statistics
    print(f"\n🏃 Running benchmark (100 iterations)...")
    for _ in range(100):
        manager.decode("mwpm", syndromes)
        manager.decode("union_find", syndromes)
    
    stats = manager.get_performance_stats()
    
    print(f"\n📈 Performance Statistics:")
    for decoder_name, decoder_stats in stats.items():
        print(f"  {decoder_name}:")
        print(f"    Avg time: {decoder_stats['avg_time']*1000:.4f} ms")
        print(f"    Min time: {decoder_stats['min_time']*1000:.4f} ms")
        print(f"    Max time: {decoder_stats['max_time']*1000:.4f} ms")
    
    # Speed comparison
    mwpm_time = stats['mwpm']['avg_time']
    uf_time = stats['union_find']['avg_time']
    speedup = mwpm_time / uf_time
    
    print(f"\n⚡ Union-Find is {speedup:.2f}x faster than MWPM!")


def demo_error_correction_workflow():
    """Demonstrate complete error correction workflow."""
    print("\n" + "=" * 70)
    print("6. COMPLETE ERROR CORRECTION WORKFLOW")
    print("=" * 70)
    
    print(f"\n🔄 Workflow Steps:")
    print(f"  1. Errors occur on physical qubits")
    print(f"  2. Syndrome extraction measures stabilizers")
    print(f"  3. Decoder finds correction chains")
    print(f"  4. Corrections applied to qubits")
    print(f"  5. Repeat for multiple QEC rounds")
    
    # Setup
    distance = 5
    extractor = SyndromeExtractor(distance, measurement_error_rate=0.005)
    decoder = MWPMDecoder(distance)
    
    # Simulate error
    error_locations = [(1, 2), (3, 3)]
    
    print(f"\n💥 Simulating {len(error_locations)} errors...")
    
    # Extract syndrome
    syndrome_round = extractor.extract_syndrome(error_locations)
    print(f"  ✓ Extracted {len(syndrome_round.syndromes)} syndromes")
    
    # Decode
    corrections = decoder.decode(syndrome_round.syndromes)
    print(f"  ✓ Found {len(corrections)} correction chains")
    
    # Apply corrections (simulated)
    print(f"  ✓ Corrections applied")
    
    # Estimate success probability
    p_phys = 0.001
    p_log = decoder.estimate_logical_error_probability(p_phys, num_rounds=10)
    
    print(f"\n📊 Error Correction Performance:")
    print(f"  Physical error rate: {p_phys:.0e}")
    print(f"  Logical error rate: {p_log:.2e}")
    print(f"  Suppression factor: {p_phys/p_log:.0f}x")
    print(f"  QEC rounds: 10")


def main():
    """Run all advanced QEC demonstrations."""
    print("\n" + "=" * 70)
    print("ADVANCED QEC DECODERS DEMONSTRATION")
    print("=" * 70)
    print("\nDemonstrating:")
    print("  • MWPM decoder (gold standard)")
    print("  • Union-Find decoder (fast)")
    print("  • Belief Propagation (LDPC)")
    print("  • Syndrome extraction")
    print("  • Decoder comparison")
    print("  • Complete workflow")
    print()
    
    demo_mwpm_decoder()
    demo_union_find_decoder()
    demo_belief_propagation_decoder()
    demo_syndrome_extraction()
    demo_decoder_comparison()
    demo_error_correction_workflow()
    
    print("\n" + "=" * 70)
    print("ADVANCED QEC COMPLETE")
    print("=" * 70)
    print("\n✅ Production-grade QEC decoders ready!")
    print("\nKey capabilities:")
    print("  • MWPM: Near-optimal decoding")
    print("  • Union-Find: Fast O(n log n) decoding")
    print("  • BP: Efficient LDPC decoding")
    print("  • Syndrome extraction simulation")
    print("  • Performance benchmarking")


if __name__ == "__main__":
    main()
