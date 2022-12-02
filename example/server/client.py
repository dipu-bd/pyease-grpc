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


def say_hello():
    print("Calling SayHello:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response = stub.SayHello(HelloRequest(name="world"))
        print(response, end="")
        print()


def lots_of_replies():
    print("Calling LotsOfReplies:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response_iterator = stub.LotsOfReplies(HelloRequest(name="world"))
        for response in response_iterator:
            print(response, end="")
        print()


def lots_of_greetings():
    print("Calling LotsOfGreetings:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response = stub.LotsOfGreetings(
            iter(
                (
                    HelloRequest(name="A"),
                    HelloRequest(name="B"),
                    HelloRequest(name="C"),
                )
            )
        )
        print(response, end="")
        print()


def bidi_hello():
    print("Calling BidiHello:")
    with grpc.insecure_channel(GRPC_ADDRESS) as channel:
        stub = GreeterStub(channel)
        response_iterator = stub.BidiHello(
            iter(
                (
                    HelloRequest(name="A"),
                    HelloRequest(name="B"),
                    HelloRequest(name="C"),
                )
            )
        )
        for response in response_iterator:
            print(response, end="")
        print()


if __name__ == "__main__":
    say_hello()
    lots_of_replies()
    lots_of_greetings()
    bidi_hello()
