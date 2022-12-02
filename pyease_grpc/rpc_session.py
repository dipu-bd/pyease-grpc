import logging
from typing import List, Optional, Union

from requests import Session
from requests.cookies import RequestsCookieJar
from requests.structures import CaseInsensitiveDict

from . import _protocol
from .protoc import Protobuf
from .rpc_method import RpcUri
from .rpc_response import RpcResponse

log = logging.getLogger(__name__)


class RpcSession(object):
    @classmethod
    def from_file(
        cls,
        proto_file: str,
        include_paths: List[str] = [],
        work_dir: Optional[str] = None,
    ):
        """Make a :class:`RpcSession` from a proto file.

        Arguments:
            proto_file (str) A *.proto file containing protobuf definitions.
            include_paths (List[str]) Additional paths to include when parsing. Default = []
            work_dir (Optional[str]): Main working folder. Default = None
        """
        return cls(
            Protobuf.from_file(
                proto_file=proto_file,
                include_paths=include_paths,
                work_dir=work_dir,
            )
        )

    @classmethod
    def from_descriptor(cls, descriptor_json: dict):
        """Make a :class:`RpcSession` from a file description set message.

        Arguments:
            descriptor_json (dict): File descriptor set message content.
        """
        return cls(Protobuf.restore(descriptor_json))

    def __init__(self, proto: Protobuf) -> None:
        """Initializes a new RpcSession.

        Arguments:
            proto (Protobuf): The protobuf definition.
        """
        self._proto = proto
        self._session = Session()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    @property
    def session(self) -> Session:
        """The internal session used for the gRPC-Web request"""
        return self._session

    def request(
        self,
        uri: Union[str, RpcUri],
        data: dict,
        headers: Optional[CaseInsensitiveDict] = None,
        timeout: Optional[float] = None,
        cookies: Optional[Union[dict, RequestsCookieJar]] = None,
        auth: Optional[tuple] = None,
        proxies: Optional[dict] = None,
        verify: bool = True,
        cert: Optional[Union[str, tuple]] = None,
    ) -> RpcResponse:
        """Calls a gRPC-Web method and gets the response.

        Arguments:
            uri (str|RpcUri): Full URL of an RPC method, or an :class:`RpcUri` instance.
            data (dict): Request message as JSON.
            headers (dict): Additional request headers.
            timeout (float): Timeout in seconds. If None, no timeout will be enforced.

        Keyword Arguments:
            cookies (dict|CookieJar): Send with the :class:`Request`.
            auth (tuple) Auth tuple or callable to enable Basic/Digest/Custom HTTP Auth.
            proxies (dict) Request proxy mappings
            verify (bool) Either a boolean, in which case it controls whether we verify
                the server's TLS certificate, or a string, in which case it must be a path
                to a CA bundle to use. Defaults to ``True``. When set to
                ``False``, requests will accept any TLS certificate presented by
                the server, and will ignore hostname mismatches and/or expired
                certificates, which will make your application vulnerable to
                man-in-the-middle (MitM) attacks. Setting verify to ``False``
                may be useful during local development or testing.
            cert (str|tuple) if String, path to ssl client cert file (.pem).
                If Tuple, ('cert', 'key') pair.

        Returns:
            An :class:`RpcResponse` with one or more payloads.
        """
        # Prepare protobuf method
        if isinstance(uri, str):
            uri = RpcUri.parse(uri)

        if uri.service not in self._proto.services:
            raise ValueError("No such service: " + uri.service)
        service = self._proto.services[uri.service]

        if uri.method not in service:
            raise ValueError("No such method: " + uri.method)
        method = service[uri.method]

        if uri.package != method.package:
            raise ValueError("Invalid package name: " + uri.package)

        # Prepare request headers
        headers = headers or CaseInsensitiveDict({})
        headers["x-grpc-web"] = "1"
        headers["content-type"] = "application/grpc-web+proto"
        if timeout is not None:
            grpc_timeout = _protocol.serialize_timeout(timeout)
            headers["grpc-timeout"] = grpc_timeout

        # Prepare request data
        message = method.serialize_request(data)
        message = _protocol.wrap_message(message)

        # Get the response
        response = self._session.post(
            uri.build(),
            data=message,
            timeout=timeout,
            headers=dict(headers),
            allow_redirects=True,
            stream=True,
            auth=auth,
            cookies=cookies,
            verify=verify,
            cert=cert,
            proxies=proxies,
        )

        return RpcResponse(response, method)
