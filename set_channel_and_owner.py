"""Quick script to set channel and owner values"""
import asyncio
from backend.database import async_session
from backend.models import Settings
from sqlalchemy import select

async def set_values():
    # GET USER INPUT
    print("\n" + "="*50)
    print("SET CHANNEL LINK AND OWNER USERNAME")
    print("="*50)
    
    channel = input("\nEnter Channel Link (e.g., https://t.me/yourchannel): ").strip()
    owner = input("Enter Owner Username (e.g., @yourusername): ").strip()
    
    async with async_session() as session:
        # Update Channel Link
        stmt = select(Settings).where(Settings.key == "bot_channel_link")
        res = await session.execute(stmt)
        setting = res.scalar_one_or_none()
        
        if setting:
            setting.value = channel
            print(f"\n✅ UPDATED channel_link: {channel}")
        else:
            session.add(Settings(key="bot_channel_link", value=channel))
            print(f"\n✅ CREATED channel_link: {channel}")
        
        # Update Owner Username  
        stmt2 = select(Settings).where(Settings.key == "bot_owner_username")
        res2 = await session.execute(stmt2)
        setting2 = res2.scalar_one_or_none()
        
        if setting2:
            setting2.value = owner
            print(f"✅ UPDATED owner_username: {owner}")
        else:
            session.add(Settings(key="bot_owner_username", value=owner))
            print(f"✅ CREATED owner_username: {owner}")
        
        await session.commit()
        print("\n" + "="*50)
        print("SUCCESS! Settings saved to database.")
        print("="*50)
        print("\nNow REDEPLOY on Koyeb to apply changes!")

if __name__ == "__main__":
    asyncio.run(set_values())
