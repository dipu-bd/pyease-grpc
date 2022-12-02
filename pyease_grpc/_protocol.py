import struct
from typing import BinaryIO, Generator, Tuple, Type

from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message

_HEADER_FORMAT = ">BI"
_HEADER_LENGTH = struct.calcsize(_HEADER_FORMAT)


def _pack_header(trailer: bool, compressed: bool, length: int) -> bytes:
    flags = (trailer << 7) | (compressed)
    return struct.pack(_HEADER_FORMAT, flags, length)


def _unpack_header(message: bytes) -> Tuple[bool, bool, int]:
    flags, length = struct.unpack(_HEADER_FORMAT, message[:_HEADER_LENGTH])
    trailer = bool(flags & (1 << 7))
    compressed = bool(flags & 1)
    return trailer, compressed, length


def wrap_message(
    message: bytes, trailer: bool = False, compressed: bool = False
) -> bytes:
    header = _pack_header(trailer, compressed, len(message))
    return header + message


def unwrap_message(message: bytes) -> Tuple[bytes, bool, bool]:
    trailer, compressed, length = _unpack_header(message)
    start = _HEADER_LENGTH
    stop = _HEADER_LENGTH + length
    data = message[start:stop]
    if length != len(data):
        raise ValueError("Invalid data length: %d" % length)
    return data, trailer, compressed


def unwrap_message_stream(
    stream: BinaryIO,
) -> Generator[Tuple[bytes, bool, bool], None, None]:
    trailer = None
    while not trailer:
        header = stream.read(_HEADER_LENGTH)
        trailer, compressed, length = _unpack_header(header)
        data = stream.read(length)
        yield data, trailer, compressed


def serialize_timeout(seconds: float):
    return f"{int(seconds * 1e9)}n"


def serialize_message(
    message_type: Type[Message],
    data: dict,
    ignore_unknown=True,
) -> bytes:
    message = message_type()
    ParseDict(data, message, ignore_unknown_fields=ignore_unknown)
    return message.SerializeToString()


def deserialize_message(
    message_type: Type[Message],
    data: bytes,
    including_defaults=True,
    float_precision=None,
    use_integers_for_enums=False,
) -> dict:
    message = message_type.FromString(data)
    return MessageToDict(
        message,
        float_precision=float_precision,
        use_integers_for_enums=use_integers_for_enums,
        including_default_value_fields=including_defaults,
    )


def deserialize_trailer(data: bytes) -> dict:
    return dict([line.split(":", 1) for line in data.decode("utf8").splitlines()])
