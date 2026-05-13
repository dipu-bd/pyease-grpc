from typing import Generator

from requests import Response

from . import _protocol
from .rpc_method import RpcMethod
from .rpc_response import RpcResponse


class RpcWebResponse(RpcResponse):
    def __init__(self, method: RpcMethod, response: Response) -> None:
        super().__init__()
        self.method = method
        self.response = response
        self.raw = response.raw
        self._payloads_ready = False

    def iter_payloads(self) -> Generator[dict, None, None]:
        if self.response.status_code >= 400:
            self._payloads = []
            self._payloads_ready = True
            return

        if self._payloads_ready:
            yield from self._payloads
            return

        payloads = []
        messages = _protocol.unwrap_message_stream(self.response)
        for message, trailer, compressed in messages:
            if compressed:
                raise NotImplementedError("Compression is not supported")
            if trailer:
                trailer = self.method.deserialize_trailer(message)
                if not trailer.is_ok():
                    raise trailer
                break
            payload = self.method.deserialize_response_dict(message)
            payloads.append(payload)
            yield payload

        self._payloads = payloads
        self._payloads_ready = True

    @property
    def headers(self) -> dict:
        return self.response.headers

    def close(self):
        """Closes the response and releases the connection back to the pool."""
        self.response.close()
