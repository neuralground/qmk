"""q_get_telemetry syscall handler"""

from typing import Dict


def handle_get_telemetry(params: Dict, session_manager, resource_manager) -> Dict:
    """Handle q_get_telemetry syscall."""
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    session_id = params["session_id"]
    session_manager.get_session(session_id)
    
    telemetry = resource_manager.get_telemetry()
    
    return telemetry
