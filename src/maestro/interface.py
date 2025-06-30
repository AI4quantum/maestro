# SPDX-License-Identifier: Apache-2.0

from typing import Dict, Any, Optional


class Message:
    """Message class for agent communication.
    Args:
        messages: data sent to an agent
    """

    def __init__(self, messages: Optional[Dict[str, Any]] = None):
        self.messages = messages or {}

    def add_message(self):
        """Add additional message"""

    def get_messages(self):
        """Get messages"""
