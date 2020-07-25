import bz2
import io

from a2s.byteio import ByteReader



class A2SFragment:
    def __init__(self, message_id, fragment_count, fragment_id, mtu,
                 decompressed_size=0, crc=0, payload=b""):
        self.message_id = message_id
        self.fragment_count = fragment_count
        self.fragment_id = fragment_id
        self.mtu = mtu
        self.decompressed_size = decompressed_size
        self.crc = crc
        self.payload = payload

    @property
    def is_compressed(self):
        return bool(self.message_id & (1 << 15))

def decode_fragment(data):
    reader = ByteReader(
        io.BytesIO(data), endian="<", encoding="utf-8")
    frag = A2SFragment(
        message_id=reader.read_uint32(),
        fragment_count=reader.read_uint8(),
        fragment_id=reader.read_uint8(),
        mtu=reader.read_uint16()
    )
    if frag.is_compressed:
        frag.decompressed_size = reader.read_uint32()
        frag.crc = reader.read_uint32()
        frag.payload = bz2.decompress(reader.read())
    else:
        frag.payload = reader.read()

    return frag
