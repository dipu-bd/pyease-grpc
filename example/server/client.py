import os
import sys

import grpc

try:
    path = os.path.realpath(os.path.abspath(__file__))
    os.chdir(os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

    from abc_pb2 import HelloRequest
    from abc_pb2_grpc import GreeterStub
finally:
    pass


GRPC_ADDRESS = "localhost:50050"


def say_hello(name):
    print("Calling SayHello:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response = stub.SayHello(HelloRequest(name=name))
        print(response, end="")
        print()


def lots_of_replies(name):
    print("Calling LotsOfReplies:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response_iterator = stub.LotsOfReplies(HelloRequest(name=name))
        for response in response_iterator:
            print(response, end="")
        print()


def lots_of_greetings(*names):
    print("Calling LotsOfGreetings:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response = stub.LotsOfGreetings(
            iter([HelloRequest(name=name) for name in names]),
        )
        print(response, end="")
        print()


def bidi_hello(*names):
    print("Calling BidiHello:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response_iterator = stub.BidiHello(
            iter([HelloRequest(name=name) for name in names]),
        )
        for response in response_iterator:
            print(response, end="")
        print()


if __name__ == "__main__":
    say_hello("world")
    lots_of_replies("world")
    lots_of_greetings("A", "B", "C")
    bidi_hello("A", "B", "C")

    try:
        say_hello("error")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")

    try:
        lots_of_replies("error")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")

    try:
        lots_of_greetings("A", "error", "C")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")

    try:
        bidi_hello("A", "error", "C")
    except grpc.RpcError as e:
        print(e.code(), e.details(), end="\n\n")
