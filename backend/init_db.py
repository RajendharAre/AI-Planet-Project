#!/usr/bin/env python3
"""
Database initialization script
Creates all tables defined in the ORM models
"""

import asyncio
from app.models.dp import engine
from app.models.orm_models import Base

async def init_database():
    """Create all database tables"""
    async with engine.begin() as conn:
        # Drop all tables first (for clean slate)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())