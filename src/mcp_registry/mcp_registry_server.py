import time
from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import Dict
import socket
import random
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread

from fastmcp_http.client import FastMCPHttpClient
from src.mcp_registry.permission_management import permission_server

app = Flask(__name__)


@dataclass
class Server:
    name: str
    description: str
    url: str
    port: int


# Global dictionaries to store servers and health status
servers: Dict[str, Server] = {}
health_cache: Dict[str, tuple[datetime, bool]] = {}

# Add constants for storage
STORAGE_FILE = Path("servers.json")

# Add constant for permission server name
PERMISSION_SERVER_NAME = "PermissionServer"


def _generate_port(
    server_url: str, start_port: int = 5000, end_port: int = 65535
) -> int:
    """Generate an available port for the server.

    Args:
        server_url: The server URL to check ports against
        start_port: Minimum port number to consider (default: 5000)
        end_port: Maximum port number to consider (default: 65535)

    Returns:
        An available port number
    """
    # Get host from server URL
    from urllib.parse import urlparse

    host = urlparse(server_url).hostname or "127.0.0.1"

    # Start with a random port in the range
    port = random.randint(start_port, end_port)

    while port <= end_port:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            sock.close()
            return port
        except socket.error:
            port += 1
        finally:
            sock.close()

    raise RuntimeError("No available ports found in the specified range")


def check_server_health(server: Server) -> bool:
    """Check if a server is healthy by pinging its health endpoint.
    Caches the result for 1 minutes.

    Args:
        server: Server instance to check

    Returns:
        bool: True if server is healthy, False otherwise
    """
    # Check if we have a recent cached result
    if server.name in health_cache:
        last_check, is_healthy = health_cache[server.name]
        if datetime.now() - last_check < timedelta(seconds=30):
            return is_healthy

    try:
        response = requests.get(f"{server.url}:{server.port}/health", timeout=5)
        is_healthy = response.status_code == 200
    except requests.RequestException:
        is_healthy = False

    health_cache[server.name] = (datetime.now(), is_healthy)
    return is_healthy


def load_servers() -> Dict[str, Server]:
    """Load servers from storage and verify they're running."""
    if not STORAGE_FILE.exists():
        return {}

    servers = {}
    try:
        with open(STORAGE_FILE, "r") as f:
            data = json.load(f)
            for server_data in data.values():
                server = Server(**server_data)
                if check_server_health(server):
                    servers[server.name] = server
                else:
                    print(f"Server {server.name} appears to be down, skipping...")
    except Exception as e:
        print(f"Error loading servers: {e}")

    return servers


def save_servers():
    """Save current servers to storage."""
    with open(STORAGE_FILE, "w") as f:
        json.dump({name: vars(server) for name, server in servers.items()}, f)


@app.route("/register_server", methods=["POST"])
def register_server():
    data = request.get_json()

    # Validate required fields
    required_fields = ["server_url", "server_name", "server_description"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Block registration of permission server name by other servers
    if data["server_name"] == PERMISSION_SERVER_NAME:
        return jsonify({"error": "Reserved server name"}), 403

    port = _generate_port(data["server_url"])

    # Create new server instance
    new_server = Server(
        url=data["server_url"],
        name=data["server_name"],
        description=data["server_description"],
        port=port,
    )

    # Add to global dictionary
    servers[data["server_name"]] = new_server
    save_servers()  # Save after registration
    print("Added server: ", data["server_name"])

    return (
        jsonify(
            {
                "message": "Server registered successfully",
                "server": {
                    "name": new_server.name,
                    "url": new_server.url,
                    "description": new_server.description,
                    "port": port,
                },
            }
        ),
        201,
    )


@app.route("/servers", methods=["GET"])
def get_servers():
    """Return a list of all registered and healthy servers."""
    return jsonify(
        [
            {
                "name": server.name,
                "url": server.url,
                "description": server.description,
                "port": server.port,
            }
            for server in servers.values()
            if check_server_health(server)
        ]
    )


@app.route("/tools", methods=["GET"])
def get_tools():
    """Return a list of tools from registered servers."""
    server_name = request.args.get("server_name")

    all_tools = []
    try:
        # Filter servers if server_name is provided
        target_servers = [servers[server_name]] if server_name else servers.values()

        for server in target_servers:
            try:
                if not check_server_health(server):
                    continue
                client = FastMCPHttpClient(f"{server.url}:{server.port}")
                for tool in client.list_tools():
                    tool.name = f"{server.name}.{tool.name}"
                    all_tools.append(tool)
            except requests.RequestException as e:
                print(f"Error fetching tools from {server.name}: {e}")
                health_cache[server.name] = (datetime.now(), False)
                continue

        return json.dumps([tool.model_dump() for tool in all_tools])
    except KeyError:
        return jsonify({"error": f"Server '{server_name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tools/call_tool", methods=["POST"])
def call_tool():
    """Call a tool on a specific server."""
    data = request.get_json()
    name = data.pop("name", None)  # Extract and remove name from arguments

    if name is None:
        return jsonify({"error": "Tool name not provided"}), 400

    server_name = None
    tool_name = name

    # Check if server name is specified (format: "server_name.tool_name")
    if "." in tool_name:
        server_name, tool_name = tool_name.split(".", 1)

        # Add permission server tool restriction
        if tool_name == "ask_for_permission" and server_name != PERMISSION_SERVER_NAME:
            return jsonify({"error": "Permission denied: unauthorized server"}), 403

        if server_name not in servers:
            return jsonify({"error": f"Server '{server_name}' not found"}), 404
        target_servers = [servers[server_name]]
    else:
        # If no server specified, search all servers for the tool
        if tool_name == "ask_for_permission":
            target_servers = [servers[PERMISSION_SERVER_NAME]]
        else:
            target_servers = [s for s in servers.values() if check_server_health(s)]

    # Try each potential server
    for server in target_servers:
        try:
            client = FastMCPHttpClient(f"{server.url}:{server.port}")
            # Check if the tool exists on this server
            available_tools = client.list_tools()
            print("AVAILABLE TOOLS", available_tools)
            if not any(t.name == tool_name for t in available_tools):
                continue

            # Found the tool, try to call it
            result = client.call_tool(
                tool_name, data
            )  # Use remaining data as arguments
            return jsonify([content.model_dump() for content in result])

        except requests.RequestException:
            # If this server fails, try the next one
            continue

    # If we get here, we didn't find the tool on any server
    error_msg = f"Tool '{tool_name}' not found"
    if server_name:
        error_msg += f" on server '{server_name}'"
    print("ERROR", error_msg)
    return jsonify({"error": error_msg}), 404


def load_permission_server():
    permission_server_url = "http://127.0.0.1"
    permission_port = _generate_port(permission_server_url)

    permission_server_instance = Server(
        name=PERMISSION_SERVER_NAME,
        description=permission_server.mcp.description,  # type: ignore
        url=permission_server_url,
        port=permission_port,
    )

    # Add to global servers dict
    servers[PERMISSION_SERVER_NAME] = permission_server_instance

    # Start permission server in a new thread with the assigned port
    permission_thread = Thread(
        target=lambda: permission_server.mcp.run_http(
            register_server=False, port=permission_port
        ),
        daemon=True,
    )
    permission_thread.start()
    time.sleep(1)


def run():
    # Register permission server first
    load_permission_server()

    # Load other servers on startup
    loaded_servers = load_servers()
    for server in loaded_servers.keys():
        if server != PERMISSION_SERVER_NAME:  # Don't override permission server
            servers[server] = loaded_servers[server]
            print("Loaded server:", server)

    save_servers()
    app.run(debug=False, port=31337)
