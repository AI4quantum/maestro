#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
from setuptools import build_meta as _orig


def _run_ui_build():
    build_script = Path(__file__).parent / "build.py"

    if not build_script.exists():
        print("Warning: build.py not found, skipping UI build")
        return

    print("=" * 60)
    print("Running UI build (npm install && npm run build)...")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(build_script)], cwd=Path(__file__).parent
    )

    if result.returncode != 0:
        print("Warning: UI build failed, but continuing with installation")
    else:
        print("UI build completed successfully")

    print("=" * 60)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    _run_ui_build()
    return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    _run_ui_build()
    return _orig.build_sdist(sdist_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    _run_ui_build()
    return _orig.build_editable(wheel_directory, config_settings, metadata_directory)


get_requires_for_build_wheel = _orig.get_requires_for_build_wheel
get_requires_for_build_sdist = _orig.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _orig.prepare_metadata_for_build_wheel

if hasattr(_orig, "get_requires_for_build_editable"):
    get_requires_for_build_editable = _orig.get_requires_for_build_editable
if hasattr(_orig, "prepare_metadata_for_build_editable"):
    prepare_metadata_for_build_editable = _orig.prepare_metadata_for_build_editable
