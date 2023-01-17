import bz2
import io

from a2s.byteio import ByteReader


class A2SFragment:
    def __init__(
        self,
        message_id: int,
        fragment_count: int,
        fragment_id: int,
        mtu: int,
        decompressed_size: int = 0,
        crc: int = 0,
        payload: bytes = b"",
    ) -> None:
        self.message_id: int = message_id
        self.fragment_count: int = fragment_count
        self.fragment_id: int = fragment_id
        self.mtu: int = mtu
        self.decompressed_size: int = decompressed_size
        self.crc: int = crc
        self.payload: bytes = payload

    @property
    def is_compressed(self) -> bool:
        return bool(self.message_id & (1 << 15))


def decode_fragment(data: bytes) -> A2SFragment:
    reader = ByteReader(io.BytesIO(data), endian="<", encoding="utf-8")
    frag = A2SFragment(
        message_id=reader.read_uint32(),
        fragment_count=reader.read_uint8(),
        fragment_id=reader.read_uint8(),
        mtu=reader.read_uint16(),
    )
    if frag.is_compressed:
        frag.decompressed_size = reader.read_uint32()
        frag.crc = reader.read_uint32()
        frag.payload = bz2.decompress(reader.read())
    else:
        frag.payload = reader.read()

    return frag
