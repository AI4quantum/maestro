import json

from fastmcp import Client
from jinja2 import Template

from maestro.agents.agent import Agent


class QueryAgent(Agent):
    def __init__(self, agent_def: dict) -> None:
        super().__init__(agent_def)
        self.db_name = agent_def["metadata"]["query_input"]["db_name"]
        self.collection_name = agent_def["metadata"]["query_input"].get(
            "collection_name", "MaestroDocs"
        )
        self.limit = agent_def["metadata"]["query_input"].get("limit", 10)
        self.output_template = Template(self.agent_output or "{{result}}")

    async def run(self, prompt: str, context=None, step_index=None) -> str:
        self.print(f"Running {self.agent_name} with prompt...")

        async with Client(
            self.agent_url or "http://localhost:8030/mcp/", timeout=30
        ) as client:
            self.print(f"Querying vector database '{self.db_name}'...")
            params = {
                "input": {
                    "db_name": self.db_name,
                    "query": prompt,
                    "limit": self.limit,
                    "collection_name": self.collection_name,
                }
            }
            tool_result = await client.call_tool("search", params)

            try:
                output = "\n\n".join(
                    [doc["text"] for doc in json.loads(tool_result.data)]
                )

                answer = self.output_template.render(result=output, prompt=prompt)

                self.print(f"Response from {self.agent_name}: {answer}\n")

                return answer
            except json.JSONDecodeError:
                self.print(f"ERROR [QueryAgent {self.agent_name}]: {tool_result.data}")
                return tool_result.data

    async def run_streaming(self, prompt: str) -> str:
        return await self.run(prompt)
