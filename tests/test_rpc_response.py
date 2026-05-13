"""Tests for RpcResponse, RpcNativeResponse, and RpcWebResponse."""

from unittest.mock import MagicMock, patch

from google.protobuf.struct_pb2 import Value
import grpc
import pytest

from pyease_grpc.rpc_response import RpcResponse
from pyease_grpc.rpc_response_native import RpcNativeResponse
from pyease_grpc.rpc_response_web import RpcWebResponse

# ---------------------------------------------------------------------------
# RpcResponse (base)
# ---------------------------------------------------------------------------


def test_response_empty_by_default():
    r = RpcResponse()
    assert r.payloads == []
    assert r.single is None


def test_response_with_initial_payloads():
    data = [{"a": 1}, {"b": 2}]
    r = RpcResponse(payloads=data)
    assert r.payloads == data


def test_response_single_returns_last():
    r = RpcResponse(payloads=[{"x": 1}, {"x": 2}])
    assert r.single == {"x": 2}


def test_response_iter_payloads():
    r = RpcResponse(payloads=[{"n": i} for i in range(3)])
    assert list(r.iter_payloads()) == [{"n": 0}, {"n": 1}, {"n": 2}]


def test_response_mutable_default_not_shared():
    # Each instance must get its own list, not share the class-level default
    r1 = RpcResponse()
    r2 = RpcResponse()
    r1._payloads.append({"x": 1})
    assert r2.payloads == []


# ---------------------------------------------------------------------------
# RpcNativeResponse
# ---------------------------------------------------------------------------


def _make_native_response(*dicts):
    """Build an RpcNativeResponse whose iterator yields real protobuf Values."""
    messages = [Value(string_value=str(d)) for d in dicts]
    channel = MagicMock(spec=grpc.Channel)
    return RpcNativeResponse(channel, iter(messages)), channel


def test_native_response_iter_payloads():
    resp, _ = _make_native_response("hello", "world")
    payloads = list(resp.iter_payloads())
    assert len(payloads) == 2


def test_native_response_cached_after_first_iter():
    resp, _ = _make_native_response("a", "b")
    first = list(resp.iter_payloads())
    second = list(resp.iter_payloads())
    assert first == second


def test_native_response_payloads_property_drains_stream():
    resp, _ = _make_native_response("x")
    # Access .payloads without calling iter_payloads first
    assert len(resp.payloads) == 1


def test_native_response_single():
    resp, _ = _make_native_response("only-one")
    assert resp.single is not None


def test_native_response_context_manager_closes_channel():
    resp, channel = _make_native_response("msg")
    with resp:
        list(resp.iter_payloads())
    channel.close.assert_called_once()


def test_native_response_context_manager_closes_on_exception():
    resp, channel = _make_native_response()
    try:
        with resp:
            raise RuntimeError("oops")
    except RuntimeError:
        pass
    channel.close.assert_called_once()


def test_native_response_close_method():
    resp, channel = _make_native_response()
    resp.close()
    channel.close.assert_called_once()


# ---------------------------------------------------------------------------
# RpcWebResponse
# ---------------------------------------------------------------------------


def _make_web_response(status_code: int, stream_frames=None):
    """Build an RpcWebResponse with a mock method and mock requests.Response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_method = MagicMock()
    mock_method.deserialize_trailer.return_value = MagicMock(is_ok=lambda: True)
    if stream_frames is not None:
        mock_method.deserialize_response_dict.side_effect = lambda b: {"raw": b.decode()}

    resp = RpcWebResponse(mock_method, mock_response)
    return resp, mock_response, mock_method


def test_web_response_4xx_yields_nothing():
    resp, _, _ = _make_web_response(400)
    assert list(resp.iter_payloads()) == []
    assert resp.payloads == []


def test_web_response_4xx_sets_ready():
    resp, _, _ = _make_web_response(404)
    list(resp.iter_payloads())
    assert resp._payloads_ready


@patch("pyease_grpc.rpc_response_web._protocol.unwrap_message_stream")
def test_web_response_yields_data_frames(mock_unwrap):
    payload = {"key": "value"}
    mock_unwrap.return_value = iter(
        [
            (b"data", False, False),
            (b"grpc-status:0\r\n", True, False),
        ]
    )
    resp, _, mock_method = _make_web_response(200)
    mock_method.deserialize_response_dict.return_value = payload
    mock_method.deserialize_trailer.return_value = MagicMock(is_ok=lambda: True)

    payloads = list(resp.iter_payloads())
    assert payloads == [payload]


@patch("pyease_grpc.rpc_response_web._protocol.unwrap_message_stream")
def test_web_response_raises_on_non_ok_trailer(mock_unwrap):
    from pyease_grpc.rpc_trailer import RpcTrailer

    error_trailer = RpcTrailer({"grpc-status": "2", "grpc-message": "internal"})
    mock_unwrap.return_value = iter(
        [
            (b"trailer", True, False),
        ]
    )
    resp, _, mock_method = _make_web_response(200)
    mock_method.deserialize_trailer.return_value = error_trailer

    with pytest.raises(RpcTrailer):
        list(resp.iter_payloads())


@patch("pyease_grpc.rpc_response_web._protocol.unwrap_message_stream")
def test_web_response_raises_on_compressed(mock_unwrap):
    mock_unwrap.return_value = iter([(b"data", False, True)])
    resp, _, _ = _make_web_response(200)

    with pytest.raises(NotImplementedError):
        list(resp.iter_payloads())


@patch("pyease_grpc.rpc_response_web._protocol.unwrap_message_stream")
def test_web_response_cached_after_first_iter(mock_unwrap):
    mock_unwrap.return_value = iter(
        [
            (b"d", False, False),
            (b"grpc-status:0\r\n", True, False),
        ]
    )
    resp, _, mock_method = _make_web_response(200)
    mock_method.deserialize_response_dict.return_value = {"n": 1}
    mock_method.deserialize_trailer.return_value = MagicMock(is_ok=lambda: True)

    first = list(resp.iter_payloads())
    second = list(resp.iter_payloads())
    assert first == second
    # unwrap_message_stream was only called once (the second iter used cache)
    assert mock_unwrap.call_count == 1


def test_web_response_headers_property():
    resp, mock_response, _ = _make_web_response(200)
    mock_response.headers = {"content-type": "application/grpc-web+proto"}
    assert resp.headers == {"content-type": "application/grpc-web+proto"}


def test_web_response_close():
    resp, mock_response, _ = _make_web_response(200)
    resp.close()
    mock_response.close.assert_called_once()
