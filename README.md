# MCP Documentation Server

A customized version of the MCP documentation server that enables integration between LLM applications (like Cursor, Claude Desktop, Windsurf) and documentation sources via the Model Context Protocol.

## Overview

This server provides MCP host applications with:
1. Access to specific documentation files (langgraph.txt and mcp.txt)
2. Tools to fetch documentation from URLs within those files

## Supported Documentation

Currently set up for:
- LangGraph Documentation (from https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/langgraph.txt)
- MCP Documentation (from https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/mcp.txt)

## Quick Start

### Setup and Run

```bash
# Clone the repository
git clone https://github.com/esakrissa/mcp-doc.git
cd mcp-doc

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e .
```

### Running the Server

You can run the server using the installed command:

```bash
# Run the server with the config file
mcpdoc \
    --json config.json \
    --transport sse \
    --port 8082 \
    --host localhost
```

Or if you prefer using UV:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server with UV
uvx --from mcpdoc mcpdoc \
    --json config.json \
    --transport sse \
    --port 8082 \
    --host localhost
```

### IDE Integration

#### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-doc": {
      "command": "mcpdoc",
      "args": [
        "--urls",
        "LangGraph:https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/langgraph.txt",
        "ModelContextProtocol:https://raw.githubusercontent.com/esakrissa/mcp-doc/main/docs/mcp.txt",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

Add to Cursor User Rules:

```
for ANY question about LangGraph and Model Context Protocol (MCP), use the mcp-doc server to help answer -- 
+ call list_doc_sources tool to get the available documentation files
+ call fetch_docs tool to read the langgraph.txt or mcp.txt file
+ reflect on the urls in langgraph.txt or mcp.txt 
+ reflect on the input question 
+ call fetch_docs on any urls relevant to the question
+ use this to answer the question
```

## Security Note

For security reasons, strict domain access controls are implemented:
- Remote documentation files: Only the specific domain is automatically allowed
- Local documentation files: No domains are automatically allowed
- Use `--allowed-domains` to explicitly add domains or `--allowed-domains '*'` to allow all (use with caution)

## References

This project is based on the original [mcpdoc by LangChain AI](https://github.com/langchain-ai/mcpdoc), modified to provide focused documentation access for LangGraph and MCP. 