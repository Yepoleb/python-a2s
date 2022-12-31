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

import asyncio
import io
import logging
import time
from typing import TYPE_CHECKING, Dict, List, NoReturn, Optional, Tuple, Type, TypeVar, Union

from a2s.a2s_fragment import A2SFragment, decode_fragment
from a2s.byteio import ByteReader
from a2s.defaults import DEFAULT_RETRIES
from a2s.exceptions import BrokenMessageError

from .info import GoldSrcInfo, InfoProtocol, SourceInfo
from .players import Player, PlayersProtocol
from .rules import RulesProtocol

if TYPE_CHECKING:
    from typing_extensions import Self

HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"
A2S_CHALLENGE_RESPONSE = 0x41
PROTOCOLS = Union[InfoProtocol, PlayersProtocol, RulesProtocol]

logger: logging.Logger = logging.getLogger("a2s")

T = TypeVar("T", bound=PROTOCOLS)


async def request_async(
    address: Tuple[str, int], timeout: float, encoding: str, a2s_proto: Type[T]
) -> Union[SourceInfo, GoldSrcInfo, List[Player], Dict[str, str]]:
    conn = await A2SStreamAsync.create(address, timeout)
    response = await request_async_impl(conn, encoding, a2s_proto)
    conn.close()
    return response


async def request_async_impl(
    conn: A2SStreamAsync,
    encoding: str,
    a2s_proto: Type[T],
    challenge: int = 0,
    retries: int = 0,
    ping: Optional[float] = None,
) -> Union[SourceInfo, GoldSrcInfo, Dict[str, str], List[Player]]:
    send_time = time.monotonic()
    resp_data = await conn.request(a2s_proto.serialize_request(challenge))
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
        return await request_async_impl(conn, encoding, a2s_proto, challenge, retries + 1, ping)

    if not a2s_proto.validate_response_type(response_type):
        raise BrokenMessageError("Invalid response type: " + hex(response_type))

    return a2s_proto.deserialize_response(reader, response_type, ping)


class A2SProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.recv_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.error_event: asyncio.Event = asyncio.Event()
        self.error: Optional[Exception] = None
        self.fragment_buf: List[A2SFragment] = []

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        header = data[:4]
        payload = data[4:]
        if header == HEADER_SIMPLE:
            logger.debug("Received single packet: %r", payload)
            self.recv_queue.put_nowait(payload)
        elif header == HEADER_MULTI:
            self.fragment_buf.append(decode_fragment(payload))
            if len(self.fragment_buf) < self.fragment_buf[0].fragment_count:
                return  # Wait for more packets to arrive
            self.fragment_buf.sort(key=lambda f: f.fragment_id)
            reassembled = b"".join(fragment.payload for fragment in self.fragment_buf)
            # Sometimes there's an additional header present
            if reassembled.startswith(b"\xFF\xFF\xFF\xFF"):
                reassembled = reassembled[4:]
            logger.debug("Received %s part packet with content: %r", len(self.fragment_buf), reassembled)
            self.recv_queue.put_nowait(reassembled)
            self.fragment_buf = []
        else:
            self.error = BrokenMessageError("Invalid packet header: " + repr(header))
            self.error_event.set()

    def error_received(self, exc: Exception) -> None:
        self.error = exc
        self.error_event.set()

    def raise_on_error(self) -> NoReturn:
        assert self.error
        error: Exception = self.error
        self.error = None
        self.error_event.clear()
        raise error


class A2SStreamAsync:
    def __init__(self, transport: asyncio.DatagramTransport, protocol: A2SProtocol, timeout: float) -> None:
        self.transport = transport
        self.protocol = protocol
        self.timeout = timeout

    def __del__(self) -> None:
        self.close()

    @classmethod
    async def create(cls, address: Tuple[str, int], timeout: float) -> Self:
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(lambda: A2SProtocol(), remote_addr=address)
        return cls(transport, protocol, timeout)

    def send(self, payload: bytes) -> None:
        logger.debug("Sending packet: %r", payload)
        packet = HEADER_SIMPLE + payload
        self.transport.sendto(packet)

    async def recv(self) -> bytes:
        queue_task = asyncio.create_task(self.protocol.recv_queue.get())
        error_task = asyncio.create_task(self.protocol.error_event.wait())
        done, pending = await asyncio.wait(
            {queue_task, error_task}, timeout=self.timeout, return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        if error_task in done:
            self.protocol.raise_on_error()
        if not done:
            raise asyncio.TimeoutError()

        return queue_task.result()

    async def request(self, payload: bytes) -> bytes:
        self.send(payload)
        return await self.recv()

    def close(self) -> None:
        self.transport.close()
