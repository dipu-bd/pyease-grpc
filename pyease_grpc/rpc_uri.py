from urllib.parse import urlparse


class RpcUri:
    @classmethod
    def parse(cls, url: str) -> "RpcUri":
        """Creates :class:`RpcUri` from an URL

        Arguments:
            url (str): A gRPC web URL
        """
        parsed = urlparse(url)
        _, path, method = parsed.path.split("/")[:3]
        package, service = path.rsplit(".", 1)
        scheme = parsed.scheme or "http"
        hostname = parsed.hostname or ""
        url = scheme + "://" + hostname
        return cls(url, package, service, method)

    def __init__(
        self,
        url: str,
        package: str,
        service: str,
        method: str,
    ) -> None:
        """URL initializer for the gRPC call.

        Arguments:
            url (str): The base address of the gRPC server. e.g. http://localhost:8080
            package (str): The package name. e.g. smpl.time.api.v1
            service (str): The service name. e.g. TimeService
            method (str): The method name to call. e.g. GetCurrentTime
        """
        self.url = url
        self.package = package
        self.service = service
        self.method = method

    def build(self) -> str:
        """Builds and returns the URL for the gRPC call."""
        url = self.url
        if not any(url.startswith(x) for x in ["http://", "https://"]):
            url = "http://" + url
        url = url.strip("/")
        url += "/" + self.package
        url += "." + self.service
        url += "/" + self.method
        return url
