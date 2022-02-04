# pyease-grpc

[![Build](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/commit.yml)
[![Release](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml/badge.svg)](https://github.com/dipu-bd/pyease-grpc/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyease-grpc.svg?logo=python)](https://pypi.org/project/pyease-grpc)
[![Python version](https://img.shields.io/pypi/pyversions/pyease-grpc.svg)](https://pypi.org/project/pyease-grpc)
[![GitHub License](https://img.shields.io/github/license/dipu-bd/pyease-grpc)](https://github.com/dipu-bd/pyease-grpc/blob/master/LICENSE)

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

To use it, you need to have a basic understanding of [how gRPC works](https://grpc.io/docs/what-is-grpc/introduction/).

Let's run the server first. There is an example project here: https://github.com/dipu-bd/grpc-web-example

Clone it and follow the instructions on the README.md to start the server.

Let' check the `example` folder for the `time_service.proto` file:

```proto
// file: time_service.proto
syntax = "proto3";

package smpl.time.api.v1;

option go_package = "github.com/kostyay/grpc-web-example/api/time/v1";

message GetCurrentTimeRequest {
}

message GetCurrentTimeResponse {
  string current_time = 1;
}

service TimeService {
  rpc GetCurrentTime(GetCurrentTimeRequest) returns (GetCurrentTimeResponse);
}
```

Suppose the gRPC web server is running at `http://localhost:8080`.

To make a request to `GetCurrentTime`:

```py
from pyease_grpc import Protobuf, RpcSession
from pyease_grpc.rpc_uri import RpcUri

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
```

The `session.request` accepts a `dict` as input and returns the response as `dict`.

### Descriptor

A more convenient way to use the client is directly using the `FileDescriptorSet`.

To generate `FileDescriptorSet` as json:

```
$ pyease-grpc -I example example/time_service.proto --output example/descriptor.json
```

Now you can use this descriptor file directly to create `Protobuf` instance.

```py
import json

with open('descriptor.json', 'r') as f:
  descriptor = json.load(f)

# Use the descriptor directly to create protobuf instance
protobuf = Protobuf.restore(descriptor)

# You can even create the session directly
session = RpcSession.from_descriptor(descriptor)
```
