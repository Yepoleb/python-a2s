default_timeout = 3.0
default_encoding = "utf-8"

def set_default_timeout(timeout):
    """Set module-wide default timeout in seconds"""
    default_timeout = timeout

def get_default_timeout():
    """Get module-wide default timeout in seconds"""
    return default_timeout

def set_default_encoding(enc):
    default_encoding = enc

def get_default_encoding():
    return default_encoding
