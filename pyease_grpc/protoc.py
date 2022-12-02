import json
import logging
import os
import shutil
import tempfile
from typing import Dict, List, Optional, Type

from google.protobuf import reflection, symbol_database
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message

from .rpc_method import MethodType, RpcMethod
from .rpc_uri import RpcUri

logger = logging.getLogger(__name__)

try:
    from grpc_tools import protoc
except ImportError as e:
    logger.debug(
        str(e) + " Run 'pip install grpcio-tools' to install it."
        " It is required to parse proto files."
    )
    protoc = None


class Protobuf:
    @classmethod
    def from_file(
        cls,
        proto_file: str,
        include_paths: List[str] = [],
        work_dir: Optional[str] = None,
    ):
        """Creates a :class:`Protobuf` from protobuf file.

        Arguments:
            proto_file (str) A *.proto file containing protobuf definitions.
            include_paths (List[str]) Additional paths to include when parsing. Default = []
            work_dir (Optional[str]): Main working folder. Default = None
        """
        basename = os.path.basename(proto_file)
        tmp_dir = work_dir or tempfile.mkdtemp(basename)
        os.makedirs(tmp_dir, exist_ok=True)
        try:
            out_file = os.path.join(tmp_dir, "descriptor.bin")
            res = _generate_descriptor(out_file, proto_file, include_paths)
            with open(res, "rb") as f:
                return cls(FileDescriptorSet.FromString(f.read()))
        finally:
            if work_dir != tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    @classmethod
    def from_proto(
        cls,
        proto: str,
        filename: str = "pyease",
        include_paths: List[str] = [],
        work_dir: Optional[str] = None,
    ):
        """Creates a :class:`Protobuf` from protobuf definitions.

        Arguments:
            proto (str) Contents of a *.proto file as string
            filename (str) A filename to use. Default = "pyease"
            include_paths (List[str]) Additional paths to include when parsing. Default = []
            work_dir (Optional[str]): Main working folder. Default = None
        """
        tmp_dir = work_dir or tempfile.mkdtemp(filename)
        os.makedirs(tmp_dir, exist_ok=True)
        try:
            proto_file = os.path.join(tmp_dir, filename + ".proto")
            with open(proto_file, "w") as f:
                f.write(proto)
            return cls.from_file(
                proto_file, include_paths + [tmp_dir], work_dir=tmp_dir
            )
        finally:
            if work_dir != tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    @classmethod
    def restore(cls, descriptor_json: dict):
        """Creates a :class:`Protobuf` from a JSON.

        Arguments:
            descriptor_json (dict) A :class:`FileDescriptorSet` message content as JSON
        """
        fds = FileDescriptorSet()
        ParseDict(descriptor_json, fds)
        return cls(fds)

    @classmethod
    def restore_file(cls, descriptor_json_file: str):
        """Creates a :class:`Protobuf` from a :class:`FileDescriptorSet` JSON content.

        Arguments:
            descriptor_json_file (str) Path to the JSON file.
        """
        with open(descriptor_json_file, "r", encoding="utf8") as fp:
            data = json.load(fp)
            return Protobuf.restore(data)

    def __init__(self, descriptor: FileDescriptorSet) -> None:
        """Initializes an instance from a :class:`FileDescriptorSet`.

        Arguments:
            descriptor (FileDescriptorSet) A file descriptor set message
        """
        self._descriptor = descriptor

        # load messages
        db = symbol_database.Default()
        self.messages: Dict[str, Type[Message]] = {}
        for proto in self._descriptor.file:
            db.pool.Add(proto)
            for message in proto.message_type:
                name = proto.package + "." + message.name
                md = db.pool.FindMessageTypeByName(name)
                self.messages[name] = reflection.MakeClass(md)

        # load services
        self.services: Dict[str, Dict[str, RpcMethod]] = {}
        for proto in self._descriptor.file:
            for service in proto.service:
                self.services[service.name] = {}
                for method in service.method:
                    method_type = _get_method_type(
                        method.client_streaming,
                        method.server_streaming,
                    )
                    self.services[service.name][method.name] = RpcMethod(
                        package=proto.package,
                        service=service.name,
                        method=method.name,
                        request=self.messages[method.input_type[1:]],
                        response=self.messages[method.output_type[1:]],
                        type=method_type,
                    )

    def __str__(self) -> str:
        return json.dumps(self.save(), ensure_ascii=False)

    @property
    def descriptor(self) -> FileDescriptorSet:
        """Returns the :class:`FileDescriptorSet` of the current protobuf"""
        return self._descriptor

    def save(self) -> dict:
        """Returns the :class:`FileDescriptorSet` of the current protobuf as JSON"""
        return MessageToDict(self._descriptor)

    def save_file(self, file_path: str) -> None:
        """Saves the :class:`FileDescriptorSet` of the current protobuf as JSON to a file

        Arguments:
            file_path (str): A file path to write the JSON content
        """
        with open(file_path, "w", encoding="utf8") as fp:
            json.dump(self.save(), fp, ensure_ascii=False)

    def get_method(self, uri: RpcUri) -> Optional[RpcMethod]:
        """Gets the method corresponding to a :class:`RpcUri`"""
        if uri.service not in self.services:
            return None
        methods = self.services[uri.service]
        if uri.method not in methods:
            return None
        method = methods[uri.method]
        if method.package != uri.package:
            return None
        return method

    def has_method(self, uri: RpcUri) -> bool:
        """Check whether the method corresponding to a :class:`RpcUri` exists"""
        return isinstance(self.get_method(uri), RpcMethod)


def _get_method_type(client_streaming: bool, server_streaming: bool):
    if client_streaming and server_streaming:
        return MethodType.stream_stream
    elif client_streaming:
        return MethodType.stream_unary
    elif server_streaming:
        return MethodType.unary_stream
    else:
        return MethodType.unary_unary


def _generate_descriptor(out_file: str, proto_file: str, include_paths: List[str] = []):
    if not protoc:
        raise ModuleNotFoundError("Missing package: 'grpcio-tools'")

    if not proto_file.endswith(".proto"):
        raise TypeError("Not a proto file")

    if not os.path.isfile(proto_file):
        raise FileNotFoundError(proto_file)

    out_file = os.path.abspath(out_file)
    proto_file = os.path.abspath(proto_file)

    if not include_paths:
        include_paths = [os.path.dirname(proto_file)]
    include_paths = [os.path.abspath(x) for x in include_paths if os.path.isdir(x)]

    protoc_py_file = os.path.abspath(protoc.__file__)
    proto_include = _resource_path("grpc_tools", "_proto")

    protoc_config = [
        protoc_py_file,
        "--proto_path",
        proto_include,
    ]

    for path in set(include_paths):
        protoc_config += [
            "--proto_path",
            str(path),
        ]

    protoc_config += [
        "--descriptor_set_out",
        out_file,
        "--include_imports",
        proto_file,
    ]

    protoc.main(protoc_config)
    return out_file


def _resource_path(package, path):
    try:
        import pkg_resources

        return pkg_resources.resource_filename(package, path)
    except Exception:
        import importlib.resources

        files = importlib.resources.files(package)
        return os.path.abspath(str(files / path))
