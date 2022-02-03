
from typing import Optional

from requests.structures import CaseInsensitiveDict


class RequestOptions:
    def __init__(self,
                 timeout: Optional[float] = None,
                 metadata=CaseInsensitiveDict({})) -> None:
        self.timeout = timeout
        self.metadata = metadata
        self.metadata['x-grpc-web'] = '1'
        self.metadata['content-type'] = 'application/grpc-web+proto'
