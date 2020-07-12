import asyncio
import logging

from a2s.exceptions import BrokenMessageError
from a2s.a2sfragment import decode_fragment



HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"

logger = logging.getLogger("a2s")

class A2SProtocol:
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
                len(fragments), reassembled)
            self.recv_queue.put_nowait(reassembled)
            self.fragment_buf = []
        else:
            self.error = BrokenMessageError(
                "Invalid packet header: " + repr(header))
            self.error_event.set()

    def error_received(self, exc):
        self.error = exc
        self.error_event.set()

    def send(self, payload):
        packet = HEADER_SIMPLE + payload
        self.transport.sendto(packet)

    async def recv(self, timeout):
        queue_task = asyncio.create_task(self.recv_queue.get())
        error_task = asyncio.create_task(self.error_event.wait())
        done, pending = await asyncio.wait({queue_task, error_task},
                     timeout=timeout, return_when=FIRST_COMPLETED)

        for task in pending: task.cancel()
        if error_task in done:
            error = self.error
            self.error = None
            self.error_event.clear()
            raise error
        if not done:
            raise asyncio.TimeoutError()

        return queue_task.result()
