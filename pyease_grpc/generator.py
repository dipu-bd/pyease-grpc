#!/usr/bin/env python3

import json
import os
import sys
from argparse import ArgumentParser

from . import __version__
from .protoc import Protobuf


def get_args():
    parser = ArgumentParser(
        "pyease-grpc", description="Generate descriptor json from a proto file."
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        type=str,
        help="The output file to write the content."
        " If not provided, the output is dumped to stdout",
    )
    parser.add_argument(
        "-I",
        "--proto_path",
        metavar="PATH",
        type=str,
        action="append",
        help="Specify the directory in which to search for imports.",
        required=True,
    )
    parser.add_argument("proto_file", type=str, help="The proto file path")
    return parser.parse_args()


def main():
    args = get_args()

    protobuf = Protobuf.from_file(
        args.proto_file,
        include_paths=args.proto_path,
    )

    output = json.dumps(protobuf.save())

    if not args.output:
        print(output)
        sys.exit(0)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(output)
