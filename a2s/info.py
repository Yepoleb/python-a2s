import io
from dataclasses import dataclass, field
from typing import Optional

from a2s.exceptions import BrokenMessageError, BufferExhaustedError
from a2s.defaults import DEFAULT_TIMEOUT, DEFAULT_ENCODING
from a2s.a2s_sync import request_sync
from a2s.a2s_async import request_async
from a2s.byteio import ByteReader
from a2s.datacls import DataclsMeta



A2S_INFO_RESPONSE = 0x49
A2S_INFO_RESPONSE_LEGACY = 0x6D

@dataclass
class SourceInfo(): # metaclass=DataclsMeta
    """Protocol version used by the server"""
    protocol: Optional[int] = None
    server_name: Optional[str] = None
    map_name: Optional[str] = None
    folder: Optional[str] = None
    game: Optional[str] = None
    app_id: Optional[int] = None
    player_count: Optional[int] = None
    max_players: Optional[int] = None
    bot_count: Optional[int] = None
    server_type: Optional[str] = None
    platform: Optional[str] = None
    password_protected: Optional[bool] = None
    vac_enabled: Optional[bool] = None
    version: Optional[str] = None
    edf: Optional[int] = 0
    port: Optional[int] = None
    steam_id: Optional[int] = None
    stv_port: Optional[int] = None
    stv_name: Optional[str] = None
    keywords: Optional[str] = None
    game_id: Optional[int] = None
    ping: Optional[float] = None

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
class GoldSrcInfo(): # metaclass=DataclsMeta
    """IP Address and port of the server"""
    address: Optional[str] = None
    server_name: Optional[str] = None
    map_name: Optional[str] = None
    folder: Optional[str] = None
    game: Optional[str] = None
    player_count: Optional[int] = None
    max_players: Optional[int] = None
    protocol: Optional[int] = None
    server_type: Optional[str] = None
    platform: Optional[str] = None
    password_protected: Optional[bool] = None
    is_mod: Optional[bool] = None
    vac_enabled: Optional[bool] = None
    bot_count: Optional[int] = None
    mod_website: Optional[str] = None
    mod_download: Optional[str] = None
    mod_version: Optional[int] = None
    mod_size: Optional[int] = None
    multiplayer_only: Optional[bool] = False
    uses_hl_dll: Optional[bool] = True
    ping: Optional[float] = None


def info(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
    return request_sync(address, timeout, encoding, InfoProtocol)

async def ainfo(address, timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
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
            resp = parse_source(reader)
        elif response_type == A2S_INFO_RESPONSE_LEGACY:
            resp = parse_goldsrc(reader)
        else:
            raise Exception(str(response_type))

        resp.ping = ping
        return resp

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
