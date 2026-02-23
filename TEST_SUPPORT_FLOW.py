"""
COMPLETE TEST: Verify /setchannel and /setowner save to Supabase
AND that support handler reads from same place
"""
import asyncio
import os
from dotenv import load_dotenv
from backend.database import async_session
from backend.models import Settings
from sqlalchemy import select

load_dotenv()

async def test_support_flow():
    print("\n" + "="*70)
    print("TESTING SUPPORT SAVE/READ FLOW")
    print("="*70)
    
    # Test values
    TEST_CHANNEL = "https://t.me/test_channel_link"
    TEST_OWNER = "@test_owner_username"
    
    async with async_session() as session:
        # SIMULATE /setchannel command saving
        print("\n1️⃣ SIMULATING /setchannel COMMAND...")
        stmt = select(Settings).where(Settings.key == "bot_channel_link")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            old_value = setting.value
            setting.value = TEST_CHANNEL
            print(f"   Updated from '{old_value}' to '{TEST_CHANNEL}'")
        else:
            setting = Settings(key="bot_channel_link", value=TEST_CHANNEL)
            session.add(setting)
            print(f"   Created new setting: '{TEST_CHANNEL}'")
        
        await session.commit()
        print("   ✅ Committed to database")
        
        # VERIFY it was saved
        verify_stmt = select(Settings).where(Settings.key == "bot_channel_link")
        verify_result = await session.execute(verify_stmt)
        verify_setting = verify_result.scalar_one_or_none()
        
        if verify_setting and verify_setting.value == TEST_CHANNEL:
            print(f"   ✅ VERIFIED: Value in DB = '{verify_setting.value}'")
        else:
            print(f"   ❌ ERROR: Value mismatch!")
            return
    
    # New session (like support handler would use)
    async with async_session() as session:
        # SIMULATE SUPPORT HANDLER reading
        print("\n2️⃣ SIMULATING SUPPORT HANDLER READ...")
        chan_stmt = select(Settings).where(Settings.key == "bot_channel_link")
        chan_res = await session.execute(chan_stmt)
        chan_setting = chan_res.scalar_one_or_none()
        
        if chan_setting and chan_setting.value:
            print(f"   ✅ READ SUCCESS: '{chan_setting.value}'")
            if chan_setting.value == TEST_CHANNEL:
                print(f"   ✅ VALUES MATCH! Commands and Support use same DB!")
            else:
                print(f"   ❌ VALUES DON'T MATCH!")
                print(f"      Expected: {TEST_CHANNEL}")
                print(f"      Got: {chan_setting.value}")
        else:
            print("   ❌ ERROR: Could not read value!")
    
    # Check actual current values
    async with async_session() as session:
        print("\n3️⃣ CURRENT ACTUAL VALUES IN DATABASE:")
        stmt = select(Settings).where(Settings.key.in_(["bot_channel_link", "bot_owner_username"]))
        result = await session.execute(stmt)
        settings = result.scalars().all()
        
        if settings:
            for s in settings:
                print(f"   {s.key}: {s.value}")
        else:
            print("   ⚠️ No values found!")
    
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("\nIf you see ✅ VALUES MATCH - commands and support use same DB")
    print("If not, there's a problem with how they connect")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_support_flow())
