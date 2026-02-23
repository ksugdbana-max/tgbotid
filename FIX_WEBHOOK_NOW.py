"""
QUICK WEBHOOK FIX - Set webhook correctly for Koyeb deployment
"""
import asyncio
from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Should be your Koyeb URL/webhook

async def fix_webhook():
    bot = Bot(token=BOT_TOKEN)
    
    print("\n" + "="*70)
    print("WEBHOOK FIX")
    print("="*70)
    
    # Delete old webhook first
    print("\n🗑️ Deleting old webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("  ✅ Old webhook deleted")
    
    if WEBHOOK_URL:
        print(f"\n📝 Setting new webhook: {WEBHOOK_URL}")
        result = await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        print(f"  ✅ Webhook set: {result}")
    else:
        print("\n⚠️ NO WEBHOOK_URL in .env - using polling mode")
    
    # Check webhook info
    print("\n📋 Current webhook info:")
    info = await bot.get_webhook_info()
    print(f"  URL: {info.url}")
    print(f"  Has custom certificate: {info.has_custom_certificate}")
    print(f"  Pending updates: {info.pending_update_count}")
    if info.last_error_message:
        print(f"  ❌ Last error: {info.last_error_message}")
        print(f"  ❌ Error date: {info.last_error_date}")
    else:
        print(f"  ✅ No errors!")
    
    await bot.session.close()
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(fix_webhook())
