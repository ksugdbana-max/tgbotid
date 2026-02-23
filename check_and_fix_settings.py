"""
Check and fix channel link and owner username in database
"""
import asyncio
from backend.database import async_session
from backend.models import Settings
from sqlalchemy import select

async def check_and_fix_settings():
    async with async_session() as session:
        # Check channel link
        chan_stmt = select(Settings).where(Settings.key == "bot_channel_link")
        chan_res = await session.execute(chan_stmt)
        chan_setting = chan_res.scalar_one_or_none()
        
        print(f"📢 Current Channel Link: {chan_setting.value if chan_setting else 'NOT SET'}")
        
        # Check owner username  
        owner_stmt = select(Settings).where(Settings.key == "bot_owner_username")
        owner_res = await session.execute(owner_stmt)
        owner_setting = owner_res.scalar_one_or_none()
        
        print(f"👤 Current Owner Username: {owner_setting.value if owner_setting else 'NOT SET'}")
        
        # Fix if placeholder values found
        if chan_setting and chan_setting.value in ["@YourChannel", "", None, "https://t.me/yourchannel"]:
            print("\n⚠️ PLACEHOLDER DETECTED in channel link!")
            new_link = input("Enter your REAL channel link (e.g., https://t.me/actualchannel): ")
            chan_setting.value = new_link
            await session.commit()
            print(f"✅ Updated channel link to: {new_link}")
        
        if owner_setting and owner_setting.value in ["@YourChannel", "", None, "@yourusername"]:
            print("\n⚠️ PLACEHOLDER DETECTED in owner username!")
            new_owner = input("Enter your REAL owner username (e.g., @yourname): ")
            owner_setting.value = new_owner
            await session.commit()
            print(f"✅ Updated owner username to: {new_owner}")
        
        if not chan_setting or not owner_setting:
            print("\n⚠️ Settings not found in database!")
            if not chan_setting:
                new_link = input("Channel link not set. Enter it now: ")
                session.add(Settings(key="bot_channel_link", value=new_link))
            if not owner_setting:
                new_owner = input("Owner username not set. Enter it now: ")
                session.add(Settings(key="bot_owner_username", value=new_owner))
            await session.commit()
            print("✅ Settings created!")

if __name__ == "__main__":
    asyncio.run(check_and_fix_settings())
