from typing import List, Optional, Tuple

from a2s.a2s_async import request_async
from a2s.a2s_protocol import A2SProtocol
from a2s.a2s_sync import request_sync
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta
from a2s.defaults import DEFAULT_ENCODING, DEFAULT_TIMEOUT

A2S_PLAYER_RESPONSE = 0x44

__all__ = (
    "Player",
    "players",
    "aplayers",
)


class Player(metaclass=DataclsMeta):
    index: int
    """Apparently an entry index, but seems to be always 0"""

    name: str
    """Name of the player"""

    score: int
    """Score of the player"""

    duration: float
    """Time the player has been connected to the server"""


def players(
    address: Tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: str = DEFAULT_ENCODING,
) -> List[Player]:
    return request_sync(address, timeout, encoding, PlayersProtocol)


async def aplayers(
    address: Tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: str = DEFAULT_ENCODING,
) -> List[Player]:
    return await request_async(address, timeout, encoding, PlayersProtocol)


class PlayersProtocol(A2SProtocol):
    @staticmethod
    def validate_response_type(response_type: int) -> bool:
        return response_type == A2S_PLAYER_RESPONSE

    @staticmethod
    def serialize_request(challenge: int) -> bytes:
        return b"\x55" + challenge.to_bytes(4, "little")

    @staticmethod
    def deserialize_response(
        reader: ByteReader, response_type: int, ping: Optional[float]
    ) -> List[Player]:
        player_count = reader.read_uint8()
        resp = [
            Player(
                index=reader.read_uint8(),
                name=reader.read_cstring(),
                score=reader.read_int32(),
                duration=reader.read_float(),
            )
            for _ in range(player_count)
        ]
        return resp
