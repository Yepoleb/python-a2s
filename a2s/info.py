import io
from dataclasses import dataclass
from typing import Optional, Generic, Union, TypeVar, overload

from a2s.exceptions import BrokenMessageError, BufferExhaustedError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2s_sync import request_sync
from a2s.a2s_async import request_async
from a2s.byteio import ByteReader



A2S_INFO_RESPONSE = 0x49
A2S_INFO_RESPONSE_LEGACY = 0x6D


StrType = TypeVar("StrType", str, bytes)  # str (default) or bytes if encoding=None is used

@dataclass
class SourceInfo(Generic[StrType]):
    protocol: int
    """Protocol version used by the server"""

    server_name: StrType
    """Display name of the server"""

    map_name: StrType
    """The currently loaded map"""

    folder: StrType
    """Name of the game directory"""

    game: StrType
    """Name of the game"""

    app_id: int
    """App ID of the game required to connect"""

    player_count: int
    """Number of players currently connected"""

    max_players: int
    """Number of player slots available"""

    bot_count: int
    """Number of bots on the server"""

    server_type: StrType
    """Type of the server:
    'd': Dedicated server
    'l': Non-dedicated server
    'p': SourceTV relay (proxy)"""

    platform: StrType
    """Operating system of the server
    'l', 'w', 'm' for Linux, Windows, macOS"""

    password_protected: bool
    """Server requires a password to connect"""

    vac_enabled: bool
    """Server has VAC enabled"""

    version: StrType
    """Version of the server software"""

    edf: int
    """Extra data field, used to indicate if extra values are included in the response"""

    ping: float
    """Round-trip time for the request in seconds, not actually sent by the server"""

    # Optional:
    port: Optional[int] = None
    """Port of the game server."""

    steam_id: Optional[int] = None
    """Steam ID of the server"""

    stv_port: Optional[int] = None
    """Port of the SourceTV server"""

    stv_name: Optional[StrType] = None
    """Name of the SourceTV server"""

    keywords: Optional[StrType] = None
    """Tags that describe the gamemode being played"""

    game_id: Optional[int] = None
    """Game ID for games that have an app ID too high for 16bit."""

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

@dataclass
class GoldSrcInfo(Generic[StrType]):
    address: StrType
    """IP Address and port of the server"""

    server_name: StrType
    """Display name of the server"""

    map_name: StrType
    """The currently loaded map"""

    folder: StrType
    """Name of the game directory"""

    game: StrType
    """Name of the game"""

    player_count: int
    """Number of players currently connected"""

    max_players: int
    """Number of player slots available"""

    protocol: int
    """Protocol version used by the server"""

    server_type: StrType
    """Type of the server:
    'd': Dedicated server
    'l': Non-dedicated server
    'p': SourceTV relay (proxy)"""

    platform: StrType
    """Operating system of the server
    'l', 'w' for Linux and Windows"""

    password_protected: bool
    """Server requires a password to connect"""

    is_mod: bool
    """Server is running a Half-Life mod instead of the base game"""

    vac_enabled: bool
    """Server has VAC enabled"""

    bot_count: int
    """Number of bots on the server"""

    ping: float
    """Round-trip time for the request in seconds, not actually sent by the server"""

    # Optional:
    mod_website: Optional[StrType]
    """URL to the mod website"""

    mod_download: Optional[StrType]
    """URL to download the mod"""

    mod_version: Optional[int]
    """Version of the mod installed on the server"""

    mod_size: Optional[int]
    """Size in bytes of the mod"""

    multiplayer_only: Optional[bool]
    """Mod supports multiplayer only"""

    uses_custom_dll: Optional[bool]
    """Mod uses a custom DLL"""

    @property
    def uses_hl_dll(self) -> Optional[bool]:
        """Compatibility alias, because it got renamed"""
        return self.uses_custom_dll


@overload
def info(address: tuple[str, int], timeout: float, encoding: str) -> Union[SourceInfo[str], GoldSrcInfo[str]]:
    ...

@overload
def info(address: tuple[str, int], timeout: float, encoding: None) -> Union[SourceInfo[bytes], GoldSrcInfo[bytes]]:
    ...

def info(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[SourceInfo[str], SourceInfo[bytes], GoldSrcInfo[str], GoldSrcInfo[bytes]]:
    return request_sync(address, timeout, encoding, InfoProtocol)

@overload
async def ainfo(address: tuple[str, int], timeout: float, encoding: str) -> Union[SourceInfo[str], GoldSrcInfo[str]]:
    ...

@overload
async def ainfo(address: tuple[str, int], timeout: float, encoding: None) -> Union[SourceInfo[bytes], GoldSrcInfo[bytes]]:
    ...

async def ainfo(
    address: tuple[str, int],
    timeout: float = DEFAULT_TIMEOUT,
    encoding: Union[str, None] = DEFAULT_ENCODING
) -> Union[SourceInfo[str], SourceInfo[bytes], GoldSrcInfo[str], GoldSrcInfo[bytes]]:
    return await request_async(address, timeout, encoding, InfoProtocol)


class InfoProtocol:
    @staticmethod
    def validate_response_type(response_type):
        return response_type in (A2S_INFO_RESPONSE, A2S_INFO_RESPONSE_LEGACY)

    @staticmethod
    def serialize_request(challenge):
        if challenge:
            return b"\x54Source Engine Query\0" + challenge.to_bytes(4, "little")
        else:
            return b"\x54Source Engine Query\0"

    @staticmethod
    def deserialize_response(reader, response_type, ping):
        if response_type == A2S_INFO_RESPONSE:
            resp = parse_source(reader, ping)
        elif response_type == A2S_INFO_RESPONSE_LEGACY:
            resp = parse_goldsrc(reader, ping)
        else:
            raise Exception(str(response_type))

        return resp

def parse_source(reader, ping):
    protocol = reader.read_uint8()
    server_name = reader.read_cstring()
    map_name = reader.read_cstring()
    folder = reader.read_cstring()
    game = reader.read_cstring()
    app_id = reader.read_uint16()
    player_count = reader.read_uint8()
    max_players = reader.read_uint8()
    bot_count = reader.read_uint8()
    server_type = reader.read_char().lower()
    platform = reader.read_char().lower()
    if platform == "o": # Deprecated mac value
        platform = "m"
    password_protected = reader.read_bool()
    vac_enabled = reader.read_bool()
    version = reader.read_cstring()

    try:
        edf = reader.read_uint8()
    except BufferExhaustedError:
        edf = 0

    resp = SourceInfo(
        protocol, server_name, map_name, folder, game, app_id, player_count, max_players,
        bot_count, server_type, platform, password_protected, vac_enabled, version, edf, ping
    )
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

def parse_goldsrc(reader, ping):
    address = reader.read_cstring()
    server_name = reader.read_cstring()
    map_name = reader.read_cstring()
    folder = reader.read_cstring()
    game = reader.read_cstring()
    player_count = reader.read_uint8()
    max_players = reader.read_uint8()
    protocol = reader.read_uint8()
    server_type = reader.read_char()
    platform = reader.read_char()
    password_protected = reader.read_bool()
    is_mod = reader.read_bool()

    # Some games don't send this section
    if is_mod and len(reader.peek()) > 2:
        mod_website = reader.read_cstring()
        mod_download = reader.read_cstring()
        reader.read(1) # Skip a NULL byte
        mod_version = reader.read_uint32()
        mod_size = reader.read_uint32()
        multiplayer_only = reader.read_bool()
        uses_custom_dll = reader.read_bool()
    else:
        mod_website = None
        mod_download = None
        mod_version = None
        mod_size = None
        multiplayer_only = None
        uses_custom_dll = None

    vac_enabled = reader.read_bool()
    bot_count = reader.read_uint8()

    return GoldSrcInfo(
        address, server_name, map_name, folder, game, player_count, max_players, protocol,
        server_type, platform, password_protected, is_mod, vac_enabled, bot_count, mod_website,
        mod_download, mod_version, mod_size, multiplayer_only, uses_custom_dll, ping
    )
