from __future__ import annotations

import io
import struct
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

from a2s.exceptions import BufferExhaustedError

if TYPE_CHECKING:
    from typing_extensions import Literal

STRUCT_OPTIONS = Literal[
    "x", "c", "b", "B", "?", "h", "H", "i", "I", "l", "L", "q", "Q", "n", "N", "e", "f", "d", "s", "p", "P"
]


class ByteReader:
    __slots__ = (
        "stream",
        "endian",
        "encoding",
    )

    def __init__(self, stream: io.BytesIO, endian: str = "=", encoding: Optional[str] = None) -> None:
        self.stream: io.BytesIO = stream
        self.endian: str = endian
        self.encoding: Optional[str] = encoding

    def read(self, size: int = -1) -> bytes:
        data = self.stream.read(size)
        if size > -1 and len(data) != size:
            raise BufferExhaustedError()

        return data

    def peek(self, size: int = -1) -> bytes:
        cur_pos = self.stream.tell()
        data = self.stream.read(size)
        self.stream.seek(cur_pos, io.SEEK_SET)
        return data

    def unpack(self, fmt: STRUCT_OPTIONS) -> Tuple[Any, ...]:
        new_fmt = self.endian + fmt
        fmt_size = struct.calcsize(fmt)
        return struct.unpack(new_fmt, self.read(fmt_size))

    def unpack_one(self, fmt: STRUCT_OPTIONS) -> Any:
        values = self.unpack(fmt)
        assert len(values) == 1
        return values[0]

    def read_int8(self) -> int:
        return self.unpack_one("b")

    def read_uint8(self) -> int:
        return self.unpack_one("B")

    def read_int16(self) -> int:
        return self.unpack_one("h")

    def read_uint16(self) -> int:
        return self.unpack_one("H")

    def read_int32(self) -> int:
        return self.unpack_one("l")

    def read_uint32(self) -> int:
        return self.unpack_one("L")

    def read_int64(self) -> int:
        return self.unpack_one("q")

    def read_uint64(self) -> int:
        return self.unpack_one("Q")

    def read_float(self) -> float:
        return self.unpack_one("f")

    def read_double(self) -> float:
        return self.unpack_one("d")

    def read_bool(self) -> bool:
        return bool(self.unpack_one("b"))

    def read_char(self) -> Union[str, bytes]:
        char = self.unpack_one("c")
        if self.encoding is not None:
            return char.decode(self.encoding, errors="replace")
        else:
            return char

    def read_cstring(self, charsize: int = 1) -> Union[str, bytes]:
        string = b""
        while True:
            c = self.read(charsize)
            if int.from_bytes(c, "little") == 0:
                break
            else:
                string += c

        if self.encoding is not None:
            return string.decode(self.encoding, errors="replace")
        else:
            return string


class ByteWriter:
    __slots__ = (
        "stream",
        "endian",
        "encoding",
    )

    def __init__(self, stream: io.BytesIO, endian: str = "=", encoding: Optional[str] = None) -> None:
        self.stream: io.BytesIO = stream
        self.endian: str = endian
        self.encoding: Optional[str] = encoding

    def write(self, *args: bytes) -> int:
        return self.stream.write(*args)

    def pack(self, fmt: str, *values: Any) -> int:
        fmt = self.endian + fmt
        return self.stream.write(struct.pack(fmt, *values))

    def write_int8(self, val: int) -> None:
        self.pack("b", val)

    def write_uint8(self, val: int) -> None:
        self.pack("B", val)

    def write_int16(self, val: int) -> None:
        self.pack("h", val)

    def write_uint16(self, val: int) -> None:
        self.pack("H", val)

    def write_int32(self, val: int) -> None:
        self.pack("l", val)

    def write_uint32(self, val: int) -> None:
        self.pack("L", val)

    def write_int64(self, val: int) -> None:
        self.pack("q", val)

    def write_uint64(self, val: int) -> None:
        self.pack("Q", val)

    def write_float(self, val: float) -> None:
        self.pack("f", val)

    def write_double(self, val: float) -> None:
        self.pack("d", val)

    def write_bool(self, val: bool) -> None:
        self.pack("b", val)

    def write_char(self, val: Union[str, bytes]) -> None:
        if self.encoding is not None:
            assert isinstance(val, str)
            self.pack("c", val.encode(self.encoding))
        else:
            self.pack("c", val)

    def write_cstring(self, val: Union[str, bytes]) -> None:
        if self.encoding is not None:
            assert isinstance(val, str)
            self.write(val.encode(self.encoding) + b"\x00")
        else:
            assert isinstance(val, bytes)
            self.write(val + b"\x00")
