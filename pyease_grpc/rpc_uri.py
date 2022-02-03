from dataclasses import dataclass
from urllib.parse import urlparse

from .protocol import deserialize_message, serialize_message


@dataclass(frozen=True)
class RpcUri:
    url: str
    package: str
    service: str
    method: str

    def build(self) -> str:
        url = self.url
        if not any(url.startswith(x) for x in ['http://', 'https://']):
            url = "http://" + url
        url = url.strip('/')
        url += '/' + self.package
        url += '.' + self.service
        url += '/' + self.method
        return url

    @classmethod
    def parse(cls, url: str) -> 'RpcUri':
        parsed = urlparse(url)
        _, path, method = parsed.path.split('/')[:3]
        package, service = path.rsplit('.', 1)
        scheme = parsed.scheme or 'http'
        hostname = parsed.hostname or ''
        url = scheme + '://' + hostname
        return cls(url, package, service, method)
 