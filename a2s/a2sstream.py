import socket
import logging

from a2s.exceptions import BrokenMessageError
from a2s.a2sfragment import decode_fragment



HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"

logger = logging.getLogger("a2s")

class A2SStream:
    def __init__(self, address, timeout):
        self.address = address
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(timeout)

    def __del__(self):
        self.close()

    def send(self, data):
        packet = HEADER_SIMPLE + data
        self._socket.sendto(packet, self.address)

    def recv(self):
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
            logger.debug("Received %s part packet with content: %r",
                         len(fragments), reassembled)
            return reassembled
        else:
            raise BrokenMessageError(
                "Invalid packet header: " + repr(header))

    def request(self, payload):
        self.send(payload)
        return self.recv()

    def close(self):
        self._socket.close()
