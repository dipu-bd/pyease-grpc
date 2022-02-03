from urllib.parse import urlparse


class RpcUri:
    def __init__(self,
                 url: str,
                 package: str,
                 service: str,
                 method: str) -> None:
        self.url = url
        self.package = package
        self.service = service
        self.method = method

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
