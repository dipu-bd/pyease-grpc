"""Tests for pyease_grpc/rpc_trailer.py — gRPC trailer / error handling."""

import grpc
import pytest

from pyease_grpc.rpc_trailer import RpcTrailer


def test_ok_status():
    t = RpcTrailer({"grpc-status": "0", "grpc-message": ""})
    assert t.is_ok()
    assert t.code() == grpc.StatusCode.OK


def test_ok_from_integer():
    t = RpcTrailer({"grpc-status": 0})
    assert t.is_ok()


def test_not_found_status():
    t = RpcTrailer({"grpc-status": "5", "grpc-message": "resource not found"})
    assert not t.is_ok()
    assert t.code() == grpc.StatusCode.NOT_FOUND
    assert t.details() == "resource not found"


def test_invalid_argument_status():
    t = RpcTrailer({"grpc-status": "3"})
    assert t.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_unknown_status_falls_back():
    t = RpcTrailer({"grpc-status": "999"})
    assert t.code() == grpc.StatusCode.UNKNOWN


def test_missing_status_falls_back():
    t = RpcTrailer({})
    assert t.code() == grpc.StatusCode.UNKNOWN


def test_string_numeric_status():
    t = RpcTrailer({"grpc-status": "  1  "})
    assert t.code() == grpc.StatusCode.CANCELLED


def test_grpc_message_in_details():
    t = RpcTrailer({"grpc-status": "2", "grpc-message": "something failed"})
    assert t.details() == "something failed"


def test_empty_message():
    t = RpcTrailer({"grpc-status": "0"})
    assert t.details() == ""


def test_is_subclass_of_rpc_error():
    t = RpcTrailer({"grpc-status": "2"})
    assert isinstance(t, grpc.RpcError)


def test_str_contains_code_and_message():
    t = RpcTrailer({"grpc-status": "2", "grpc-message": "boom"})
    s = str(t)
    assert "UNKNOWN" in s
    assert "boom" in s


@pytest.mark.parametrize("code", list(grpc.StatusCode))
def test_all_grpc_status_codes_recognized(code):
    numeric, name = code.value
    t = RpcTrailer({"grpc-status": str(numeric)})
    assert t.code() == code
