"""
q_status syscall handler

Handles job status queries.
"""

from typing import Dict


def handle_status(params: Dict, session_manager, job_manager) -> Dict:
    """
    Handle q_status syscall.
    
    Args:
        params: Request parameters with:
            - job_id: Job identifier
            - session_id: Session identifier
        session_manager: SessionManager instance
        job_manager: JobManager instance
    
    Returns:
        Dictionary with job status including:
        - job_id: Job identifier
        - state: Current job state
        - progress: Execution progress
        - events: Measurement events (if completed)
        - telemetry: Execution telemetry (if completed)
        - error: Error information (if failed)
    
    Raises:
        ValueError: If parameters are invalid
        KeyError: If job or session not found
        PermissionError: If job belongs to different session
    """
    # Validate parameters
    if "job_id" not in params:
        raise ValueError("Missing 'job_id' parameter")
    
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    job_id = params["job_id"]
    session_id = params["session_id"]
    
    # Validate session exists
    session_manager.get_session(session_id)
    
    # Get job status
    status = job_manager.get_job_status(job_id, session_id)
    
    return status
