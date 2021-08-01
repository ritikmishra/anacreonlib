class AuthenticationException(Exception):
    """Thrown when we have issues authenticating"""

    pass


class HexArcException(Exception):
    """Thrown when we try to make a request that violates some invariant of Anacreon

    For example,
        - You cannot sell resources that you don't have
        - You cannot designate a world that doesn't belong to you
    and so on.
    """

    pass
