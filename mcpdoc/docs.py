"""A server for LangGraph and MCP documentation.

This is used as a way to test the doc functionality via MCP.
"""

# /usr/bin/env python3
import httpx
from markdownify import markdownify
from mcp.server.fastmcp import FastMCP

server = FastMCP(name="mcp-doc")

ALLOWED_PREFIX = "https://raw.githubusercontent.com/"

HTTPX_CLIENT = httpx.AsyncClient(follow_redirects=False)


@server.tool()
async def get_docs(url: str = "langgraph_overview") -> str:
    """Get documentation for LangGraph or MCP.

    Always fetch the overview first to get a list of available URLs:
    - Use "langgraph_overview" for LangGraph documentation
    - Use "mcp_overview" for MCP documentation

    Args:
        url: The URL to fetch. Must start with https://raw.githubusercontent.com/
        or be one of the overview options.
    """
    if url == "langgraph_overview":
        url = "https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/langgraph.txt"
    elif url == "mcp_overview":
        url = "https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/mcp.txt"

    if not url.startswith(ALLOWED_PREFIX):
        return (
            "Error: Invalid url. Must start with https://raw.githubusercontent.com/ "
            'or be one of the overview options ("langgraph_overview" or "mcp_overview")'
        )

    response = await HTTPX_CLIENT.get(url)
    response.raise_for_status()
    if response.status_code == 200:
        # Convert HTML to markdown
        markdown_content = markdownify(response.text)
        return markdown_content
    else:
        return "Encountered an error while fetching the URL."


if __name__ == "__main__":
    server.run(transport="stdio")
