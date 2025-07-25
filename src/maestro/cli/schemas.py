"""Embedded JSON schemas for Maestro validation."""

AGENT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/AI4quantum/maestro/schemas/agent_schema.json",
    "title": "Maestro Agent",
    "description": "A schema for defining Maestro workflows in YAML or JSON",
    "type": "object",
    "properties": {
        "apiVersion": {"type": "string", "description": "API version maestro/v1alpha1"},
        "kind": {"type": "string", "description": "must be Agent"},
        "metadata": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "agent name"},
                "labels": {
                    "type": "object",
                    "description": "agent labels, key: value pairs",
                },
            },
            "required": ["name"],
        },
        "spec": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Short human-readable desciption of this agent",
                },
                "model": {
                    "type": "string",
                    "description": "The LLM model for this agent",
                },
                "framework": {
                    "type": "string",
                    "description": "The agent framework type. beeai, crewai, remote or mock",
                },
                "mode": {
                    "type": "string",
                    "description": "The mode of the agent.  remote or local",
                },
                "tools": {
                    "type": "array",
                    "description": "tool list of the agent",
                    "items": {"type": "string"},
                },
                "instructions": {
                    "type": "string",
                    "description": "The instruction (context) to pass to this agent",
                },
                "code": {
                    "type": "string",
                    "description": "The (optional) code defintion for the agent",
                },
                "input": {
                    "type": "string",
                    "description": "instructions for the agent",
                },
                "output": {
                    "type": "string",
                    "description": "instructions for the agent",
                },
                "url": {
                    "type": "string",
                    "description": "The (optional) url to send a request to the agent",
                },
            },
        },
    },
}

TOOL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/AI4quantum/maestro/schemas/tool_schema.json",
    "title": "Maestro Tool",
    "description": "A schema for defining Maestro tools in YAML or JSON",
    "type": "object",
    "properties": {
        "apiVersion": {"type": "string", "description": "API version maestro/v1alpha1"},
        "kind": {"type": "string", "description": "must be Tool"},
        "metadata": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "tool name"},
                "labels": {
                    "type": "object",
                    "description": "tool labels, key: value pairs",
                },
            },
            "required": ["name"],
        },
        "spec": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Short human-readable description of this tool",
                },
                "type": {"type": "string", "description": "The type of tool"},
                "url": {"type": "string", "description": "The URL for the tool"},
                "parameters": {"type": "object", "description": "Tool parameters"},
            },
        },
    },
}

WORKFLOW_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/AI4quantum/maestro/schemas/workflow_schema.json",
    "title": "Maestro Workflow",
    "description": "A schema for defining Maestro workflows in YAML or JSON",
    "type": "object",
    "properties": {
        "apiVersion": {"type": "string", "description": "API version maestro/v1alpha1"},
        "kind": {"type": "string", "description": "must be Workflow"},
        "metadata": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "workflow name"},
                "labels": {
                    "type": "object",
                    "description": "workflow labels, key: value pairs",
                },
            },
            "required": ["name"],
        },
        "spec": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Short human-readable description of this workflow",
                },
                "steps": {
                    "type": "array",
                    "description": "List of workflow steps",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "agent": {"type": "string"},
                            "input": {"type": "string"},
                            "output": {"type": "string"},
                            "condition": {"type": "string"},
                            "loop": {"type": "object"},
                            "parallel": {"type": "array"},
                        },
                    },
                },
                "cron": {
                    "type": "string",
                    "description": "Cron expression for scheduling",
                },
            },
        },
    },
}

# Schema mapping for easy lookup
SCHEMA_MAP = {"Agent": AGENT_SCHEMA, "Tool": TOOL_SCHEMA, "Workflow": WORKFLOW_SCHEMA}
