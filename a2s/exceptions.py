__all__ = (
    "BrokenMessageError",
    "BufferExhaustedError",
)


class BrokenMessageError(Exception):
    pass


class BufferExhaustedError(BrokenMessageError):
    pass
