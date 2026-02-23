import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def verify_connection():
    db_url = os.getenv("DATABASE_URL")
    print(f"Testing Connection to: {db_url.split('@')[-1]}") # Hide password
    
    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connection Successful!")
            print(f"Database Version: {version}")
            
            # Check if tables exist
            result = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';"))
            tables = result.scalars().all()
            print(f"Existing Tables: {tables}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_connection())
