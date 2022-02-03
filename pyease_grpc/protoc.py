import importlib
import importlib.resources
import importlib.util
import os
import shutil
import tempfile
from typing import Dict, Type

from google.protobuf import reflection, symbol_database
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.message import Message
from grpc_tools import protoc

from .rpc_method import RpcMethod


class Protobuf:

    @classmethod
    def string(cls, proto: str, filename: str = 'pyease'):
        tmpdir = os.path.abspath(tempfile.mkdtemp(filename))
        os.makedirs(tmpdir, exist_ok=True)
        try:
            proto_file = os.path.join(tmpdir, filename + '.proto')
            with open(proto_file, 'w') as f:
                f.write(proto)
            return cls.file(proto_file, tmpdir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @classmethod
    def file(cls, proto_file: str, root_dir: str):
        basename = os.path.basename(proto_file)
        tmpdir = tempfile.mkdtemp(basename)
        os.makedirs(tmpdir, exist_ok=True)
        try:
            desc = Protobuf._generate_descriptor(tmpdir, proto_file, root_dir)
            return cls(desc)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @staticmethod
    def _generate_descriptor(outdir: str, proto_file: str, root_dir: str):
        if not proto_file.endswith('.proto'):
            raise TypeError('Not a proto file')

        if not os.path.isfile(proto_file):
            raise FileNotFoundError(proto_file)

        outdir = os.path.abspath(outdir)
        root_dir = os.path.abspath(root_dir)
        proto_file = os.path.abspath(proto_file)
        outfile = os.path.join(outdir, 'descriptor.bin')

        grpc_tool_path = importlib.resources.files('grpc_tools')
        protoc_file = os.path.abspath(str(grpc_tool_path / 'protoc.py'))
        proto_include = os.path.abspath(str(grpc_tool_path / '_proto'))

        protoc.main([
            protoc_file,
            '--proto_path', proto_include,
            '--proto_path', root_dir,
            '--descriptor_set_out', outfile,
            '--include_imports',
            proto_file,
        ])

        with open(outfile, 'rb') as f:
            return FileDescriptorSet.FromString(f.read())

    def __init__(self, descriptor: FileDescriptorSet) -> None:
        self.descriptor = descriptor
        self._load_messages()
        self._load_services()

    def _load_messages(self):
        db = symbol_database.Default()
        self.messages: Dict[str, Type[Message]] = {}
        for proto in self.descriptor.file:
            fd = db.pool.Add(proto)
            for name in fd.message_types_by_name:
                message = fd.message_types_by_name[name]
                message_type = reflection.MakeClass(message)
                registered = db.RegisterMessage(message_type)
                self.messages[fd.package + '.' + name] = registered

    def _load_services(self):
        self.services: Dict[str, Dict[str, RpcMethod]] = {}
        for proto in self.descriptor.file:
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
