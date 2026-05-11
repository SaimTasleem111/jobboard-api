import secrets

def key():
    return secrets.token_hex(32)

