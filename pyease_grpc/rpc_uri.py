from urllib.parse import urlparse


class RpcUri(object):
    @classmethod
    def parse(cls, url: str) -> "RpcUri":
        """Creates :class:`RpcUri` from an URL

        Arguments:
            url (str): A gRPC web URL
        """
        parsed = urlparse(url)
        url_path, package_path, method = parsed.path.rsplit("/", 3)
        package, service = package_path.rsplit(".", 1)
        if not parsed.hostname:
            raise ValueError("Hostname is required")
        url = parsed.hostname + "/" + url_path.rstrip("/")
        if parsed.scheme:
            url = parsed.scheme + "://" + url
        return cls(url, package, service, method)

    def __init__(
        self,
        base_url: str,
        package: str,
        service: str,
        method: str,
    ) -> None:
        """URL builder for a gRPC call.

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

    @property
    def path(self) -> str:
        """Returns the path of the gRPC method."""
        return f"/{self.package}.{self.service}/{self.method}"

    def build(self) -> str:
        """Builds and returns the URL for the gRPC-Web call."""
        url = self.base_url.rstrip("/")
        if url and url.split("://", 1)[0] not in ["http", "https"]:
            url = "http://" + url.split("://", 1)[-1]
        url += self.path
        return url
