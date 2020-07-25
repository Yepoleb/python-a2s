import time
import io

from a2s.exceptions import BrokenMessageError, BufferExhaustedError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2sstream import A2SStream
from a2s.a2sasync import A2SStreamAsync
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta



A2S_INFO_RESPONSE = 0x49
A2S_INFO_RESPONSE_LEGACY = 0x6D

class SourceInfo(metaclass=DataclsMeta):
    """Protocol version used by the server"""
    protocol: int

    """Display name of the server"""
    server_name: str

    """The currently loaded map"""
    map_name: str

    """Name of the game directory"""
    folder: str

    """Name of the game"""
    game: str

    """App ID of the game required to connect"""
    app_id: int

    """Number of players currently connected"""
    player_count: int

    """Number of player slots available"""
    max_players: int

    """Number of bots on the server"""
    bot_count: int

    """Type of the server:
    'd': Dedicated server
    'l': Non-dedicated server
    'p': SourceTV relay (proxy)"""
    server_type: str

    """Operating system of the server
    'l', 'w', 'm' for Linux, Windows, macOS"""
    platform: str

    """Server requires a password to connect"""
    password_protected: bool

    """Server has VAC enabled"""
    vac_enabled: bool

    """Version of the server software"""
    version: str

    # Optional:
    """Extra data field, used to indicate if extra values are
    included in the response"""
    edf: int = 0

    """Port of the game server."""
    port: int

    """Steam ID of the server"""
    steam_id: int

    """Port of the SourceTV server"""
    stv_port: int

    """Name of the SourceTV server"""
    stv_name: str

    """Tags that describe the gamemode being played"""
    keywords: str

    """Game ID for games that have an app ID too high for 16bit."""
    game_id: int

    # Client determined values:
    """Round-trip delay time for the request in seconds"""
    ping: float

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

class GoldSrcInfo(metaclass=DataclsMeta):
    """IP Address and port of the server"""
    address: str

    """Display name of the server"""
    server_name: str

    """The currently loaded map"""
    map_name: str

    """Name of the game directory"""
    folder: str

    """Name of the game"""
    game: str

    """Number of players currently connected"""
    player_count: int

    """Number of player slots available"""
    max_players: int

    """Protocol version used by the server"""
    protocol: int

    """Type of the server:
    'd': Dedicated server
    'l': Non-dedicated server
    'p': SourceTV relay (proxy)"""
    server_type: str

    """Operating system of the server
    'l', 'w' for Linux and Windows"""
    platform: str

    """Server requires a password to connect"""
    password_protected: bool

    """Server is running a Half-Life mod instead of the base game"""
    is_mod: bool

    """Server has VAC enabled"""
    vac_enabled: bool

    """Number of bots on the server"""
    bot_count: int

    # Optional:
    """URL to the mod website"""
    mod_website: str

    """URL to download the mod"""
    mod_download: str

    """Version of the mod installed on the server"""
    mod_version: int

    """Size in bytes of the mod"""
    mod_size: int

    """Mod supports multiplayer only"""
    multiplayer_only: bool = False

    """Mod uses a custom DLL"""
    uses_hl_dll: bool = True

    # Client determined values:
    """Round-trip delay time for the request in seconds"""
    ping: float

def parse_source(reader):
    resp = SourceInfo()
    resp.protocol = reader.read_uint8()
    resp.server_name = reader.read_cstring()
    resp.map_name = reader.read_cstring()
    resp.folder = reader.read_cstring()
    resp.game = reader.read_cstring()
    resp.app_id = reader.read_uint16()
    resp.player_count = reader.read_uint8()
    resp.max_players = reader.read_uint8()
    resp.bot_count = reader.read_uint8()
    resp.server_type = reader.read_char().lower()
    resp.platform = reader.read_char().lower()
    if resp.platform == "o": # Deprecated mac value
        resp.platform = "m"
    resp.password_protected = reader.read_bool()
    resp.vac_enabled = reader.read_bool()
    resp.version = reader.read_cstring()

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

def parse_goldsrc(reader):
    resp = GoldSrcInfo()
    resp.address = reader.read_cstring()
    resp.server_name = reader.read_cstring()
    resp.map_name = reader.read_cstring()
    resp.folder = reader.read_cstring()
    resp.game = reader.read_cstring()
    resp.player_count = reader.read_uint8()
    resp.max_players = reader.read_uint8()
    resp.protocol = reader.read_uint8()
    resp.server_type = reader.read_char()
    resp.platform = reader.read_char()
    resp.password_protected = reader.read_bool()
    resp.is_mod = reader.read_bool()

    # Some games don't send this section
    if resp.is_mod and len(reader.peek()) > 2:
        resp.mod_website = reader.read_cstring()
        resp.mod_download = reader.read_cstring()
        reader.read(1) # Skip a NULL byte
        resp.mod_version = reader.read_uint32()
        resp.mod_size = reader.read_uint32()
        resp.multiplayer_only = reader.read_bool()
        resp.uses_custom_dll = reader.read_bool()

    resp.vac_enabled = reader.read_bool()
    resp.bot_count = reader.read_uint8()

    return resp

def info_response(resp_data, ping, encoding):
    reader = ByteReader(
        io.BytesIO(resp_data), endian="<", encoding=encoding)

    response_type = reader.read_uint8()
    if response_type == A2S_INFO_RESPONSE:
        resp = parse_source(reader)
    elif response_type == A2S_INFO_RESPONSE_LEGACY:
        resp = parse_goldsrc(reader)
    else:
        raise BrokenMessageError(
            "Invalid response type: " + str(response_type))

    resp.ping = ping
    return resp

def info(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = A2SStream(address, timeout)
    send_time = time.monotonic()
    resp_data = conn.request(b"\x54Source Engine Query\0")
    recv_time = time.monotonic()
    conn.close()
    ping = recv_time - send_time

    return info_response(resp_data, ping, encoding)

async def ainfo(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    conn = await A2SStreamAsync.create(address, timeout)
    send_time = time.monotonic()
    resp_data = await conn.request(b"\x54Source Engine Query\0")
    recv_time = time.monotonic()
    conn.close()
    ping = recv_time - send_time

    return info_response(resp_data, ping, encoding)
