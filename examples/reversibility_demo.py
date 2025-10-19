#!/usr/bin/env python3
"""
Reversibility and Migration Demo

Demonstrates Phase 3 features:
- REV segment analysis
- Uncomputation (reversing operations)
- Checkpointing and rollback
- State migration
"""

from kernel.reversibility import (
    REVAnalyzer,
    UncomputationEngine,
    CheckpointManager,
    MigrationManager
)
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.qec_profiles import parse_profile_string


def demo_rev_segment_analysis():
    """Demonstrate REV segment identification."""
    print("="*60)
    print("Demo 1: REV Segment Analysis")
    print("="*60)
    print("\nIdentifying reversible segments in a quantum circuit...\n")
    
    # Create a circuit with multiple segments
    graph = {
        "nodes": [
            {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"]},
            
            # First REV segment: H, CNOT
            {"id": "h1", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
            {"id": "cnot1", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h1"]},
            
            # Measurement (boundary)
            {"id": "m1", "op": "MEASURE_Z", "qubits": ["q1"], 
             "outputs": ["m1"], "deps": ["cnot1"]},
            
            # Second REV segment: X, RZ, Y
            {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["m1"]},
            {"id": "rz", "op": "RZ", "qubits": ["q0"], 
             "params": {"theta": 1.57}, "deps": ["x"]},
            {"id": "y", "op": "Y", "qubits": ["q0"], "deps": ["rz"]},
            
            # Final measurement
            {"id": "m2", "op": "MEASURE_Z", "qubits": ["q0"], 
             "outputs": ["m2"], "deps": ["y"]},
            
            {"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], 
             "deps": ["m1", "m2"]}
        ],
        "edges": []
    }
    
    # Analyze segments
    analyzer = REVAnalyzer(graph)
    segments = analyzer.analyze()
    
    print(f"Total segments found: {len(segments)}")
    print(f"Reversible segments: {len(analyzer.get_reversible_segments())}\n")
    
    # Show each reversible segment
    for i, segment in enumerate(analyzer.get_reversible_segments(), 1):
        print(f"Segment {i}:")
        print(f"  Operations: {', '.join(segment.node_ids)}")
        print(f"  Length: {len(segment)} operations")
        print(f"  Qubits: {', '.join(segment.qubits_used)}")
        print(f"  Reversible: {segment.is_reversible}")
        print()
    
    # Get statistics
    stats = analyzer.get_segment_stats()
    print("Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ REV segment analysis complete!\n")
    return graph, analyzer


def demo_uncomputation(graph, analyzer):
    """Demonstrate uncomputation of REV segments."""
    print("="*60)
    print("Demo 2: Uncomputation (Reversing Operations)")
    print("="*60)
    print("\nGenerating inverse operations to reverse computation...\n")
    
    engine = UncomputationEngine()
    nodes = {node['id']: node for node in graph['nodes']}
    
    # Get first reversible segment
    rev_segments = analyzer.get_reversible_segments()
    if not rev_segments:
        print("No reversible segments found!")
        return
    
    segment = rev_segments[0]
    
    print(f"Original segment operations:")
    for node_id in segment.node_ids:
        node = nodes[node_id]
        print(f"  {node_id}: {node['op']}")
    
    # Generate inverse operations
    inverse_ops = engine.uncompute_segment(segment, nodes)
    
    print(f"\nInverse operations (in reverse order):")
    for inv_op in inverse_ops:
        orig_id = inv_op['original_node']
        print(f"  {inv_op['id']}: {inv_op['op']} (inverse of {orig_id})")
    
    # Get cost estimate
    cost = engine.get_uncomputation_cost(segment, nodes)
    print(f"\nUncomputation cost:")
    print(f"  Operations: {cost['num_operations']}")
    print(f"  Estimated time: {cost['estimated_time_units']} units")
    print(f"  Qubits affected: {cost['qubits_affected']}")
    
    # Verify correctness
    is_valid = engine.verify_uncomputation(segment, nodes)
    print(f"\nVerification: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    print("\n✅ Uncomputation demo complete!\n")


def demo_checkpointing():
    """Demonstrate checkpointing and rollback."""
    print("="*60)
    print("Demo 3: Checkpointing and Rollback")
    print("="*60)
    print("\nCreating quantum state checkpoints...\n")
    
    # Set up resources
    resource_mgr = EnhancedResourceManager()
    checkpoint_mgr = CheckpointManager(max_checkpoints=5)
    
    # Allocate qubits
    profile = parse_profile_string("logical:surface_code(d=3)")
    resource_mgr.alloc_logical_qubits(["q0", "q1"], profile)
    
    print("Allocated 2 qubits with Surface Code (d=3)")
    print(f"Physical qubits used: {resource_mgr.get_telemetry()['resource_usage']['physical_qubits_used']}\n")
    
    # Create checkpoint 1
    ckpt1 = checkpoint_mgr.create_checkpoint(
        job_id="demo_job",
        epoch=1,
        node_id="after_allocation",
        resource_manager=resource_mgr,
        metadata={"description": "Initial state"}
    )
    print(f"Checkpoint 1 created: {ckpt1.checkpoint_id}")
    print(f"  Qubits saved: {list(ckpt1.qubit_states.keys())}")
    
    # Simulate some operations (modify state)
    print("\nSimulating quantum operations...")
    
    # Create checkpoint 2
    ckpt2 = checkpoint_mgr.create_checkpoint(
        job_id="demo_job",
        epoch=5,
        node_id="after_gates",
        resource_manager=resource_mgr,
        metadata={"description": "After gate operations"}
    )
    print(f"\nCheckpoint 2 created: {ckpt2.checkpoint_id}")
    
    # List all checkpoints
    all_ckpts = checkpoint_mgr.list_checkpoints()
    print(f"\nTotal checkpoints: {len(all_ckpts)}")
    
    # Restore from checkpoint 1
    print(f"\nRestoring from checkpoint 1...")
    result = checkpoint_mgr.restore_checkpoint(ckpt1.checkpoint_id, resource_mgr)
    print(f"  Restored qubits: {result['qubits_restored']}")
    print(f"  Restored to epoch: {result['epoch']}")
    
    print("\n✅ Checkpointing demo complete!\n")


def demo_migration():
    """Demonstrate state migration."""
    print("="*60)
    print("Demo 4: State Migration at Fence Points")
    print("="*60)
    print("\nIdentifying migration points and migrating state...\n")
    
    # Set up managers
    checkpoint_mgr = CheckpointManager()
    migration_mgr = MigrationManager(checkpoint_mgr)
    resource_mgr = EnhancedResourceManager()
    
    # Create a circuit with fence points
    graph = {
        "nodes": [
            {"id": "alloc", "op": "ALLOC_LQ", "outputs": ["q0", "q1"]},
            {"id": "h", "op": "H", "qubits": ["q0"], "deps": ["alloc"]},
            {"id": "cnot", "op": "CNOT", "qubits": ["q0", "q1"], "deps": ["h"]},
            
            # Fence point (explicit migration point)
            {"id": "fence1", "op": "FENCE", "deps": ["cnot"]},
            
            {"id": "x", "op": "X", "qubits": ["q0"], "deps": ["fence1"]},
            {"id": "m", "op": "MEASURE_Z", "qubits": ["q0"], 
             "outputs": ["m0"], "deps": ["x"]},
            {"id": "free", "op": "FREE_LQ", "qubits": ["q0", "q1"], "deps": ["m"]}
        ],
        "edges": []
    }
    
    # Identify migration points
    migration_points = migration_mgr.identify_migration_points(graph)
    
    print(f"Migration points found: {len(migration_points)}\n")
    
    for i, point in enumerate(migration_points, 1):
        print(f"Point {i}: {point.node_id}")
        print(f"  Is fence: {point.is_fence}")
        print(f"  Can migrate: {point.can_migrate}")
        print(f"  Live qubits: {len(point.qubits_live)}")
        if point.reason:
            print(f"  Reason: {point.reason}")
        print()
    
    # Simulate migration at fence point
    fence_point = [p for p in migration_points if p.is_fence][0]
    
    # Allocate qubits for migration
    profile = parse_profile_string("logical:surface_code(d=3)")
    resource_mgr.alloc_logical_qubits(["q0", "q1"], profile)
    
    print(f"Initiating migration at {fence_point.node_id}...")
    migration_record = migration_mgr.initiate_migration(
        job_id="demo_job",
        migration_point=fence_point,
        from_context="local_simulator",
        to_context="remote_cluster",
        resource_manager=resource_mgr
    )
    
    print(f"  Migration ID: {migration_record.migration_id}")
    print(f"  From: {migration_record.from_context}")
    print(f"  To: {migration_record.to_context}")
    print(f"  Checkpoint: {migration_record.checkpoint_id}")
    
    # Complete migration
    print(f"\nCompleting migration...")
    migration_mgr.complete_migration(
        migration_record.migration_id,
        resource_mgr,
        success=True
    )
    
    # Validate migration
    is_valid, error = migration_mgr.validate_migration(migration_record.migration_id)
    print(f"  Validation: {'✅ Valid' if is_valid else f'❌ Invalid: {error}'}")
    
    # Get migration stats
    stats = migration_mgr.get_migration_stats()
    print(f"\nMigration statistics:")
    print(f"  Total migrations: {stats['total_migrations']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    
    print("\n✅ Migration demo complete!\n")


def main():
    """Run all reversibility demos."""
    print("\n" + "="*60)
    print("QMK Reversibility & Migration Demo")
    print("Phase 3 Features")
    print("="*60 + "\n")
    
    # Demo 1: REV segment analysis
    graph, analyzer = demo_rev_segment_analysis()
    
    # Demo 2: Uncomputation
    demo_uncomputation(graph, analyzer)
    
    # Demo 3: Checkpointing
    demo_checkpointing()
    
    # Demo 4: Migration
    demo_migration()
    
    # Summary
    print("="*60)
    print("Summary")
    print("="*60)
    print("""
Phase 3 features demonstrated:

1. REV Segment Analysis
   - Automatic identification of reversible segments
   - Segment statistics and validation
   
2. Uncomputation
   - Inverse operation generation
   - Cost estimation
   - Verification of correctness

3. Checkpointing
   - State snapshots at any point
   - Rollback capability
   - Multiple checkpoint management

4. State Migration
   - Migration point identification
   - Fence-based migration
   - Validation and statistics

These features enable:
- Fault tolerance through rollback
- Resource migration for load balancing
- Energy-efficient ancilla cleanup
- Flexible execution strategies
""")
    
    print("✅ All demos completed successfully!\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
