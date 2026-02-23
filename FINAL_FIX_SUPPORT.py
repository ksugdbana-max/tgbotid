"""
FINAL FIX: Set your actual values in Supabase
This ensures support links work correctly
"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# YOUR ACTUAL VALUES
CHANNEL = "https://t.me/akhilportal"
OWNER = "@akhilescrow"

print("\n" + "="*70)
print("FINAL FIX: SETTING SUPPORT VALUES IN SUPABASE")
print("="*70)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Delete ALL old values first
print("\n🗑️ Clearing old values...")
supabase.table("settings").delete().in_("key", ["bot_channel_link", "bot_owner_username"]).execute()

# Set YOUR values
print(f"📝 Setting channel: {CHANNEL}")
supabase.table("settings").insert({"key": "bot_channel_link", "value": CHANNEL}).execute()

print(f"📝 Setting owner: {OWNER}")
supabase.table("settings").insert({"key": "bot_owner_username", "value": OWNER}).execute()

# Verify
print("\n✅ Verifying...")
result = supabase.table("settings").select("*").in_("key", ["bot_channel_link", "bot_owner_username"]).execute()

for row in result.data:
    print(f"  ✅ {row['key']}: {row['value']}")

print("\n" + "="*70)
print("✅ COMPLETE!")
print("="*70)
print("\nNOW:")
print("1. Redeploy on Koyeb (if not already done)")
print("2. Wait 30 seconds")
print("3. Click 'Support' button")
print("4. Should show YOUR values!")
print("\n" + "="*70)
