import json
import logging
import os
import shutil
import tempfile
from typing import Dict, Generator, List, Optional, Type

from google.protobuf.descriptor_pb2 import FileDescriptorSet
from google.protobuf.message import Message

from . import _protocol
from .rpc_method import RpcMethod
from .rpc_method_type import get_method_type
from .rpc_uri import RpcUri

logger = logging.getLogger(__name__)


class Protobuf(object):
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
            res = _protocol.generate_descriptor(out_file, proto_file, include_paths)
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
        fds = _protocol.parse_message(FileDescriptorSet, descriptor_json)
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
        self.messages = _protocol.load_messages(self._descriptor)
        self.services: Dict[str, Dict[str, RpcMethod]] = {}
        for method in _load_rpc_methods(self._descriptor, self.messages):
            self.services.setdefault(method.service, {})
            self.services[method.service][method.method] = method

    def __str__(self) -> str:
        return json.dumps(self.save(), ensure_ascii=False)

    @property
    def descriptor(self) -> FileDescriptorSet:
        """Returns the :class:`FileDescriptorSet` of the current protobuf"""
        return self._descriptor

    def save(self) -> dict:
        """Returns the :class:`FileDescriptorSet` of the current protobuf as JSON"""
        return _protocol.message_to_dict(self._descriptor)

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


def _load_rpc_methods(
    fds: FileDescriptorSet,
    messages: Dict[str, Type[Message]],
) -> Generator[RpcMethod, None, None]:
    for proto in fds.file:
        for service in proto.service:
            for method in service.method:
                method_type = get_method_type(
                    method.client_streaming,
                    method.server_streaming,
                )
                yield RpcMethod(
                    package=proto.package,
                    service=service.name,
                    method=method.name,
                    type=method_type,
                    request=messages[method.input_type[1:]],
                    response=messages[method.output_type[1:]],
                )
