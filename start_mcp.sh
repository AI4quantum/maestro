#!/usr/bin/env bash

uv run python src/maestro/maestro_mcp/server.py --port ${1:-"8000"}
