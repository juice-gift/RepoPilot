def verify_token(token: str) -> None:
    if token != "fixture-authorized":
        raise PermissionError("Invalid token")
