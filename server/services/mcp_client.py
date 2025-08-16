"""
MCP Client to connect FastAPI server with FastMCP Google Workspace tools via HTTP
"""
import asyncio
import logging
import httpx
import json
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class GoogleWorkspaceMCPClient:
    """
    MCP Client to interface with Google Workspace FastMCP server via HTTP
    This allows the FastAPI application to use MCP tools
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001"):
        self.server_url = mcp_server_url
        self.client: Optional[httpx.AsyncClient] = None
        self.connected = False
        self.available_tools = []
        
    async def connect_to_server(self):
        """Connect to the Google Workspace MCP server via HTTP"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection by checking health
            response = await self.client.get(f"{self.server_url}/health")
            if response.status_code == 200:
                self.connected = True
                logger.info(f"Connected to MCP server at {self.server_url}")
                
                # Try to get available tools (this might not be directly available via HTTP)
                # We'll define the known tools based on our server configuration
                self.available_tools = [
                    {"name": "gmail_send", "description": "Send an email via Gmail"},
                    {"name": "gmail_search", "description": "Search emails in Gmail"},
                    {"name": "calendar_search", "description": "Search calendar events"},
                    {"name": "calendar_create_event", "description": "Create a calendar event"},
                    {"name": "tasks_list", "description": "List tasks"},
                    {"name": "tasks_create", "description": "Create a new task"},
                ]
                
                logger.info(f"MCP server connected with tools: {[tool['name'] for tool in self.available_tools]}")
                return True
            else:
                logger.error(f"Failed to connect to MCP server: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.client:
            await self.client.aclose()
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server"""
        return self.available_tools if self.connected else []
    
    async def call_tool_via_auth(self, tool_name: str, arguments: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Call a Google Workspace tool through the FastMCP server via HTTP
        """
        if not self.connected or not self.client:
            raise Exception("Not connected to MCP server")
        
        try:
            logger.info(f"Calling FastMCP tool: {tool_name} with args: {arguments} for user: {user_email}")
            
            # FastMCP exposes tools at /tools/{tool_name}
            endpoint = f"{self.server_url}/tools/{tool_name}"
            
            # Prepare the request payload - FastMCP expects arguments plus any context
            payload = {
                **arguments,
                "user_google_email": user_email  # This is the parameter name the tools expect
            }
            
            logger.info(f"Calling endpoint: {endpoint} with payload: {payload}")
            
            response = await self.client.post(
                endpoint,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"✅ Successfully called {tool_name} via FastMCP")
                    return {
                        "success": True,
                        "tool_name": tool_name,
                        "result": result,
                        "arguments": arguments
                    }
                except Exception as json_error:
                    # Sometimes FastMCP returns plain text
                    result_text = response.text
                    logger.info(f"✅ FastMCP returned text response: {result_text[:200]}...")
                    return {
                        "success": True,
                        "tool_name": tool_name,
                        "result": result_text,
                        "arguments": arguments
                    }
            elif response.status_code == 404:
                logger.error(f"Tool {tool_name} not found on FastMCP server")
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": f"Tool '{tool_name}' not found on MCP server",
                    "arguments": arguments
                }
            elif response.status_code == 401:
                logger.error(f"Authentication required for tool {tool_name}")
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": f"Authentication required for {tool_name}. Please authenticate with Google first.",
                    "arguments": arguments,
                    "auth_required": True
                }
            else:
                error_text = response.text
                logger.error(f"Tool {tool_name} returned status {response.status_code}: {error_text}")
                return {
                    "success": False,
                    "tool_name": tool_name,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "arguments": arguments
                }
                
        except httpx.RequestError as e:
            logger.error(f"Request failed for {tool_name}: {e}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": f"Network error calling MCP server: {str(e)}",
                "arguments": arguments
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e),
                "arguments": arguments
            }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool with arguments - simplified version"""
        return await self.call_tool_via_auth(tool_name, arguments, "default_user")
    
    async def search_calendar_events(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """Search calendar events using MCP tools"""
        return await self.call_tool("calendar_search", {
            "query": query,
            "max_results": max_results
        })
    
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
        return await self.call_tool("gmail_search", {
            "query": query,
            "max_results": max_results
        })
    
    async def create_task(self, title: str, notes: str = "", due_date: str = None) -> Dict[str, Any]:
        """Create a task using MCP tools"""
        return await self.call_tool("tasks_create", {
            "title": title,
            "notes": notes,
            "due": due_date
        })
    
    async def list_tasks(self, task_list: str = "@default", max_results: int = 20) -> Dict[str, Any]:
        """List tasks using MCP tools"""
        return await self.call_tool("tasks_list", {
            "task_list": task_list,
            "max_results": max_results
        })

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
