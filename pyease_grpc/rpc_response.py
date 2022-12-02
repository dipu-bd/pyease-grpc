from typing import Generator, Optional

from requests import Response

from . import _protocol
from .rpc_method import RpcMethod


class RpcResponse(object):
    def __init__(
        self,
        response: Response,
        method: RpcMethod,
    ) -> None:
        self.response = response
        self.raw = response.raw
        self.method = method
        self.trailer = None
        self._payloads = None
        self._payload_consumed = False

    def raise_for_status(self):
        """Raises :class:`HTTPError`, if one occurred."""
        self.response.raise_for_status()

    def close(self):
        """Releases the connection back to the pool.

        Once this method has been called the underlying raw object must not be accessed again."""
        self.response.close()

    def iter_payloads(self) -> Generator[dict, None, None]:
        if self._payload_consumed:
            yield from self._payloads
            return

        if self.response.status_code >= 400:
            self._payload_consumed = True
            self._payloads = []
            return

        payloads = []
        messages = _protocol.unwrap_message_stream(self.response)
        for message, trailer, compressed in messages:
            if compressed:
                continue
            if trailer:
                self.trailer = self.method.deserialize_trailer(message)
                break
            payload = self.method.deserialize_response(message)
            payloads.append(payload)
            yield payload

        self._payload_consumed = True
        self._payloads = payloads

    @property
    def headers(self) -> dict:
        return self.response.headers

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def status_message(self):
        return self.response.reason

    @property
    def payloads(self):
        if not self._payload_consumed:
            list(self.iter_payloads())
        return self._payloads

    @property
    def single(self) -> Optional[dict]:
        """Returns the last response payload"""
        if not self.payloads:
            return None
        return self.payloads[-1]

    @property
    def grpc_message(self) -> Optional[str]:
        """Returns the grpc-message or `None` if it is not available"""
        if not self.trailer:
            return None
        return self.trailer.get("grpc-message", "")

    @property
    def grpc_status(self) -> Optional[int]:
        """Returns the grpc-status or `-1` if it is not available"""
        if not self.trailer:
            return -1
        status = self.trailer.get("grpc-status", "")
        if not status.isdigit():
            return -1
        return int(status)
