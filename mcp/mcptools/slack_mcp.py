from fastmcp import FastMCP
import os
import asyncio
from slack_sdk import WebClient

mcp = FastMCP("slack")


@mcp.tool()
async def post_slack_message(message: str, channel: str) -> str:
    """Post a slack message to channel.

    Args:
        message: messege posted to the channel
        channel: channel ID of the message posted
    """
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        print("Error: SLACK_BOT_TOKEN environment variable not set.")
        return
    client = WebClient(token=slack_token)
    try:
        result = client.chat_postMessage(channel=channel, text=message)
        print(f"Message posted to channel {channel}: {result['ts']}")
    except Exception as e:
        print(f"Error posting message: {e}")


def main():
    port = int(os.getenv("MCP_SLACK_PORT", 30055))
    asyncio.run(mcp.run(transport="http", host="0.0.0.0", port=port))


if __name__ == "__main__":
    main()
