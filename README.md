# pyease-grpc

[![Build](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml)
[![Release](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyease-grpc.svg?logo=python)](https://pypi.org/project/pyease-grpc)
[![Python version](https://img.shields.io/pypi/pyversions/pyease-grpc.svg)](https://pypi.org/project/pyease-grpc)
[![GitHub License](https://img.shields.io/github/license/dipu-bd/pyease-grpc)](https://github.com/dipu-bd/pyease-grpc/blob/master/LICENSE)
[![Downloads](https://pepy.tech/badge/pyease-grpc/month)](https://pepy.tech/project/pyease-grpc)

Easy to use gRPC-web client in python

## Tutorial

This package provides a `requests` like interface to make calls to gRPC-Web servers.

### Installation

Install the package using:

```
$ pip install pyease-grpc
```

Run the following to check if it has been installed correctly:

```
$ pyease-grpc --version
```

### Introduction

> You need to have a basic understanding of [how gRPC works](https://grpc.io/docs/what-is-grpc/introduction/).

An example server and client can be found in the `example` folder.

```
> cd example
> docker compose up
```

It runs a grpc server and creates an envoy proxy for grpc-web access.

The grpc server address: `localhost:50050`
The envoy proxy address: `http://localhost:8080`

Now let's check the `example/server` folder for the `abc.proto` file:

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

To make a request to `SayHello`:

```py
from pyease_grpc import Protobuf, RpcSession, RpcUri

protobuf = Protobuf.from_file("example/server/abc.proto")
session = RpcSession(protobuf)

response = session.request(
    RpcUri(
      "http://localhost:8080",
      package="pyease.sample.v1",
      service="Greeter",
      method="SayHello",
    ),
    {
      "name": "world"
    },
)
response.raise_for_status()

result = response.single
print(result['reply'])
```

The `session.request` accepts request data as a `dict` and returns the response as a `dict`.

> gRPC-web currently supports 2 RPC modes: Unary RPCs, Server-side Streaming RPCs.
> Client-side and Bi-directional streaming is not currently supported.
>
> Source: https://github.com/grpc/grpc-web#streaming-support

### Descriptor

The `FileDescriptorSet` is the faster way to load Protobuf.

To generate `FileDescriptorSet` as json:

```
$ pyease-grpc -I example/server example/server/abc.proto --output abc_fds.json
```

Now you can use this descriptor file directly to create a `Protobuf` instance.

```py
# Use the descriptor directly to create protobuf instance
protobuf = Protobuf.restore_file('abc_fds.json')

# You can even create the session directly from descriptor
session = RpcSession.from_descriptor(descriptor)
```
