# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum
from typing import Callable, Union

from .beeai_agent import BeeAIAgent, BeeAILocalAgent
from .crewai_agent import CrewAIAgent
from .dspy_agent import DspyAgent
from .openai_agent import OpenAIAgent
from .remote_agent import RemoteAgent
from .mock_agent import MockAgent
from .custom_agent import CustomAgent
from .code_agent import CodeAgent


class AgentFramework(StrEnum):
    """Enumeration of supported frameworks"""

    BEEAI = "beeai"
    CREWAI = "crewai"
    DSPY = "dspy"
    OPENAI = "openai"
    MOCK = "mock"
    REMOTE = "remote"
    CUSTOM = "custom"
    CODE = "code"

    # Not yet supported
    # LANGFLOW = 'langflow'


class AgentFactory:
    """Factory class for handling agent frameworks"""

    @staticmethod
    def create_agent(
        framework: AgentFramework, mode="local"
    ) -> Callable[
        ...,
        Union[
            BeeAIAgent,
            BeeAILocalAgent,
            CrewAIAgent,
            DspyAgent,
            OpenAIAgent,
            RemoteAgent,
            CodeAgent,
            MockAgent,
        ],
    ]:
        """Create an instance of the specified agent framework.

        Args:
            framework (AgentFramework): The framework to create. Must be a valid enum value.

        Returns:
            A new instance of the corresponding agent class.
        """
        factories = {
            AgentFramework.BEEAI: BeeAILocalAgent,
            AgentFramework.CREWAI: CrewAIAgent,
            AgentFramework.DSPY: DspyAgent,
            AgentFramework.OPENAI: OpenAIAgent,
            AgentFramework.CODE: CodeAgent,
            AgentFramework.MOCK: MockAgent,
        }

        remote_factories = {
            AgentFramework.BEEAI: BeeAIAgent,
            AgentFramework.REMOTE: RemoteAgent,
            AgentFramework.MOCK: MockAgent,
        }
        if framework == "custom":
            return CustomAgent

        if framework not in factories and framework not in remote_factories:
            raise ValueError(f"Unknown framework: {framework}")

        if mode == "remote" or framework == AgentFramework.REMOTE:
            return remote_factories[framework]
        else:
            return factories[framework]

    @classmethod
    def get_factory(
        cls, framework: str, mode="local"
    ) -> Callable[
        ...,
        Union[
            BeeAIAgent,
            BeeAILocalAgent,
            CrewAIAgent,
            DspyAgent,
            OpenAIAgent,
            RemoteAgent,
            CodeAgent,
            MockAgent,
        ],
    ]:
        """Get a factory function for the specified agent type."""
        return cls.create_agent(framework, mode)
