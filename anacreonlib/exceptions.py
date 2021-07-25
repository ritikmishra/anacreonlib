from typing import Any


class AuthenticationException(Exception):
    """Thrown when we have issues authenticating"""
    pass

class HexArcException(Exception):
    """Thrown when the server gets mad at us"""
    pass
