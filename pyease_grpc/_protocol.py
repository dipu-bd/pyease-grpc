import logging
import os
import struct
from typing import Dict, Generator, List, Tuple, Type

from google.protobuf import reflection, symbol_database
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message
from requests import Response
from requests.exceptions import InvalidHeader, ContentDecodingError

logger = logging.getLogger(__name__)

_HEADER_FORMAT = ">BI"
_HEADER_LENGTH = struct.calcsize(_HEADER_FORMAT)
_DEFAULT_CHUNK_SIZE = 512


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
        raise ContentDecodingError(f"Expected {length} bytes, got {len(data)} bytes")
    return data, trailer, compressed


def unwrap_message_stream(
    response: Response,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
) -> Generator[Tuple[bytes, bool, bool], None, None]:
    it = response.iter_content(chunk_size)

    def read_upto(length, previous):
        while len(previous) < length:
            try:
                previous += next(it)
            except StopIteration:
                break
        return previous[:length], previous[length:]

    content = b""
    trailer = None
    while not trailer:
        header, content = read_upto(_HEADER_LENGTH, content)
        if len(header) != _HEADER_LENGTH:
            raise InvalidHeader(
                f"Expected {_HEADER_LENGTH} bytes, got {len(header)} bytes"
            )
        trailer, compressed, length = _unpack_header(header)
        data, content = read_upto(length, content)
        if length != len(data):
            raise ContentDecodingError(
                f"Expected {length} bytes, got {len(data)} bytes"
            )
        yield data, trailer, compressed


def serialize_timeout(seconds: float):
    return f"{int(seconds * 1e9)}n"


def parse_message(
    message_type: Type[Message],
    data: dict,
    ignore_unknown=True,
) -> bytes:
    message = message_type()
    return ParseDict(data, message, ignore_unknown_fields=ignore_unknown)


def serialize_message(
    message_type: Type[Message],
    data: dict,
    ignore_unknown=True,
) -> bytes:
    message = parse_message(message_type, data, ignore_unknown)
    return message.SerializeToString()


def message_to_dict(
    message: Message,
    including_defaults=True,
    float_precision=None,
    use_integers_for_enums=False,
) -> dict:
    return MessageToDict(
        message,
        float_precision=float_precision,
        use_integers_for_enums=use_integers_for_enums,
        including_default_value_fields=including_defaults,
    )


def deserialize_message(message_type: Type[Message], data: bytes) -> dict:
    return message_type.FromString(data)


def deserialize_trailer(data: bytes) -> dict:
    return dict([line.split(":", 1) for line in data.decode("utf8").splitlines()])


def load_messages(fds: FileDescriptorSet) -> Dict[str, Type[Message]]:
    db = symbol_database.Default()
    messages: Dict[str, Type[Message]] = {}
    for proto in fds.file:
        db.pool.Add(proto)
        for message in proto.message_type:
            name = proto.package + "." + message.name
            md = db.pool.FindMessageTypeByName(name)
            messages[name] = reflection.MakeClass(md)
    return messages


def get_resource_path(package, path):
    try:
        import pkg_resources

        return pkg_resources.resource_filename(package, path)
    except Exception:
        import importlib.resources

        files = importlib.resources.files(package)
        return os.path.abspath(str(files / path))


def generate_descriptor(out_file: str, proto_file: str, include_paths: List[str] = []):
    try:
        from grpc_tools import protoc
    except ImportError as e:
        logger.debug(
            str(e) + " Run 'pip install grpcio-tools' to install it."
            " It is required to parse proto files."
        )
        raise ModuleNotFoundError("Missing package: 'grpcio-tools'") from e

    if not os.path.isfile(proto_file):
        raise FileNotFoundError(proto_file)

    out_file = os.path.abspath(out_file)
    proto_file = os.path.abspath(proto_file)

    if not include_paths:
        include_paths = [os.path.dirname(proto_file)]
    include_paths = [os.path.abspath(x) for x in include_paths if os.path.isdir(x)]

    protoc_py_file = os.path.abspath(protoc.__file__)
    proto_include = get_resource_path("grpc_tools", "_proto")

    protoc_config = [
        protoc_py_file,
        "--proto_path",
        proto_include,
    ]

    for path in set(include_paths):
        protoc_config += [
            "--proto_path",
            str(path),
        ]

    protoc_config += [
        "--descriptor_set_out",
        out_file,
        "--include_imports",
        proto_file,
    ]

    protoc.main(protoc_config)
    return out_file
