"""
AI Service for Groq + LangChain integration with MCP tools
"""
import logging
import os
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from database.models import User
from services.mcp_client import mcp_client

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is required")
        
        # Initialize Groq model
        try:
            from groq import Groq
            self.client = Groq(api_key=self.groq_api_key)
            self.model_name = "llama-3.1-8b-instant"  # Using a reliable Groq model
            logger.info("Successfully initialized Groq client")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise
    
    def create_system_prompt(self, user: User) -> str:
        """Create system prompt for the AI assistant"""
        return f"""You are a helpful AI assistant named Rituo that can help users manage their Google Workspace tools.

You have access to the following capabilities:
- Google Calendar: Schedule, modify, and manage calendar events
- Gmail: Send emails, read messages, manage labels
- Google Tasks: Create and manage task lists and tasks

User Information:
- Name: {user.name}
- Email: {user.email}

When users ask for help with scheduling, email management, or task organization, you can use the appropriate MCP tools to help them.

Instructions:
1. Be helpful and conversational
2. When users request calendar, email, or task actions, explain what you're doing
3. If you need to use MCP tools, describe the action you're taking
4. Always be clear about what you can and cannot do
5. If something requires Google authentication, guide them through the process

Current conversation context will be provided with each message."""

    async def process_message(
        self, 
        user_message: str, 
        user: User,
        chat_history: List[Dict[str, Any]] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Process a user message and return AI response
        """
        try:
            # Create system prompt
            system_prompt = self.create_system_prompt(user)
            
            # Prepare messages for the model
            messages = [SystemMessage(content=system_prompt)]
            
            # Add chat history if provided (limit to last 10 messages for context)
            if chat_history:
                for message in chat_history[-10:]:
                    if message.get("role") == "user":
                        messages.append(HumanMessage(content=message.get("content", "")))
                    elif message.get("role") == "assistant":
                        messages.append(AIMessage(content=message.get("content", "")))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Get response from Groq
            response = await self._get_ai_response(messages)
            
            # Check if the response indicates need for MCP tools
            enhanced_response = await self._process_with_mcp_tools(
                response, user_message, user, context or {}
            )
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error while processing your message. Please try again."
    
    async def _get_ai_response(self, messages: List[Any]) -> str:
        """Get response from Groq model"""
        try:
            # Convert messages to Groq format
            groq_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    groq_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    groq_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    groq_messages.append({"role": "assistant", "content": msg.content})
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=groq_messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise
    
    async def _process_with_mcp_tools(
        self, 
        ai_response: str, 
        user_message: str, 
        user: User,
        context: Dict[str, Any]
    ) -> str:
        """
        Process AI response and determine if MCP tools should be used
        This is where we'll integrate with your existing MCP tools
        """
        try:
            user_message_lower = user_message.lower()
            
            # Check for execution triggers
            execution_triggers = [
                "yes", "do it", "go ahead", "proceed", "run", "execute", 
                "mcp server", "google calendar", "add the event", "create the event",
                "schedule it", "make it happen"
            ]
            
            is_execution_request = any(trigger in user_message_lower for trigger in execution_triggers)
            
            # Calendar-related keywords
            calendar_keywords = [
                "schedule", "meeting", "appointment", "calendar", "event", 
                "book", "reserve", "plan", "arrange", "tomorrow", "today", "time"
            ]
            
            # Gmail-related keywords
            email_keywords = [
                "email", "mail", "send", "message", "compose", "reply", "inbox"
            ]
            
            # Tasks-related keywords
            task_keywords = [
                "task", "todo", "reminder", "list", "complete", "finish"
            ]
            
            # If this is an execution request and we detect intent, actually call MCP tools
            if is_execution_request:
                
                # Calendar execution
                if any(keyword in user_message_lower for keyword in calendar_keywords):
                    logger.info("Executing calendar action via MCP server")
                    result = await self._execute_calendar_action(user_message, user, context)
                    if result.get("success"):
                        return f"✅ **Calendar Event Created Successfully!**\n\n{result.get('message', 'Event has been added to your Google Calendar.')}\n\n{ai_response}"
                    else:
                        return f"❌ **Calendar Action Failed:**\n{result.get('error', 'Unknown error occurred')}\n\n{ai_response}"
                
                # Email execution  
                elif any(keyword in user_message_lower for keyword in email_keywords):
                    logger.info("Executing email action via MCP server")
                    result = await self._execute_email_action(user_message, user, context)
                    if result.get("success"):
                        return f"✅ **Email Action Completed!**\n\n{result.get('message', 'Email action completed successfully.')}\n\n{ai_response}"
                    else:
                        return f"❌ **Email Action Failed:**\n{result.get('error', 'Unknown error occurred')}\n\n{ai_response}"
                
                # Task execution
                elif any(keyword in user_message_lower for keyword in task_keywords):
                    logger.info("Executing task action via MCP server")
                    result = await self._execute_task_action(user_message, user, context)
                    if result.get("success"):
                        return f"✅ **Task Action Completed!**\n\n{result.get('message', 'Task action completed successfully.')}\n\n{ai_response}"
                    else:
                        return f"❌ **Task Action Failed:**\n{result.get('error', 'Unknown error occurred')}\n\n{ai_response}"

            mcp_actions = []
            
            # Check for calendar actions
            if any(keyword in user_message_lower for keyword in calendar_keywords):
                mcp_actions.append(self._suggest_calendar_action(user_message, user))
            
            # Check for email actions
            if any(keyword in user_message_lower for keyword in email_keywords):
                mcp_actions.append(self._suggest_email_action(user_message, user))
            
            # Check for task actions
            if any(keyword in user_message_lower for keyword in task_keywords):
                mcp_actions.append(self._suggest_task_action(user_message, user))
            
            # If MCP actions are suggested, append them to the response
            if mcp_actions:
                action_text = "\n\n🔧 **Available Actions:**\n" + "\n".join(filter(None, mcp_actions))
                return ai_response + action_text
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing MCP tools: {e}")
            return ai_response  # Return original response if MCP processing fails
    
    def _suggest_calendar_action(self, user_message: str, user: User) -> Optional[str]:
        """Suggest calendar-related MCP actions"""
        if "schedule" in user_message.lower() or "meeting" in user_message.lower():
            return "📅 I can help you schedule this meeting. Would you like me to create a calendar event?"
        elif "check" in user_message.lower() or "what" in user_message.lower():
            return "📅 I can check your calendar for you. Let me search for your upcoming events."
        return "📅 I can help you with calendar management through Google Calendar."
    
    def _suggest_email_action(self, user_message: str, user: User) -> Optional[str]:
        """Suggest email-related MCP actions"""
        if "send" in user_message.lower():
            return "📧 I can help you send that email. Would you like me to compose it for you?"
        elif "check" in user_message.lower() or "inbox" in user_message.lower():
            return "📧 I can check your email inbox for you. Let me search for relevant messages."
        return "📧 I can help you with email management through Gmail."
    
    def _suggest_task_action(self, user_message: str, user: User) -> Optional[str]:
        """Suggest task-related MCP actions"""
        if "create" in user_message.lower() or "add" in user_message.lower():
            return "✅ I can create that task for you in Google Tasks. Would you like me to add it?"
        elif "list" in user_message.lower() or "show" in user_message.lower():
            return "✅ I can show you your current tasks. Let me fetch your task list."
        return "✅ I can help you manage tasks through Google Tasks."

    async def _execute_calendar_action(self, user_message: str, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calendar actions via MCP server"""
        try:
            # Simple parsing for calendar events - can be enhanced with NLP
            from datetime import datetime, timedelta
            import re
            
            # Parse meeting details from user message
            title = "New Meeting"
            start_time = None
            attendees = []
            
            # Extract title (meeting with X, X meeting, etc.)
            meeting_match = re.search(r'meeting with (.+?)(?:\s|$|at|tomorrow|today)', user_message.lower())
            if meeting_match:
                title = f"Meeting with {meeting_match.group(1).title()}"
                attendees = [meeting_match.group(1).lower()]
            
            # Extract time info
            tomorrow_match = re.search(r'tomorrow.*?(\d{1,2}(?::\d{2})?\s*(?:am|pm))', user_message.lower())
            today_match = re.search(r'today.*?(\d{1,2}(?::\d{2})?\s*(?:am|pm))', user_message.lower())
            
            if tomorrow_match:
                time_str = tomorrow_match.group(1)
                # Parse time and set for tomorrow
                tomorrow = datetime.now() + timedelta(days=1)
                # Simple time parsing - enhance as needed
                if '2 pm' in time_str.lower() or '2pm' in time_str.lower():
                    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            elif today_match:
                time_str = today_match.group(1)
                today = datetime.now()
                if '2 pm' in time_str.lower() or '2pm' in time_str.lower():
                    start_time = today.replace(hour=14, minute=0, second=0, microsecond=0)
            
            if not start_time:
                # Default to tomorrow 2 PM if no specific time found
                tomorrow = datetime.now() + timedelta(days=1)
                start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            
            end_time = start_time + timedelta(hours=1)  # Default 1-hour meeting
            
            # Call MCP server to create calendar event
            result = await self.execute_mcp_action(
                "calendar_create",
                {
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "description": f"Meeting scheduled via AI assistant",
                    "attendees": attendees,
                    "location": ""
                },
                user
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"📅 **Event Created:** {title}\n⏰ **Time:** {start_time.strftime('%Y-%m-%d at %I:%M %p')}\n👥 **Attendees:** {', '.join(attendees) if attendees else 'None'}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error executing calendar action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_email_action(self, user_message: str, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email actions via MCP server"""
        try:
            # Simple email parsing - enhance as needed
            if "send" in user_message.lower():
                return await self.execute_mcp_action(
                    "email_send",
                    {
                        "to": "",  # Would need better parsing
                        "subject": "Email via AI Assistant",
                        "body": "This email was sent via the AI assistant.",
                        "cc": "",
                        "bcc": ""
                    },
                    user
                )
            elif "search" in user_message.lower() or "check" in user_message.lower():
                return await self.execute_mcp_action(
                    "email_search", 
                    {
                        "query": "is:unread",
                        "max_results": 10
                    },
                    user
                )
            else:
                return {"success": False, "error": "Email action not recognized"}
                
        except Exception as e:
            logger.error(f"Error executing email action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_task_action(self, user_message: str, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task actions via MCP server"""
        try:
            logger.info(f"_execute_task_action called with message: {user_message}")
            if "create" in user_message.lower() or "add" in user_message.lower():
                # Parse task title from message - extract actual title
                title = self._extract_task_title(user_message)
                logger.info(f"Parsed task title: {title}")
                # Simple parsing - can be enhanced
                result = await self.execute_mcp_action(
                    "task_create",
                    {
                        "task_list_id": "@default",
                        "title": title,
                        "notes": "Created via AI assistant",
                        "due_date": None
                    },
                    user
                )
                logger.info(f"MCP action result: {result}")
                return result
            elif "list" in user_message.lower() or "show" in user_message.lower():
                return await self.execute_mcp_action(
                    "task_list",
                    {
                        "task_list_id": "@default",
                        "max_results": 10
                    },
                    user
                )
            else:
                return {"success": False, "error": "Task action not recognized"}
                
        except Exception as e:
            logger.error(f"Error executing task action: {e}")
            return {"success": False, "error": str(e)}

    def _extract_task_title(self, user_message: str) -> str:
        """Extract task title from user message"""
        import re
        
        # Look for patterns like "create a task to X" or "add task X"  
        patterns = [
            r'(?:create|add).*?task.*?to\s+(.*?)(?:\s|$)',
            r'(?:create|add).*?task.*?:\s+(.*?)(?:\s|$)',
            r'(?:create|add).*?task\s+(.*?)(?:\s|$)',
            r'task.*?to\s+(.*?)(?:\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                title = match.group(1).strip()
                # Capitalize first letter
                return title.capitalize()
        
        # Fallback to extracting everything after common task creation words
        fallback_patterns = [
            r'(?:create|add|make).*?(?:task|todo|reminder).*?(?:for|to|about)\s+(.*)',
            r'(?:task|todo|reminder).*?(?:for|to|about)\s+(.*)'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                title = match.group(1).strip()
                return title.capitalize()
        
        # Final fallback
        return "New Task via AI Assistant"

    async def execute_mcp_action(self, action_type: str, params: Dict[str, Any], user: User) -> Dict[str, Any]:
        """
        Execute MCP tool actions based on user requests
        """
        try:
            logger.info(f"execute_mcp_action called: action_type={action_type}, params={params}, user_email={user.email}")
            
            if not mcp_client.connected:
                logger.error("MCP client not connected")
                return {
                    "success": False,
                    "error": "MCP client not connected. Please ensure the Google Workspace server is running."
                }
            
            logger.info("MCP client is connected, proceeding with action")
            
            # Use the authenticated user's email for all MCP calls
            user_email = user.email
            
            if action_type == "calendar_search":
                return await mcp_client.call_tool_via_auth(
                    "calendar_search",
                    {
                        "query": params.get("query", ""),
                        "max_results": params.get("max_results", 10),
                        "time_min": params.get("time_min"),
                        "time_max": params.get("time_max")
                    },
                    user_email
                )
            
            elif action_type == "calendar_create":
                return await mcp_client.call_tool_via_auth(
                    "calendar_create_event",
                    {
                        "summary": params.get("title", ""),
                        "start_time": params.get("start_time", ""),
                        "end_time": params.get("end_time", ""),
                        "description": params.get("description", ""),
                        "attendees": params.get("attendees", []),
                        "location": params.get("location", "")
                    },
                    user_email
                )
            
            elif action_type == "email_send":
                return await mcp_client.call_tool_via_auth(
                    "gmail_send",
                    {
                        "to": params.get("to", ""),
                        "subject": params.get("subject", ""),
                        "body": params.get("body", ""),
                        "cc": params.get("cc", ""),
                        "bcc": params.get("bcc", "")
                    },
                    user_email
                )
            
            elif action_type == "email_search":
                return await mcp_client.call_tool_via_auth(
                    "gmail_search",
                    {
                        "query": params.get("query", ""),
                        "page_size": params.get("max_results", 10)
                    },
                    user_email
                )
            
            elif action_type == "task_create":
                logger.info(f"Calling MCP client for task_create with params: {params}")
                result = await mcp_client.call_tool_via_auth(
                    "tasks_create",
                    {
                        "task_list_id": params.get("task_list_id", "@default"),
                        "title": params.get("title", ""),
                        "notes": params.get("notes", ""),
                        "due": params.get("due_date")
                    },
                    user_email
                )
                logger.info(f"MCP client returned result: {result}")
                return result
            
            elif action_type == "task_list":
                return await mcp_client.call_tool_via_auth(
                    "tasks_list",
                    {
                        "task_list_id": params.get("task_list_id", "@default"),
                        "max_results": params.get("max_results", 20)
                    },
                    user_email
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            logger.error(f"Error executing MCP action {action_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global AI service instance
ai_service = AIService()
