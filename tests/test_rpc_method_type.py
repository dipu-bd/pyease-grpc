"""Tests for pyease_grpc/rpc_method_type.py."""
import pytest

from pyease_grpc.rpc_method_type import MethodType, get_method_type


@pytest.mark.parametrize(
    "client_streaming,server_streaming,expected",
    [
        (False, False, MethodType.unary_unary),
        (False, True, MethodType.unary_stream),
        (True, False, MethodType.stream_unary),
        (True, True, MethodType.stream_stream),
    ],
)
def test_get_method_type(client_streaming, server_streaming, expected):
    assert get_method_type(client_streaming, server_streaming) is expected


def test_method_type_str():
    assert str(MethodType.unary_unary) == "unary_unary"
    assert str(MethodType.unary_stream) == "unary_stream"
    assert str(MethodType.stream_unary) == "stream_unary"
    assert str(MethodType.stream_stream) == "stream_stream"


def test_method_type_values_are_strings():
    for mt in MethodType:
        assert isinstance(mt.value, str)
