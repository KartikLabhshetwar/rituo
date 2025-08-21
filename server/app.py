"""
Rituo Unified Server - Handles both FastAPI and MCP in one process
Clean, maintainable architecture with Google Workspace AI Assistant
"""
import asyncio
import logging
import os
import threading
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to hold MCP server
mcp_server = None

def start_mcp_server():
    """Start MCP server in background thread"""
    global mcp_server
    try:
        from server import server, configure_server_for_http, set_transport_mode
        
        # Configure MCP server for HTTP
        set_transport_mode("streamable-http")
        configure_server_for_http()
        
        # Run MCP server on port 8001
        mcp_port = int(os.getenv("PORT", 8001))
        logger.info(f"Starting MCP server on port {mcp_port}")
        
        # Run in background thread
        def run_mcp():
            server.run(transport="streamable-http", port=mcp_port, host="0.0.0.0")
        
        mcp_thread = threading.Thread(target=run_mcp, daemon=True)
        mcp_thread.start()
        logger.info("✅ MCP server started in background")
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Rituo Unified Server")
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("✅ Connected to MongoDB")
        
        # Start MCP server in background
        start_mcp_server()
        
        # Wait a moment for MCP server to start
        await asyncio.sleep(2)
        
        # Initialize MCP client connection
        from services.mcp_client import initialize_mcp_client
        await initialize_mcp_client()
        logger.info("✅ MCP client connected")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Rituo Unified Server")
    try:
        # Cleanup MCP client
        from services.mcp_client import cleanup_mcp_client
        await cleanup_mcp_client()
        logger.info("✅ MCP client cleaned up")
        
        # Close MongoDB connection
        await close_mongo_connection()
        logger.info("✅ MongoDB connection closed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create unified FastAPI app
app = FastAPI(
    title="Rituo - Google Workspace AI Assistant",
    description="Unified server with FastAPI + MCP for Google Workspace integration",
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
