"""
AI Agent module for the Maestro Builder API
Integrates with Maestro's existing agent framework to provide intelligent YAML generation.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import json

# Add the Maestro source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from maestro.agents.openai_agent import OpenAIAgent
except ImportError as e:
    print(f"Warning: Could not import Maestro modules: {e}")
    print("Running in standalone mode without Maestro integration")


class MaestroBuilderAgent:
    """
    AI agent specialized in generating Maestro YAML configurations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the underlying AI agent"""
        if self.api_key and "OpenAIAgent" in globals():
            try:
                # Create a specialized agent for YAML generation
                agent_config = {
                    "type": "openai",
                    "config": {
                        "model": "gpt-4",
                        "api_key": self.api_key,
                        "temperature": 0.1,  # Lower temperature for more consistent YAML generation
                    },
                    "description": "Specialized agent for generating Maestro YAML configurations",
                }
                self.agent = OpenAIAgent(agent_config)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI agent: {e}")
                self.agent = None
        else:
            print("Warning: No OpenAI API key found, running in fallback mode")

    def generate_response(
        self, user_message: str, current_yamls: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate an intelligent response and update YAML files based on user input.

        Args:
            user_message: The user's message
            current_yamls: Current YAML file contents

        Returns:
            Dictionary with response text and updated YAML files
        """
        if self.agent:
            return self._generate_with_ai(user_message, current_yamls)
        else:
            return self._generate_fallback(user_message, current_yamls)

    def _generate_with_ai(
        self, user_message: str, current_yamls: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate response using the AI agent"""
        try:
            # Create a comprehensive prompt for the AI
            prompt = self._create_ai_prompt(user_message, current_yamls)

            # Get response from AI agent
            response = self.agent.run(prompt)

            # Parse the response to extract YAML updates
            updated_yamls = self._parse_ai_response(response, current_yamls)

            return {"response": response, "yaml_files": updated_yamls}

        except Exception as e:
            print(f"Error in AI generation: {e}")
            return self._generate_fallback(user_message, current_yamls)

    def _generate_fallback(
        self, user_message: str, current_yamls: Dict[str, str]
    ) -> Dict[str, Any]:
        """Fallback response generation without AI"""
        message_lower = user_message.lower()

        response = f"I understand you want to: '{user_message}'. I'll help you build the appropriate Maestro configuration."

        updated_yamls = current_yamls.copy()

        # Basic keyword-based YAML generation
        if any(
            keyword in message_lower for keyword in ["agent", "openai", "gpt", "llm"]
        ):
            updated_yamls["agents.yaml"] = self._generate_agents_yaml(user_message)

        if any(
            keyword in message_lower
            for keyword in ["workflow", "step", "process", "pipeline"]
        ):
            updated_yamls["workflow.yaml"] = self._generate_workflow_yaml(user_message)

        return {"response": response, "yaml_files": updated_yamls}

    def _create_ai_prompt(
        self, user_message: str, current_yamls: Dict[str, str]
    ) -> str:
        """Create a comprehensive prompt for the AI agent"""
        prompt = f"""
You are a Maestro AI Builder assistant. Your task is to help users create agents.yaml and workflow.yaml files for the Maestro framework.

Current user request: {user_message}

Current YAML files:
{json.dumps(current_yamls, indent=2)}

Please provide:
1. A helpful response to the user's request
2. Updated YAML files that reflect the user's requirements

Guidelines for YAML generation:
- Use proper YAML syntax
- Include helpful comments
- Follow Maestro's schema for agents and workflows
- Use environment variables for sensitive data (e.g., ${{OPENAI_API_KEY}})
- Make the configuration practical and functional

Please respond with:
1. A natural, helpful response to the user
2. Updated YAML content for both agents.yaml and workflow.yaml files
"""
        return prompt

    def _parse_ai_response(
        self, response: str, current_yamls: Dict[str, str]
    ) -> Dict[str, str]:
        """Parse AI response to extract YAML updates"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        updated_yamls = current_yamls.copy()

        # Try to extract YAML content from the response
        # Look for YAML blocks in the response
        if "agents.yaml" in response.lower():
            # Extract agents.yaml content
            agents_start = response.find("agents:")
            if agents_start != -1:
                # Find the end of the YAML block
                yaml_content = self._extract_yaml_block(response, agents_start)
                if yaml_content:
                    updated_yamls["agents.yaml"] = yaml_content

        if "workflow.yaml" in response.lower():
            # Extract workflow.yaml content
            workflow_start = response.find("workflow:")
            if workflow_start != -1:
                yaml_content = self._extract_yaml_block(response, workflow_start)
                if yaml_content:
                    updated_yamls["workflow.yaml"] = yaml_content

        return updated_yamls

    def _extract_yaml_block(self, text: str, start_pos: int) -> Optional[str]:
        """Extract YAML block from text starting at a given position"""
        try:
            # Find the end of the YAML block by looking for proper indentation
            lines = text[start_pos:].split("\n")
            yaml_lines = []

            for line in lines:
                if line.strip() and not line.startswith("#"):
                    yaml_lines.append(line)
                elif line.strip() == "" and yaml_lines:
                    break

            if yaml_lines:
                return "\n".join(yaml_lines)
        except Exception:
            pass

        return None

    def _generate_agents_yaml(self, user_message: str) -> str:
        """Generate a basic agents.yaml template"""
        return f"""# Agents configuration generated from conversation
agents:
  example_agent:
    type: openai
    config:
      model: gpt-4
      api_key: ${{OPENAI_API_KEY}}
      temperature: 0.7
    description: "Agent created based on: {user_message}"
"""

    def _generate_workflow_yaml(self, user_message: str) -> str:
        """Generate a basic workflow.yaml template"""
        return f"""# Workflow configuration generated from conversation
workflow:
  name: "Generated Workflow"
  description: "Workflow created based on: {user_message}"
  steps:
    - name: "example_step"
      agent: "example_agent"
      input:
        prompt: "Process the request"
"""

    def validate_yaml(self, yaml_content: str, yaml_type: str) -> bool:
        """
        Validate YAML content against Maestro schemas.

        Args:
            yaml_content: The YAML content to validate
            yaml_type: Either 'agents' or 'workflow'

        Returns:
            True if valid, False otherwise
        """
        try:
            # Parse YAML to check syntax
            parsed = yaml.safe_load(yaml_content)

            # Basic validation based on expected structure
            if yaml_type == "agents":
                return "agents" in parsed and isinstance(parsed["agents"], dict)
            elif yaml_type == "workflow":
                return "workflow" in parsed and isinstance(parsed["workflow"], dict)

            return True

        except yaml.YAMLError:
            return False
        except Exception:
            return False
