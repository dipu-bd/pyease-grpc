from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    FileDescriptorSet,
    MethodDescriptorProto,
    ServiceDescriptorProto,
)


def make_file_descriptor(
    file_name: str,
    package: str = "test.v1",
    request_name: str = "Request",
    response_name: str = "Response",
    service_name: str = "TestService",
    method_name: str = "DoIt",
    client_streaming: bool = False,
    server_streaming: bool = False,
) -> FileDescriptorProto:
    req = DescriptorProto(name=request_name)
    req.field.add(
        name="value",
        number=1,
        type=FieldDescriptorProto.TYPE_STRING,
        label=FieldDescriptorProto.LABEL_OPTIONAL,
    )
    res = DescriptorProto(name=response_name)
    res.field.add(
        name="result",
        number=1,
        type=FieldDescriptorProto.TYPE_STRING,
        label=FieldDescriptorProto.LABEL_OPTIONAL,
    )
    input_type = f".{package}.{request_name}" if package else f".{request_name}"
    output_type = f".{package}.{response_name}" if package else f".{response_name}"
    method = MethodDescriptorProto(
        name=method_name,
        input_type=input_type,
        output_type=output_type,
        client_streaming=client_streaming,
        server_streaming=server_streaming,
    )
    service = ServiceDescriptorProto(name=service_name)
    service.method.append(method)

    proto = FileDescriptorProto(name=file_name, syntax="proto3")
    if package:
        proto.package = package
    proto.message_type.append(req)
    proto.message_type.append(res)
    proto.service.append(service)
    return proto


def make_fds(file_name: str, package: str = "test.v1", **kwargs) -> FileDescriptorSet:
    fds = FileDescriptorSet()
    fds.file.append(make_file_descriptor(file_name=file_name, package=package, **kwargs))
    return fds
