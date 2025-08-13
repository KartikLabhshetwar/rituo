"""
Authentication services for frontend user management
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import httpx
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from database.connection import get_database
from database.models import User, UserResponse
from bson import ObjectId

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.google_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """Verify Google OAuth token"""
        logger.info("=== Starting Google Token Verification ===")
        logger.info(f"Token length: {len(token)}")
        logger.info(f"Google Client ID: {self.google_client_id}")
        
        if not self.google_client_id:
            logger.error("GOOGLE_OAUTH_CLIENT_ID environment variable is not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: Google OAuth client ID not configured"
            )
        
        try:
            logger.info("Calling Google's token verification...")
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), self.google_client_id
            )
            logger.info("Google token verification successful")
            logger.info(f"Token issuer: {idinfo.get('iss')}")
            logger.info(f"Token audience: {idinfo.get('aud')}")
            logger.info(f"User email: {idinfo.get('email')}")
            logger.info(f"User name: {idinfo.get('name')}")
            
            # Validate issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"Invalid issuer: {idinfo['iss']}")
                raise ValueError('Wrong issuer.')
            
            # Validate audience matches our client ID
            if idinfo.get('aud') != self.google_client_id:
                logger.error(f"Token audience mismatch. Expected: {self.google_client_id}, Got: {idinfo.get('aud')}")
                raise ValueError('Invalid audience.')
            
            logger.info("=== Google Token Verification Completed Successfully ===")
            return idinfo
            
        except ValueError as e:
            logger.error(f"Google token verification failed (ValueError): {e}")
            logger.error("=== Google Token Verification Failed ===")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Google token verification failed (Unexpected): {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.error("=== Google Token Verification Failed ===")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification error: {str(e)}"
            )

    async def exchange_auth_code(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token and get user info"""
        logger.info("=== Starting Authorization Code Exchange ===")
        
        if not self.google_client_id or not self.google_client_secret:
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: Google OAuth credentials not configured"
            )
        
        try:
            # Exchange authorization code for access token
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:8001/oauth2callback"
            }
            
            logger.info("Exchanging authorization code for access token...")
            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                
                if token_response.status_code != 200:
                    logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to exchange authorization code"
                    )
                
                token_info = token_response.json()
                access_token = token_info.get("access_token")
                id_token_str = token_info.get("id_token")
                
                if not access_token:
                    logger.error("No access token received from Google")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="No access token received from Google"
                    )
                
                logger.info("Access token received successfully")
                
                # Get user info from Google
                userinfo_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
                userinfo_response = await client.get(userinfo_url)
                
                if userinfo_response.status_code != 200:
                    logger.error(f"Failed to get user info: {userinfo_response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to get user information from Google"
                    )
                
                user_info = userinfo_response.json()
                logger.info(f"User info retrieved successfully for: {user_info.get('email')}")
                logger.info("=== Authorization Code Exchange Completed Successfully ===")
                
                return user_info
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authorization code exchange: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.error("=== Authorization Code Exchange Failed ===")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authorization code exchange error: {str(e)}"
            )

    async def get_or_create_user(self, google_user_info: Dict[str, Any]) -> User:
        """Get existing user or create new user from Google OAuth info"""
        logger.info("=== Starting Get or Create User ===")
        logger.info(f"Google user info: {google_user_info}")
        
        db = get_database()
        logger.info("Database connection obtained")
        
        # Try to find existing user by Google ID
        # Google OAuth2 v2 userinfo endpoint returns 'id' instead of 'sub'
        google_id = google_user_info.get("sub") or google_user_info.get("id")
        if not google_id:
            raise ValueError("Google user info missing both 'sub' and 'id' fields")
        logger.info(f"Looking for existing user with Google ID: {google_id}")
        existing_user = await db.users.find_one({"google_id": google_id})
        
        if existing_user:
            logger.info(f"Found existing user: {existing_user.get('email')}")
            # Update last login and any changed info
            update_data = {
                "last_login": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "name": google_user_info.get("name", existing_user.get("name")),
                "picture": google_user_info.get("picture", existing_user.get("picture")),
            }
            
            logger.info("Updating existing user...")
            await db.users.update_one(
                {"_id": existing_user["_id"]}, 
                {"$set": update_data}
            )
            
            # Fetch updated user
            updated_user = await db.users.find_one({"_id": existing_user["_id"]})
            # Convert ObjectId to string for Pydantic model
            if updated_user and "_id" in updated_user:
                updated_user["_id"] = str(updated_user["_id"])
            logger.info("User updated successfully")
            logger.info("=== Get or Create User Completed (Existing User) ===")
            return User(**updated_user)
        
        else:
            logger.info("No existing user found, creating new user...")
            # Create new user
            new_user_data = {
                "email": google_user_info["email"],
                "google_id": google_id,  # Use the google_id we already determined above
                "name": google_user_info.get("name", ""),
                "picture": google_user_info.get("picture"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc),
                "is_active": True,
                "preferences": {}
            }
            
            logger.info(f"Creating user with data: {new_user_data}")
            result = await db.users.insert_one(new_user_data)
            new_user_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
            
            logger.info(f"Created new user: {google_user_info['email']} with ID: {result.inserted_id}")
            logger.info("=== Get or Create User Completed (New User) ===")
            return User(**new_user_data)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            db = get_database()
            user_data = await db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                # Convert ObjectId to string for Pydantic model
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            db = get_database()
            user_data = await db.users.find_one({"email": email})
            if user_data:
                # Convert ObjectId to string for Pydantic model
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    def user_to_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse"""
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            picture=user.picture,
            created_at=user.created_at,
            last_login=user.last_login,
            preferences=user.preferences
        )

# Global auth service instance
auth_service = AuthService()
