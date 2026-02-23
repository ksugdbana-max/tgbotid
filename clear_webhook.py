import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("BOT_TOKEN")
    bot = Bot(token=token)
    print("Deleting webhook and dropping pending updates...")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    print("Done! Webhook cleared. ✅")

if __name__ == "__main__":
    asyncio.run(main())
