import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

try:
    path = os.path.realpath(os.path.abspath(__file__))
    os.chdir(os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

    from abc_pb2 import HelloRequest, HelloResponse
    from abc_pb2_grpc import GreeterServicer, add_GreeterServicer_to_server
finally:
    pass

NUMBER_OF_REPLY = 5


class Greeter(GreeterServicer):
    def SayHello(self, request: HelloRequest, context):
        print("Serving SayHello =>", request, end="")
        time.sleep(1)
        return HelloResponse(reply=f"Hello, {request.name}!")

    def LotsOfReplies(self, request, context):
        print("Serving LotsOfReplies =>", request, end="")
        for i in range(NUMBER_OF_REPLY):
            time.sleep(1)
            yield HelloResponse(reply=f"Hello, {request.name} no. {i}!")

    def LotsOfGreetings(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        names = ", ".join([request.name for request in request_iterator])
        print("Serving LotsOfGreetings =>", names, end="")
        time.sleep(1)
        return HelloResponse(reply=f"Hello, {names}!")

    def BidiHello(self, request_iterator, context):
        print("Serving BidiHello =>", request_iterator, end="")
        for request in request_iterator:
            time.sleep(1)
            yield HelloResponse(reply=f"Hello, {request.name}!")


async def async_serve(listen_addr) -> None:
    server = grpc.aio.server()
    add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port(listen_addr)
    print("Server started, listening on " + listen_addr)
    await server.start()
    await server.wait_for_termination()


def serve(listen_addr):
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port(listen_addr)
    print("Server started, listening on " + listen_addr)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    listen_addr = "[::]:50050"
    if len(sys.argv) >= 2 and sys.argv[1] == "async":
        asyncio.run(async_serve(listen_addr))
    else:
        serve(listen_addr)
