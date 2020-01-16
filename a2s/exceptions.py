class BrokenMessageError(Exception):
    pass

class BufferExhaustedError(BrokenMessageError):
    pass
