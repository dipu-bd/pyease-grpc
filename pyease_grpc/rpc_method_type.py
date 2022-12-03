from enum import Enum


class MethodType(Enum):
    unary_unary = "unary_unary"
    unary_stream = "unary_stream"
    stream_unary = "stream_unary"
    stream_stream = "stream_stream"

    def __str__(self) -> str:
        return self.value


def get_method_type(client_streaming: bool, server_streaming: bool) -> MethodType:
    from .rpc_method import MethodType

    if client_streaming and server_streaming:
        return MethodType.stream_stream
    elif client_streaming:
        return MethodType.stream_unary
    elif server_streaming:
        return MethodType.unary_stream
    else:
        return MethodType.unary_unary
