from typing import Type

from google.protobuf.message import Message

from .protocol import deserialize_message, serialize_message
from .rpc_uri import RpcUri


class RpcMethod:
    def __init__(self,
                 package: str,
                 service: str,
                 method: str,
                 request: Type[Message],
                 response: Type[Message]) -> None:
        self.package = package
        self.service = service
        self.method = method
        self.request = request
        self.response = response

    def build_url(self, url: str):
        return RpcUri(
            url=url,
            package=self.package,
            service=self.service,
            method=self.method
        ).build()

    def serialize_request(self, data: dict) -> bytes:
        return serialize_message(self.request, data)

    def deserialize_response(self, data: bytes) -> dict:
        return deserialize_message(self.response, data)
