from typing import Type

from google.protobuf.message import Message

from . import _protocol
from .rpc_method_type import MethodType
from .rpc_trailer import RpcTrailer
from .rpc_uri import RpcUri


class RpcMethod(object):
    def __init__(
        self,
        package: str,
        service: str,
        method: str,
        request: Type[Message],
        response: Type[Message],
        type: MethodType = MethodType.unary_unary,
    ) -> None:
        self.package = package
        self.service = service
        self.method = method
        self.request = request
        self.response = response
        self.type = type

    def __str__(self) -> str:
        return str(
            dict(
                package=self.package,
                service=self.service,
                method=self.method,
                type=str(self.type),
                request=self.request.__name__,
                response=self.response.__name__,
            )
        )

    def get_uri(self, base_url: str):
        """Gets the :class:`RpcUri` corresponding to this method.

        Arguments:
            base_url (str): The base address. e.g. http://localhost:8080

        Returns:
            An :class:`RpcUri` corresponding to this method.
        """
        return RpcUri(
            base_url=base_url,
            package=self.package,
            service=self.service,
            method=self.method,
        ).build()

    def parse_request(self, data: dict) -> Message:
        return _protocol.parse_message(self.request, data)

    def serialize_request(self, data: dict) -> bytes:
        return self.parse_request(data).SerializeToString()

    def deserialize_response(self, data: bytes) -> Message:
        return _protocol.deserialize_message(self.response, data)

    def deserialize_response_dict(self, data: bytes) -> dict:
        return _protocol.message_to_dict(self.deserialize_response(data))

    def deserialize_trailer(self, trailer: bytes) -> RpcTrailer:
        trailer = _protocol.deserialize_trailer(trailer)
        return RpcTrailer(trailer)
