from dataclasses import dataclass
from typing import Type

from google.protobuf.message import Message

from .protocol import deserialize_message, serialize_message
from .rpc_uri import RpcUri


@dataclass(frozen=True)
class RpcMethod:
    package: str
    service: str
    method: str
    request: Type[Message]
    response: Type[Message]

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
