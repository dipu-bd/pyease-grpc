from typing import List, Optional

from requests import Response


class RpcResponse(object):
    def __init__(self,
                 original: Response,
                 payloads: List[dict],
                 trailers: dict) -> None:
        self.original = original
        self.payloads = payloads
        self.trailers = trailers

    @property
    def status_code(self):
        return self.original.status_code

    @property
    def grpc_status(self):
        return self.trailers["grpc-status"]

    @property
    def grpc_message(self):
        return self.trailers["grpc-message"]

    @property
    def q_message(self):
        return self.trailers["q-message"]

    @property
    def q_detail(self):
        return self.trailers["q-detail"]

    def raise_for_status(self):
        self.original.raise_for_status()

    @property
    def single(self) -> Optional[dict]:
        if not self.payloads:
            return None
        return self.payloads[0]
