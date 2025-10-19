"""q_wait syscall handler"""

from typing import Dict


def handle_wait(params: Dict, session_manager, job_manager) -> Dict:
    """Handle q_wait syscall."""
    if "job_id" not in params:
        raise ValueError("Missing 'job_id' parameter")
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    job_id = params["job_id"]
    session_id = params["session_id"]
    timeout_ms = params.get("timeout_ms")
    
    session_manager.get_session(session_id)
    status = job_manager.wait_for_job(job_id, session_id, timeout_ms)
    
    return status
