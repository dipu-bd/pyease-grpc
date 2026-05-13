"""Tests for pyease_grpc/rpc_uri.py — URL parsing and building."""

import pytest

from pyease_grpc.rpc_uri import RpcUri

# ---------------------------------------------------------------------------
# RpcUri.parse
# ---------------------------------------------------------------------------


def test_parse_simple_url():
    uri = RpcUri.parse("http://localhost:8080/pkg.Service/Method")
    assert uri.package == "pkg"
    assert uri.service == "Service"
    assert uri.method == "Method"
    assert uri.base_url == "http://localhost:8080"


def test_parse_nested_package():
    uri = RpcUri.parse("http://localhost/a.b.c.d.Service/Method")
    assert uri.package == "a.b.c.d"
    assert uri.service == "Service"
    assert uri.method == "Method"


def test_parse_url_with_base_path():
    # Regression: rsplit("/", 3) would crash here; rsplit("/", 2) is correct
    uri = RpcUri.parse("http://localhost:8080/v1/prefix/pkg.Service/Method")
    assert uri.method == "Method"
    assert uri.service == "Service"
    assert uri.package == "pkg"


def test_parse_https_scheme_preserved():
    uri = RpcUri.parse("https://example.com/svc.Api/Call")
    assert uri.base_url.startswith("https://")


def test_parse_missing_hostname_raises():
    with pytest.raises(ValueError, match="Hostname is required"):
        RpcUri.parse("/pkg.Service/Method")


def test_parse_roundtrip():
    original = "http://localhost:50051/mypackage.MyService/MyMethod"
    uri = RpcUri.parse(original)
    assert uri.build() == original


# ---------------------------------------------------------------------------
# RpcUri.build
# ---------------------------------------------------------------------------


def test_build_adds_http_when_no_scheme():
    uri = RpcUri("localhost:8080", "pkg", "Svc", "Method")
    assert uri.build().startswith("http://")


def test_build_strips_trailing_slash_from_base():
    uri = RpcUri("http://localhost:8080/", "pkg", "Svc", "Method")
    assert "///" not in uri.build()


def test_build_produces_correct_path():
    uri = RpcUri("http://localhost", "a.b", "MySvc", "MyMethod")
    assert uri.build() == "http://localhost/a.b.MySvc/MyMethod"


def test_build_preserves_https():
    uri = RpcUri("https://api.example.com", "pkg", "Svc", "RPC")
    assert uri.build().startswith("https://")


# ---------------------------------------------------------------------------
# RpcUri.path
# ---------------------------------------------------------------------------


def test_path_property():
    uri = RpcUri("http://host", "my.pkg", "MySvc", "MyRpc")
    assert uri.path == "/my.pkg.MySvc/MyRpc"


# ---------------------------------------------------------------------------
# RpcUri.__str__
# ---------------------------------------------------------------------------


def test_str_equals_build():
    uri = RpcUri("http://localhost", "pkg", "Svc", "Method")
    assert str(uri) == uri.build()
