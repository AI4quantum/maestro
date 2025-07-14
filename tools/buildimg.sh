#!/bin/bash

CONTAINER_CMD="${CONTAINER_CMD:=docker}"

# extract version from pyproject.toml
PYPROJECT_TOML="pyproject.toml"
VERSION=$(grep -E '^(version|tool\.poetry\.version) *= *"[^"]+"' "$PYPROJECT_TOML" | \
          head -n 1 | \
          sed -E 's/.*"([^"]+)".*/\1/')

# build distribution
uv build

# build container images
$CONTAINER_CMD build -t maestro-base:$VERSION -f Dockerfile-base --build-arg MAESTRO_VERSION=$VERSION
$CONTAINER_CMD build -t maestro-cli:$VERSION -f Dockerfile-cli --build-arg MAESTRO_VERSION=$VERSION
