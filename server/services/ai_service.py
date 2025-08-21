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
        Uses intelligent intent detection to automatically execute actions
        """
        try:
            user_message_lower = user_message.lower()
            
            # Detect intent and automatically execute appropriate MCP tools
            intent_result = await self._detect_and_execute_intent(user_message, user, context)
            
            if intent_result:
                if intent_result.get("success"):
                    return f"✅ **Action Completed Successfully!**\n\n{intent_result.get('message', 'Action completed.')}\n\n{ai_response}"
                else:
                    return f"❌ **Action Failed:**\n{intent_result.get('error', 'Unknown error occurred')}\n\n{ai_response}"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing MCP tools: {e}")
            return ai_response
    
    async def _detect_and_execute_intent(self, user_message: str, user: User, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect user intent and automatically execute appropriate MCP tools
        """
        import re
        from datetime import datetime, timedelta
        
        user_message_lower = user_message.lower()
        
        # Calendar intent detection
        if any(keyword in user_message_lower for keyword in ["schedule", "meeting", "appointment", "calendar", "event"]):
            return await self._execute_calendar_action(user_message, user, context)
        
        # Email intent detection
        elif any(keyword in user_message_lower for keyword in ["send email", "email", "compose", "mail"]):
            return await self._execute_email_action(user_message, user, context)
        
        # Tasks intent detection
        elif any(keyword in user_message_lower for keyword in ["create task", "add task", "task", "todo", "reminder"]):
            return await self._execute_task_action(user_message, user, context)
        
        # Calendar search intent
        elif any(keyword in user_message_lower for keyword in ["what meetings", "check calendar", "calendar today", "schedule today"]):
            return await self._execute_calendar_search(user_message, user, context)
        
        return None
    
    async def _execute_calendar_search(self, user_message: str, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calendar search via MCP server"""
        try:
            # Determine search parameters based on message
            query = ""
            if "today" in user_message.lower():
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                query = f"after:{today}"
            elif "tomorrow" in user_message.lower():
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                query = f"after:{tomorrow}"
            
            result = await mcp_client.search_calendar_events(
                query=query,
                max_results=10,
                user_email=user.email
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"📅 **Calendar Search Results:**\n{result.get('result', 'No events found.')}"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error executing calendar search: {e}")
            return {"success": False, "error": str(e)}
    
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
                # Don't add attendees for now, as we need proper email parsing
            
            # Extract time info
            tomorrow_match = re.search(r'tomorrow.*?(\d{1,2}(?::\d{2})?\s*(?:am|pm))', user_message.lower())
            today_match = re.search(r'today.*?(\d{1,2}(?::\d{2})?\s*(?:am|pm))', user_message.lower())
            
            if tomorrow_match:
                time_str = tomorrow_match.group(1)
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
            result = await mcp_client.create_calendar_event(
                title=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description="Meeting scheduled via AI assistant",
                attendees=attendees,
                user_email=user.email
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
            if "send" in user_message.lower():
                # For now, just search emails as sending requires more complex parsing
                result = await mcp_client.search_emails(
                    query="is:unread",
                    max_results=5,
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"📧 **Recent Unread Emails:**\n{result.get('result', 'No unread emails found.')}"
                    }
                else:
                    return result
                    
            elif "search" in user_message.lower() or "check" in user_message.lower():
                result = await mcp_client.search_emails(
                    query="is:unread",
                    max_results=10,
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"📧 **Email Search Results:**\n{result.get('result', 'No emails found.')}"
                    }
                else:
                    return result
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
                # Parse task title from message
                title = self._extract_task_title(user_message)
                logger.info(f"Parsed task title: {title}")
                
                result = await mcp_client.create_task(
                    title=title,
                    notes="Created via AI assistant",
                    due_date=None,
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"✅ **Task Created:** {title}\n📝 **Notes:** Created via AI assistant"
                    }
                else:
                    return result
                    
            elif "list" in user_message.lower() or "show" in user_message.lower():
                result = await mcp_client.list_tasks(
                    task_list="@default",
                    max_results=10,
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"✅ **Your Tasks:**\n{result.get('result', 'No tasks found.')}"
                    }
                else:
                    return result
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

# Global AI service instance
ai_service = AIService()
