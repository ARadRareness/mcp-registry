import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QScrollArea,
    QLabel,
    QToolBar,
    QLineEdit,
    QTextEdit,
    QCheckBox,
)

from mcp.types import Tool
from fastmcp_http.client import FastMCPHttpClient


class ServerTreeItem(QTreeWidgetItem):
    def __init__(self, name: str, is_server: bool = False):
        super().__init__([name])
        self.is_server = is_server
        self.server_name = name if is_server else None
        self.tool_name = None if is_server else name


class MCPExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCP Server Explorer")
        self.resize(1000, 600)

        self.client = FastMCPHttpClient("http://127.0.0.1:31337")

        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Add refresh button
        refresh_btn = QPushButton("Refresh Servers")
        refresh_btn.clicked.connect(self.refresh_servers)
        toolbar.addWidget(refresh_btn)

        # Create main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        # Create server tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Servers")
        self.tree.itemClicked.connect(self.on_item_selected)
        self.splitter.addWidget(self.tree)

        # Create info panel
        self.info_scroll = QScrollArea()
        self.info_scroll.setWidgetResizable(True)
        self.info_widget = QWidget()
        self.info_layout = QVBoxLayout(self.info_widget)
        self.info_scroll.setWidget(self.info_widget)
        self.splitter.addWidget(self.info_scroll)

        # Set initial splitter sizes
        self.splitter.setSizes([300, 700])

        # Load servers
        self.refresh_servers()

    def refresh_servers(self):
        self.tree.clear()

        try:
            with open("servers.json") as f:
                servers = json.load(f)

            available_servers = set(
                server.name for server in self.client.list_servers()
            )

            # Get the directory of the current script
            script_dir = Path(__file__).parent

            for server_name, server_info in servers.items():
                server_item = ServerTreeItem(server_name, is_server=True)
                self.tree.addTopLevelItem(server_item)

                # Check if server is online and set icon
                is_online = server_name in available_servers
                icon_path = script_dir / ("green.png" if is_online else "red.png")
                icon = QIcon(str(icon_path))
                # Set icon size to 12x12 pixels
                self.tree.setIconSize(QSize(10, 10))
                server_item.setIcon(0, icon)

                if is_online:
                    # Get tools for online server
                    tools = self.client.list_tools(server_name)
                    for tool in tools:
                        # Strip server name from tool name
                        display_name = tool.name.split(".")[-1]
                        tool_item = ServerTreeItem(display_name)
                        tool_item.full_tool_name = (
                            tool.name
                        )  # Store full name for reference
                        server_item.addChild(tool_item)

                    # Expand the server item
                    server_item.setExpanded(True)

        except Exception as e:
            print(f"Error loading servers: {e}")

    def get_server_tools(self, server_info) -> list[Tool]:
        return self.client.list_tools(server_info["name"])

    def on_item_selected(self, item: ServerTreeItem):
        # Clear previous info
        for i in reversed(range(self.info_layout.count())):
            layout_item = self.info_layout.itemAt(i)
            if layout_item.widget():  # Check if the item has a widget
                layout_item.widget().setParent(None)
            else:
                self.info_layout.removeItem(layout_item)

        if item.is_server:
            self.show_server_info(item.server_name)
        else:
            self.show_tool_info(item.parent().server_name, item.tool_name)

    def show_server_info(self, server_name: str):
        with open("servers.json") as f:
            servers = json.load(f)

        server = servers[server_name]

        # Display server information
        for label in [
            f"Server Name: {server['name']}",
            f"Description: {server['description']}",
            f"URL: {server['url']}:{server['port']}",
            "\nAvailable Tools:",
        ]:
            self.info_layout.addWidget(QLabel(label))

        # Get and display tool information
        tools = self.get_server_tools(server)
        for tool in tools:
            display_name = tool.name.split(".")[-1]
            self.info_layout.addWidget(QLabel(f"\n• {display_name}"))
            if tool.description:
                self.info_layout.addWidget(QLabel(f"  {tool.description}"))

        self.info_layout.addStretch()

    def show_tool_info(self, server_name: str, tool_name: str):
        # Get tool info
        tools = self.get_server_tools({"name": server_name})
        full_tool_name = f"{server_name}.{tool_name}"
        tool = next((t for t in tools if t.name == full_tool_name), None)

        if tool:
            # Display stripped tool name
            display_name = tool.name.split(".")[-1]
            self.info_layout.addWidget(QLabel(f"Tool Name: {display_name}"))
            self.info_layout.addWidget(QLabel(f"Description: {tool.description}"))

            # Add input fields section
            self.info_layout.addWidget(QLabel("\nInputs:"))
            input_widgets = {}
            for prop_name, prop_info in tool.inputSchema.get("properties", {}).items():
                # Create label and input field for each property
                field_label = QLabel(f"  {prop_info.get('title', prop_name)}:")
                self.info_layout.addWidget(field_label)

                if prop_info.get("type") == "boolean":
                    input_field = QCheckBox()
                    input_widgets[prop_name] = input_field
                else:  # default to text input
                    input_field = QLineEdit()
                    input_widgets[prop_name] = input_field
                self.info_layout.addWidget(input_field)

            # Add output section
            self.info_layout.addWidget(QLabel("\nOutput:"))
            output_field = QTextEdit()
            output_field.setReadOnly(True)
            output_field.setMinimumHeight(100)
            self.info_layout.addWidget(output_field)

            # Add invoke button
            invoke_btn = QPushButton("Invoke Tool")
            invoke_btn.clicked.connect(
                lambda: self.invoke_tool(server_name, tool, input_widgets, output_field)
            )
            self.info_layout.addWidget(invoke_btn)
            self.info_layout.addStretch()

    def invoke_tool(
        self, server_name: str, tool: Tool, input_widgets: dict, output_field: QTextEdit
    ):
        try:
            servers = self.client.list_servers()
            server_info = next((s for s in servers if s.name == server_name), None)
            if server_info is None:
                output_field.setText(f"Server {server_name} not found")
                return

            # Collect input values
            inputs = {}
            for name, widget in input_widgets.items():
                if isinstance(widget, QCheckBox):
                    inputs[name] = widget.isChecked()
                else:
                    inputs[name] = widget.text()

            # Call the tool
            output_field.setText("Invoking tool...")
            print(f"Invoking tool {tool.name} with inputs: {inputs}")
            result = self.client.call_tool(tool.name, inputs)

            # Display results
            output_text = ""
            for content in result:
                if hasattr(content, "text"):
                    output_text += content.text + "\n"
                else:
                    output_text += f"Received content of type: {type(content)}\n"

            output_field.setText(output_text)

        except Exception as e:
            output_field.setText(f"Error invoking tool: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MCPExplorer()
    window.show()
    sys.exit(app.exec())
