"""
Chat API routes for frontend
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from auth.dependencies import get_current_user
from database.models import (
    User, ChatSessionResponse, ChatSessionDetailResponse,
    CreateChatRequest, SendMessageRequest, UpdateChatTitleRequest,
    ChatMessage
)
from services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.get("/", response_model=List[ChatSessionResponse])
async def get_user_chats(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat sessions for the current user
    """
    try:
        sessions = await chat_service.get_user_chat_sessions(
            user_id=str(current_user.id),
            limit=limit
        )
        return sessions
    except Exception as e:
        logger.error(f"Error getting user chats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chats"
        )

@router.post("/", response_model=ChatSessionResponse)
async def create_chat(
    request: CreateChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session
    """
    try:
        chat_session = await chat_service.create_chat_session(
            user_id=str(current_user.id),
            title=request.title
        )
        
        return ChatSessionResponse(
            id=str(chat_session.id),
            title=chat_session.title,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            message_count=len(chat_session.messages),
            is_active=chat_session.is_active
        )
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat"
        )

@router.get("/{chat_id}", response_model=ChatSessionDetailResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific chat session with messages
    """
    try:
        chat_session = await chat_service.get_chat_session(
            session_id=chat_id,
            user_id=str(current_user.id)
        )
        
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return chat_session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat"
        )

@router.post("/{chat_id}/messages", response_model=ChatMessage)
async def send_message(
    chat_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to a chat session
    """
    try:
        message = await chat_service.add_message_to_chat(
            session_id=chat_id,
            user_id=str(current_user.id),
            content=request.content,
            role=request.role
        )
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )

@router.patch("/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    request: UpdateChatTitleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update chat session title
    """
    try:
        success = await chat_service.update_chat_title(
            session_id=chat_id,
            user_id=str(current_user.id),
            title=request.title
        )
        
        if success:
            return JSONResponse(
                content={"message": "Chat title updated successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chat title"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat {chat_id} title: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat title"
        )

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat session
    """
    try:
        success = await chat_service.delete_chat_session(
            session_id=chat_id,
            user_id=str(current_user.id)
        )
        
        if success:
            return JSONResponse(
                content={"message": "Chat deleted successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chat"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat"
        )
