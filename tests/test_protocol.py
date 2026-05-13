"""Tests for pyease_grpc/_protocol.py — framing, serialization, descriptor helpers."""

import struct
from unittest.mock import MagicMock

import pytest
from requests.exceptions import ContentDecodingError, InvalidHeader

from pyease_grpc._protocol import (
    _HEADER_FORMAT,
    _HEADER_LENGTH,
    _ensure_fds_in_pool,
    _strip_extension_brackets,
    deserialize_trailer,
    load_messages,
    serialize_timeout,
    unwrap_message,
    unwrap_message_stream,
    wrap_message,
)

from .conftest import make_fds

# ---------------------------------------------------------------------------
# wrap_message / unwrap_message
# ---------------------------------------------------------------------------


def test_wrap_unwrap_roundtrip():
    data = b"hello world"
    result, trailer, compressed = unwrap_message(wrap_message(data))
    assert result == data
    assert not trailer
    assert not compressed


def test_wrap_trailer_flag():
    data = b"trailer content"
    _, trailer, _ = unwrap_message(wrap_message(data, trailer=True))
    assert trailer


def test_wrap_compressed_flag():
    data = b"compressed content"
    _, _, compressed = unwrap_message(wrap_message(data, compressed=True))
    assert compressed


def test_wrap_empty_payload():
    result, _, _ = unwrap_message(wrap_message(b""))
    assert result == b""


def test_header_length_is_five_bytes():
    assert _HEADER_LENGTH == 5


def test_unwrap_length_mismatch_raises():
    # Header claims 100 bytes, only a few bytes follow
    header = struct.pack(_HEADER_FORMAT, 0, 100)
    with pytest.raises(ContentDecodingError):
        unwrap_message(header + b"short")


# ---------------------------------------------------------------------------
# unwrap_message_stream
# ---------------------------------------------------------------------------


def _build_stream(*payloads: bytes, trailer_data: bytes = b"grpc-status:0\r\n") -> bytes:
    stream = b"".join(wrap_message(p) for p in payloads)
    stream += wrap_message(trailer_data, trailer=True)
    return stream


def _mock_response(data: bytes, chunk_size: int = 0) -> MagicMock:
    mock = MagicMock()
    if chunk_size:
        chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]
    else:
        chunks = [data]
    mock.iter_content.return_value = iter(chunks)
    return mock


def test_stream_single_message():
    payload = b"single"
    frames = list(unwrap_message_stream(_mock_response(_build_stream(payload))))
    data_frames = [f for f in frames if not f[1]]
    assert len(data_frames) == 1
    assert data_frames[0][0] == payload


def test_stream_multiple_messages():
    payloads = [b"one", b"two", b"three"]
    frames = list(unwrap_message_stream(_mock_response(_build_stream(*payloads))))
    data_frames = [f[0] for f in frames if not f[1]]
    assert data_frames == payloads


def test_stream_last_frame_is_trailer():
    frames = list(unwrap_message_stream(_mock_response(_build_stream(b"msg"))))
    assert frames[-1][1] is True  # trailer flag


def test_stream_empty_payload():
    frames = list(unwrap_message_stream(_mock_response(_build_stream(b""))))
    data_frames = [f for f in frames if not f[1]]
    assert data_frames[0][0] == b""


def test_stream_chunked_delivery():
    payload = b"chunked-data"
    stream = _build_stream(payload)
    # Deliver in 1-byte chunks to exercise the read_upto reassembly loop
    frames = list(unwrap_message_stream(_mock_response(stream, chunk_size=1)))
    data_frames = [f[0] for f in frames if not f[1]]
    assert data_frames[0] == payload


def test_stream_truncated_header_raises():
    mock = MagicMock()
    mock.iter_content.return_value = iter([b"\x00\x00"])  # 2 bytes, need 5
    with pytest.raises(InvalidHeader):
        list(unwrap_message_stream(mock))


def test_stream_truncated_body_raises():
    # Header says 50 bytes but stream ends immediately
    header = struct.pack(_HEADER_FORMAT, 0, 50)
    mock = MagicMock()
    mock.iter_content.return_value = iter([header + b"short"])
    with pytest.raises(ContentDecodingError):
        list(unwrap_message_stream(mock))


# ---------------------------------------------------------------------------
# serialize_timeout
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (1.0, "1000000000n"),
        (0.5, "500000000n"),
        (0.0, "0n"),
        (60.0, "60000000000n"),
    ],
)
def test_serialize_timeout(seconds, expected):
    assert serialize_timeout(seconds) == expected


# ---------------------------------------------------------------------------
# deserialize_trailer
# ---------------------------------------------------------------------------


def test_deserialize_trailer_simple():
    data = b"grpc-status:0\r\ngrpc-message:OK"
    result = deserialize_trailer(data)
    assert result["grpc-status"] == "0"
    assert result["grpc-message"] == "OK"


def test_deserialize_trailer_value_with_colon():
    data = b"grpc-message:error: something went wrong"
    result = deserialize_trailer(data)
    assert result["grpc-message"] == "error: something went wrong"


def test_deserialize_trailer_single_entry():
    data = b"grpc-status:2"
    assert deserialize_trailer(data) == {"grpc-status": "2"}


# ---------------------------------------------------------------------------
# _strip_extension_brackets
# ---------------------------------------------------------------------------


def test_strip_flat_bracket_key():
    obj = {"[pkg.option]": "value", "normal": 1}
    _strip_extension_brackets(obj)
    assert "pkg.option" in obj
    assert obj["pkg.option"] == "value"
    assert "[pkg.option]" not in obj
    assert obj["normal"] == 1


def test_strip_no_brackets_unchanged():
    obj = {"a": 1, "b": {"c": 2}}
    _strip_extension_brackets(obj)
    assert obj == {"a": 1, "b": {"c": 2}}


def test_strip_recursion_into_nested_dict():
    obj = {"outer": {"[pkg.inner]": "deep"}}
    _strip_extension_brackets(obj)
    assert "pkg.inner" in obj["outer"]
    assert "[pkg.inner]" not in obj["outer"]


def test_strip_recursion_into_list_of_dicts():
    obj = {"items": [{"[pkg.opt]": "x"}, {"plain": "y"}]}
    _strip_extension_brackets(obj)
    assert "pkg.opt" in obj["items"][0]
    assert "[pkg.opt]" not in obj["items"][0]
    assert "plain" in obj["items"][1]


def test_strip_bracket_key_value_is_also_recursed():
    # Regression test: the original code used `elif` so bracket key values
    # were never recursed into. The fix changed it to `if`.
    obj = {"[pkg.outer]": {"[pkg.inner]": "deep_value", "normal": 1}}
    _strip_extension_brackets(obj)
    assert "pkg.outer" in obj
    assert "[pkg.outer]" not in obj
    inner = obj["pkg.outer"]
    assert "pkg.inner" in inner
    assert "[pkg.inner]" not in inner
    assert inner["pkg.inner"] == "deep_value"


def test_strip_non_dict_passthrough():
    assert _strip_extension_brackets("string") == "string"
    assert _strip_extension_brackets(42) == 42
    assert _strip_extension_brackets(None) is None


def test_strip_multiple_bracket_keys():
    obj = {"[a.b]": 1, "[c.d]": 2, "plain": 3}
    _strip_extension_brackets(obj)
    assert set(obj.keys()) == {"a.b", "c.d", "plain"}


# ---------------------------------------------------------------------------
# load_messages
# ---------------------------------------------------------------------------


def test_load_messages_with_package():
    fds = make_fds("load_messages_pkg.proto", package="load.messages.v1")
    messages = load_messages(fds)
    assert "load.messages.v1.Request" in messages
    assert "load.messages.v1.Response" in messages


def test_load_messages_returns_message_classes():
    from google.protobuf.message import Message

    fds = make_fds("load_messages_cls.proto", package="load.messages.cls.v1")
    messages = load_messages(fds)
    cls = messages["load.messages.cls.v1.Request"]
    # The value is a class, not an instance
    assert isinstance(cls(), Message)


def test_load_messages_without_package():
    # Proto with no package — key should be bare message name, not ".MessageName"
    from google.protobuf.descriptor_pb2 import (
        DescriptorProto,
        FieldDescriptorProto,
        FileDescriptorProto,
        FileDescriptorSet,
    )

    proto = FileDescriptorProto(name="no_package_load.proto", syntax="proto3")
    msg = DescriptorProto(name="StandaloneMsg")
    msg.field.add(
        name="x",
        number=1,
        type=FieldDescriptorProto.TYPE_INT32,
        label=FieldDescriptorProto.LABEL_OPTIONAL,
    )
    proto.message_type.append(msg)
    fds = FileDescriptorSet()
    fds.file.append(proto)

    messages = load_messages(fds)
    assert "StandaloneMsg" in messages
    assert ".StandaloneMsg" not in messages


# ---------------------------------------------------------------------------
# _ensure_fds_in_pool (idempotent)
# ---------------------------------------------------------------------------


def test_ensure_fds_in_pool_is_idempotent():
    fds = make_fds("ensure_pool_idem.proto", package="ensure.pool.v1")
    # Calling twice must not raise
    _ensure_fds_in_pool(fds)
    _ensure_fds_in_pool(fds)
