"""
q_submit syscall handler

Handles QVM graph submission for execution.
"""

from typing import Dict


def handle_submit(params: Dict, session_manager, job_manager) -> Dict:
    """
    Handle q_submit syscall.
    
    Args:
        params: Request parameters with:
            - graph: QVM graph to execute
            - session_id: Session identifier
            - policy: Optional execution policy
        session_manager: SessionManager instance
        job_manager: JobManager instance
    
    Returns:
        Dictionary with:
        - job_id: New job identifier
        - state: Initial job state
        - estimated_epochs: Estimated execution time
    
    Raises:
        ValueError: If parameters are invalid
        KeyError: If session not found
        RuntimeError: If quota exceeded or capabilities missing
    """
    # Validate parameters
    if "graph" not in params:
        raise ValueError("Missing 'graph' parameter")
    
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    graph = params["graph"]
    session_id = params["session_id"]
    policy = params.get("policy")
    
    # Validate graph structure
    if not isinstance(graph, dict):
        raise ValueError("'graph' must be a dictionary")
    
    if "nodes" not in graph or "edges" not in graph:
        raise ValueError("Graph must have 'nodes' and 'edges'")
    
    # Validate session
    session = session_manager.get_session(session_id)
    
    # Check capabilities based on graph operations
    required_caps = _extract_required_capabilities(graph)
    
    if required_caps:
        cap_check = session_manager.check_capabilities(session_id, required_caps)
        
        if not cap_check["has_all"]:
            raise RuntimeError(
                f"Insufficient capabilities. Missing: {cap_check['missing']}"
            )
    
    # Register job with session
    result = job_manager.submit_job(
        session_id=session_id,
        graph=graph,
        policy=policy
    )
    
    job_id = result["job_id"]
    
    # Track job in session
    session_manager.register_job(session_id, job_id)
    
    return result


def _extract_required_capabilities(graph: Dict) -> list:
    """
    Extract required capabilities from graph operations.
    
    Args:
        graph: QVM graph
    
    Returns:
        List of required capabilities
    """
    required = set()
    
    for node in graph.get("nodes", []):
        op = node.get("op", "")
        
        # Allocation operations
        if op in ["ALLOC_LQ", "ALLOC"]:
            required.add("CAP_ALLOC")
        
        # Teleportation operations
        elif op in ["TELEPORT_SEND", "TELEPORT_RECV"]:
            required.add("CAP_TELEPORT")
        
        # Magic state operations
        elif op in ["MAGIC_T", "MAGIC_CCZ"]:
            required.add("CAP_MAGIC")
        
        # Channel operations
        elif op in ["LINK"]:
            required.add("CAP_LINK")
    
    return list(required)
