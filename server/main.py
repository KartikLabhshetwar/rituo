#!/usr/bin/env python3
"""
MCP Server entry point - Simplified approach
"""
import asyncio
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for MCP server"""
    
    try:
        # Import the server components
        from server import server, configure_server_for_http, set_transport_mode
        
        # Set default transport to streamable-http
        transport = "streamable-http"
        port = int(os.getenv("PORT", "8001"))
        
        logger.info(f"Configuring MCP Server for {transport} on port {port}")
        
        # Configure for HTTP transport
        set_transport_mode(transport)
        configure_server_for_http()
        
        logger.info("Starting MCP Server...")
        
        # Run the server
        server.run(transport=transport, port=port)
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"❌ Failed to import server components: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user")
        print("MCP Server stopped")
    except Exception as e:
        logger.error(f"MCP Server error: {e}", exc_info=True)
        print(f"❌ MCP Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
