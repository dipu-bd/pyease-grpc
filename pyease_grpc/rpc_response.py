from typing import List, Optional

from requests import HTTPError, Response


class RpcResponse(object):
    def __init__(
        self,
        original: Response,
        payloads: List[dict] = [],
        trailer: dict = {},
    ) -> None:
        self.original = original
        self.payloads = payloads
        self.trailer = trailer

    @property
    def headers(self) -> dict:
        return self.original.headers

    @property
    def status_code(self) -> int:
        return self.original.status_code

    @property
    def status_message(self):
        return self.original.reason

    @property
    def single(self) -> Optional[dict]:
        """Returns the first response payload"""
        if not self.payloads:
            return None
        return self.payloads[0]

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

    def raise_for_status(self):
        """Raises :class:`HTTPError`, if one occurred."""
        self.original.raise_for_status()

        http_error_msg = ""
        if self.grpc_status != 0:
            http_error_msg = f"{self.grpc_status} GRPC Error: {self.grpc_message}"

        if http_error_msg:
            raise HTTPError(http_error_msg, response=self)
