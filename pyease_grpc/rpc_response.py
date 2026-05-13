from collections import deque
from typing import Generator, List, Optional


class RpcResponse(object):
    def __init__(
        self,
        payloads: Optional[List[dict]] = None,
    ) -> None:
        self._payloads: List[dict] = payloads if payloads is not None else []
        self._payloads_ready = True

    def iter_payloads(self) -> Generator[dict, None, None]:
        yield from self._payloads

    @property
    def payloads(self) -> List[dict]:
        if not self._payloads_ready:
            deque(self.iter_payloads(), maxlen=0)
        return self._payloads

    @property
    def single(self) -> Optional[dict]:
        """Returns the last response payload"""
        if not self.payloads:
            return None
        return self.payloads[-1]
