import io
import logging
from typing import Optional, Union

import requests
from requests.structures import CaseInsensitiveDict

from . import _protocol
from .protoc import Protobuf
from .rpc_method import RpcUri
from .rpc_response import RpcResponse

log = logging.getLogger(__name__)


class RpcSession(object):
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
        self._session = requests.Session()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def request(
        self,
        uri: Union[str, RpcUri],
        data: dict,
        headers: Optional[CaseInsensitiveDict] = None,
        timeout: Optional[float] = None,
    ) -> RpcResponse:
        """Make gRPC-web request.

        Arguments:
            uri (str|RpcUri): URL builder object.
            data (dict): JSON serializable request data.
            headers ([dict]): Additional request headers.
            timeout ([float]): Timeout in seconds.

        Returns:
            RpcResponse:  The response with one or more payloads.
        """
        # Prepare request data
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

        headers = headers or CaseInsensitiveDict({})
        headers["x-grpc-web"] = "1"
        headers["content-type"] = "application/grpc-web+proto"
        if timeout is not None:
            grpc_timeout = _protocol.serialize_timeout(timeout)
            headers["grpc-timeout"] = grpc_timeout

        message = method.serialize_request(data)
        message = _protocol.wrap_message(message)

        # Fetch response
        response = self._session.post(
            uri.build(),
            data=message,
            timeout=timeout,
            headers=dict(headers),
            allow_redirects=True,
            stream=True,
        )

        rpc_response = RpcResponse(response)
        if rpc_response.status_code >= 400:
            return rpc_response

        # Read content stream
        content = response.content
        response.close()

        # Process response content
        buffer = io.BytesIO(content)
        messages = list(_protocol.unwrap_message_stream(buffer))
        buffer.close()

        for message, trailer, compressed in messages:
            if compressed:
                break
            if trailer:
                rpc_response.trailer = method.deserialize_trailer(message)
                break
            parsed = method.deserialize_response(message)
            rpc_response.payloads.append(parsed)

        return rpc_response
