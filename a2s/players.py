import io

from a2s.exceptions import BrokenMessageError
from a2s.defaults import default_encoding, default_timeout
from a2s.a2sstream import request
from a2s.byteio import ByteReader



A2S_PLAYER_RESPONSE = 0x44
A2S_CHALLENGE_RESPONSE = 0x41

class PlayerEntry:
    def __init__(self, index, name, score, duration):
        self.index = index
        self.name = name
        self.score = score
        self.duration = duration

class PlayersResponse:
    def __init__(self, player_count, players):
        self.player_count = player_count
        self.players = players

def players(address, challenge=0, timeout=default_timeout):
    resp_data = request(
        address, b"\x55" + challenge.to_bytes(4, "little"), timeout)
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=default_encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_CHALLENGE_RESPONSE:
        challenge = reader.read_int32()
        return players(address, challenge, timeout)

    if response_type != A2S_PLAYER_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    player_count = reader.read_uint8()
    resp = PlayersResponse(
        player_count=player_count,
        players=[
            PlayerEntry(
                index=reader.read_uint8(),
                name=reader.read_cstring(),
                score=reader.read_int32(),
                duration=reader.read_float()
            )
            for player_num in range(player_count)
        ]
    )

    return resp
