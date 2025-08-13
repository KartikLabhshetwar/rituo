"""
AI Service for Groq + LangChain integration with MCP tools
"""
import logging
import os
from typing import Dict, Any, Optional, List
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool
from database.models import User
from mcp_client import mcp_client

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is required")
        
        # Initialize Groq model via LangChain
        try:
            self.model = init_chat_model(
                model="qwen/qwen3-32b",
                model_provider="groq",
                api_key=self.groq_api_key
            )
            logger.info("Successfully initialized Groq model")
        except Exception as e:
            logger.error(f"Failed to initialize Groq model: {e}")
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
            # For now, use synchronous call - can be made async later
            response = self.model.invoke(messages)
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
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
            # Simple keyword detection for now - can be enhanced with more sophisticated intent recognition
            user_message_lower = user_message.lower()
            
            # Calendar-related keywords
            calendar_keywords = [
                "schedule", "meeting", "appointment", "calendar", "event", 
                "book", "reserve", "plan", "arrange"
            ]
            
            # Gmail-related keywords
            email_keywords = [
                "email", "mail", "send", "message", "compose", "reply", "inbox"
            ]
            
            # Tasks-related keywords
            task_keywords = [
                "task", "todo", "reminder", "list", "complete", "finish"
            ]
            
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

    async def execute_mcp_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tool actions based on user requests
        """
        try:
            if not mcp_client.connected:
                return {
                    "success": False,
                    "error": "MCP client not connected. Please ensure the Google Workspace server is running."
                }
            
            if action_type == "calendar_search":
                return await mcp_client.search_calendar_events(
                    query=params.get("query", ""),
                    max_results=params.get("max_results", 10)
                )
            
            elif action_type == "calendar_create":
                return await mcp_client.create_calendar_event(
                    title=params.get("title", ""),
                    start_time=params.get("start_time", ""),
                    end_time=params.get("end_time", ""),
                    description=params.get("description", ""),
                    attendees=params.get("attendees", [])
                )
            
            elif action_type == "email_send":
                return await mcp_client.send_email(
                    to=params.get("to", []),
                    subject=params.get("subject", ""),
                    body=params.get("body", ""),
                    cc=params.get("cc", []),
                    bcc=params.get("bcc", [])
                )
            
            elif action_type == "email_search":
                return await mcp_client.search_emails(
                    query=params.get("query", ""),
                    max_results=params.get("max_results", 10)
                )
            
            elif action_type == "task_create":
                return await mcp_client.create_task(
                    title=params.get("title", ""),
                    notes=params.get("notes", ""),
                    due_date=params.get("due_date")
                )
            
            elif action_type == "task_list":
                return await mcp_client.list_tasks(
                    task_list=params.get("task_list", "@default"),
                    max_results=params.get("max_results", 20)
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
