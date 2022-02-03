
from typing import List, Optional

from requests import Response


class RpcResponse(object):
    def __init__(self,
                 original: Response,
                 payloads: List[dict]) -> None:
        self.original = original
        self.payloads = payloads

    @property
    def status_code(self):
        return self.original.status_code

    def raise_for_status(self):
        self.original.raise_for_status()

    @property
    def single(self) -> Optional[dict]:
        if not self.payloads:
            return None
        return self.payloads[0]
