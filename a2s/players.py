import io
from typing import List

from a2s.exceptions import BrokenMessageError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING, \
    DEFAULT_RETRIES
from a2s.a2sstream import A2SStream
from a2s.a2sasync import A2SStreamAsync
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta



A2S_PLAYER_RESPONSE = 0x44
A2S_CHALLENGE_RESPONSE = 0x41

class Player(metaclass=DataclsMeta):
    """Apparently an entry index, but seems to be always 0"""
    index: int

    """Name of the player"""
    name: str

    """Score of the player"""
    score: int

    """Time the player has been connected to the server"""
    duration: float

def players_response(reader):
    player_count = reader.read_uint8()
    resp = [
        Player(
            index=reader.read_uint8(),
            name=reader.read_cstring(),
            score=reader.read_int32(),
            duration=reader.read_float()
        )
        for player_num in range(player_count)
    ]

    return resp

def players(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = A2SStream(address, timeout)
    reader = players_request(conn, encoding)
    conn.close()
    return players_response(reader)

def players_request(conn, encoding, challenge=0, retries=0):
    resp_data = conn.request(b"\x55" + challenge.to_bytes(4, "little"))
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError(
                "Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return players_request(
            conn, encoding, challenge, retries + 1)

    if response_type != A2S_PLAYER_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    return reader

async def aplayers(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = await A2SStreamAsync.create(address, timeout)
    reader = await players_request_async(conn, encoding)
    conn.close()
    return players_response(reader)

async def players_request_async(conn, encoding, challenge=0, retries=0):
    resp_data = await conn.request(b"\x55" + challenge.to_bytes(4, "little"))
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        if retries >= DEFAULT_RETRIES:
            raise BrokenMessageError(
                "Server keeps sending challenge responses")
        challenge = reader.read_uint32()
        return await players_request_async(
            conn, encoding, challenge, retries + 1)

    if response_type != A2S_PLAYER_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    return reader
