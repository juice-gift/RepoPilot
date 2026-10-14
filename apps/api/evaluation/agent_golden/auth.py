def verify_token(token: str) -> None:
    if token != "trusted":
        raise PermissionError("Invalid token")
