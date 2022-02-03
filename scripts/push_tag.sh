#!/bin/bash

VERSION=$(sed -nr "s/[^']+'([^']+)'$/\1/p" pyease_grpc/__init__.py)

# git push --delete origin "v$VERSION"
# git tag -d "v$VERSION"
git tag "v$VERSION"
git push --tags
