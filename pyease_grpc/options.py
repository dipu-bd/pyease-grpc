from dataclasses import dataclass
from typing import Optional

from requests.structures import CaseInsensitiveDict


@dataclass
class RequestOptions:
    timeout: Optional[float] = None
    metadata = CaseInsensitiveDict({
        'x-grpc-web': '1',
        'content-type': 'application/grpc-web+proto',
    })
