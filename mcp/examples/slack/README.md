# Slack post message MCP tool

This MCP tool has one function that posts a message to the specified slack channel.

```python
async def post_slack_message(message: str, channel: str) -> str:
    """Post a slack message to channel.

    Args:
        message: messege posted to the channel
        channel: channel ID of the message posted
    """
```

## Environment variables

* SLACK_BOT_TOKEN: This is slack access token (required)  
* MCP_SLACK_PORT: MCP server port (optional, default 30055)
* OPENAI_API_KEY: for OpenAI framework
* OPENAI_BASE_URL: for OpenAI framework

## Run example

start mcp server
```cmd
python slack_mcp.py
```

Register mcp server
```cmd
maestro create tools.yaml
```

Update workflow
Update the channel id in the prompt string in the workflow.yaml file

Run a workflow
```
maestro run agent.yaml workflow.yaml
```
