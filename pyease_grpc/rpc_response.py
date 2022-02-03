from dataclasses import dataclass
from typing import List, Optional

from requests import Response


@dataclass(frozen=True)
class RpcResponse(object):
    original: Response
    payloads: List[dict]

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
