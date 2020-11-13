import requests


class AuthenticationException(Exception):
    """Thrown when we have issues authenticating"""

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class HexArcException(Exception):
    """Thrown when the server gets mad at us"""

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


if __name__ == "__main__":
    requests.post("http://anacreon.kronosaur.com/api/getObjects", data={}).json()
