"""
Script to delete all test accounts (fake phone numbers) from database
Only keeps real accounts added through admin panel
"""
import asyncio
from backend.database import async_session
from backend.models import Account
from sqlalchemy import select, delete

async def delete_test_accounts():
    """Delete test accounts with fake phone numbers"""
    async with async_session() as session:
        # Pattern: test accounts have phone numbers like +8123456001, +9123456002
        # Real accounts should have proper international format
        
        # Get all accounts
        stmt = select(Account)
        result = await session.execute(stmt)
        accounts = result.scalars().all()
        
        deleted = 0
        kept = 0
        
        for account in accounts:
            # Test account pattern check
            # Test accounts created by script have 6-digit repeating patterns
            if "123456" in account.phone_number:
                session.delete(account)
                print(f"🗑️  Deleted test account: {account.phone_number}")
                deleted += 1
            else:
                print(f"✅ Keeping real account: {account.phone_number}")
                kept += 1
        
        await session.commit()
        
        print(f"\n{'='*60}")
        print(f"✨ Cleanup Complete!")
        print(f"🗑️  Deleted: {deleted} test accounts")
        print(f"✅ Kept: {kept} real accounts")
        print(f"{'='*60}")

if __name__ == "__main__":
    print("🧹 Deleting Test Accounts...\n")
    asyncio.run(delete_test_accounts())
