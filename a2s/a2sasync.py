import asyncio
import logging

from a2s.exceptions import BrokenMessageError
from a2s.a2sfragment import decode_fragment



HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"

logger = logging.getLogger("a2s")

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
