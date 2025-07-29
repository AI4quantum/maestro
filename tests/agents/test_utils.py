# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM
import os

from maestro.agents.utils import is_url, is_file, get_content

valid = {
    "url": "https://raw.githubusercontent.com/AI4quantum/maestro/refs/heads/main/README.md",
    "path": os.path.join(os.path.dirname(__file__), "../../CODE_OF_CONDUCT.md"),
    "string": "Some content",
    "list": ["Some", "multiline", "content"],
}
invalid = {
    "url": "raw.githubusercontent.com/AI4quantum/maestro/refs/heads/main/README.md",
    "path": "./NOT_A_FILE.md",
}


def test_is_url():
    assert is_url(valid["url"]) is True
    assert is_url(invalid["url"]) is False
    assert is_url(valid["path"]) is False
    assert is_url(valid["string"]) is False


def test_is_file():
    assert is_file(valid["path"]) is True
    assert is_file(invalid["path"]) is False
    assert is_file(valid["string"]) is False
    assert is_file(valid["url"]) is False


def test_get_content():
    assert "# Maestro" in get_content(valid["url"])
    assert "# Contributor Covenant Code of Conduct" in get_content(valid["path"])
    assert get_content(valid["string"]) == valid["string"]
    assert get_content(valid["list"]) == valid["list"]
    assert get_content(invalid["url"]) == invalid["url"]
    assert get_content(invalid["path"]) == invalid["path"]
