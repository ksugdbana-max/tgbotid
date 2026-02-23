"""
SET VALUES USING SUPABASE CLIENT - This will work!
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_KEY not in .env!")
    exit(1)

# Your values
CHANNEL = "https://t.me/akhilportal"
USERNAME = "@akhilescrow"

print("\n" + "="*70)
print("SETTING IN SUPABASE")
print("="*70)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Delete old values
print("🗑️ Deleting old values...")
supabase.table("settings").delete().in_("key", ["bot_channel_link", "bot_owner_username"]).execute()

# Insert new values
print("📝 Inserting YOUR values...")
supabase.table("settings").insert({"key": "bot_channel_link", "value": CHANNEL}).execute()
supabase.table("settings").insert({"key": "bot_owner_username", "value": USERNAME}).execute()

# Verify
print("\n✅ Verifying...")
result = supabase.table("settings").select("*").in_("key", ["bot_channel_link", "bot_owner_username"]).execute()

for row in result.data:
    print(f"  ✅ {row['key']}: {row['value']}")

print("\n" + "="*70)
print("✅ DONE! Values set in Supabase!")
print("="*70)
print("\nWait 30 seconds, then test Support button!")
print("="*70)
