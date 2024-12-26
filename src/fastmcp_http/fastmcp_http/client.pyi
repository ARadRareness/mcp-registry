from typing import Any, List
from mcp import Tool, Resource
from mcp.types import Prompt, TextContent, ImageContent, EmbeddedResource

class FastMCPHttpClient:
    base_url: str

    def __init__(self, base_url: str) -> None:
        """Initialize the FastMCP HTTP client.

        Args:
            base_url: Base URL of the FastMCP HTTP server
        """
        ...

    def list_tools(self) -> List[Tool]:
        """List available tools from the server."""
        ...

    def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool with the given arguments."""
        ...

    def list_resources(self) -> List[Resource]:
        """List available resources from the server."""
        ...

    def read_resource(self, uri: str) -> bytes:
        """Read a resource from the server."""
        ...

    def list_prompts(self) -> List[Prompt]:
        """List available prompts from the server."""
        ...

    def get_prompt(self, name: str, arguments: dict[str, Any]) -> Prompt:
        """Get a prompt with the given arguments."""
        ...
