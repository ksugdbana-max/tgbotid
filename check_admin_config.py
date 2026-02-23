"""
Quick diagnostic: Test if commands work locally
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("COMMAND DIAGNOSTICS")
print("=" * 60)

# Check environment variable
admin_id = os.getenv("ADMIN_TELEGRAM_ID", "NOT_SET")
print(f"\nADMIN_TELEGRAM_ID: {admin_id}")

# Check if it's a valid number
if admin_id != "NOT_SET":
    try:
        admin_int = int(admin_id)
        print(f"✅ Valid admin ID: {admin_int}")
    except:
        print(f"❌ INVALID! '{admin_id}' is not a number!")
else:
    print("❌ NOT SET! Commands won't work without this!")

print("\n" + "=" * 60)
print("WHAT TO CHECK IN KOYEB:")
print("=" * 60)
print("1. Environment variable ADMIN_TELEGRAM_ID must be set")
print("2. Must be YOUR Telegram user ID (number)")
print("3. Get your ID: /start your bot, check logs")
print("\nIf ADMIN_TELEGRAM_ID is wrong, commands will say 'admin-only'")
