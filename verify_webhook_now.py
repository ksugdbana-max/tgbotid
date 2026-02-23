"""
Force verify and reset Telegram webhook
"""
import requests

BOT_TOKEN = "8220540161:AAEDKjtZrmKimiXffkAHy0vG8KANCaOdS4E"
WEBHOOK_URL = "https://doubtful-chelsae-decstorroyal-43b44335.koyeb.app/webhook"

print("🔍 Checking current webhook status...")
info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
info = info_response.json()

if info['ok']:
    result = info['result']
    print(f"\n📊 Current Status:")
    print(f"URL: {result.get('url', 'NOT SET')}")
    print(f"Pending: {result.get('pending_update_count', 0)}")
    print(f"Last Error: {result.get('last_error_message', 'None')}")
    print(f"Last Error Date: {result.get('last_error_date', 'None')}")
    
    if result.get('url') != WEBHOOK_URL:
        print(f"\n⚠️ MISMATCH! Expected: {WEBHOOK_URL}")
        print(f"            Got: {result.get('url')}")
        
        print("\n🔄 Fixing webhook...")
        # Delete
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
        
        # Set new
        set_response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": WEBHOOK_URL, "drop_pending_updates": True}
        )
        print(f"Set result: {set_response.json()}")
        
        # Verify
        verify = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
        v_result = verify.json()['result']
        print(f"\n✅ New URL: {v_result.get('url')}")
        print(f"✅ Pending: {v_result.get('pending_update_count')}")
        print("\n🎯 Try /start now!")
    else:
        print("\n✅ Webhook URL correct!")
        print("Try sending /start to the bot.")
