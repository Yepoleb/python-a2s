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

from __future__ import annotations

import io
import logging
import socket
import time
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union

from a2s.a2s_fragment import decode_fragment
from a2s.byteio import ByteReader
from a2s.defaults import DEFAULT_RETRIES
from a2s.exceptions import BrokenMessageError

from .info import GoldSrcInfo, InfoProtocol, SourceInfo
from .players import Player, PlayersProtocol
from .rules import RulesProtocol

HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"
A2S_CHALLENGE_RESPONSE = 0x41
PROTOCOLS = Union[InfoProtocol, RulesProtocol, PlayersProtocol]

logger: logging.Logger = logging.getLogger("a2s")

T = TypeVar("T", InfoProtocol, RulesProtocol, PlayersProtocol)


def request_sync(
    address: Tuple[str, int], timeout: float, encoding: str, a2s_proto: Type[T]
) -> Union[List[Player], GoldSrcInfo, SourceInfo, Dict[str, str]]:
    conn = A2SStream(address, timeout)
    response = request_sync_impl(conn, encoding, a2s_proto)  # type: ignore
    conn.close()
    return response


def request_sync_impl(
    conn: A2SStream, encoding: str, a2s_proto: Type[T], challenge: int = 0, retries: int = 0, ping: Optional[float] = None
) -> Union[SourceInfo, GoldSrcInfo, Dict[str, str], List[Player]]:
    send_time = time.monotonic()
    resp_data = conn.request(a2s_proto.serialize_request(challenge))
    recv_time = time.monotonic()
    # Only set ping on first packet received
    if retries == 0:
        ping = recv_time - send_time

    reader = ByteReader(io.BytesIO(resp_data), endian="<", encoding=encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError("Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return request_sync_impl(conn, encoding, a2s_proto, challenge, retries + 1, ping)

    if not a2s_proto.validate_response_type(response_type):
        raise BrokenMessageError("Invalid response type: " + hex(response_type))

    return a2s_proto.deserialize_response(reader, response_type, ping)


class A2SStream:
    def __init__(self, address: Tuple[str, int], timeout: float) -> None:
        self.address: Tuple[str, int] = address
        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(timeout)

    def __del__(self) -> None:
        self.close()

    def send(self, data: bytes) -> None:
        logger.debug("Sending packet: %r", data)
        packet = HEADER_SIMPLE + data
        self._socket.sendto(packet, self.address)

    def recv(self) -> bytes:
        packet = self._socket.recv(65535)
        header = packet[:4]
        data = packet[4:]
        if header == HEADER_SIMPLE:
            logger.debug("Received single packet: %r", data)
            return data
        elif header == HEADER_MULTI:
            fragments = [decode_fragment(data)]
            while len(fragments) < fragments[0].fragment_count:
                packet = self._socket.recv(4096)
                fragments.append(decode_fragment(packet[4:]))
            fragments.sort(key=lambda f: f.fragment_id)
            reassembled = b"".join(fragment.payload for fragment in fragments)
            # Sometimes there's an additional header present
            if reassembled.startswith(b"\xFF\xFF\xFF\xFF"):
                reassembled = reassembled[4:]
            logger.debug("Received %s part packet with content: %r", len(fragments), reassembled)
            return reassembled
        else:
            raise BrokenMessageError("Invalid packet header: " + repr(header))

    def request(self, payload: bytes) -> bytes:
        self.send(payload)
        return self.recv()

    def close(self) -> None:
        self._socket.close()
