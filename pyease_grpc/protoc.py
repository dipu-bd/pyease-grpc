import logging
import os
import shutil
import tempfile
from typing import Dict, List, Optional, Type

from google.protobuf import reflection, symbol_database
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message

from .rpc_method import RpcMethod

logger = logging.getLogger(__name__)

try:
    from grpc_tools import protoc
except ImportError as e:
    logger.debug(str(e) +
                 " Run 'pip install grpcio-tools' to install it."
                 " It is required to parse proto files.")
    protoc = None


class Protobuf:

    @classmethod
    def from_proto(cls,
                   proto: str,
                   filename: str = 'pyease',
                   include_paths: List[str] = [],
                   work_dir: Optional[str] = None):
        tmp_dir = work_dir or tempfile.mkdtemp(filename)
        os.makedirs(tmp_dir, exist_ok=True)
        try:
            proto_file = os.path.join(tmp_dir, filename + '.proto')
            with open(proto_file, 'w') as f:
                f.write(proto)
            return cls.from_file(proto_file,
                                 include_paths + [tmp_dir],
                                 work_dir=tmp_dir)
        finally:
            if work_dir != tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    @classmethod
    def from_file(cls,
                  proto_file: str,
                  include_paths: List[str] = [],
                  work_dir: Optional[str] = None):
        basename = os.path.basename(proto_file)
        tmp_dir = work_dir or tempfile.mkdtemp(basename)
        os.makedirs(tmp_dir, exist_ok=True)
        try:
            out_file = os.path.join(tmp_dir, 'descriptor.bin')
            res = _generate_descriptor(out_file, proto_file, include_paths)
            with open(res, 'rb') as f:
                return cls(FileDescriptorSet.FromString(f.read()))
        finally:
            if work_dir != tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def __init__(self, descriptor: FileDescriptorSet) -> None:
        self._descriptor = descriptor
        self._load_messages()
        self._load_services()

    def _load_messages(self):
        db = symbol_database.Default()
        self.messages: Dict[str, Type[Message]] = {}
        for proto in self._descriptor.file:
            fd = db.pool.Add(proto)
            for name in fd.message_types_by_name:
                message = fd.message_types_by_name[name]
                message_type = reflection.MakeClass(message)
                registered = db.RegisterMessage(message_type)
                self.messages[fd.package + '.' + name] = registered

    def _load_services(self):
        self.services: Dict[str, Dict[str, RpcMethod]] = {}
        for proto in self._descriptor.file:
            for service in proto.service:
                self.services[service.name] = {}
                for method in service.method:
                    self.services[service.name][method.name] = RpcMethod(
                        package=proto.package,
                        service=service.name,
                        method=method.name,
                        request=self.messages[method.input_type[1:]],
                        response=self.messages[method.output_type[1:]]
                    )

    @property
    def descriptor(self) -> FileDescriptorSet:
        return self._descriptor

    def save(self) -> dict:
        return MessageToDict(self._descriptor)

    @classmethod
    def restore(cls, descriptor_json: dict):
        fds = FileDescriptorSet()
        ParseDict(descriptor_json, fds)
        return cls(fds)


def _generate_descriptor(out_file: str,
                         proto_file: str,
                         include_paths: List[str] = []):
    if not protoc:
        raise ModuleNotFoundError("Missing package: 'grpcio-tools'")

    if not proto_file.endswith('.proto'):
        raise TypeError('Not a proto file')

    if not os.path.isfile(proto_file):
        raise FileNotFoundError(proto_file)

    out_file = os.path.abspath(out_file)
    proto_file = os.path.abspath(proto_file)

    if not include_paths:
        include_paths = [os.path.dirname(proto_file)]
    include_paths = [
        os.path.abspath(x) for x in include_paths if os.path.isdir(x)
    ]

    protoc_py_file = os.path.abspath(protoc.__file__)
    proto_include = _resource_path('grpc_tools', '_proto')

    protoc_config = [
        protoc_py_file,
        '--proto_path', proto_include,
    ]

    for path in set(include_paths):
        protoc_config += [
            '--proto_path', str(path),
        ]

    protoc_config += [
        '--descriptor_set_out', out_file,
        '--include_imports',
        proto_file,
    ]

    protoc.main(protoc_config)
    return out_file


def _resource_path(package, path):
    try:
        import importlib.resources
        files = importlib.resources.files(package)
        return os.path.abspath(str(files / path))
    except ImportError:
        import pkg_resources
        return pkg_resources.resource_filename(package, path)
