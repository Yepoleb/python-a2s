from typing import Dict, Optional, Tuple

from a2s.a2s_async import request_async
from a2s.a2s_sync import request_sync
from a2s.byteio import ByteReader
from a2s.defaults import DEFAULT_ENCODING, DEFAULT_TIMEOUT

A2S_RULES_RESPONSE = 0x45


def rules(address: Tuple[str, int], timeout: float = DEFAULT_TIMEOUT, encoding: str = DEFAULT_ENCODING) -> Dict[str, str]:
    return request_sync(address, timeout, encoding, RulesProtocol)


async def arules(
    address: Tuple[str, int], timeout: float = DEFAULT_TIMEOUT, encoding: str = DEFAULT_ENCODING
) -> Dict[str, str]:
    return await request_async(address, timeout, encoding, RulesProtocol)


class RulesProtocol:
    @staticmethod
    def validate_response_type(response_type: int) -> bool:
        return response_type == A2S_RULES_RESPONSE

    @staticmethod
    def serialize_request(challenge: int) -> bytes:
        return b"\x56" + challenge.to_bytes(4, "little")

    @staticmethod
    def deserialize_response(reader: ByteReader, response_type: int, ping: Optional[float]) -> Dict[str, str]:
        rule_count = reader.read_int16()
        # Have to use tuples to preserve evaluation order
        resp = dict((reader.read_cstring(), reader.read_cstring()) for _ in range(rule_count))
        return resp
