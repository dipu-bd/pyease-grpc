import grpc


class RpcTrailer(grpc.RpcError):
    def __init__(self, trailer: dict) -> None:
        self._trailer = trailer or {}
        self._message = str(self._trailer.get("grpc-message", ""))

        status = self._trailer.get("grpc-status", 2)
        if not isinstance(status, int):
            status = str(status)
            if status.isdigit():
                status = int(status)

        self._code = grpc.StatusCode.UNKNOWN
        for status_code in grpc.StatusCode:
            code, name = status_code.value
            if code == status or name == status:
                self._code = status_code
                break

        super().__init__(f"[{self._code.name}] gRPC Error: {self._message}")

    def code(self):
        return self._code

    def details(self):
        return self._message

    def is_ok(self):
        return self._code == grpc.StatusCode.OK
