MAX_ATTEMPTS = 3

def verify_token(token):
    return token

class Auth:
    def check(self, token):
        return verify_token(token)
