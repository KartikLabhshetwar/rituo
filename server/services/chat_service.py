"""
Chat services for managing chat sessions and messages
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from database.connection import get_database
from database.models import (
    ChatSession, ChatMessage, ChatSessionResponse, 
    ChatSessionDetailResponse, User
)
from bson import ObjectId

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        pass

    async def create_chat_session(self, user_id: str, title: str = "New Chat") -> ChatSession:
        """Create a new chat session for user"""
        try:
            db = get_database()
            
            chat_data = {
                "user_id": user_id,  # Keep as string, don't convert to ObjectId
                "title": title,
                "messages": [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "metadata": {}
            }
            
            result = await db.chat_sessions.insert_one(chat_data)
            chat_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
            
            logger.info(f"Created new chat session for user {user_id}: {result.inserted_id}")
            return ChatSession(**chat_data)
            
        except Exception as e:
            logger.error(f"Error creating chat session for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session"
            )

    async def create_chat_session_with_custom_id(self, user_id: str, custom_id: str, title: str = "New Chat") -> ChatSession:
        """Create a new chat session with a custom ID"""
        try:
            db = get_database()
            
            chat_data = {
                "custom_id": custom_id,  # Store the custom ID
                "user_id": user_id,  # Keep as string, don't convert to ObjectId
                "title": title,
                "messages": [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "metadata": {}
            }
            
            result = await db.chat_sessions.insert_one(chat_data)
            chat_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
            
            logger.info(f"Created new chat session with custom ID {custom_id} for user {user_id}: {result.inserted_id}")
            return ChatSession(**chat_data)
            
        except Exception as e:
            logger.error(f"Error creating chat session with custom ID {custom_id} for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session"
            )

    async def get_user_chat_sessions(self, user_id: str, limit: int = 50) -> List[ChatSessionResponse]:
        """Get all chat sessions for a user"""
        try:
            db = get_database()
            
            # Query both string and ObjectId formats for backward compatibility
            cursor = db.chat_sessions.find(
                {
                    "$or": [
                        {"user_id": user_id},  # String format (new)
                        {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                    ],
                    "is_active": True
                }
            ).sort("updated_at", -1).limit(limit)
            
            sessions = []
            async for session_data in cursor:
                sessions.append(ChatSessionResponse(
                    id=str(session_data["_id"]),
                    title=session_data.get("title", "New Chat"),
                    created_at=session_data["created_at"],
                    updated_at=session_data["updated_at"],
                    message_count=len(session_data.get("messages", [])),
                    is_active=session_data.get("is_active", True)
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting chat sessions for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve chat sessions"
            )

    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[ChatSessionDetailResponse]:
        """Get a specific chat session with messages"""
        try:
            db = get_database()
            
            session_data = None
            
            # Try to find by ObjectId first
            try:
                if ObjectId.is_valid(session_id):
                    session_data = await db.chat_sessions.find_one({
                        "_id": ObjectId(session_id),
                        "$or": [
                            {"user_id": user_id},  # String format (new)
                            {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                        ],
                        "is_active": True
                    })
            except:
                pass
            
            # If not found by ObjectId, try by custom_id
            if not session_data:
                session_data = await db.chat_sessions.find_one({
                    "custom_id": session_id,
                    "$or": [
                        {"user_id": user_id},  # String format (new)
                        {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                    ],
                    "is_active": True
                })
            
            if not session_data:
                return None
            
            return ChatSessionDetailResponse(
                id=str(session_data["_id"]),
                title=session_data.get("title", "New Chat"),
                messages=session_data.get("messages", []),
                created_at=session_data["created_at"],
                updated_at=session_data["updated_at"],
                is_active=session_data.get("is_active", True)
            )
            
        except Exception as e:
            logger.error(f"Error getting chat session {session_id} for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve chat session"
            )

    async def add_message_to_chat(
        self, 
        session_id: str, 
        user_id: str, 
        content: str, 
        role: str = "user"
    ) -> ChatMessage:
        """Add a message to a chat session"""
        try:
            db = get_database()
            
            # Try to find existing session by ObjectId first, then by custom ID
            session = None
            
            # Check if session_id is a valid ObjectId
            try:
                if ObjectId.is_valid(session_id):
                    session = await db.chat_sessions.find_one({
                        "_id": ObjectId(session_id),
                        "$or": [
                            {"user_id": user_id},  # String format (new)
                            {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                        ],
                        "is_active": True
                    })
            except:
                pass
            
            # If not found by ObjectId, try to find by custom ID field
            if not session:
                session = await db.chat_sessions.find_one({
                    "custom_id": session_id,
                    "$or": [
                        {"user_id": user_id},  # String format (new)
                        {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                    ],
                    "is_active": True
                })
            
            # If still not found, create a new session with the custom ID
            if not session:
                logger.info(f"Creating new chat session with custom ID: {session_id}")
                new_session = await self.create_chat_session_with_custom_id(user_id, session_id, "New Chat")
                session = {
                    "_id": ObjectId(new_session.id),
                    "custom_id": session_id,
                    "user_id": user_id,
                    "title": "New Chat",
                    "messages": [],
                    "created_at": new_session.created_at,
                    "updated_at": new_session.updated_at,
                    "is_active": True
                }
            
            # Create new message
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc),
                metadata={}
            )
            
            # Add message to session using the correct identifier
            update_filter = {"_id": session["_id"]}
            await db.chat_sessions.update_one(
                update_filter,
                {
                    "$push": {"messages": message.model_dump()},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            logger.info(f"Added message to chat session {session_id}")
            return message
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding message to chat session {session_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message to chat"
            )

    async def update_chat_title(self, session_id: str, user_id: str, title: str) -> bool:
        """Update chat session title"""
        try:
            db = get_database()
            
            result = await db.chat_sessions.update_one(
                {
                    "_id": ObjectId(session_id),
                    "$or": [
                        {"user_id": user_id},  # String format (new)
                        {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                    ],
                    "is_active": True
                },
                {
                    "$set": {
                        "title": title,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            logger.info(f"Updated title for chat session {session_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating chat session {session_id} title: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chat title"
            )

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Soft delete a chat session"""
        try:
            db = get_database()
            
            result = await db.chat_sessions.update_one(
                {
                    "_id": ObjectId(session_id),
                    "$or": [
                        {"user_id": user_id},  # String format (new)
                        {"user_id": ObjectId(user_id)}  # ObjectId format (legacy)
                    ]
                },
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            logger.info(f"Deleted chat session {session_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chat session"
            )

# Global chat service instance
chat_service = ChatService()
