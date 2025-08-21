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
        self.groq_api_key = os.getenv("GROQ_API_KEY")  # Optional fallback
        self.client = None  # Will be initialized per request with user's key
        self.model_name = "llama-3.1-8b-instant"  # Using a reliable Groq model
        
        # Initialize fallback client if environment key exists
        if self.groq_api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_api_key)
                logger.info("Successfully initialized fallback Groq client")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback Groq client: {e}")
        else:
            logger.info("No fallback GROQ_API_KEY found - will use user-provided keys only")
    
    def create_system_prompt(self, user: User) -> str:
        """Create system prompt for the AI assistant"""
        return f"""You are Rituo, an AI assistant that helps {user.name} manage their Google Workspace.

User: {user.name} ({user.email})

Instructions:
1. When users ask for actions (schedule meetings, send emails, create tasks), execute them using available tools
2. Provide natural, conversational responses using the actual results from the tools
3. Include useful details like event IDs or links only when they're actually provided by the tools
4. Be helpful and friendly while being accurate about what actually happened
5. If something fails, explain what went wrong in plain language

Available capabilities:
- Google Calendar: Create and manage events
- Gmail: Send emails and search messages  
- Google Tasks: Create and manage tasks

Response style:
- Natural and conversational
- Use actual results from tools
- Include links/IDs only if provided
- Be specific about what was accomplished

Examples:
User: "Schedule meeting tomorrow 2pm"
Response: "I've scheduled your meeting for tomorrow at 2:00 PM. The event has been added to your calendar."

User: "Send email to john@company.com"
Response: "I've sent your email to john@company.com successfully."""

    async def process_message(
        self, 
        user_message: str, 
        user: User,
        chat_history: List[Dict[str, Any]] = None,
        context: Dict[str, Any] = None,
        groq_api_key: str = None
    ) -> str:
        """
        Process a user message and return AI response
        """
        try:
            # Use user's API key if provided, otherwise fall back to environment
            api_key = groq_api_key or self.groq_api_key
            if not api_key:
                raise ValueError("No Groq API key available. Please provide your API key.")
            
            # Create Groq client with user's API key
            from groq import Groq
            client = Groq(api_key=api_key)
            
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
            response = await self._get_ai_response(messages, client)
            
            # Check if the response indicates need for MCP tools
            enhanced_response = await self._process_with_mcp_tools(
                response, user_message, user, context or {}
            )
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error while processing your message. Please try again."
    
    async def _get_ai_response(self, messages: List[Any], client = None) -> str:
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
            
            # Use provided client or fall back to instance client
            groq_client = client or self.client
            
            # Call Groq API
            response = groq_client.chat.completions.create(
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
                    # Return ONLY the MCP tool result, not the AI response
                    return intent_result.get('message', 'Action completed.')
                else:
                    # Return ONLY the error, not the AI response
                    return f"❌ {intent_result.get('error', 'Unknown error occurred')}"
            
            # Only return AI response if no MCP action was taken
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
        
        # Email intent detection - enhanced patterns
        elif (any(keyword in user_message_lower for keyword in ["send email", "send mail", "send a mail", "write email", "write mail", "write a mail", "compose"]) or
              ("send" in user_message_lower and ("mail" in user_message_lower or "email" in user_message_lower)) or
              ("send" in user_message_lower and ("to" in user_message_lower and "@" in user_message)) or
              ("write" in user_message_lower and ("mail" in user_message_lower or "email" in user_message_lower)) or
              ("list" in user_message_lower and ("mail" in user_message_lower or "email" in user_message_lower))):
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
            
            # Check if user wants to list/view events or calendars
            if any(word in user_message.lower() for word in ["list", "show", "what", "check", "see", "look"]):
                # Check if they want to list calendars specifically
                if "calendar" in user_message.lower() and ("list" in user_message.lower() or "show" in user_message.lower()) and "event" not in user_message.lower():
                    result = await mcp_client.list_calendars(user_email=user.email)
                    
                    if result.get("success"):
                        calendars_data = result.get("result", "")
                        
                        # Ensure calendars_data is a string
                        if not isinstance(calendars_data, str):
                            calendars_data = str(calendars_data)
                        
                        return {
                            "success": True,
                            "message": f"Here are your available calendars:\n\n{calendars_data}"
                        }
                    else:
                        error_msg = result.get("error", "Failed to get calendars")
                        return {
                            "success": False,
                            "error": f"I couldn't get your calendars. {error_msg}"
                        }
                # Get date from message (tomorrow, today, specific date)
                target_date = None
                if "tomorrow" in user_message.lower():
                    tomorrow = datetime.now() + timedelta(days=1)
                    target_date = tomorrow.strftime("%Y-%m-%d")
                elif "today" in user_message.lower():
                    target_date = datetime.now().strftime("%Y-%m-%d")
                
                result = await mcp_client.get_calendar_events(
                    time_min=target_date,
                    time_max=None,  # Let mcp_client calculate the proper end time
                    max_results=10,
                    user_email=user.email
                )
                
                if result.get("success"):
                    events_data = result.get("result", "")
                    
                    # Ensure events_data is a string
                    if not isinstance(events_data, str):
                        events_data = str(events_data)
                    
                    # Format the events data for better readability
                    formatted_events = self._format_calendar_events(events_data)
                    
                    date_label = "tomorrow" if target_date and "tomorrow" in user_message.lower() else "today" if target_date and "today" in user_message.lower() else "for the specified date"
                    return {
                        "success": True,
                        "message": f"📅 **Calendar Events {date_label.title()}**\n\n{formatted_events}"
                    }
                else:
                    error_msg = result.get("error", "Failed to get calendar events")
                    return {
                        "success": False,
                        "error": f"I couldn't get your calendar events. {error_msg}"
                    }
            
            # Parse meeting details from user message for creating events
            title = "New Meeting"
            start_time = None
            attendees = []
            
            # Extract title (meeting with X, X meeting, etc.)
            meeting_match = re.search(r'meeting with (.+?)(?:\s|$|at|tomorrow|today)', user_message.lower())
            if meeting_match:
                title = f"Meeting with {meeting_match.group(1).title()}"
                # Don't add attendees for now, as we need proper email parsing
            
            # Extract time info with better parsing
            start_time = self._parse_datetime_from_message(user_message)
            
            if not start_time:
                # Default to tomorrow 2 PM if no specific time found
                tomorrow = datetime.now() + timedelta(days=1)
                start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            
            end_time = start_time + timedelta(hours=1)  # Default 1-hour meeting
            
            # Get user's timezone or default to a reasonable one
            user_timezone = self._get_user_timezone(user_message, user)
            
            # Call MCP server to create calendar event
            result = await mcp_client.create_calendar_event(
                title=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description="Meeting scheduled via AI assistant",
                attendees=attendees,
                user_email=user.email,
                timezone=user_timezone
            )
            
            if result.get("success"):
                # Create natural response using actual MCP result
                mcp_result = result.get("result", "")
                
                # Ensure mcp_result is a string
                if not isinstance(mcp_result, str):
                    mcp_result = str(mcp_result)
                
                # Check if the result contains a link
                # Format the calendar response nicely
                import re
                link_match = re.search(r'Link:\s*(https?://[^\s]+)', mcp_result)
                event_id_match = re.search(r'ID:\s*([^\s,]+)', mcp_result)
                
                natural_response = f"📅 **Meeting Scheduled Successfully!**\n\n"
                natural_response += f"**Event:** {title}\n"
                natural_response += f"**Date:** {start_time.strftime('%B %d, %Y')}\n"
                natural_response += f"**Time:** {start_time.strftime('%I:%M %p')}\n"
                
                if link_match:
                    natural_response += f"**Calendar Link:** [Open in Google Calendar]({link_match.group(1)})\n"
                if event_id_match:
                    natural_response += f"**Event ID:** `{event_id_match.group(1)}`"
                
                return {
                    "success": True,
                    "message": natural_response
                }
            else:
                error_msg = result.get("error", "Failed to create calendar event")
                return {
                    "success": False,
                    "error": f"I couldn't create the meeting. {error_msg}"
                }
            
            # Check for delete/cancel requests  
            if any(word in user_message.lower() for word in ["delete", "cancel", "remove"]):
                return {
                    "success": False,
                    "error": "To delete calendar events, I need the specific event ID. You can get event IDs by listing your events first, then use 'delete event with ID [event_id]' or delete them directly in Google Calendar."
                }
                
        except Exception as e:
            logger.error(f"Error executing calendar action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_email_action(self, user_message: str, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email actions via MCP server"""
        try:
            from services.mcp_client import mcp_client
            
            if "send" in user_message.lower():
                # Try to parse email sending request
                to, subject, body = self._parse_email_send_request(user_message)
                
                if to and subject and body:
                    result = await mcp_client.send_email(
                        to=to,  # send_email expects a string
                        subject=subject,
                        body=body,
                        user_email=user.email
                    )
                    
                    if result.get("success"):
                        return {
                            "success": True,
                            "message": f"I've sent your email to {to} successfully."
                        }
                    else:
                        error_msg = result.get("error", "Failed to send email")
                        
                        # Check if it's a permission issue
                        if "insufficient" in error_msg.lower() or "authentication" in error_msg.lower() or "403" in error_msg:
                            return {
                                "success": False,
                                "error": f"🚫 **Gmail Send Permission Missing**\n\n📧 **The Issue:** Your current authentication only includes Gmail *read* permissions, but sending emails requires Gmail *send* permissions.\n\n🔧 **Quick Fix:**\n1. **Clear your current session:** Go to [Google Account Settings](https://myaccount.google.com/permissions)\n2. **Remove 'Rituo' app access** (this clears old permissions)\n3. **Re-login to Rituo** - you'll be prompted for Gmail send permissions\n4. **Grant all Gmail permissions** when prompted\n\n💡 **Why this happens:** Google separates read and send permissions for security. You initially logged in with read-only access.\n\n🏢 **Corporate accounts:** If you're using a company Google Workspace account, contact your IT administrator to enable Gmail API access."
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"❌ **Email Send Failed**\n\n{error_msg}"
                            }
                else:
                    # If parsing failed, search recent emails instead
                    result = await mcp_client.search_gmail_messages(
                        query="is:unread",
                        page_size=5,
                        user_email=user.email
                    )
                    
                    if result.get("success"):
                        email_results = result.get('result', 'No unread emails found.')
                        
                        # Ensure email_results is a string
                        if not isinstance(email_results, str):
                            email_results = str(email_results)
                            
                        return {
                            "success": True,
                            "message": f"Here are your recent unread emails:\n\n{email_results}"
                        }
                    else:
                        return result
                    
            elif "search" in user_message.lower() or "check" in user_message.lower() or "inbox" in user_message.lower():
                # Extract search query if provided
                search_query = self._extract_email_search_query(user_message)
                
                result = await mcp_client.search_gmail_messages(
                    query=search_query,
                    page_size=10,
                    user_email=user.email
                )
                
                if result.get("success"):
                    email_results = result.get('result', 'No emails found.')
                    
                    # Ensure email_results is a string
                    if not isinstance(email_results, str):
                        email_results = str(email_results)
                        
                    return {
                        "success": True,
                        "message": f"Here's what I found in your emails:\n\n{email_results}"
                    }
                else:
                    return result
                    
            elif "draft" in user_message.lower():
                # Try to parse draft creation request
                to, subject, body = self._parse_email_send_request(user_message)
                
                result = await mcp_client.draft_gmail_message(
                    subject=subject or "Draft",
                    body=body or "Draft message created via AI assistant",
                    to=[to] if to else [],
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"I've created a draft email for you. You can find it in your Gmail drafts."
                    }
                else:
                    error_msg = result.get("error", "Failed to create draft")
                    return {
                        "success": False,
                        "error": f"I couldn't create the draft. {error_msg}"
                    }
            elif "label" in user_message.lower():
                if "list" in user_message.lower() or "show" in user_message.lower():
                    # List Gmail labels
                    result = await mcp_client.list_gmail_labels(user_email=user.email)
                    
                    if result.get("success"):
                        labels_data = result.get('result', 'No labels found.')
                        
                        # Ensure labels_data is a string
                        if not isinstance(labels_data, str):
                            labels_data = str(labels_data)
                            
                        return {
                            "success": True,
                            "message": f"Here are your Gmail labels:\n\n{labels_data}"
                        }
                    else:
                        return result
                else:
                    return {
                        "success": False,
                        "error": "I can help you list Gmail labels. Try 'show my email labels'."
                    }
            else:
                return {"success": False, "error": "Email action not recognized. I can help you send emails, search emails, create drafts, or manage labels."}
                
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
                    # Extract task ID from result if available
                    task_result = result.get("result", "")
                    task_id_match = None
                    if isinstance(task_result, str):
                        import re
                        task_id_match = re.search(r'ID:\s*([^\s,]+)', task_result)
                    
                    response = f"✅ **Task Created Successfully!**\n\n"
                    response += f"**Task:** {title}\n"
                    response += f"**Status:** Pending\n"
                    if task_id_match:
                        response += f"**Task ID:** `{task_id_match.group(1)}`"
                    
                    return {
                        "success": True,
                        "message": response
                    }
                else:
                    error_msg = result.get("error", "Failed to create task")
                    return {
                        "success": False,
                        "error": f"I couldn't create the task. {error_msg}"
                    }
                    
            elif "list" in user_message.lower() or "show" in user_message.lower():
                result = await mcp_client.list_tasks(
                    task_list_id=None,  # Will auto-detect default
                    max_results=10,
                    user_email=user.email
                )
                
                if result.get("success"):
                    task_results = result.get('result', 'No tasks found.')
                    
                    # Ensure task_results is a string
                    if not isinstance(task_results, str):
                        task_results = str(task_results)
                    
                    # Format the tasks for better readability
                    formatted_tasks = self._format_task_list(task_results)
                        
                    return {
                        "success": True,
                        "message": f"✅ **Your Tasks**\n\n{formatted_tasks}"
                    }
                else:
                    return result
                    
            elif "delete" in user_message.lower() or "remove" in user_message.lower():
                # Extract task ID from the message
                import re
                
                # Look for task ID patterns
                id_patterns = [
                    r'(?:id|ID)\s*[:\[\(]?\s*([a-zA-Z0-9_-]+)',  # "id: xyz" or "ID [xyz]"
                    r'task\s+([a-zA-Z0-9_-]+)',  # "task xyz"
                    r'([a-zA-Z0-9_-]{10,})'  # Long alphanumeric strings (likely IDs)
                ]
                
                task_id = None
                task_list_id = None
                
                for pattern in id_patterns:
                    match = re.search(pattern, user_message)
                    if match:
                        task_id = match.group(1)
                        break
                
                if task_id:
                    # Get default task list ID first
                    try:
                        task_lists_result = await mcp_client.get_default_task_list(user_email=user.email)
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
                    
                    # Try to delete the task
                    result = await mcp_client.delete_task(
                        task_list_id=task_list_id,
                        task_id=task_id,
                        user_email=user.email
                    )
                    
                    if result.get("success"):
                        return {
                            "success": True,
                            "message": f"🗑️ **Task Deleted Successfully!**\n\nTask with ID `{task_id}` has been removed from your task list."
                        }
                    else:
                        error_msg = result.get("error", "Failed to delete task")
                        return {
                            "success": False,
                            "error": f"I couldn't delete the task. {error_msg}"
                        }
                else:
                    return {
                        "success": False,
                        "error": "I need the specific task ID to delete it. You can get task IDs by listing your tasks first."
                    }
                
            elif "update" in user_message.lower() or "modify" in user_message.lower() or "change" in user_message.lower():
                # Extract task info from the message
                import re
                
                # Try to parse: 'update "taskname" to "newtaskname"'
                update_pattern = r'update\s*["\']?([^"\']+?)["\']?\s*to\s*["\']?([^"\']+)["\']?'
                match = re.search(update_pattern, user_message, re.IGNORECASE)
                
                if match:
                    old_task_name = match.group(1).strip()
                    new_task_name = match.group(2).strip()
                    
                    # First, list tasks to find the task ID by name
                    task_list_result = await mcp_client.list_tasks(
                        task_list_id=None,  # Auto-detect default
                        max_results=50,
                        user_email=user.email
                    )
                    
                    if task_list_result.get("success"):
                        tasks_data = task_list_result.get("result", "")
                        
                        # Find task ID by matching the old task name
                        task_id = None
                        task_list_id = None
                        
                        # Look for the task name in the result
                        if old_task_name.lower() in tasks_data.lower():
                            # Extract task ID from the text
                            lines = tasks_data.split('\n')
                            for i, line in enumerate(lines):
                                if old_task_name.lower() in line.lower():
                                    # Look for ID in the same line or next line
                                    id_match = re.search(r'ID:\s*([a-zA-Z0-9_-]+)', line)
                                    if not id_match and i + 1 < len(lines):
                                        id_match = re.search(r'ID:\s*([a-zA-Z0-9_-]+)', lines[i + 1])
                                    if id_match:
                                        task_id = id_match.group(1)
                                        break
                        
                        if task_id:
                            # Get default task list ID
                            try:
                                task_lists_result = await mcp_client.get_default_task_list(user_email=user.email)
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
                            
                            # Update the task
                            result = await mcp_client.update_task(
                                task_list_id=task_list_id,
                                task_id=task_id,
                                title=new_task_name,
                                user_email=user.email
                            )
                            
                            if result.get("success"):
                                return {
                                    "success": True,
                                    "message": f"✏️ **Task Updated Successfully!**\n\n**Old Name:** {old_task_name}\n**New Name:** {new_task_name}\n**Task ID:** `{task_id}`"
                                }
                            else:
                                error_msg = result.get("error", "Failed to update task")
                                return {
                                    "success": False,
                                    "error": f"I couldn't update the task. {error_msg}"
                                }
                        else:
                            return {
                                "success": False,
                                "error": f"I couldn't find a task named '{old_task_name}'. Please check the task name and try again."
                            }
                    else:
                        return {
                            "success": False,
                            "error": "I couldn't list your tasks to find the one to update."
                        }
                else:
                    return {
                        "success": False,
                        "error": "Please use the format: 'update \"old task name\" to \"new task name\"' or provide the task ID."
                    }
            else:
                return {"success": False, "error": "Task action not recognized"}
                
        except Exception as e:
            logger.error(f"Error executing task action: {e}")
            return {"success": False, "error": str(e)}

    def _extract_task_title(self, user_message: str) -> str:
        """Extract task title from user message"""
        import re
        
        # Comprehensive patterns for task title extraction
        patterns = [
            # "add a new task as sleep at 11 pm today"
            r'(?:create|add|make).*?(?:new\s+)?task\s+as\s+(.*?)(?:\s*$)',
            # "create a task to do something"
            r'(?:create|add|make).*?task.*?to\s+(.*?)(?:\s*$)',
            # "add task: something" 
            r'(?:create|add|make).*?task.*?:\s*(.*?)(?:\s*$)',
            # "add task something"
            r'(?:create|add|make).*?task\s+(.*?)(?:\s*$)',
            # "task for something"
            r'task.*?(?:for|to|about)\s+(.*?)(?:\s*$)',
            # "new task something"
            r'new\s+task\s+(.*?)(?:\s*$)',
            # Generic "add something" (when in task context)
            r'(?:create|add|make)\s+(.*?)(?:\s*$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Remove quotes if present
                title = re.sub(r'^["\']|["\']$', '', title)
                # Don't return if it's too generic or empty
                if title and len(title.strip()) > 2 and title.lower() not in ['task', 'todo', 'reminder']:
                    return title.strip()
        
        # Final fallback
        return "New Task via AI Assistant"
    
    def _parse_datetime_from_message(self, user_message: str):
        """Parse date and time from user message using dateutil and proper timezone handling"""
        from datetime import datetime, timedelta
        from dateutil import parser, tz
        import re
        import time
        
        # Normalize the message
        msg = user_message.lower().strip()
        
        # Get current time in local timezone
        local_tz = tz.tzlocal()
        now = datetime.now(local_tz)
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        # Enhanced time patterns with more comprehensive coverage
        time_patterns = [
            r'(?:at\s+)?(\d{1,2})\s*:?\s*(\d{2})?\s*(am|pm)',  # "at 5 pm", "5:30 pm", "5pm"
            r'(?:at\s+)?(\d{1,2})\s*(am|pm)',  # "at 5pm", "5 pm"
            r'(?:at\s+)?(\d{1,2}):(\d{2})',  # "at 17:30", "5:30" (24-hour format)
        ]
        
        # Date patterns with better detection
        is_tomorrow = any(word in msg for word in ['tomorrow', 'next day', 'tmrw'])
        is_today = any(word in msg for word in ['today', 'this day', 'now', 'right now'])
        
        # Extract time
        time_match = None
        for pattern in time_patterns:
            time_match = re.search(pattern, msg)
            if time_match:
                break
        
        if not time_match:
            # Try natural language parsing with dateutil
            try:
                # Extract potential time strings
                time_strings = re.findall(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b', msg)
                if time_strings:
                    parsed_time = parser.parse(time_strings[0], default=now)
                    # Combine with appropriate date
                    if is_tomorrow:
                        return parsed_time.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
                    else:
                        result_time = parsed_time.replace(year=today.year, month=today.month, day=today.day)
                        # If time is in the past today, use tomorrow
                        if result_time <= now:
                            return result_time.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
                        return result_time
            except (ValueError, TypeError):
                pass
            return None
            
        # Parse time components
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        
        # Handle AM/PM conversion
        if len(time_match.groups()) >= 3 and time_match.group(3):
            ampm = time_match.group(3)
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
        
        # Determine base date
        if is_tomorrow:
            base_date = tomorrow
        elif is_today:
            base_date = today
        else:
            # Smart date detection: if time is in the past today, assume tomorrow
            base_date = today
            potential_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if potential_time <= now:
                base_date = tomorrow
        
        # Create the final datetime with proper timezone
        naive_dt = datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
        # Use replace() method instead of localize() for dateutil timezones
        result = naive_dt.replace(tzinfo=local_tz)
        return result
    
    def _get_user_timezone(self, user_message: str, user: User) -> str:
        """Get user's timezone using dateutil's automatic detection"""
        from dateutil import tz
        import time
        
        # Check if user has timezone in their profile (if we add this field later)
        # if hasattr(user, 'timezone') and user.timezone:
        #     return user.timezone
        
        # Use dateutil's automatic local timezone detection
        try:
            local_tz = tz.tzlocal()
            
            # Try to get IANA timezone name from the timezone object
            if hasattr(local_tz, 'zone') and local_tz.zone:
                return local_tz.zone
            
            # Try to get timezone name from the _tzinfos attribute (common in dateutil)
            if hasattr(local_tz, '_tzinfos') and local_tz._tzinfos:
                # This might contain the actual timezone info
                for tzinfo in local_tz._tzinfos:
                    if hasattr(tzinfo, 'zone') and tzinfo.zone:
                        return tzinfo.zone
            
            # Try to get timezone name from system's tzname
            try:
                # Get system timezone name from the astimezone method
                import datetime
                now = datetime.datetime.now()
                local_dt = now.astimezone()
                
                # Try to get the timezone name
                if hasattr(local_dt.tzinfo, 'zone'):
                    return local_dt.tzinfo.zone
                elif hasattr(local_dt.tzinfo, 'tzname'):
                    tz_name = local_dt.tzinfo.tzname(local_dt)
                    if tz_name and tz_name != 'tzlocal()':
                        return tz_name
                
                # Fallback: determine timezone from UTC offset
                offset = local_dt.utcoffset().total_seconds() / 3600
                
                # Map common offsets to IANA timezones (focusing on major ones)
                offset_to_tz = {
                    5.5: "Asia/Kolkata",   # India Standard Time
                    5.75: "Asia/Kathmandu", # Nepal Time 
                    5.0: "Asia/Karachi",   # Pakistan Standard Time
                    0.0: "UTC",            # Coordinated Universal Time
                    1.0: "Europe/London",  # GMT+1 (CET)
                    2.0: "Europe/Berlin",  # Central European Time
                    -5.0: "America/New_York", # Eastern Time
                    -6.0: "America/Chicago",  # Central Time
                    -7.0: "America/Denver",   # Mountain Time
                    -8.0: "America/Los_Angeles", # Pacific Time
                    8.0: "Asia/Shanghai",     # China Standard Time
                    9.0: "Asia/Tokyo",        # Japan Standard Time
                    -3.0: "America/Sao_Paulo" # Brazil Time
                }
                
                return offset_to_tz.get(offset, "UTC")
                    
            except Exception:
                pass
                
        except Exception:
            pass
            
        # Final fallback to UTC
        return "UTC"
    
    def _parse_email_send_request(self, user_message: str) -> tuple[str, str, str]:
        """Parse email send request to extract to, subject, and body"""
        import re
        
        # Try to extract email components using various patterns
        to_match = re.search(r'(?:to|send.*?to)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', user_message.lower())
        
        # More flexible patterns for subject and body
        subject_match = re.search(r'(?:subject|title|about)(?:\s+is)?[:\s]+(.+?)(?:\s+body|\s+message|\s+saying|$)', user_message, re.IGNORECASE)
        
        # Try multiple patterns for body/message content
        body_patterns = [
            r'(?:saying|tell them|message is|body is|content is)[:\s]+"([^"]+)"',  # "saying 'message'"
            r'(?:saying|tell them|message)[:\s]+(.+?)(?:\.|$)',  # "saying message"
            r'as\s+"([^"]+)"',  # "as 'message'"
            r'as\s+([^"\']+?)(?:\s*$)',  # "as message"
            r'"([^"]+)"',  # Just text in quotes
            r'\'([^\']+)\'',  # Text in single quotes
        ]
        
        body_match = None
        for pattern in body_patterns:
            body_match = re.search(pattern, user_message, re.IGNORECASE)
            if body_match:
                break
        
        to = to_match.group(1) if to_match else None
        subject = subject_match.group(1).strip() if subject_match else None
        body = body_match.group(1).strip() if body_match else None
        
        # If no explicit subject but we have a body, use a default subject
        if to and body and not subject:
            subject = "Message from Rituo"
        
        # Clean up subject and body
        if subject:
            subject = subject.strip('"\'')
        if body:
            body = body.strip('"\'')
            
        return to, subject, body
    
    def _format_calendar_events(self, events_data: str) -> str:
        """Format calendar events for better readability"""
        if "No events found" in events_data:
            return "📭 No events scheduled"
        
        import re
        
        # Extract individual events using regex
        event_pattern = r'"([^"]+)"\s*\(Starts:\s*([^,]+),\s*Ends:\s*([^)]+)\)\s*ID:\s*([^\s|]+)(?:\s*\|\s*Link:\s*([^\s]+))?'
        events = re.findall(event_pattern, events_data)
        
        if not events:
            # Fallback to original format if parsing fails
            return events_data
        
        formatted = []
        for i, (title, start, end, event_id, link) in enumerate(events, 1):
            # Parse and format the datetime
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start.replace('T', ' ').replace('+05:30', ''))
                end_dt = datetime.fromisoformat(end.replace('T', ' ').replace('+05:30', ''))
                
                time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                date_str = start_dt.strftime('%B %d, %Y')
                
                event_str = f"**{i}. {title}**\n"
                event_str += f"   📅 {date_str}\n"
                event_str += f"   🕐 {time_str}\n"
                if link:
                    event_str += f"   🔗 [Open in Calendar]({link})\n"
                
                formatted.append(event_str)
            except:
                # Fallback if datetime parsing fails
                formatted.append(f"**{i}. {title}**\n   📅 {start} - {end}\n")
        
        return "\n".join(formatted)
    
    def _format_task_list(self, task_data: str) -> str:
        """Format task list for better readability"""
        if "No tasks found" in task_data or not task_data.strip():
            return "📝 No tasks found"
        
        import re
        
        # Extract individual tasks using regex
        task_pattern = r'([^\n\r]+)\s*\(ID:\s*([^)]+)\)\s*Status:\s*([^\n\r]+)\s*Notes:\s*([^\n\r]*)\s*Updated:\s*([^\n\r]*)'
        tasks = re.findall(task_pattern, task_data)
        
        if not tasks:
            # Fallback to original format if parsing fails
            return task_data
        
        formatted = []
        for i, (title, task_id, status, notes, updated) in enumerate(tasks, 1):
            status_emoji = "✅" if status.strip().lower() == "completed" else "📝"
            
            task_str = f"{status_emoji} **{i}. {title.strip()}**\n"
            task_str += f"   📋 Status: {status.strip()}\n"
            if notes.strip() and notes.strip() != "Created via AI assistant":
                task_str += f"   📄 Notes: {notes.strip()}\n"
            task_str += f"   🆔 ID: `{task_id.strip()}`\n"
            
            formatted.append(task_str)
        
        return "\n".join(formatted)
    
    def _extract_email_search_query(self, user_message: str) -> str:
        """Extract email search query from user message"""
        import re
        
        # Look for specific search terms
        if "unread" in user_message.lower():
            return "is:unread"
        elif "important" in user_message.lower():
            return "is:important"
        elif "starred" in user_message.lower():
            return "is:starred"
        elif "from" in user_message.lower():
            from_match = re.search(r'from\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', user_message.lower())
            if from_match:
                return f"from:{from_match.group(1)}"
        elif "subject" in user_message.lower():
            subject_match = re.search(r'subject[:\s]+(.+)', user_message, re.IGNORECASE)
            if subject_match:
                return f"subject:{subject_match.group(1).strip()}"
        
        # Default to recent emails
        return "in:inbox"

# Global AI service instance
ai_service = AIService()
