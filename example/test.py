import os
import sys

import grpc

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


def say_hello(name):
    print("-" * 25)
    print("Calling SayHello:")
    rpc_uri = RpcUri(
        base_url="http://localhost:8080",
        package="pyease.sample.v1",
        service="Greeter",
        method="SayHello",
    )
    print("uri", "=", rpc_uri)
    with RpcSession.from_file(PROTO_FILE) as session:
        response = session.request(rpc_uri, {"name": name})

    print(response.single["reply"])

    print()
    print(response.payloads)
    print("-" * 25)
    print()


def lots_of_replies(name):
    print("-" * 25)
    print("Calling LotsOfReplies:")
    rpc_uri = RpcUri(
        base_url="http://localhost:8080",
        package="pyease.sample.v1",
        service="Greeter",
        method="LotsOfReplies",
    )
    print("uri", "=", rpc_uri)
    with RpcSession.from_file(PROTO_FILE) as session:
        response = session.request(rpc_uri, {"name": name})

    for payload in response.iter_payloads():
        print(payload["reply"])

    print()
    print(response.payloads)
    print("-" * 25)
    print()


if __name__ == "__main__":
    load_protobuf()

    say_hello("world")
    lots_of_replies("world")

    try:
        say_hello("error")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")

    try:
        lots_of_replies("error")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")
