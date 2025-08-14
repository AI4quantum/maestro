import json

from fastmcp import Client
from jinja2 import Template

from maestro.agents.agent import Agent


class QueryAgent(Agent):
    def __init__(self, agent_def: dict) -> None:
        super().__init__(agent_def)
        self.db_name = agent_def["spec"]["database"]
        self.collection_name = agent_def["spec"].get("collection", "MaestroDocs")
        self.limit = agent_def["spec"].get("results_limit", 10)
        self.output_template = Template(self.agent_output or "{{output}}")

    async def run(self, prompt: str) -> str:
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

            if isinstance(tool_result.data, str):
                self.print(f"ERROR [QueryAgent {self.agent_name}]: {tool_result.data}")
                return tool_result.data

            output = "\n\n".join(
                [doc["text"] for doc in json.loads(tool_result.content[0].text)]
            )

            answer = self.output_template.render(output=output, prompt=prompt)

            self.print(f"Response from {self.agent_name}: {answer}\n")

            return answer

    async def run_streaming(self, prompt: str) -> str:
        return await self.run(prompt)
