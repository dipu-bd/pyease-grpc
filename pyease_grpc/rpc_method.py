from enum import Enum
from typing import Type

from google.protobuf.message import Message

from ._protocol import deserialize_message, deserialize_trailer, serialize_message
from .rpc_uri import RpcUri


class MethodType(Enum):
    unary_unary = "unary_unary"
    unary_stream = "unary_stream"
    stream_unary = "stream_unary"
    stream_stream = "stream_stream"

    def __str__(self) -> str:
        return self.value


class RpcMethod:
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

    def serialize_request(self, data: dict) -> bytes:
        return serialize_message(self.request, data)

    def deserialize_response(self, data: bytes) -> dict:
        return deserialize_message(self.response, data)

    def deserialize_trailer(self, trailer: bytes) -> dict:
        return deserialize_trailer(trailer)
