import requests
import time
import json

BOT_TOKEN = "8220540161:AAEDKjtZrmKimiXffkAHy0vG8KANCaOdS4E"
WEBHOOK_URL = "https://doubtful-chelsae-decstorroyal-43b44335.koyeb.app/webhook"

print("🔧 Fixing Bot Webhook...")
print()

# Step 1: Delete webhook
print("1️⃣ Deleting old webhook...")
r1 = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
    json={"drop_pending_updates": True}
)
print(f"   {r1.json()}")
time.sleep(2)

# Step 2: Set new webhook
print("\n2️⃣ Setting new webhook...")
r2 = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True,
        "allowed_updates": ["message", "callback_query"],
        "max_connections": 100
    }
)
print(f"   {r2.json()}")
time.sleep(2)

# Step 3: Verify
print("\n3️⃣ Verifying webhook...")
r3 = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
info = r3.json()
print(json.dumps(info, indent=2))

if info['result']['url']:
    print("\n✅ SUCCESS! Bot webhook is SET!")
    print(f"   URL: {info['result']['url']}")
    print("\n🎉 Send /start to your bot now - it should respond!")
else:
    print("\n❌ FAILED! Webhook is still empty!")
    print("   Check if Koyeb app is running and accessible")
