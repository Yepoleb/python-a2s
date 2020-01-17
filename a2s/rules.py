import io

from a2s.exceptions import BrokenMessageError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING, \
    DEFAULT_RETRIES
from a2s.a2sstream import request
from a2s.byteio import ByteReader



A2S_RULES_RESPONSE = 0x45
A2S_CHALLENGE_RESPONSE = 0x41

def rules(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    return rules_impl(address, timeout, encoding)

def rules_impl(address, timeout, encoding, challenge=0, retries=0):
    resp_data = request(
        address, b"\x56" + challenge.to_bytes(4, "little"), timeout)
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    # A2S_RESPONSE misteriously seems to add a FF FF FF FF
    # long to the beginning of the response which isn't
    # mentioned on the wiki.
    #
    # Behaviour witnessed with TF2 server 94.23.226.200:2045
    # As of 2015-11-22, Quake Live servers on steam do not
    # Source: valve-python messages.py
    if reader.peek(4) == b"\xFF\xFF\xFF\xFF":
        reader.read(4)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError(
                "Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return rules_impl(
            address, timeout, encoding, challenge, retries + 1)

    if response_type != A2S_RULES_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    rule_count = reader.read_int16()
    # Have to use tuples to preserve evaluation order
    resp = dict(
        (reader.read_cstring(), reader.read_cstring())
        for rule_num in range(rule_count)
    )

    return resp
