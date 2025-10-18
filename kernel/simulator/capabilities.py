DEFAULT_CAPS = {
    "CAP_ALLOC": True,
    "CAP_LINK": False,
    "CAP_TELEPORT": False,
    "CAP_MAGIC": False,
}

def has_caps(required, granted):
    return all(granted.get(c, False) for c in required)
