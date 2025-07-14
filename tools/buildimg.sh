#!/bin/bash

CONTAINER_CMD="${CONTAINER_CMD:=docker}"
VERSION=$1

# extract version from pyproject.toml
PYPROJECT_TOML="pyproject.toml"

# build distribution
uv build

# build container images
$CONTAINER_CMD build -t maestro-base:$VERSION -f Dockerfile-base --build-arg MAESTRO_VERSION=$VERSION
$CONTAINER_CMD build -t maestro-cli:$VERSION -f Dockerfile-cli --build-arg MAESTRO_VERSION=$VERSION
