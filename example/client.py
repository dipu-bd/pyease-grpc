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

protobuf = Protobuf.from_file("time_service.proto")
session = RpcSession(protobuf)

response = session.request(
    RpcUri(
        "http://localhost:8080",
        package="smpl.time.api.v1",
        service="TimeService",
        method="GetCurrentTime",
    ),
    {},
)
response.raise_for_status()

print("trailer", "=", response.trailer)
print("result", "=", response.single)

print("grpc_message", "=", response.grpc_message)
print("grpc_status", "=", response.grpc_status)
print("time", "=", response.single["currentTime"])
