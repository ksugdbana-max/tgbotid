"""
Quick webhook checker to diagnose bot unresponsiveness
"""
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def check_webhook():
    """Check current webhook configuration"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            
            if data.get("ok"):
                info = data.get("result", {})
                print("\n" + "="*50)
                print("WEBHOOK STATUS")
                print("="*50)
                print(f"URL: {info.get('url', 'NOT SET')}")
                print(f"Has Custom Certificate: {info.get('has_custom_certificate', False)}")
                print(f"Pending Update Count: {info.get('pending_update_count', 0)}")
                print(f"Last Error Date: {info.get('last_error_date', 'None')}")
                print(f"Last Error Message: {info.get('last_error_message', 'None')}")
                print(f"Max Connections: {info.get('max_connections', 'Default')}")
                print("="*50)
                
                # Diagnosis
                if not info.get('url'):
                    print("\n❌ PROBLEM: Webhook URL not set!")
                    print("Solution: Redeploy on Koyeb or run: python fix_webhook.py")
                elif info.get('last_error_message'):
                    print(f"\n⚠️ WARNING: Webhook has errors!")
                    print(f"Error: {info.get('last_error_message')}")
                elif info.get('pending_update_count', 0) > 100:
                    print(f"\n⚠️ WARNING: {info.get('pending_update_count')} pending updates!")
                    print("Bot might be crashed or not processing updates.")
                else:
                    print("\n✅ Webhook looks healthy!")
            else:
                print(f"\n❌ API ERROR: {data}")

if __name__ == "__main__":
    asyncio.run(check_webhook())
