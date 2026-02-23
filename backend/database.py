
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase / Postgres requires asyncpg driver
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    # Fallback to local sqlite if no env var
    DB_URL = "sqlite+aiosqlite:///./bot_db.db"

# Ensure async driver is used
if "postgresql" in DB_URL and "asyncpg" not in DB_URL:
    DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# Engine options
engine_kwargs = {
    "echo": True
}

# Only add pooling arguments for PostgreSQL (SQLite doesn't support them)
if "postgresql" in DB_URL:
    engine_kwargs.update({
        "pool_size": 40,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 15
    })

engine = create_async_engine(DB_URL, **engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all) # Careful with this
            await conn.run_sync(Base.metadata.create_all)
        print("✅ DATABASE: Successfully connected to Supabase/Postgres!", flush=True)
    except Exception as e:
        print(f"❌ DATABASE ERROR: Could not connect to database: {e}", flush=True)
