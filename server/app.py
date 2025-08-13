"""
FastAPI application for Rituo - Google Workspace AI Assistant
This runs the REST API for the frontend, separate from the MCP server
"""
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Import database connection
from database.connection import connect_to_mongo, close_mongo_connection

# Import API routes
from api.auth_routes import router as auth_router 
from api.chat_routes import router as chat_router
from api.ai_routes import router as ai_router

# Import MCP client for AI service
from mcp_client import initialize_mcp_client, cleanup_mcp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Rituo FastAPI application")
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("Connected to MongoDB")
        
        # Initialize MCP client
        await initialize_mcp_client()
        logger.info("Initialized MCP client")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rituo FastAPI application")
    try:
        # Cleanup MCP client
        await cleanup_mcp_client()
        logger.info("Cleaned up MCP client")
        
        # Close MongoDB connection
        await close_mongo_connection()
        logger.info("Closed MongoDB connection")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="Rituo API",
    description="AI Assistant for Google Workspace",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
        "https://accounts.google.com",  # Allow Google OAuth
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ai_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "rituo-api",
        "version": "1.0.0"
    })

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Rituo API",
        "description": "AI Assistant for Google Workspace",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"Starting Rituo API server on port {port}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
