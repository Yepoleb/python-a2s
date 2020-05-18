import socket
import bz2
import io
import logging

from a2s.exceptions import BrokenMessageError
from a2s.byteio import ByteReader



HEADER_SIMPLE = b"\xFF\xFF\xFF\xFF"
HEADER_MULTI = b"\xFE\xFF\xFF\xFF"

logger = logging.getLogger("a2s")

class A2SFragment:
    def __init__(self, message_id, fragment_count, fragment_id, mtu,
                 decompressed_size=0, crc=0, payload=b""):
        self.message_id = message_id
        self.fragment_count = fragment_count
        self.fragment_id = fragment_id
        self.mtu = mtu
        self.decompressed_size = decompressed_size
        self.crc = crc
        self.payload = payload

    @property
    def is_compressed(self):
        return bool(self.message_id & (1 << 15))

def decode_fragment(data):
    reader = ByteReader(
        io.BytesIO(data), endian="<", encoding="utf-8")
    frag = A2SFragment(
        message_id=reader.read_uint32(),
        fragment_count=reader.read_uint8(),
        fragment_id=reader.read_uint8(),
        mtu=reader.read_uint16()
    )
    if frag.is_compressed:
        frag.decompressed_size = reader.read_uint32()
        frag.crc = reader.read_uint32()
        frag.payload = bz2.decompress(reader.read())
    else:
        frag.payload = reader.read()

    return frag

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

    def close(self):
        self._socket.close()

def request(address, data, timeout):
    stream = A2SStream(address, timeout)
    stream.send(data)
    resp = stream.recv()
    stream.close()
    return resp
