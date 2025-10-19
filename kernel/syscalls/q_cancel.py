"""q_cancel syscall handler"""

from typing import Dict


def handle_cancel(params: Dict, session_manager, job_manager) -> Dict:
    """Handle q_cancel syscall."""
    if "job_id" not in params:
        raise ValueError("Missing 'job_id' parameter")
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    job_id = params["job_id"]
    session_id = params["session_id"]
    
    session_manager.get_session(session_id)
    result = job_manager.cancel_job(job_id, session_id)
    
    return result
