from typing import Generator, Iterable

import grpc
from google.protobuf.message import Message

from . import _protocol
from .rpc_response import RpcResponse


class RpcNativeResponse(RpcResponse):
    def __init__(
        self,
        channel: grpc.Channel,
        response_iter: Iterable[Message],
    ) -> None:
        super().__init__()
        self.channel = channel
        self._response_iterator = response_iter
        self._payloads_ready = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def iter_payloads(self) -> Generator[dict, None, None]:
        if self._payloads_ready:
            yield from self._payloads
            return

        payloads = []
        for message in self._response_iterator:
            if not message:
                continue
            payload = _protocol.message_to_dict(message)
            payloads.append(payload)
            yield payload

        self._payloads = payloads
        self._payloads_ready = True

    def close(self):
        """Closes the Channel and releases all resources held by it."""
        self.channel.close()
