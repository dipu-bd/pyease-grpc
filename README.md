# pyease-grpc

[![Build](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml)
[![Release](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyease-grpc.svg?logo=python)](https://pypi.org/project/pyease-grpc)
[![Python version](https://img.shields.io/pypi/pyversions/pyease-grpc.svg)](https://pypi.org/project/pyease-grpc)
[![GitHub License](https://img.shields.io/github/license/dipu-bd/pyease-grpc)](https://github.com/dipu-bd/pyease-grpc/blob/master/LICENSE)
[![Downloads](https://pepy.tech/badge/pyease-grpc/month)](https://pepy.tech/project/pyease-grpc)

Easy to use gRPC-web client in python

### Installation

Install the package using:

```
$ pip install pyease-grpc
```

Run the following to check if it has been installed correctly:

```
$ pyease-grpc --version
```

## Tutorial

> Before you start, you need to have a basic understanding of [how gRPC works](https://grpc.io/docs/what-is-grpc/introduction/).

This package provides a `requests` like interface to make calls to native gRPC and gRPC-Web servers.

### Example Server

An example server and client can be found in the `example` folder.

```
> cd example
> docker compose up
```

It uses two ports:

- Native gRPC server: `localhost:50050`
- gRPC-Web server using envoy: `http://localhost:8080`

You can test the native serve with the client:

```
$ python example/server/client.py
Calling SayHello:
reply: "Hello, world!"

Calling LotsOfReplies:
reply: "Hello, world no. 0!"
reply: "Hello, world no. 1!"
reply: "Hello, world no. 2!"
reply: "Hello, world no. 3!"
reply: "Hello, world no. 4!"

Calling LotsOfGreetings:
reply: "Hello, A, B, C!"

Calling BidiHello:
reply: "Hello, A!"
reply: "Hello, B!"
reply: "Hello, C!"
```

### Loading the Protobuf

The proto file is located at `example/server/abc.proto`

```proto
// file: example/server/abc.proto
syntax = "proto3";

package pyease.sample.v1;

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloResponse);
  rpc LotsOfReplies(HelloRequest) returns (stream HelloResponse);
  rpc LotsOfGreetings(stream HelloRequest) returns (HelloResponse);
  rpc BidiHello(stream HelloRequest) returns (stream HelloResponse);
}

message HelloRequest {
  string name = 1;
}

message HelloResponse {
  string reply = 1;
}
```

You can directly load this file using `pyease_grpc` without generating any stubs:

```py
from pyease_grpc import Protobuf

protobuf = Protobuf.from_file("example/server/abc.proto")
```

Internally, it converts the proto file into `FileDescriptorSet` message.

It is recommended to use the `FileDescriptorSet` json to load the `Protobuf` faster.

To generate the `FileDescriptorSet` json from a proto file:

```
$ pyease-grpc -I example/server example/server/abc.proto --output abc_fds.json
```

Now you can use this descriptor file directly to create a `Protobuf` instance.

```py
protobuf = Protobuf.restore_file('abc_fds.json')
```

### Getting response from gRPC-Web

For **Unary RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.request(
    RpcUri(
      base_url="http://localhost:8080",
      package="pyease.sample.v1",
      service="Greeter",
      method="SayHello",
    ),
    {
      "name": "world"
    },
)
response.raise_for_status()

print(response.single['reply'])
```

For a **Server-side Streaming RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.request(
    RpcUri(
      base_url="http://localhost:8080",
      package="pyease.sample.v1",
      service="Greeter",
      method="LotsOfReplies",
    ),
    {
      "name": "world",
    },
)
response.raise_for_status()

for payload in response.iter_payloads():
    print(payload["reply"])
```

> gRPC-Web currently supports 2 RPC modes: Unary RPCs, Server-side Streaming RPCs.
> Client-side and Bi-directional streaming is not currently supported.

### Using the native gRPC protocol

You can also directly call a method using the native gRPC protocol.

For **Unary RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.call(
    RpcUri(
      base_url="localhost:50050",
      package="pyease.sample.v1",
      service="Greeter",
      method="SayHello",
    ),
    {
      "name": "world",
    }
)

print(response.single["reply"])
print(response.payloads)
```

For a **Server-side Streaming RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.call(
    RpcUri(
      base_url="localhost:50050",
      package="pyease.sample.v1",
      service="Greeter",
      method="LotsOfReplies",
    ),
    {
      "name": "world",
    },
)

for payload in response.iter_payloads():
    print(payload["reply"])
print(response.payloads)
```

For a **Client-Side Streaming RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.call(
    RpcUri(
      base_url="localhost:50050",
      package="pyease.sample.v1",
      service="Greeter",
      method="LotsOfGreetings",
    ),
    iter(
      [
        {"name": "A"},
        {"name": "B"},
        {"name": "C"},
      ]
    ),
)

print(response.single["reply"])
print(response.payloads)
```

For a **Bidirectional Streaming RPC** request:

```py
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
response = session.call(
    RpcUri(
      base_url="localhost:50050",
      package="pyease.sample.v1",
      service="Greeter",
      method="BidiHello",
    ),
    iter(
      [
        {"name": "A"},
        {"name": "B"},
        {"name": "C"},
      ]
    ),
)

for payload in response.iter_payloads():
    print(payload["reply"])
print(response.payloads)
```

### Error Handling

Errors are raised as soon as they appear.

List of errors that can appear during `request`:

- `ValueError`: If the requested method, service or package is not found
- `requests.exceptions.InvalidHeader`: If the header of expected length is not found
- `requests.exceptions.ContentDecodingError`: If the data of expected length is not found
- `NotImplementedError`: If compression is enabled in the response headers
- `grpc.RpcError`: If the grpc-status is non-zero

List of errors that can appear during `call`:

- `ValueError`: If the requested method, service or package is not found
- `grpc.RpcError`: If the grpc-status is non-zero

To get the `grpc-status` and `grpc-message`, you can add a try-catch to your call. e.g.:

```py
import grpc
from pyease_grpc import RpcSession, RpcUri

session = RpcSession.from_file("example/server/abc.proto")
rpc_uri = RpcUri(
  base_url="localhost:50050",
  package="pyease.sample.v1",
  service="Greeter",
  method="SayHello",
)
try:
  response = session.call(rpc_uri, {"name": "error"})
  print(response.single["reply"])
except grpc.RpcError as e:
  print('grpc status', e.code())
  print('grpc message', e.details())
```
