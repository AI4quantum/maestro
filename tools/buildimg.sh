#!/bin/bash

CONTAINER_CMD="${CONTAINER_CMD:=docker}"
GITHUB_ORG="${GITHUB_ORG:=ai4quantum}"

# extract version from pyproject.toml
PYPROJECT_TOML="pyproject.toml"
VERSION=$(grep -E '^(version|tool\.poetry\.version) *= *"[^"]+"' "$PYPROJECT_TOML" | head -n 1 | sed -E 's/.*"([^"]+)".*/\1/')
echo $VERSION

# build distribution
uv build

# build container images
$CONTAINER_CMD build -t ghcr.io/$GITHUB_ORG/maestro:$VERSION -f Dockerfile --build-arg MAESTRO_VERSION=$VERSION --build-arg GITHUB_ORG=$GITHUB_ORG .
$CONTAINER_CMD build -t ghcr.io/$GITHUB_ORG/maestro-cli:$VERSION -f Dockerfile-cli --debug --build-arg MAESTRO_VERSION=$VERSION --build-arg GITHUB_ORG=$GITHUB_ORG .
