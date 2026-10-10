"""Streamable HTTP MCP server for simulated protected actions."""

from .app import CapabilityGateway, create_server, operation_resource

__all__ = ["CapabilityGateway", "create_server", "operation_resource"]
