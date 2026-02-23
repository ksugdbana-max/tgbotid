import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from backend.database import async_session
from backend.models import Settings
from sqlalchemy import select

# ⚠️ CHANGE THIS TO YOUR CHANNEL!
YOUR_CHANNEL_LINK = "https://t.me/YOURCHANNEL"  # ← EDIT THIS LINE!

async def set_channel_link():
    """Set the bot channel link for force join feature"""
    
    print("🔧 Setting Channel Link for Force Join...")
    print(f"Channel: {YOUR_CHANNEL_LINK}")
    print()
    
    async with async_session() as session:
        # Check if channel link setting exists
        result = await session.execute(
            select(Settings).where(Settings.key == "bot_channel_link")
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            # Update existing
            old_value = setting.value
            setting.value = YOUR_CHANNEL_LINK
            print(f"✅ Updated channel link")
            print(f"   Old: {old_value}")
            print(f"   New: {YOUR_CHANNEL_LINK}")
        else:
            # Create new
            new_setting = Settings(
                key="bot_channel_link",
                value=YOUR_CHANNEL_LINK
            )
            session.add(new_setting)
            print(f"✅ Created new channel link setting")
            print(f"   Value: {YOUR_CHANNEL_LINK}")
        
        await session.commit()
        print()
        print("✅ SAVED TO DATABASE!")
        print()
        print("📋 Next Steps:")
        print("1. Make sure your bot is admin in your channel")
        print("2. Add bot to channel with NO permissions")
        print("3. Test with /start from non-member account")
        print()
        print("Force join is now ACTIVE! 🔒")

if __name__ == "__main__":
    if "YOURCHANNEL" in YOUR_CHANNEL_LINK:
        print("❌ ERROR: You need to edit the script first!")
        print("   Change YOUR_CHANNEL_LINK to your actual channel")
        print("   Example: https://t.me/mychannel")
        print("   OR: @mychannel")
    else:
        asyncio.run(set_channel_link())
