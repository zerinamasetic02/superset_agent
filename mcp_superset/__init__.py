"""Superset MCP server: tools to build and manage Apache Superset dashboards from Cursor."""

from mcp_superset.client import SupersetClient, SupersetAPIError
from mcp_superset.server import main

__all__ = ["SupersetClient", "SupersetAPIError", "main"]
