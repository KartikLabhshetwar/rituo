"""
MCP Client to connect FastAPI server with FastMCP Google Workspace tools
Uses proper FastMCP Client for MCP protocol communication
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

logger = logging.getLogger(__name__)

class GoogleWorkspaceMCPClient:
    """
    Proper MCP Client to interface with Google Workspace FastMCP server
    Uses FastMCP Client for protocol-compliant communication
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001/mcp"):
        self.server_url = mcp_server_url
        self.client: Optional[Client] = None
        self.connected = False
        self.available_tools = []
        
    async def connect_to_server(self):
        """Connect to the Google Workspace MCP server using proper MCP protocol"""
        try:
            # Create FastMCP client - no auth needed as we'll handle auth per-request
            self.client = Client(self.server_url)
            
            # Test connection with ping
            async with self.client:
                await self.client.ping()
                
                # Get available tools from the MCP server
                tools = await self.client.list_tools()
                self.available_tools = [
                    {"name": tool.name, "description": tool.description or ""}
                    for tool in tools
                ]
                
                self.connected = True
                logger.info(f"Connected to MCP server at {self.server_url}")
                logger.info(f"Available MCP tools: {[tool['name'] for tool in self.available_tools]}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server"""
        return self.available_tools if self.connected else []
    
    async def call_tool_via_auth(self, tool_name: str, arguments: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Call a Google Workspace tool through the FastMCP server using proper MCP protocol
        """
        if not self.connected or not self.client:
            raise Exception("Not connected to MCP server")
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments} for user: {user_email}")
            
            # Add user email to arguments as expected by MCP tools
            tool_arguments = {
                **arguments,
                "user_google_email": user_email
            }
            
            # Use proper MCP client to call tool
            async with self.client:
                result = await self.client.call_tool(tool_name, tool_arguments)
                
                logger.info(f"✅ Successfully called {tool_name} via MCP protocol")
                return {
                    "success": True,
                    "tool_name": tool_name,
                    "result": result,
                    "arguments": arguments
                }
                
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            
            # Handle specific error types
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": f"Authentication required for {tool_name}. Please ensure Google OAuth is configured.",
                    "arguments": arguments,
                    "auth_required": True
                }
            elif "not found" in str(e).lower():
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": f"Tool '{tool_name}' not found on MCP server",
                    "arguments": arguments
                }
            else:
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": str(e),
                    "arguments": arguments
                }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool with arguments - simplified version"""
        return await self.call_tool_via_auth(tool_name, arguments, "default_user")
    
    async def search_calendar_events(self, query: str = "", max_results: int = 10, user_email: str = "") -> Dict[str, Any]:
        """Search calendar events using MCP tools"""
        return await self.call_tool_via_auth("search_events", {
            "query": query,
            "max_results": max_results
        }, user_email)
    
    async def create_calendar_event(self, title: str, start_time: str, end_time: str, 
                                  description: str = "", attendees: List[str] = None, user_email: str = "") -> Dict[str, Any]:
        """Create a calendar event using MCP tools"""
        arguments = {
            "summary": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "attendees": attendees or []
        }
        return await self.call_tool_via_auth("create_event", arguments, user_email)
    
    async def send_email(self, to: List[str], subject: str, body: str, 
                        cc: List[str] = None, bcc: List[str] = None, user_email: str = "") -> Dict[str, Any]:
        """Send an email using MCP tools"""
        arguments = {
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc or [],
            "bcc": bcc or []
        }
        return await self.call_tool_via_auth("send_gmail_message", arguments, user_email)
    
    async def search_emails(self, query: str, max_results: int = 10, user_email: str = "") -> Dict[str, Any]:
        """Search emails using MCP tools"""
        arguments = {
            "query": query,
            "page_size": max_results
        }
        return await self.call_tool_via_auth("search_gmail_messages", arguments, user_email)
    
    async def create_task(self, title: str, notes: str = "", due_date: str = None, user_email: str = "") -> Dict[str, Any]:
        """Create a task using MCP tools"""
        arguments = {
            "title": title,
            "notes": notes,
            "due": due_date
        }
        return await self.call_tool_via_auth("create_task", arguments, user_email)
    
    async def list_tasks(self, task_list: str = "@default", max_results: int = 20, user_email: str = "") -> Dict[str, Any]:
        """List tasks using MCP tools"""
        arguments = {
            "task_list": task_list,
            "max_results": max_results
        }
        return await self.call_tool_via_auth("list_tasks", arguments, user_email)

# Global MCP client instance
mcp_client = GoogleWorkspaceMCPClient()

async def initialize_mcp_client():
    """Initialize the global MCP client"""
    try:
        success = await mcp_client.connect_to_server()
        if success:
            logger.info("MCP client initialized successfully")
        else:
            logger.warning("MCP client initialization failed - MCP tools will use simulated responses")
        return success
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return False

async def cleanup_mcp_client():
    """Cleanup the global MCP client"""
    try:
        await mcp_client.disconnect()
        logger.info("MCP client cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up MCP client: {e}")
