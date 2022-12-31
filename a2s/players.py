"""
MIT License

Copyright (c) 2020 Gabriel Huber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import List, Optional, Tuple

from a2s.a2s_async import request_async
from a2s.a2s_sync import request_sync
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta
from a2s.defaults import DEFAULT_ENCODING, DEFAULT_TIMEOUT

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


def players(address: Tuple[str, int], timeout: float = DEFAULT_TIMEOUT, encoding: str = DEFAULT_ENCODING) -> List[Player]:
    return request_sync(address, timeout, encoding, PlayersProtocol)


async def aplayers(
    address: Tuple[str, int], timeout: float = DEFAULT_TIMEOUT, encoding: str = DEFAULT_ENCODING
) -> List[Player]:
    return await request_async(address, timeout, encoding, PlayersProtocol)


class PlayersProtocol:
    @staticmethod
    def validate_response_type(response_type: int) -> bool:
        return response_type == A2S_PLAYER_RESPONSE

    @staticmethod
    def serialize_request(challenge: int) -> bytes:
        return b"\x55" + challenge.to_bytes(4, "little")

    @staticmethod
    def deserialize_response(reader: ByteReader, response_type: int, ping: Optional[float]) -> List[Player]:
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
