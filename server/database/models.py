"""
User and Chat models for MongoDB
"""
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema

class ChatMessage(BaseModel):
    """Individual chat message model"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional message metadata")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChatSession(BaseModel):
    """Chat session model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference to user")
    title: str = Field(default="New Chat", description="Chat session title")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True, description="Whether the chat session is active")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session metadata")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class User(BaseModel):
    """User model for MongoDB"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr = Field(..., description="User email address")
    google_id: str = Field(..., description="Google OAuth ID")
    name: str = Field(..., description="User full name")
    picture: Optional[str] = Field(None, description="User profile picture URL")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    google_refresh_token: Optional[str] = Field(None, description="Google OAuth refresh token")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Request/Response models for API
class UserResponse(BaseModel):
    """User response model for API"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

class ChatSessionResponse(BaseModel):
    """Chat session response model for API"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool

class ChatSessionDetailResponse(BaseModel):
    """Detailed chat session response model for API"""
    id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    is_active: bool

class CreateChatRequest(BaseModel):
    """Request model for creating a new chat"""
    title: Optional[str] = "New Chat"

class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    content: str
    role: str = "user"

class UpdateChatTitleRequest(BaseModel):
    """Request model for updating chat title"""
    title: str
