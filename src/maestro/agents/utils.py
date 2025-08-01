# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Common utility functions for agents."""

import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def is_url(text):
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_filepath(text, yaml_file):
    if os.path.isabs(text) and os.path.exists(text):
        return text
    base_path = os.path.dirname(yaml_file)
    path = os.path.join(base_path, text)
    if os.path.exists(path):
        return path
    return None


def get_content(text, yaml_file):
    if text is None:
        return None
    if isinstance(text, list):
        return text
    if is_url(text):
        if "gist.github" in text:
            text += "/raw"
        elif "github" in text:
            text += "?raw=true"
        with urlopen(text) as response:
            return response.read().decode("utf-8")
    path = get_filepath(text, yaml_file)
    if path is not None:
        return Path(path).read_text()
    return text
