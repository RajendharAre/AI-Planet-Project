# Database Initialization and Migration Script

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import Base, create_tables, drop_tables, check_db_connection
from app.models.orm_models import *  # Import all models

async def init_database():
    """
    Initialize the database with all tables
    """
    print("🚀 Initializing PostgreSQL database...")
    
    # Check database connection
    print("🔍 Checking database connection...")
    if not await check_db_connection():
        print("❌ Database connection failed. Please check your DATABASE_URL in .env file")
        print(f"Current DATABASE_URL: {settings.DATABASE_URL}")
        print("\nMake sure PostgreSQL is running and credentials are correct.")
        return False
    
    print("✅ Database connection successful!")
    
    # Create all tables
    print("📊 Creating database tables...")
    try:
        await create_tables()
        print("✅ All tables created successfully!")
        
        # Create default admin user if needed
        await create_default_data()
        
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

async def create_default_data():
    """
    Create default data for the application
    """
    from app.core.database import AsyncSessionLocal
    from app.models.orm_models import User, SystemSettings
    from passlib.context import CryptContext
    import uuid
    
    print("👤 Creating default admin user...")
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == "admin@aiplanet.com"))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create default admin user
                admin_user = User(
                    id=uuid.uuid4(),
                    email="admin@aiplanet.com",
                    username="admin",
                    full_name="AI Planet Administrator",
                    hashed_password=pwd_context.hash("admin123"),  # Change this in production!
                    is_active=True,
                    is_admin=True,
                    bio="Default administrator account"
                )
                session.add(admin_user)
                print("✅ Default admin user created (admin@aiplanet.com / admin123)")
            else:
                print("ℹ️  Admin user already exists")
            
            # Create default system settings
            default_settings = [
                {
                    "key": "app_version",
                    "value": {"version": "2.0.0", "build": "001"},
                    "description": "Application version information"
                },
                {
                    "key": "embedding_model",
                    "value": {"provider": "gemini", "model": "text-embedding-004"},
                    "description": "Default embedding model configuration"
                },
                {
                    "key": "chat_model",
                    "value": {"provider": "gemini", "model": "gemini-1.5-flash"},
                    "description": "Default chat model configuration"
                },
                {
                    "key": "max_file_size",
                    "value": {"size_mb": 10, "size_bytes": 10485760},
                    "description": "Maximum file upload size"
                }
            ]
            
            for setting_data in default_settings:
                result = await session.execute(
                    select(SystemSettings).where(SystemSettings.key == setting_data["key"])
                )
                existing_setting = result.scalar_one_or_none()
                
                if not existing_setting:
                    setting = SystemSettings(
                        id=uuid.uuid4(),
                        key=setting_data["key"],
                        value=setting_data["value"],
                        description=setting_data["description"]
                    )
                    session.add(setting)
            
            await session.commit()
            print("✅ Default system settings created")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating default data: {e}")

async def reset_database():
    """
    Reset the database by dropping and recreating all tables
    """
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Database reset cancelled")
        return
    
    print("🗑️  Dropping all tables...")
    await drop_tables()
    print("✅ All tables dropped")
    
    print("📊 Recreating tables...")
    await create_tables()
    print("✅ Tables recreated")
    
    await create_default_data()
    print("🎉 Database reset completed!")

def print_help():
    """
    Print help information
    """
    print("""
🚀 AI Planet Database Management

Usage: python init_db.py [command]

Commands:
  init     - Initialize database with all tables and default data
  reset    - Reset database (WARNING: Deletes all data)
  help     - Show this help message

Examples:
  python init_db.py init    # Initialize database
  python init_db.py reset   # Reset database (careful!)
  python init_db.py         # Same as 'init'

Prerequisites:
1. PostgreSQL must be running
2. Create a database (e.g., 'ai_planet_db')
3. Update DATABASE_URL in .env file:
   DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_planet_db
4. Install dependencies: pip install -r requirements.txt

Default Admin User:
  Email: admin@aiplanet.com
  Password: admin123
  (Change password after first login!)
""")

async def main():
    """
    Main function to handle command line arguments
    """
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "init"
    
    if command == "help":
        print_help()
    elif command == "init":
        success = await init_database()
        if success:
            print("\n🎉 Database initialization completed successfully!")
            print("📝 Don't forget to:")
            print("   1. Change the default admin password")
            print("   2. Update your .env file with proper API keys")
            print("   3. Set up your production database credentials")
        else:
            print("\n❌ Database initialization failed!")
            sys.exit(1)
    elif command == "reset":
        await reset_database()
    else:
        print(f"❌ Unknown command: {command}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())