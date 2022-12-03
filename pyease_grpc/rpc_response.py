from collections import deque
from typing import Generator, List, Optional


class RpcResponse(object):
    def __init__(
        self,
        payloads: List[dict] = [],
    ) -> None:
        self._payloads = payloads
        self._payload_consumed = True

    def iter_payloads(self) -> Generator[dict, None, None]:
        yield from self._payloads

    @property
    def payloads(self):
        if not self._payload_consumed:
            deque(self.iter_payloads(), maxlen=0)
        return self._payloads

    @property
    def single(self) -> Optional[dict]:
        """Returns the last response payload"""
        if not self.payloads:
            return None
        return self.payloads[-1]
