"""
Check if database still has unique constraint on phone_number
Run this to see the actual constraint in production DB
"""
import asyncio
from backend.database import async_session, engine
from sqlalchemy import text

async def check_constraints():
    async with async_session() as session:
        # Check PostgreSQL constraints on accounts table
        result = await session.execute(text("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'accounts' 
            AND constraint_type = 'UNIQUE';
        """))
        
        constraints = result.fetchall()
        
        if constraints:
            print("⚠️ FOUND UNIQUE CONSTRAINTS:")
            for constraint in constraints:
                print(f"  - {constraint[0]} ({constraint[1]})")
            print("\n❌ Database still has unique constraint!")
            print("Run: python migrate_remove_phone_unique.py")
        else:
            print("✅ No unique constraints on accounts table")
            print("✅ Database allows duplicate phone numbers!")

if __name__ == "__main__":
    asyncio.run(check_constraints())
