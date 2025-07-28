# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Common utility functions for agents."""

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def is_url(text):
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_file(text):
    try:
        return Path(text).exists()
    except OSError:
        return False


def get_content(text):
    if text is None:
        return None
    if isinstance(text, list):
        return text
    if is_url(text):
        with urlopen(text) as response:
            return response.read().decode("utf-8")
    if is_file(text):
        return Path(text).read_text()
    return text
