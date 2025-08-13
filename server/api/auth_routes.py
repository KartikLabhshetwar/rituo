"""
Authentication API routes for frontend
"""
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from auth.frontend_auth import auth_service
from auth.dependencies import get_current_user, get_optional_user
from database.models import User, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class GoogleAuthRequest(BaseModel):
    """Google OAuth token request"""
    token: str = None
    authorization_code: str = None
    state: str = None

class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """
    Authenticate user with Google OAuth token or authorization code
    """
    logger.info("=== Google Auth Request Started ===")
    
    try:
        google_user_info = None
        
        # Handle both JWT token and authorization code flows
        if request.token:
            logger.info(f"Processing JWT token (first 50 chars): {request.token[:50]}...")
            google_user_info = await auth_service.verify_google_token(request.token)
        elif request.authorization_code:
            logger.info(f"Processing authorization code: {request.authorization_code[:20]}...")
            # Exchange authorization code for user info
            google_user_info = await auth_service.exchange_auth_code(request.authorization_code)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either token or authorization_code must be provided"
            )
        
        logger.info(f"Google auth verified successfully for user: {google_user_info.get('email')}")
        logger.info(f"Google user info: {google_user_info}")
        
        # Get or create user in database
        logger.info("Getting or creating user in database...")
        user = await auth_service.get_or_create_user(google_user_info)
        logger.info(f"User processed successfully: {user.email} (ID: {user.id})")
        
        # Create JWT tokens
        logger.info("Creating JWT tokens...")
        token_data = {"user_id": str(user.id), "email": user.email}
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token(token_data)
        logger.info(f"JWT tokens created successfully - Access token (first 20 chars): {access_token[:20]}...")
        
        response_data = AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=auth_service.user_to_response(user)
        )
        
        logger.info(f"User authenticated successfully: {user.email}")
        logger.info("=== Google Auth Request Completed Successfully ===")
        
        return response_data
        
    except HTTPException as e:
        logger.error(f"HTTP Exception during Google authentication: {e.detail}")
        logger.error("=== Google Auth Request Failed (HTTP Exception) ===")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Google authentication: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=== Google Auth Request Failed (Unexpected Error) ===")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        payload = auth_service.verify_token(request.refresh_token, "refresh")
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify user still exists and is active
        user = await auth_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        token_data = {"user_id": user_id, "email": email}
        access_token = auth_service.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return auth_service.user_to_response(current_user)

@router.post("/logout")
async def logout():
    """
    Logout user (client should remove tokens)
    """
    return JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=status.HTTP_200_OK
    )

@router.get("/google-config")
async def get_google_config():
    """
    Get Google OAuth client configuration for frontend
    """
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth client ID not configured"
        )
    
    return {
        "client_id": client_id
    }

@router.get("/check")
async def check_auth_status(current_user: User = Depends(get_optional_user)):
    """
    Check if user is authenticated
    """
    if current_user:
        return {
            "authenticated": True,
            "user": auth_service.user_to_response(current_user)
        }
    else:
        return {"authenticated": False}
