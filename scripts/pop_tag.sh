#!/bin/bash

VERSION=$(python . -v | awk '{print $2}')

git push --delete origin "v$VERSION"
git tag -d "v$VERSION"
