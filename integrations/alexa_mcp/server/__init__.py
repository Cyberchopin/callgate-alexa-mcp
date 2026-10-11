"""Streamable HTTP MCP server for simulated protected actions."""

from .app import CapabilityGateway, create_server, operation_resource
from .approval import ApprovalFlow, add_approval_routes

__all__ = ["ApprovalFlow", "CapabilityGateway", "add_approval_routes", "create_server",
           "operation_resource"]
