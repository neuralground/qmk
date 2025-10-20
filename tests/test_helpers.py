"""
Test Helper Utilities

Common utilities for QMK tests.
"""

# Standard test capabilities - all enabled for integration testing
TEST_CAPABILITIES = {
    "CAP_ALLOC": True,
    "CAP_COMPUTE": True,
    "CAP_MEASURE": True,
    "CAP_TELEPORT": True,
    "CAP_MAGIC": True,
    "CAP_LINK": True,
    "CAP_CHECKPOINT": True,
    "CAP_DEBUG": True
}


def create_test_executor(**kwargs):
    """
    Create an EnhancedExecutor with test capabilities.
    
    This helper ensures all tests use executors with proper capabilities,
    benefiting from automatic resource lifecycle management.
    
    Args:
        **kwargs: Additional arguments to pass to EnhancedExecutor
                 (e.g., seed, max_physical_qubits)
    
    Returns:
        EnhancedExecutor configured for testing
    
    Example:
        executor = create_test_executor(seed=42)
        result = executor.execute(qvm_graph)
    """
    from kernel.executor.enhanced_executor import EnhancedExecutor
    
    # Merge test capabilities with any user-provided caps
    caps = TEST_CAPABILITIES.copy()
    if 'caps' in kwargs:
        caps.update(kwargs['caps'])
        del kwargs['caps']
    
    return EnhancedExecutor(caps=caps, **kwargs)
