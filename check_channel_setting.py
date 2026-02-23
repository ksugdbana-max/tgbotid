import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from backend.database import async_session
from backend.models import Settings
from sqlalchemy import select

async def check_settings():
    async with async_session() as session:
        # Check if channel link is set
        result = await session.execute(
            select(Settings).where(Settings.key == "bot_channel_link")
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            print(f"✅ Channel Link IS SET: {setting.value}")
        else:
            print("❌ Channel Link NOT SET in database!")
            print("\nYou need to:")
            print("1. Go to admin panel")
            print("2. Payment Settings")
            print("3. Set 'Channel Link' to your channel URL")
            print("   Example: https://t.me/yourchannel")

asyncio.run(check_settings())
