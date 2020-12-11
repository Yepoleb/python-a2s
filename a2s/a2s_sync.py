import socket
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


def request_sync(address, timeout, encoding, a2s_proto):
    conn = A2SStream(address, timeout)
    response = request_sync_impl(conn, encoding, a2s_proto)
    conn.close()
    return response

def request_sync_impl(conn, encoding, a2s_proto, challenge=0, retries=0, ping=None):
    send_time = time.monotonic()
    resp_data = conn.request(a2s_proto.serialize_request(challenge))
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
        return request_sync_impl(
            conn, encoding, a2s_proto, challenge, retries + 1, ping)

    if not a2s_proto.validate_response_type(response_type):
        raise BrokenMessageError(
            "Invalid response type: " + hex(response_type))

    return a2s_proto.deserialize_response(reader, response_type, ping)


class A2SStream:
    def __init__(self, address, timeout):
        self.address = address
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(timeout)

    def __del__(self):
        self.close()

    def send(self, data):
        logger.debug("Sending packet: %r", data)
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
            # Sometimes there's an additional header present
            if reassembled.startswith(b"\xFF\xFF\xFF\xFF"):
                reassembled = reassembled[4:]
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
