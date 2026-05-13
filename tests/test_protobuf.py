"""Tests for pyease_grpc/protobuf.py — descriptor loading, save/restore round-trip."""

import pytest

from pyease_grpc.protobuf import Protobuf
from pyease_grpc.rpc_method import RpcMethod
from pyease_grpc.rpc_method_type import MethodType
from pyease_grpc.rpc_uri import RpcUri

from .conftest import make_fds

# ---------------------------------------------------------------------------
# Fixture — a Protobuf built from a programmatic FDS (no grpcio-tools needed)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def proto():
    fds = make_fds(
        file_name="protobuf_test.proto",
        package="protobuf.test.v1",
        service_name="GreeterService",
        method_name="SayHello",
        request_name="HelloRequest",
        response_name="HelloResponse",
    )
    return Protobuf(fds)


@pytest.fixture(scope="module")
def streaming_proto():
    from google.protobuf.descriptor_pb2 import FileDescriptorSet

    from .conftest import make_file_descriptor

    fds = FileDescriptorSet()
    fds.file.append(
        make_file_descriptor(
            "protobuf_streaming.proto",
            package="protobuf.stream.v1",
            service_name="StreamSvc",
            method_name="ServerStream",
            server_streaming=True,
        )
    )
    fds.file.append(
        make_file_descriptor(
            "protobuf_bidi.proto",
            package="protobuf.bidi.v1",
            service_name="BidiSvc",
            method_name="BidiStream",
            client_streaming=True,
            server_streaming=True,
        )
    )
    return fds


# ---------------------------------------------------------------------------
# Message loading
# ---------------------------------------------------------------------------


def test_messages_loaded(proto):
    assert "protobuf.test.v1.HelloRequest" in proto.messages
    assert "protobuf.test.v1.HelloResponse" in proto.messages


def test_messages_are_constructible(proto):
    from google.protobuf.message import Message

    cls = proto.messages["protobuf.test.v1.HelloRequest"]
    assert isinstance(cls(), Message)


# ---------------------------------------------------------------------------
# Service / method discovery
# ---------------------------------------------------------------------------


def test_service_registered(proto):
    assert "GreeterService" in proto.services


def test_method_registered(proto):
    assert "SayHello" in proto.services["GreeterService"]


def test_method_type_is_unary_unary(proto):
    method = proto.services["GreeterService"]["SayHello"]
    assert method.type == MethodType.unary_unary


def test_method_package(proto):
    method = proto.services["GreeterService"]["SayHello"]
    assert method.package == "protobuf.test.v1"


def test_method_is_rpc_method_instance(proto):
    method = proto.services["GreeterService"]["SayHello"]
    assert isinstance(method, RpcMethod)


# ---------------------------------------------------------------------------
# get_method / has_method
# ---------------------------------------------------------------------------


def test_get_method_success(proto):
    uri = RpcUri("http://localhost", "protobuf.test.v1", "GreeterService", "SayHello")
    assert proto.get_method(uri) is not None


def test_get_method_wrong_service(proto):
    uri = RpcUri("http://localhost", "protobuf.test.v1", "NoSuchService", "SayHello")
    assert proto.get_method(uri) is None


def test_get_method_wrong_method(proto):
    uri = RpcUri("http://localhost", "protobuf.test.v1", "GreeterService", "NoSuchMethod")
    assert proto.get_method(uri) is None


def test_get_method_wrong_package(proto):
    uri = RpcUri("http://localhost", "wrong.package", "GreeterService", "SayHello")
    assert proto.get_method(uri) is None


def test_has_method_true(proto):
    uri = RpcUri("http://localhost", "protobuf.test.v1", "GreeterService", "SayHello")
    assert proto.has_method(uri)


def test_has_method_false(proto):
    uri = RpcUri("http://localhost", "protobuf.test.v1", "GreeterService", "Ghost")
    assert not proto.has_method(uri)


# ---------------------------------------------------------------------------
# save / restore round-trip
# ---------------------------------------------------------------------------


def test_save_returns_dict(proto):
    result = proto.save()
    assert isinstance(result, dict)


def test_save_restore_roundtrip(proto):
    saved = proto.save()
    restored = Protobuf.restore(saved)
    assert "GreeterService" in restored.services
    assert "SayHello" in restored.services["GreeterService"]


def test_save_is_idempotent(proto):
    first = proto.save()
    second = proto.save()
    assert first == second


def test_str_is_valid_json(proto):
    import json

    text = str(proto)
    parsed = json.loads(text)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Streaming method types loaded from FDS
# ---------------------------------------------------------------------------


def test_server_streaming_method_type(streaming_proto):
    proto = Protobuf(streaming_proto)
    method = proto.services["StreamSvc"]["ServerStream"]
    assert method.type == MethodType.unary_stream


def test_bidi_streaming_method_type(streaming_proto):
    from google.protobuf.descriptor_pb2 import FileDescriptorSet

    from .conftest import make_file_descriptor

    fds = FileDescriptorSet()
    fds.file.append(
        make_file_descriptor(
            "protobuf_bidi2.proto",
            package="protobuf.bidi2.v1",
            service_name="BidiSvc2",
            method_name="BidiStream",
            client_streaming=True,
            server_streaming=True,
        )
    )
    pb = Protobuf(fds)
    assert pb.services["BidiSvc2"]["BidiStream"].type == MethodType.stream_stream


# ---------------------------------------------------------------------------
# restore_file
# ---------------------------------------------------------------------------


def test_restore_file(proto, tmp_path):
    path = tmp_path / "descriptor.json"
    proto.save_file(str(path))
    restored = Protobuf.restore_file(str(path))
    assert "GreeterService" in restored.services
