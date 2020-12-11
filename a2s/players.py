import io

from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2s_sync import request_sync
from a2s.a2s_async import request_async
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta



A2S_PLAYER_RESPONSE = 0x44


class Player(metaclass=DataclsMeta):
    """Apparently an entry index, but seems to be always 0"""
    index: int

    """Name of the player"""
    name: str

    """Score of the player"""
    score: int

    """Time the player has been connected to the server"""
    duration: float


def players(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    return request_sync(address, timeout, encoding, PlayersProtocol)

async def aplayers(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
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
