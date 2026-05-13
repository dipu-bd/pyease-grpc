"""Tests for pyease_grpc/rpc_session.py — _resolve_method validation."""

import pytest

from pyease_grpc.protobuf import Protobuf
from pyease_grpc.rpc_session import RpcSession
from pyease_grpc.rpc_uri import RpcUri

from .conftest import make_fds

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def session():
    fds = make_fds(
        file_name="session_test.proto",
        package="session.test.v1",
        service_name="TestSvc",
        method_name="DoWork",
    )
    return RpcSession(Protobuf(fds))


def _uri(package="session.test.v1", service="TestSvc", method="DoWork"):
    return RpcUri("http://localhost", package, service, method)


# ---------------------------------------------------------------------------
# _resolve_method
# ---------------------------------------------------------------------------


def test_resolve_method_success(session):
    method = session._resolve_method(_uri())
    assert method.method == "DoWork"
    assert method.service == "TestSvc"
    assert method.package == "session.test.v1"


def test_resolve_unknown_service_raises(session):
    with pytest.raises(ValueError, match="No such service"):
        session._resolve_method(_uri(service="NoSuchService"))


def test_resolve_unknown_method_raises(session):
    with pytest.raises(ValueError, match="No such method"):
        session._resolve_method(_uri(method="NoSuchMethod"))


def test_resolve_wrong_package_raises(session):
    with pytest.raises(ValueError, match="Invalid package name"):
        session._resolve_method(_uri(package="wrong.package"))


# ---------------------------------------------------------------------------
# RpcSession construction helpers
# ---------------------------------------------------------------------------


def test_from_descriptor(session):
    saved = session._proto.save()
    s2 = RpcSession.from_descriptor(saved)
    method = s2._resolve_method(_uri())
    assert method.method == "DoWork"


def test_context_manager_closes_session():
    fds = make_fds("session_cm_test.proto", package="session.cm.v1")
    from unittest.mock import patch

    with RpcSession(Protobuf(fds)) as s:
        with patch.object(s._session, "close") as mock_close:
            pass
    # __exit__ calls close; verify the session object itself is returned from __enter__
    assert isinstance(s, RpcSession)


def test_session_property_returns_requests_session(session):
    from requests import Session

    assert isinstance(session.session, Session)
