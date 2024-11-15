import io
from typing import overload, Union

from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2s_sync import request_sync
from a2s.a2s_async import request_async
from a2s.byteio import ByteReader



A2S_RULES_RESPONSE = 0x45


@overload
def rules(address: tuple[str, int], timeout: float, encoding: str) -> dict[str, str]:
    ...

@overload
def rules(address: tuple[str, int], timeout: float, encoding: None) -> dict[bytes, bytes]:
    ...

def rules(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[dict[str, str], dict[bytes, bytes]]:
    return request_sync(address, timeout, encoding, RulesProtocol)

@overload
async def arules(address: tuple[str, int], timeout: float, encoding: str) -> dict[str, str]:
    ...

@overload
async def arules(address: tuple[str, int], timeout: float, encoding: None) -> dict[bytes, bytes]:
    ...

async def arules(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[dict[str, str], dict[bytes, bytes]]:
    return await request_async(address, timeout, encoding, RulesProtocol)


class RulesProtocol:
    @staticmethod
    def validate_response_type(response_type):
        return response_type == A2S_RULES_RESPONSE

    @staticmethod
    def serialize_request(challenge):
        return b"\x56" + challenge.to_bytes(4, "little")

    @staticmethod
    def deserialize_response(reader, response_type, ping):
        rule_count = reader.read_int16()
        # Have to use tuples to preserve evaluation order
        resp = dict(
            (reader.read_cstring(), reader.read_cstring())
            for rule_num in range(rule_count)
        )
        return resp
