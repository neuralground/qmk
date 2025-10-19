"""
q_negotiate_caps syscall handler

Handles capability negotiation during session establishment.
"""

from typing import Dict


def handle_negotiate_caps(params: Dict, session_manager) -> Dict:
    """
    Handle q_negotiate_caps syscall.
    
    Args:
        params: Request parameters with:
            - requested: List of requested capabilities
            - tenant_id: Optional tenant identifier (defaults to "default")
        session_manager: SessionManager instance
    
    Returns:
        Dictionary with:
        - session_id: New session ID
        - granted: List of granted capabilities
        - denied: List of denied capabilities
        - quota: Resource quotas
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate parameters
    if "requested" not in params:
        raise ValueError("Missing 'requested' parameter")
    
    requested = params["requested"]
    
    if not isinstance(requested, list):
        raise ValueError("'requested' must be a list")
    
    # Get tenant ID (default to "default" for single-tenant mode)
    tenant_id = params.get("tenant_id", "default")
    
    # Negotiate capabilities
    result = session_manager.negotiate_capabilities(
        tenant_id=tenant_id,
        requested=requested
    )
    
    return result
