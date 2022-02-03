import io
import logging
from typing import Optional, Union

import requests

from . import protocol
from .options import RequestOptions
from .protoc import Protobuf
from .rpc_method import RpcUri
from .rpc_response import RpcResponse

log = logging.getLogger(__name__)


class RpcSession(object):

    @classmethod
    def from_descriptor(cls, descriptor_json: dict):
        return cls(Protobuf.restore(descriptor_json))

    def __init__(self, proto: Protobuf) -> None:
        """Initialize a new RpcSession.

        Args:
            proto (Protobuf): The protobuf definition.
        """
        self._proto = proto
        self._session = requests.Session()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def request(self,
                uri: Union[str, RpcUri],
                data: dict,
                opt: Optional[RequestOptions] = None) -> RpcResponse:
        """Make gRPC-web request.

        Args:
            uri (str|RpcUri): URL builder object.
            data (dict): JSON serializable request data.
            opt ([RequestOptions]): Request options.

        Returns:
            RpcResponse:  The response with one or more payloads.
        """
        # Prepare request data
        if isinstance(uri, str):
            uri = RpcUri.parse(uri)

        if uri.service not in self._proto.services:
            raise ValueError('No such service: ' + uri.service)
        service = self._proto.services[uri.service]

        if uri.method not in service:
            raise ValueError('No such method: ' + uri.method)
        method = service[uri.method]

        if uri.package != method.package:
            raise ValueError('Invalid package name: ' + uri.package)

        opt = opt or RequestOptions()
        if opt.timeout is not None:
            grpc_timeout = protocol.serialize_timeout(opt.timeout)
            opt.metadata['grpc-timeout'] = grpc_timeout

        message = method.serialize_request(data)
        message = protocol.wrap_message(message)

        # Fetch response
        response = self._session.post(
            uri.build(),
            data=message,
            timeout=opt.timeout,
            headers=dict(opt.metadata),
            allow_redirects=True,
            stream=True,
        )
        if response.status_code >= 400:
            return RpcResponse(original=response, payloads=[])

        # Read content stream
        content = response.content
        response.close()

        # Process response content
        buffer = io.BytesIO(content)
        messages = list(protocol.unwrap_message_stream(buffer))
        buffer.close()

        payloads = []
        for message, trailer, compressed in messages:
            if trailer:
                break
            payloads.append(method.deserialize_response(message))

        return RpcResponse(original=response, payloads=payloads)
