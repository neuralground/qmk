"""q_open_chan syscall handler"""

from typing import Dict


def handle_open_chan(params: Dict, session_manager, resource_manager) -> Dict:
    """Handle q_open_chan syscall."""
    if "vq_a" not in params:
        raise ValueError("Missing 'vq_a' parameter")
    if "vq_b" not in params:
        raise ValueError("Missing 'vq_b' parameter")
    if "session_id" not in params:
        raise ValueError("Missing 'session_id' parameter")
    
    vq_a = params["vq_a"]
    vq_b = params["vq_b"]
    session_id = params["session_id"]
    options = params.get("options", {})
    
    session = session_manager.get_session(session_id)
    
    if not session.has_capability("CAP_LINK"):
        raise RuntimeError("Missing capability: CAP_LINK")
    
    fidelity = options.get("fidelity", 0.99)
    channel_id = f"ch_{vq_a}_{vq_b}"
    
    resource_manager.open_channel(channel_id, vq_a, vq_b, fidelity)
    session_manager.register_channel(session_id, channel_id)
    
    return {
        "channel_id": channel_id,
        "actual_fidelity": fidelity,
        "purification_rounds": 0
    }
