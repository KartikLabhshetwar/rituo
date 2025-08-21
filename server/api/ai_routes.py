"""
Chat endpoint for AI interaction
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel
from auth.dependencies import get_current_user
from database.models import User
from services.chat_service import chat_service
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ChatRequest(BaseModel):
    """AI chat request"""
    message: str
    chat_id: str
    context: dict = {}

class ChatResponse(BaseModel):
    """AI chat response"""
    response: str
    chat_id: str
    message_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    x_groq_api_key: str = Header(None, alias="X-Groq-API-Key")
):
    """
    Chat with AI and get response using MCP tools
    This endpoint will:
    1. Add user message to chat
    2. Process with AI/Groq + Langchain
    3. Execute MCP tools if needed (calendar, gmail, tasks)
    4. Add AI response to chat
    5. Return response
    """
    try:
        # Add user message to chat
        user_message = await chat_service.add_message_to_chat(
            session_id=request.chat_id,
            user_id=str(current_user.id),
            content=request.message,
            role="user"
        )
        
        # Get chat history for context
        chat_session = await chat_service.get_chat_session(
            session_id=request.chat_id,
            user_id=str(current_user.id)
        )
        
        chat_history = []
        if chat_session and chat_session.messages:
            # Convert messages to dict format for AI service
            chat_history = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in chat_session.messages[:-1]  # Exclude the just-added user message
            ]
        
        # Check if user provided their own Groq API key
        if not x_groq_api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Groq API key is required. Please add your API key in the settings."
            )
        
        # Process with AI service (Groq + LangChain) using user's API key
        ai_response_content = await ai_service.process_message(
            user_message=request.message,
            user=current_user,
            chat_history=chat_history,
            context=request.context,
            groq_api_key=x_groq_api_key
        )
        
        # Add AI response to chat
        ai_message = await chat_service.add_message_to_chat(
            session_id=request.chat_id,
            user_id=str(current_user.id),
            content=ai_response_content,
            role="assistant"
        )
        
        return ChatResponse(
            response=ai_response_content,
            chat_id=request.chat_id,
            message_id=ai_message.id
        )
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
