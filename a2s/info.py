import time
import io

from a2s.exceptions import BrokenMessageError
from a2s.defaults import default_encoding, default_timeout
from a2s.a2sstream import request
from a2s.byteio import ByteReader



A2S_INFO_RESPONSE = 0x49

class InfoResponse:
    def __init__(self, protocol, server_name, map_name, folder, game,
                 app_id, player_count, max_players, bot_count,
                 server_type, platform, password_protected, vac_enabled,
                 version, edf=0, port=0, steam_id=0, stv_port=0,
                 stv_name="", keywords="", game_id=0):
        self.protocol = protocol
        self.server_name = server_name
        self.map_name = map_name
        self.folder = folder
        self.game = game
        self.app_id = app_id
        self.player_count = player_count
        self.max_players = max_players
        self.bot_count = bot_count
        self.server_type = server_type.lower()
        self.platform = platform.lower()
        if self.platform == "o":
            self.platform = "m"
        self.password_protected = password_protected
        self.vac_enabled = vac_enabled
        self.version = version

        self.edf = edf
        self.port = port
        self.steam_id = steam_id
        self.stv_port = stv_port
        self.stv_name = stv_name
        self.keywords = keywords
        self.game_id = game_id

    @property
    def has_port(self):
        return bool(self.edf & 0x80)

    @property
    def has_steam_id(self):
        return bool(self.edf & 0x10)

    @property
    def has_stv(self):
        return bool(self.edf & 0x40)

    @property
    def has_keywords(self):
        return bool(self.edf & 0x20)

    @property
    def has_game_id(self):
        return bool(self.edf & 0x01)


def info(address, timeout=default_timeout):
    send_time = time.monotonic()
    resp_data = request(address, b"\x54Source Engine Query\0", timeout)
    recv_time = time.monotonic()
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=default_encoding)

    response_type = reader.read_uint8()
    if response_type != A2S_INFO_RESPONSE:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    resp = InfoResponse(
        protocol=reader.read_uint8(),
        server_name=reader.read_cstring(),
        map_name=reader.read_cstring(),
        folder=reader.read_cstring(),
        game=reader.read_cstring(),
        app_id=reader.read_uint16(),
        player_count=reader.read_uint8(),
        max_players=reader.read_uint8(),
        bot_count=reader.read_uint8(),
        server_type=reader.read_char(),
        platform=reader.read_char(),
        password_protected=reader.read_bool(),
        vac_enabled=reader.read_bool(),
        version=reader.read_cstring()
    )
    resp.ping = recv_time - send_time

    try:
        resp.edf = reader.read_uint8()
    except BufferExhaustedError:
        pass

    if resp.has_port:
        resp.port = reader.read_uint16()
    if resp.has_steam_id:
        resp.steam_id = reader.read_uint64()
    if resp.has_stv:
        resp.stv_port = reader.read_uint16()
        resp.stv_name = reader.read_cstring()
    if resp.has_keywords:
        resp.keywords = reader.read_cstring()
    if resp.has_game_id:
        resp.game_id = reader.read_uint64()

    return resp
