import os

from pyease_grpc import Protobuf, RpcSession
from pyease_grpc.rpc_uri import RpcUri

os.chdir(os.path.dirname(__file__))
protobuf = Protobuf.from_file('time_service.proto')
session = RpcSession(protobuf)

response = session.request(
    RpcUri('http://localhost:8080', package='smpl.time.api.v1',
           service='TimeService', method='GetCurrentTime'),
    {},
)
response.raise_for_status()

result = response.single
print(result['currentTime'])
