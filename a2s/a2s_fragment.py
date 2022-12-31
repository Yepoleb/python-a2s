"""
MIT License

Copyright (c) 2020 Gabriel Huber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import bz2
import io

from a2s.byteio import ByteReader


class A2SFragment:
    __slots__ = (
        "message_id",
        "fragment_count",
        "fragment_id",
        "mtu",
        "decompressed_size",
        "crc",
        "payload",
    )

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
