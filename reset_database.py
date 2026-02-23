"""
Database Reset Script
This will DELETE ALL DATA from the database but keep the table structure intact.
Run this to get a fresh start without changing any code.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("❌ DATABASE_URL not found in environment variables!")
    print("Please make sure deploy.env is loaded or set DATABASE_URL")
    exit(1)

# Ensure async driver
if "postgresql" in DB_URL and "asyncpg" not in DB_URL:
    DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")

async def reset_database():
    """Delete all data from all tables in correct order"""
    
    engine = create_async_engine(DB_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    print("\n" + "="*60)
    print("⚠️  DATABASE RESET - ALL DATA WILL BE DELETED")
    print("="*60 + "\n")
    
    async with async_session() as session:
        try:
            # Delete in order to respect foreign key constraints
            # Child tables first, then parent tables
            
            print("🗑️  Deleting purchases...")
            await session.execute(text("DELETE FROM purchases"))
            
            print("🗑️  Deleting deposits...")
            await session.execute(text("DELETE FROM deposits"))
            
            print("🗑️  Deleting accounts...")
            await session.execute(text("DELETE FROM accounts"))
            
            print("🗑️  Deleting countries...")
            await session.execute(text("DELETE FROM countries"))
            
            print("🗑️  Deleting users...")
            await session.execute(text("DELETE FROM users"))
            
            print("🗑️  Deleting settings...")
            await session.execute(text("DELETE FROM settings"))
            
            # Commit the transaction
            await session.commit()
            
            print("\n" + "="*60)
            print("✅ DATABASE RESET COMPLETE!")
            print("="*60)
            print("\nAll data has been deleted. Tables structure intact.")
            print("Your code remains unchanged.\n")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during reset: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will DELETE ALL DATA from your database!")
    print("Tables will remain but all data will be lost.\n")
    
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm == "RESET":
        asyncio.run(reset_database())
    else:
        print("\n❌ Reset cancelled. Database unchanged.")
