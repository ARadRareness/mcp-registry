from typing import Any, Optional
from flask import Flask
from mcp.server.fastmcp import FastMCP

class FastMCPHttpServer(FastMCP):
    flask_app: Flask

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **settings: Any,
    ) -> None:
        """Initialize the FastMCP HTTP server.

        Args:
            name: Optional name for the server
            **settings: Additional settings to pass to FastMCP
        """
        ...

    def _setup_routes(self) -> None:
        """Set up the Flask routes for the HTTP server.

        Sets up the following endpoints:
        - GET /tools: List available tools
        - POST /tools/<name>: Call a specific tool
        - GET /resources: List available resources
        - GET /resources/<uri>: Read a specific resource
        - GET /prompts: List available prompts
        - POST /prompts/<name>: Get a specific prompt
        """
        ...

    def register_server(
        self,
        server_url: str = "http://127.0.0.1",
        registry_url: str = "http://127.0.0.1:31337",
    ) -> int:
        """Register the server with the registry. Returns the port to use for the server.

        Args:
            server_url: URL of the server to register.
            registry_url: URL of the registry to register with.
        """
        ...

    def run_http(
        self, host: str = "0.0.0.0", register_server: bool = True, port: int = 5000
    ) -> None:
        """Run the FastMCP HTTP server.

        Args:
            host: Host to bind to (default: "0.0.0.0")
            port: Port to listen on (default: 5000)
            register_server: Whether to register the server with the registry (default: True)
        """
        ...
