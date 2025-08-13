"""
Chat endpoint for AI interaction
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
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
    current_user: User = Depends(get_current_user)
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
        
        # Process with AI service (Groq + LangChain)
        ai_response_content = await ai_service.process_message(
            user_message=request.message,
            user=current_user,
            chat_history=chat_history,
            context=request.context
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

@router.post("/test-chat", response_model=ChatResponse)
async def test_chat_without_auth(request: ChatRequest):
    """
    Test chat endpoint without authentication (for development/testing)
    """
    try:
        # Create a mock user for testing
        from database.models import User
        from bson import ObjectId
        
        mock_user = User(
            id=ObjectId("507f1f77bcf86cd799439011"),  # Fixed test ID
            email="test@example.com",
            google_id="test_google_id",
            name="Test User",
            picture=None
        )
        
        # Process with AI service (Groq + LangChain)
        ai_response_content = await ai_service.process_message(
            user_message=request.message,
            user=mock_user,
            chat_history=[],
            context=request.context
        )
        
        return ChatResponse(
            response=ai_response_content,
            chat_id=request.chat_id,
            message_id=f"test_msg_{hash(ai_response_content) % 10000}"
        )
        
    except Exception as e:
        logger.error(f"Error in test AI chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process test chat message: {str(e)}"
        )
