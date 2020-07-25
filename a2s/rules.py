import io

from a2s.exceptions import BrokenMessageError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING, \
    DEFAULT_RETRIES
from a2s.a2sstream import A2SStream
from a2s.a2sasync import A2SStreamAsync
from a2s.byteio import ByteReader



A2S_RULES_RESPONSE = 0x45
A2S_CHALLENGE_RESPONSE = 0x41

def rules_response(reader):
    rule_count = reader.read_int16()
    # Have to use tuples to preserve evaluation order
    resp = dict(
        (reader.read_cstring(), reader.read_cstring())
        for rule_num in range(rule_count)
    )

    return resp

def rules(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = A2SStream(address, timeout)
    reader = rules_request(conn, encoding)
    conn.close()
    return rules_response(reader)

def rules_request(conn, encoding, challenge=0, retries=0):
    resp_data = conn.request(b"\x56" + challenge.to_bytes(4, "little"))
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
        return rules_request(
            conn, encoding, challenge, retries + 1)

    if response_type != A2S_RULES_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    return reader

async def arules(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = await A2SStreamAsync.create(address, timeout)
    reader = await rules_request_async(conn, encoding)
    conn.close()
    return rules_response(reader)

async def rules_request_async(conn, encoding, challenge=0, retries=0):
    resp_data = await conn.request(b"\x56" + challenge.to_bytes(4, "little"))
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    if reader.peek(4) == b"\xFF\xFF\xFF\xFF":
        reader.read(4)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError(
                "Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return await rules_request_async(
            conn, encoding, challenge, retries + 1)

    if response_type != A2S_RULES_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    return reader
