#!/usr/bin/env python3

from argparse import ArgumentParser
import json
import os
import sys

from . import __version__
from .protobuf import Protobuf


def get_args():
    parser = ArgumentParser("pyease-grpc", description="Generate descriptor json from a proto file.")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        type=str,
        help="The output file to write the content. If not provided, the output is dumped to stdout",
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

    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(output)
