__all__ = ("A2SProtocol",)


from typing import Any, Optional

from .byteio import ByteReader


class A2SProtocol:
    @staticmethod
    def serialize_request(challenge: int) -> bytes:
        raise NotImplementedError()

    @staticmethod
    def validate_response_type(response_type: int) -> bool:
        raise NotImplementedError()

    @staticmethod
    def deserialize_response(
        reader: ByteReader, response_type: int, ping: Optional[float]
    ) -> Any:
        raise NotImplementedError()
