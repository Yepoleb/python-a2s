import asyncio
import logging
import time
import io

from a2s.exceptions import BrokenMessageError
from a2s.a2s_fragment import decode_fragment
from a2s.defaults import DEFAULT_RETRIES
from a2s.byteio import ByteReader



HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"
A2S_CHALLENGE_RESPONSE = 0x41

logger = logging.getLogger("a2s")


async def request_async(address, timeout, encoding, a2s_proto):
    conn = await A2SStreamAsync.create(address, timeout)
    response = await request_async_impl(conn, encoding, a2s_proto)
    conn.close()
    return response

async def request_async_impl(conn, encoding, a2s_proto, challenge=0, retries=0, ping=None):
    send_time = time.monotonic()
    resp_data = await conn.request(a2s_proto.serialize_request(challenge))
    recv_time = time.monotonic()
    # Only set ping on first packet received
    if retries == 0:
        ping = recv_time - send_time

    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError(
                "Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return await request_async_impl(
            conn, encoding, a2s_proto, challenge, retries + 1, ping)

    if not a2s_proto.validate_response_type(response_type):
        raise BrokenMessageError(
            "Invalid response type: " + hex(response_type))

    return a2s_proto.deserialize_response(reader, response_type, ping)


class A2SProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.recv_queue = asyncio.Queue()
        self.error_event = asyncio.Event()
        self.error = None
        self.fragment_buf = []

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, packet, addr):
        header = packet[:4]
        payload = packet[4:]
        if header == HEADER_SIMPLE:
            logger.debug("Received single packet: %r", payload)
            self.recv_queue.put_nowait(payload)
        elif header == HEADER_MULTI:
            self.fragment_buf.append(decode_fragment(payload))
            if len(self.fragment_buf) < self.fragment_buf[0].fragment_count:
                return # Wait for more packets to arrive
            self.fragment_buf.sort(key=lambda f: f.fragment_id)
            reassembled = b"".join(
                fragment.payload for fragment in self.fragment_buf)
            # Sometimes there's an additional header present
            if reassembled.startswith(b"\xFF\xFF\xFF\xFF"):
                reassembled = reassembled[4:]
            logger.debug("Received %s part packet with content: %r",
                len(self.fragment_buf), reassembled)
            self.recv_queue.put_nowait(reassembled)
            self.fragment_buf = []
        else:
            self.error = BrokenMessageError(
                "Invalid packet header: " + repr(header))
            self.error_event.set()

    def error_received(self, exc):
        self.error = exc
        self.error_event.set()

    def raise_on_error(self):
        error = self.error
        self.error = None
        self.error_event.clear()
        raise error

class A2SStreamAsync:
    def __init__(self, transport, protocol, timeout):
        self.transport = transport
        self.protocol = protocol
        self.timeout = timeout

    def __del__(self):
        self.close()

    @classmethod
    async def create(cls, address, timeout):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: A2SProtocol(), remote_addr=address)
        return cls(transport, protocol, timeout)

    def send(self, payload):
        logger.debug("Sending packet: %r", payload)
        packet = HEADER_SIMPLE + payload
        self.transport.sendto(packet)

    async def recv(self):
        queue_task = asyncio.create_task(self.protocol.recv_queue.get())
        error_task = asyncio.create_task(self.protocol.error_event.wait())
        done, pending = await asyncio.wait({queue_task, error_task},
                     timeout=self.timeout, return_when=asyncio.FIRST_COMPLETED)

        for task in pending: task.cancel()
        if error_task in done:
           self.protocol.raise_on_error()
        if not done:
            raise asyncio.TimeoutError()

        return queue_task.result()

    async def request(self, payload):
        self.send(payload)
        return await self.recv()

    def close(self):
        self.transport.close()
