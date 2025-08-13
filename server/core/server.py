"""
Core server instance for MCP tools

This module provides the central server instance that all tool modules
can import and register their tools with.
"""

# Import the server instance from the main server module
from server import server

# Export the server instance
__all__ = ['server']
