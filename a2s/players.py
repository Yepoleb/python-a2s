import io
from dataclasses import dataclass
from typing import Generic, Union, TypeVar, overload

from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2s_sync import request_sync
from a2s.a2s_async import request_async
from a2s.byteio import ByteReader



A2S_PLAYER_RESPONSE = 0x44


StrType = TypeVar("StrType", str, bytes)  # str (default) or bytes if encoding=None is used

@dataclass
class Player(Generic[StrType]):
    index: int
    """Apparently an entry index, but seems to be always 0"""

    name: StrType
    """Name of the player"""

    score: int
    """Score of the player"""

    duration: float
    """Time the player has been connected to the server"""


@overload
def players(address: tuple[str, int], timeout: float, encoding: str) -> list[Player[str]]:
    ...

@overload
def players(address: tuple[str, int], timeout: float, encoding: None) -> list[Player[bytes]]:
    ...

def players(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[list[Player[str]], list[Player[bytes]]]:
    return request_sync(address, timeout, encoding, PlayersProtocol)

@overload
async def aplayers(address: tuple[str, int], timeout: float, encoding: str) -> list[Player[str]]:
    ...

@overload
async def aplayers(address: tuple[str, int], timeout: float, encoding: None) -> list[Player[bytes]]:
    ...

async def aplayers(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[list[Player[str]], list[Player[bytes]]]:
    return await request_async(address, timeout, encoding, PlayersProtocol)


class PlayersProtocol:
    @staticmethod
    def validate_response_type(response_type):
        return response_type == A2S_PLAYER_RESPONSE

    @staticmethod
    def serialize_request(challenge):
        return b"\x55" + challenge.to_bytes(4, "little")

    @staticmethod
    def deserialize_response(reader, response_type, ping):
        player_count = reader.read_uint8()
        resp = [
            Player(
                index=reader.read_uint8(),
                name=reader.read_cstring(),
                score=reader.read_int32(),
                duration=reader.read_float()
            )
            for player_num in range(player_count)
        ]
        return resp
