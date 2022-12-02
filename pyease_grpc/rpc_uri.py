from urllib.parse import urlparse


class RpcUri:
    @classmethod
    def parse(cls, url: str) -> "RpcUri":
        """Creates :class:`RpcUri` from an URL

        Arguments:
            url (str): A gRPC web URL
        """
        parsed = urlparse(url)
        url_path, package_path, method = parsed.path.rsplit("/", 3)
        package, service = package_path.rsplit(".", 1)
        scheme = parsed.scheme or "http"
        hostname = parsed.hostname or ""
        url = scheme + "://" + hostname + "/" + url_path
        return cls(url.rstrip("/"), package, service, method)

    def __init__(
        self,
        base_url: str,
        package: str,
        service: str,
        method: str,
    ) -> None:
        """URL initializer for the gRPC call.

        Arguments:
            base_url (str): The base address of the gRPC server. e.g. http://localhost:8080
            package (str): The package name. e.g. smpl.time.api.v1
            service (str): The service name. e.g. TimeService
            method (str): The method name to call. e.g. GetCurrentTime
        """
        self.base_url = base_url
        self.package = package
        self.service = service
        self.method = method

    def __str__(self) -> str:
        return self.build()

    def build(self) -> str:
        """Builds and returns the URL for the gRPC call."""
        url = self.base_url.rstrip("/")
        if not any(url.startswith(x) for x in ["http://", "https://"]):
            url = "http://" + url.lstrip("//")
        url += "/" + self.package
        url += "." + self.service
        url += "/" + self.method
        return url
