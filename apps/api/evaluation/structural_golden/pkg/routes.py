from .service import verify_token as verify
import pkg.service as service

def check(token):
    return verify(token)

def duplicate():
    return 1

def duplicate():
    return 2

check("demo")
service.verify_token("demo")
duplicate()
missing()

def shadow(verify):
    return verify("demo")
