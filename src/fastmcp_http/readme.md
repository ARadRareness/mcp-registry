# FastMCP-HTTP

FastMCP-HTTP is a Python package that provides a HTTP REST client-server solution for MCP. It offers a unified interface for accessing tools, prompts and resources through HTTP endpoints.


## Installation

### From PyPI

```bash
pip install fastmcp-http
```

### From source

To build and install the package from source:

1. Clone the repository
2. Navigate to the project directory
3. Install build and twine
   ```bash
   python -m pip install build
   ```
4. Build the package:
   ```bash
   python -m build
   ```
5. Install the package:
   ```bash
   pip install dist/fastmcp_http-X.Y.Z-py3-none-any.whl
   ```

# Examples

## FastMCPHttpServer

```python
from fastmcp_http.server import FastMCPHttpServer

mcp = FastMCPHttpServer("MyServer", description="My MCP Server")

@mcp.tool()
def my_tool(text: str) -> str:
    return f"Processed: {text}"

if __name__ == "__main__":
    mcp.run_http(register_server=False, port=15151)
```

## FastMCPHttpClient

```python
from fastmcp_http.client import FastMCPHttpClient


def main():
    client = FastMCPHttpClient("http://127.0.0.1:15151")

    tools = client.list_tools()
    print(tools)

    result = client.call_tool("my_tool", {"text": "Hello, World!"})
    print(result)


if __name__ == "__main__":
    main()
```