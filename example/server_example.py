"""
FastMCP Echo Server
"""

import logging
from fastmcp_http.server import FastMCPHttpServer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create server
mcp = FastMCPHttpServer("EchoServer", description="A Server that echoes text")


@mcp.tool()
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"


@mcp.resource("echo://static")
def echo_resource() -> str:
    return "Echo!"


@mcp.resource("echo://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"


@mcp.prompt("echo")
def echo_prompt(text: str) -> str:
    return text


if __name__ == "__main__":
    mcp.run_http()
