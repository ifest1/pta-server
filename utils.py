import base64

def decode64(data):
    return base64.b64decode(data)

def encode64(data):
    return base64.b64encode(data)