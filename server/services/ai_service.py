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
        return f"""You are Rituo, a helpful AI assistant that can directly manage Google Workspace tools for authenticated users.

You have DIRECT access to the following capabilities:
- Google Calendar: Schedule, modify, and manage calendar events
- Gmail: Send emails, read messages, manage labels  
- Google Tasks: Create and manage task lists and tasks

User Information:
- Name: {user.name}
- Email: {user.email}
- Status: ✅ Authenticated and ready to use Google Workspace

IMPORTANT INSTRUCTIONS:
1. The user is already authenticated - DO NOT ask for authentication or permissions
2. When users request actions, execute them immediately using available tools
3. Be concise and action-oriented - focus on results, not explanations
4. For time-based requests, use the user's local timezone when possible
5. Confirm successful actions with brief, helpful summaries

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
            from services.mcp_client import mcp_client
            
            if "send" in user_message.lower():
                # Try to parse email sending request
                to, subject, body = self._parse_email_send_request(user_message)
                
                if to and subject and body:
                    result = await mcp_client.send_gmail_message(
                        to=to,
                        subject=subject,
                        body=body,
                        user_email=user.email
                    )
                    
                    if result.get("success"):
                        return {
                            "success": True,
                            "message": f"📧 **Email Sent Successfully!**\n{result.get('result', 'Email sent.')}"
                        }
                    else:
                        return result
                else:
                    # If parsing failed, search recent emails instead
                    result = await mcp_client.search_gmail_messages(
                        query="is:unread",
                        page_size=5,
                        user_email=user.email
                    )
                    
                    if result.get("success"):
                        return {
                            "success": True,
                            "message": f"📧 **Recent Unread Emails:**\n{result.get('result', 'No unread emails found.')}\n\n💡 To send an email, please specify: recipient, subject, and message content."
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
                    return {
                        "success": True,
                        "message": f"📧 **Email Search Results:**\n{result.get('result', 'No emails found.')}"
                    }
                else:
                    return result
                    
            elif "draft" in user_message.lower():
                # Try to parse draft creation request
                to, subject, body = self._parse_email_send_request(user_message)
                
                result = await mcp_client.draft_gmail_message(
                    subject=subject or "Draft",
                    body=body or "Draft message created via AI assistant",
                    to=to,
                    user_email=user.email
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"📧 **Draft Created Successfully!**\n{result.get('result', 'Draft created.')}"
                    }
                else:
                    return result
            else:
                return {"success": False, "error": "Email action not recognized. I can help you send emails, search emails, or create drafts."}
                
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
        subject_match = re.search(r'(?:subject|title|about)(?:\s+is)?[:\s]+(.+?)(?:\s+body|\s+message|\s+saying|$)', user_message, re.IGNORECASE)
        body_match = re.search(r'(?:body|message|saying|tell them|content)[:\s]+(.+)', user_message, re.IGNORECASE)
        
        # Alternative patterns for body
        if not body_match:
            body_match = re.search(r'"([^"]+)"', user_message)  # Text in quotes
        
        to = to_match.group(1) if to_match else None
        subject = subject_match.group(1).strip() if subject_match else None
        body = body_match.group(1).strip() if body_match else None
        
        # Clean up subject and body
        if subject:
            subject = subject.strip('"\'')
        if body:
            body = body.strip('"\'')
            
        return to, subject, body
    
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
