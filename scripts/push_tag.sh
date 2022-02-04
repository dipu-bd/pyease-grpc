#!/bin/bash

VERSION=$(python . -v | awk '{print $2}')

git tag "v$VERSION"
git push --tags
