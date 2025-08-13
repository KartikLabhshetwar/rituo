"""
Database connection and configuration for MongoDB
"""
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

database = Database()

async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "rituo_app")
    
    try:
        database.client = AsyncIOMotorClient(mongodb_url)
        database.database = database.client[database_name]
        
        # Test the connection
        await database.client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {mongodb_url}")
        logger.info(f"Using database: {database_name}")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    return database.database
