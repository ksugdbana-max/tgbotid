"""
Delete test accounts from PRODUCTION database (Supabase)
"""
import asyncio
from backend.database import async_session
from backend.models import Account
from sqlalchemy import delete

async def delete_production_test_accounts():
    """Delete all test accounts with pattern '123456' in phone number"""
    async with async_session() as session:
        # Delete all accounts with pattern "123456" in phone number
        # This catches test accounts like +8123456001, +9123456002, etc.
        stmt = delete(Account).where(Account.phone_number.contains("123456"))
        result = await session.execute(stmt)
        await session.commit()
        
        deleted_count = result.rowcount
        
        print("="*60)
        print(f"✨ Production Database Cleanup Complete!")
        print(f"🗑️  Deleted: {deleted_count} test accounts")
        print(f"✅ Database is now clean!")
        print("="*60)
        
        return deleted_count

if __name__ == "__main__":
    print("🧹 Deleting Test Accounts from PRODUCTION Database...\n")
    asyncio.run(delete_production_test_accounts())
