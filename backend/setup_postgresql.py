#!/usr/bin/env python3
"""
PostgreSQL Database Setup and Verification Script
Ensures clean PostgreSQL-only setup and removes any unnecessary files
"""

import asyncio
import os
import sys
import asyncpg
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import check_db_connection, create_tables, drop_tables
from app.models.orm_models import *  # Import all models

async def verify_postgresql_connection():
    """Verify PostgreSQL connection and database setup"""
    print("🔍 Verifying PostgreSQL Connection...")
    
    try:
        # Parse DATABASE_URL to extract connection details
        db_url = settings.DATABASE_URL
        print(f"Database URL: {db_url}")
        
        # Test basic connection
        connection_ok = await check_db_connection()
        if connection_ok:
            print("✅ PostgreSQL connection successful!")
            return True
        else:
            print("❌ PostgreSQL connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def check_database_tables():
    """Check if database tables exist and are properly created"""
    print("\n📊 Checking Database Tables...")
    
    try:
        # Connect directly using asyncpg to check tables
        # Extract connection details from DATABASE_URL
        import re
        db_url = settings.DATABASE_URL
        # Parse postgresql+asyncpg://user:pass@host:port/database
        match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        
        if not match:
            print("❌ Could not parse DATABASE_URL")
            return False
            
        user, password, host, port, database = match.groups()
        # URL decode password if needed
        password = password.replace('%40', '@').replace('%2A', '*')
        
        conn = await asyncpg.connect(
            user=user, 
            password=password, 
            host=host, 
            port=port, 
            database=database
        )
        
        # Check if tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        table_names = [table['table_name'] for table in tables]
        
        print(f"Found {len(table_names)} tables:")
        for table in table_names:
            print(f"  ✅ {table}")
        
        # Check expected tables
        expected_tables = [
            'users', 'documents', 'document_chunks', 'workflows', 
            'workflow_documents', 'workflow_executions', 'chat_sessions', 
            'chat_messages', 'system_settings'
        ]
        
        missing_tables = [table for table in expected_tables if table not in table_names]
        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
        else:
            print("\n✅ All expected tables found!")
        
        await conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

async def initialize_database():
    """Initialize database with all tables and default data"""
    print("\n🚀 Initializing PostgreSQL Database...")
    
    try:
        # Create all tables
        await create_tables()
        print("✅ Tables created successfully!")
        
        # Import the initialization function
        from init_db import create_default_data
        await create_default_data()
        print("✅ Default data created!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def clean_unnecessary_files():
    """Remove any unnecessary files (MySQL, SQLite, etc.)"""
    print("\n🧹 Cleaning unnecessary files...")
    
    unnecessary_patterns = [
        "*.sqlite*",
        "*.db-*",
        "*mysql*",
        "database.sqlite",
        "test.db"
    ]
    
    cleaned_files = []
    backend_path = Path(__file__).parent
    
    for pattern in unnecessary_patterns:
        for file_path in backend_path.rglob(pattern):
            if file_path.is_file() and file_path.name != "ai_planet.db":  # Keep our SQLite fallback
                try:
                    file_path.unlink()
                    cleaned_files.append(str(file_path))
                except Exception as e:
                    print(f"Could not remove {file_path}: {e}")
    
    if cleaned_files:
        print(f"✅ Removed {len(cleaned_files)} unnecessary files:")
        for file in cleaned_files:
            print(f"  🗑️  {file}")
    else:
        print("✅ No unnecessary files found!")

def show_database_status():
    """Show current database configuration"""
    print("\n📋 Database Configuration:")
    print(f"  Database URL: {settings.DATABASE_URL}")
    print(f"  Database Type: PostgreSQL")
    print(f"  Pool Size: {settings.DB_POOL_SIZE}")
    print(f"  Max Overflow: {settings.DB_MAX_OVERFLOW}")
    
    # Show pgAdmin connection details
    import re
    db_url = settings.DATABASE_URL
    match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    
    if match:
        user, password, host, port, database = match.groups()
        password_display = password.replace('%40', '@').replace('%2A', '*')
        
        print(f"\n🐘 pgAdmin Connection Details:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  Username: {user}")
        print(f"  Password: {password_display}")

async def main():
    """Main setup and verification function"""
    print("🐘 PostgreSQL Database Setup & Verification")
    print("=" * 50)
    
    # Step 1: Clean unnecessary files
    clean_unnecessary_files()
    
    # Step 2: Show database configuration
    show_database_status()
    
    # Step 3: Verify connection
    connection_ok = await verify_postgresql_connection()
    if not connection_ok:
        print("\n❌ Cannot proceed without database connection!")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file DATABASE_URL")
        print("3. Verify database 'ai_planet_db' exists")
        print("4. Try connecting with pgAdmin")
        return False
    
    # Step 4: Check tables
    tables_exist = await check_database_tables()
    
    # Step 5: Initialize if needed
    if not tables_exist:
        print("\n⚙️  Tables missing, initializing database...")
        init_success = await initialize_database()
        if not init_success:
            return False
    
    # Step 6: Final verification
    print("\n🎉 Database Setup Complete!")
    print("\nNext steps:")
    print("1. Start the backend server: python -m uvicorn app.main:app --reload --port 8000")
    print("2. Start the frontend: cd ../frontend && npm run dev")
    print("3. Access the application: http://localhost:5173")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)