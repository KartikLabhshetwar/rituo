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
            # In internal mode, connect without authentication since auth is disabled
            internal_mode = os.getenv("MCP_INTERNAL_MODE", "true").lower() == "true"
            
            if internal_mode:
                logger.info("🔧 Connecting to MCP server in internal mode (no auth required)")
                self.client = Client(self.server_url)
            else:
                # For external mode, we'd need proper OAuth tokens
                logger.info("🔐 Connecting to MCP server in external mode (auth required)")
                # TODO: Implement proper OAuth token retrieval for external mode
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
                logger.info(f"✅ Connected to MCP server at {self.server_url}")
                logger.info(f"📋 Available MCP tools: {[tool['name'] for tool in self.available_tools]}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
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
                
                # Extract the actual content from CallToolResult
                if hasattr(result, 'content') and result.content:
                    # Handle list of content items
                    if isinstance(result.content, list) and len(result.content) > 0:
                        first_content = result.content[0]
                        if hasattr(first_content, 'text'):
                            result_text = first_content.text
                        else:
                            result_text = str(first_content)
                    else:
                        result_text = str(result.content)
                elif hasattr(result, 'text'):
                    result_text = result.text
                else:
                    result_text = str(result)
                
                return {
                    "success": True,
                    "tool_name": tool_name,
                    "result": result_text,
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
                                  description: str = "", attendees: List[str] = None, 
                                  user_email: str = "", timezone: str = None) -> Dict[str, Any]:
        """Create a calendar event using MCP tools"""
        arguments = {
            "summary": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "attendees": attendees or []
        }
        if timezone:
            arguments["timezone"] = timezone
        return await self.call_tool_via_auth("create_event", arguments, user_email)
    
    async def get_calendar_events(self, time_min: str = None, time_max: str = None, max_results: int = 10, calendar_id: str = "primary", user_email: str = "") -> Dict[str, Any]:
        """Get calendar events using MCP tools"""
        from datetime import datetime, timedelta
        
        # Default to tomorrow if no dates provided
        if not time_min:
            tomorrow = datetime.now() + timedelta(days=1)
            time_min = tomorrow.strftime("%Y-%m-%d")
        
        # Fix the date range issue - if time_max is the same as time_min, we need to extend it to the end of the day
        if not time_max:
            if time_min:
                # Parse time_min and add 1 day to get the full day
                if "T" in time_min:
                    start_dt = datetime.fromisoformat(time_min.replace('Z', ''))
                else:
                    start_dt = datetime.strptime(time_min, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=1)
                time_max = end_dt.strftime("%Y-%m-%d")
            else:
                time_max = time_min
        else:
            # If time_max is the same date as time_min (e.g., both "2025-08-21"), extend time_max to end of day
            if time_min and time_max == time_min and "T" not in time_max:
                # Both are date-only and the same - extend time_max to next day
                if "T" in time_min:
                    start_dt = datetime.fromisoformat(time_min.replace('Z', ''))
                else:
                    start_dt = datetime.strptime(time_min, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=1)
                time_max = end_dt.strftime("%Y-%m-%d")
        
        arguments = {
            "calendar_id": calendar_id,
            "time_min": time_min,
            "time_max": time_max,
            "max_results": max_results
        }
        return await self.call_tool_via_auth("get_events", arguments, user_email)
    
    async def list_calendars(self, user_email: str = "") -> Dict[str, Any]:
        """List available calendars using MCP tools"""
        arguments = {}
        return await self.call_tool_via_auth("list_calendars", arguments, user_email)
    
    async def get_calendar_event(self, event_id: str, calendar_id: str = "primary", user_email: str = "") -> Dict[str, Any]:
        """Get a specific calendar event using MCP tools"""
        arguments = {
            "event_id": event_id,
            "calendar_id": calendar_id
        }
        return await self.call_tool_via_auth("get_event", arguments, user_email)
    
    async def modify_calendar_event(self, event_id: str, calendar_id: str = "primary", 
                                  summary: str = None, start_time: str = None, end_time: str = None,
                                  description: str = None, attendees: List[str] = None, 
                                  timezone: str = None, user_email: str = "") -> Dict[str, Any]:
        """Modify a calendar event using MCP tools"""
        arguments = {
            "event_id": event_id,
            "calendar_id": calendar_id
        }
        if summary:
            arguments["summary"] = summary
        if start_time:
            arguments["start_time"] = start_time
        if end_time:
            arguments["end_time"] = end_time
        if description:
            arguments["description"] = description
        if attendees:
            arguments["attendees"] = attendees
        if timezone:
            arguments["timezone"] = timezone
            
        return await self.call_tool_via_auth("modify_event", arguments, user_email)
    
    async def delete_calendar_event(self, event_id: str, calendar_id: str = "primary", user_email: str = "") -> Dict[str, Any]:
        """Delete a calendar event using MCP tools"""
        arguments = {
            "event_id": event_id,
            "calendar_id": calendar_id
        }
        return await self.call_tool_via_auth("delete_event", arguments, user_email)
    
    async def send_email(self, to: str, subject: str, body: str, 
                        cc: str = None, bcc: str = None, user_email: str = "") -> Dict[str, Any]:
        """Send an email using MCP tools"""
        arguments = {
            "to": to,
            "subject": subject,
            "body": body
        }
        if cc:
            arguments["cc"] = cc
        if bcc:
            arguments["bcc"] = bcc
        return await self.call_tool_via_auth("send_gmail_message", arguments, user_email)
    
    async def search_emails(self, query: str, max_results: int = 10, user_email: str = "") -> Dict[str, Any]:
        """Search emails using MCP tools"""
        arguments = {
            "query": query,
            "page_size": max_results
        }
        return await self.call_tool_via_auth("search_gmail_messages", arguments, user_email)
    
    async def get_default_task_list(self, user_email: str = "") -> Dict[str, Any]:
        """Get the user's default task list"""
        return await self.call_tool_via_auth("list_task_lists", {"max_results": 1}, user_email)
    
    async def create_task(self, title: str, notes: str = "", due_date: str = None, task_list_id: str = None, user_email: str = "") -> Dict[str, Any]:
        """Create a task using MCP tools"""
        # If no task_list_id provided, get the default one
        if not task_list_id:
            try:
                task_lists_result = await self.get_default_task_list(user_email)
                if task_lists_result.get("success") and "result" in task_lists_result:
                    # Parse the result to extract the first task list ID
                    result_text = task_lists_result["result"]
                    # Look for ID pattern in the result
                    import re
                    id_match = re.search(r"ID:\s*([\w-]+)", result_text)
                    if id_match:
                        task_list_id = id_match.group(1)
                    else:
                        # Fallback to @default
                        task_list_id = "@default"
                else:
                    task_list_id = "@default"
            except Exception as e:
                logger.warning(f"Failed to get default task list, using @default: {e}")
                task_list_id = "@default"
        
        arguments = {
            "task_list_id": task_list_id,
            "title": title,
            "notes": notes,
            "due": due_date
        }
        return await self.call_tool_via_auth("create_task", arguments, user_email)
    
    async def list_tasks(self, task_list_id: str = None, max_results: int = 20, user_email: str = "") -> Dict[str, Any]:
        """List tasks using MCP tools"""
        # If no task_list_id provided, get the default one
        if not task_list_id:
            try:
                task_lists_result = await self.get_default_task_list(user_email)
                if task_lists_result.get("success") and "result" in task_lists_result:
                    import re
                    id_match = re.search(r"ID:\s*([\w-]+)", task_lists_result["result"])
                    if id_match:
                        task_list_id = id_match.group(1)
                    else:
                        task_list_id = "@default"
                else:
                    task_list_id = "@default"
            except Exception as e:
                logger.warning(f"Failed to get default task list, using @default: {e}")
                task_list_id = "@default"
        
        arguments = {
            "task_list_id": task_list_id,
            "max_results": max_results
        }
        return await self.call_tool_via_auth("list_tasks", arguments, user_email)
    
    async def list_task_lists(self, max_results: int = 10, user_email: str = "") -> Dict[str, Any]:
        """List all task lists using MCP tools"""
        arguments = {"max_results": max_results}
        return await self.call_tool_via_auth("list_task_lists", arguments, user_email)
    
    async def get_task_list(self, task_list_id: str, user_email: str = "") -> Dict[str, Any]:
        """Get a specific task list using MCP tools"""
        arguments = {"task_list_id": task_list_id}
        return await self.call_tool_via_auth("get_task_list", arguments, user_email)
    
    async def create_task_list(self, title: str, user_email: str = "") -> Dict[str, Any]:
        """Create a new task list using MCP tools"""
        arguments = {"title": title}
        return await self.call_tool_via_auth("create_task_list", arguments, user_email)
    
    async def update_task_list(self, task_list_id: str, title: str, user_email: str = "") -> Dict[str, Any]:
        """Update a task list using MCP tools"""
        arguments = {
            "task_list_id": task_list_id,
            "title": title
        }
        return await self.call_tool_via_auth("update_task_list", arguments, user_email)
    
    async def delete_task_list(self, task_list_id: str, user_email: str = "") -> Dict[str, Any]:
        """Delete a task list using MCP tools"""
        arguments = {"task_list_id": task_list_id}
        return await self.call_tool_via_auth("delete_task_list", arguments, user_email)
    
    async def get_task(self, task_list_id: str, task_id: str, user_email: str = "") -> Dict[str, Any]:
        """Get a specific task using MCP tools"""
        arguments = {
            "task_list_id": task_list_id,
            "task_id": task_id
        }
        return await self.call_tool_via_auth("get_task", arguments, user_email)
    
    async def update_task(self, task_list_id: str, task_id: str, title: str = None, 
                         notes: str = None, status: str = None, due: str = None, 
                         user_email: str = "") -> Dict[str, Any]:
        """Update a task using MCP tools"""
        arguments = {
            "task_list_id": task_list_id,
            "task_id": task_id
        }
        if title:
            arguments["title"] = title
        if notes:
            arguments["notes"] = notes
        if status:
            arguments["status"] = status
        if due:
            arguments["due"] = due
            
        return await self.call_tool_via_auth("update_task", arguments, user_email)
    
    async def delete_task(self, task_list_id: str, task_id: str, user_email: str = "") -> Dict[str, Any]:
        """Delete a task using MCP tools"""
        arguments = {
            "task_list_id": task_list_id,
            "task_id": task_id
        }
        return await self.call_tool_via_auth("delete_task", arguments, user_email)
    
    async def move_task(self, task_list_id: str, task_id: str, parent: str = None, 
                       previous: str = None, user_email: str = "") -> Dict[str, Any]:
        """Move a task to a different position using MCP tools"""
        arguments = {
            "task_list_id": task_list_id,
            "task_id": task_id
        }
        if parent:
            arguments["parent"] = parent
        if previous:
            arguments["previous"] = previous
            
        return await self.call_tool_via_auth("move_task", arguments, user_email)
    
    async def clear_completed_tasks(self, task_list_id: str, user_email: str = "") -> Dict[str, Any]:
        """Clear completed tasks from a task list using MCP tools"""
        arguments = {"task_list_id": task_list_id}
        return await self.call_tool_via_auth("clear_completed_tasks", arguments, user_email)
    
    async def debug_user_scopes(self, user_email: str = "") -> Dict[str, Any]:
        """Debug function to check what scopes the user actually has"""
        try:
            # This will help us see what's wrong with Gmail permissions
            result = await self.call_tool_via_auth("start_google_auth", {
                "user_email": user_email,
                "service_name": "gmail"
            }, user_email)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Debug failed: {str(e)}"
            }
    
    # Gmail Methods
    async def search_gmail_messages(self, query: str, page_size: int = 10, user_email: str = "") -> Dict[str, Any]:
        """Search Gmail messages using MCP tools"""
        arguments = {
            "query": query,
            "page_size": page_size
        }
        return await self.call_tool_via_auth("search_gmail_messages", arguments, user_email)
    
    async def get_gmail_message_content(self, message_id: str, user_email: str = "") -> Dict[str, Any]:
        """Get Gmail message content using MCP tools"""
        arguments = {
            "message_id": message_id
        }
        return await self.call_tool_via_auth("get_gmail_message_content", arguments, user_email)
    
    async def get_gmail_messages_content_batch(self, message_ids: List[str], format: str = "full", user_email: str = "") -> Dict[str, Any]:
        """Get batch Gmail messages content using MCP tools"""
        arguments = {
            "message_ids": message_ids,
            "format": format
        }
        return await self.call_tool_via_auth("get_gmail_messages_content_batch", arguments, user_email)
    
    async def send_gmail_message(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None, 
                                thread_id: str = None, in_reply_to: str = None, references: str = None, 
                                user_email: str = "") -> Dict[str, Any]:
        """Send Gmail message using MCP tools"""
        arguments = {
            "to": to,
            "subject": subject,
            "body": body
        }
        if cc:
            arguments["cc"] = cc
        if bcc:
            arguments["bcc"] = bcc
        if thread_id:
            arguments["thread_id"] = thread_id
        if in_reply_to:
            arguments["in_reply_to"] = in_reply_to
        if references:
            arguments["references"] = references
            
        return await self.call_tool_via_auth("send_gmail_message", arguments, user_email)
    
    async def draft_gmail_message(self, subject: str, body: str, to: str = None, cc: str = None, bcc: str = None,
                                 thread_id: str = None, in_reply_to: str = None, references: str = None,
                                 user_email: str = "") -> Dict[str, Any]:
        """Create Gmail draft using MCP tools"""
        arguments = {
            "subject": subject,
            "body": body
        }
        if to:
            arguments["to"] = to
        if cc:
            arguments["cc"] = cc
        if bcc:
            arguments["bcc"] = bcc
        if thread_id:
            arguments["thread_id"] = thread_id
        if in_reply_to:
            arguments["in_reply_to"] = in_reply_to
        if references:
            arguments["references"] = references
            
        return await self.call_tool_via_auth("draft_gmail_message", arguments, user_email)
    
    async def get_gmail_thread_content(self, thread_id: str, user_email: str = "") -> Dict[str, Any]:
        """Get Gmail thread content using MCP tools"""
        arguments = {
            "thread_id": thread_id
        }
        return await self.call_tool_via_auth("get_gmail_thread_content", arguments, user_email)
    
    async def get_gmail_threads_content_batch(self, thread_ids: List[str], format: str = "full", user_email: str = "") -> Dict[str, Any]:
        """Get multiple Gmail threads content using MCP tools"""
        arguments = {
            "thread_ids": thread_ids,
            "format": format
        }
        return await self.call_tool_via_auth("get_gmail_threads_content_batch", arguments, user_email)
    
    async def list_gmail_labels(self, user_email: str = "") -> Dict[str, Any]:
        """List Gmail labels using MCP tools"""
        arguments = {}
        return await self.call_tool_via_auth("list_gmail_labels", arguments, user_email)
    
    async def manage_gmail_label(self, action: str, name: str = None, label_id: str = None, 
                                label_list_visibility: str = "labelShow", message_list_visibility: str = "show",
                                user_email: str = "") -> Dict[str, Any]:
        """Manage Gmail labels using MCP tools"""
        arguments = {
            "action": action,
            "label_list_visibility": label_list_visibility,
            "message_list_visibility": message_list_visibility
        }
        if name:
            arguments["name"] = name
        if label_id:
            arguments["label_id"] = label_id
            
        return await self.call_tool_via_auth("manage_gmail_label", arguments, user_email)
    
    async def modify_gmail_message_labels(self, message_id: str, add_label_ids: List[str] = None, 
                                         remove_label_ids: List[str] = None, user_email: str = "") -> Dict[str, Any]:
        """Modify Gmail message labels using MCP tools"""
        arguments = {
            "message_id": message_id
        }
        if add_label_ids:
            arguments["add_label_ids"] = add_label_ids
        if remove_label_ids:
            arguments["remove_label_ids"] = remove_label_ids
            
        return await self.call_tool_via_auth("modify_gmail_message_labels", arguments, user_email)
    
    async def batch_modify_gmail_message_labels(self, message_ids: List[str], add_label_ids: List[str] = None, 
                                              remove_label_ids: List[str] = None, user_email: str = "") -> Dict[str, Any]:
        """Batch modify Gmail message labels using MCP tools"""
        arguments = {
            "message_ids": message_ids
        }
        if add_label_ids:
            arguments["add_label_ids"] = add_label_ids
        if remove_label_ids:
            arguments["remove_label_ids"] = remove_label_ids
            
        return await self.call_tool_via_auth("batch_modify_gmail_message_labels", arguments, user_email)

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
