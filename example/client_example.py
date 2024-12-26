"""
FastMCP Echo Client Example
"""

from fastmcp_http.client import FastMCPHttpClient


def main():
    # Create client
    client = FastMCPHttpClient("http://127.0.0.1:31337")

    servers = client.list_servers()
    print(servers)

    tools = client.list_tools()
    print(tools)

    result = client.call_tool("EchoServer.echo_tool", {"text": "Hello, World!"})
    print(result)


if __name__ == "__main__":
    main()
