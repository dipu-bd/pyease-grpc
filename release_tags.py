"""Maintainer helpers for version tags (replaces ``python setup.py push_tag`` / ``pop_tag``)."""
import os
import sys

from pyease_grpc import __version__ as VERSION


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("push", "pop"):
        print("Usage: python release_tags.py push|pop", file=sys.stderr)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "push":
        os.system(f'git tag "v{VERSION}"')
        os.system("git push --tags")
    else:
        os.system(f'git push --delete origin "v{VERSION}"')
        os.system(f'git tag -d "v{VERSION}"')


if __name__ == "__main__":
    main()
