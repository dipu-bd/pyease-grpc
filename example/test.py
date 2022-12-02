import os
import sys

try:
    path = os.path.realpath(os.path.abspath(__file__))
    os.chdir(os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

    from pyease_grpc import Protobuf, RpcSession
    from pyease_grpc.rpc_uri import RpcUri
finally:
    pass

PROTO_FILE = os.path.join("server", "abc.proto")


def load_protobuf():
    protobuf = Protobuf.from_file(PROTO_FILE)
    print("protobuf", "=", protobuf)
    print()


def say_hello():
    print("-" * 25)
    print("Calling SayHello:")
    rpc_uri = RpcUri(
        "http://localhost:8080",
        package="pyease.sample.v1",
        service="Greeter",
        method="SayHello",
    )
    print("uri", "=", rpc_uri)
    with RpcSession.from_file(PROTO_FILE) as session:
        response = session.request(rpc_uri, {"name": "world"})
        response.raise_for_status()

    print(response.single["reply"])

    print()
    print("payloads", "=", response.payloads)
    print("trailer", "=", response.trailer)
    print("grpc_status", "=", response.grpc_status)
    print("grpc_message", "=", response.grpc_message)
    print("-" * 25)
    print()


def lots_of_replies():
    print("-" * 25)
    print("Calling LotsOfReplies:")
    rpc_uri = RpcUri(
        "http://localhost:8080",
        package="pyease.sample.v1",
        service="Greeter",
        method="LotsOfReplies",
    )
    print("uri", "=", rpc_uri)
    with RpcSession.from_file(PROTO_FILE) as session:
        response = session.request(rpc_uri, {"name": "world"})
        response.raise_for_status()

    for payload in response.iter_payloads():
        print(payload["reply"])

    print()
    print("payloads", "=", response.payloads)
    print("trailer", "=", response.trailer)
    print("grpc_status", "=", response.grpc_status)
    print("grpc_message", "=", response.grpc_message)
    print("-" * 25)
    print()


if __name__ == "__main__":
    load_protobuf()
    say_hello()
    lots_of_replies()
