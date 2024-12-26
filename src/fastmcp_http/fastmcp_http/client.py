from typing import Any, List, Optional
import requests
from mcp import Tool, Resource
from mcp.types import Prompt, TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel


class Server(BaseModel):
    name: str
    description: str
    url: str
    port: int


class FastMCPHttpClient:
    def __init__(self, base_url: str):
        """Initialize the FastMCP HTTP client.

        Args:
            base_url: Base URL of the FastMCP HTTP server
        """
        self.base_url = base_url.rstrip("/")

    def list_servers(self) -> List[Server]:
        """List available servers from the server, only works for registry servers."""
        response = requests.get(f"{self.base_url}/servers")
        response.raise_for_status()
        return [Server.model_validate(server) for server in response.json()]

    def list_tools(self, server_name: Optional[str] = None) -> List[Tool]:
        """List available tools from the server."""
        params = {}
        if server_name is not None:
            params["server_name"] = server_name

        response = requests.get(f"{self.base_url}/tools", params=params)
        response.raise_for_status()
        return [Tool.model_validate(tool) for tool in response.json()]

    def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool with the given arguments."""
        payload = {"name": name, **arguments}
        response = requests.post(f"{self.base_url}/tools/call_tool", json=payload)
        response.raise_for_status()

        contents = []
        for content_data in response.json():
            if content_data.get("type") == "text":
                contents.append(TextContent.model_validate(content_data))
            elif content_data.get("type") == "image":
                contents.append(ImageContent.model_validate(content_data))
            elif content_data.get("type") == "embedded_resource":
                contents.append(EmbeddedResource.model_validate(content_data))
            else:
                raise ValueError(f"Unknown content type: {content_data.get('type')}")
        return contents

    def list_resources(self) -> List[Resource]:
        """List available resources from the server."""
        response = requests.get(f"{self.base_url}/resources")
        response.raise_for_status()
        return [Resource.model_validate(resource) for resource in response.json()]

    def read_resource(self, uri: str) -> bytes:
        """Read a resource from the server."""
        response = requests.get(f"{self.base_url}/resources/{uri}")
        response.raise_for_status()
        return response.content

    def list_prompts(self) -> List[Prompt]:
        """List available prompts from the server."""
        response = requests.get(f"{self.base_url}/prompts")
        response.raise_for_status()
        return [Prompt.model_validate(prompt) for prompt in response.json()]

    def get_prompt(self, name: str, arguments: dict[str, Any]) -> Prompt:
        """Get a prompt with the given arguments."""
        response = requests.post(f"{self.base_url}/prompts/{name}", json=arguments)
        response.raise_for_status()
        return response.json()
