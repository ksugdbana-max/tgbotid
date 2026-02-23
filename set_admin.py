import asyncio
from backend.database import async_session
from backend.models import User
from sqlalchemy import select, update

async def set_admin(tg_id: int):
    async with async_session() as session:
        telegram_id = 7390087516  # User provided ID
        print(f"Processing Admin: {telegram_id}")
        
        # Check if user exists, if not create them
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("User not found. Creating new user...")
            user = User(
                telegram_id=telegram_id,
                username="admin_user",
                full_name="Admin",
                balance=0.0
            )
            session.add(user)
            await session.commit()
            print("User created.")
            
        # Update to ADMIN
        user.role = "ADMIN"
        # user.password_hash = ... (If using password login, otherwise telegram auth is sufficient for now)
        await session.commit()
        print(f"Successfully set {tg_id} as admin! ✅")

if __name__ == "__main__":
    tg_id = 7390087516
    asyncio.run(set_admin(tg_id))
