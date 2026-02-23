"""
DIRECT CHECK: What's actually in Supabase right now?
"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE credentials not in .env!")
    exit(1)

print("\n" + "="*70)
print("DIRECT SUPABASE CHECK")
print("="*70)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get current values
result = supabase.table("settings").select("*").in_("key", ["bot_channel_link", "bot_owner_username"]).execute()

print("\n📋 CURRENT VALUES IN SUPABASE:")
if result.data:
    for row in result.data:
        print(f"  {row['key']}: {row['value']}")
else:
    print("  ⚠️ NO VALUES FOUND!")

print("\n" + "="*70)
print("PROBLEM IDENTIFIED:")
print("="*70)

if not result.data:
    print("\n❌ VALUES ARE MISSING FROM SUPABASE!")
    print("\nREASONS:")
    print("1. Commands saved to LOCAL database, not Supabase")
    print("2. Bot on Koyeb uses Supabase, but local bot uses local DB")
    print("3. Need to set values DIRECTLY in Supabase")
    print("\nSOLUTION:")
    print("Run: python SET_SUPABASE_CLIENT.py")
    print("This sets values directly in Supabase")
elif any("yourchannel" in row['value'].lower() or "akhilportal" in row['value'].lower() for row in result.data if row['value']):
    print("\n❌ OLD PLACEHOLDER VALUES STILL IN SUPABASE!")
    print("\nSOLUTION:")
    print("Run: python SET_SUPABASE_CLIENT.py")
    print("This replaces placeholders with your real values")
else:
    print("\n✅ VALUES LOOK CORRECT IN SUPABASE!")
    print("\nIf support still shows wrong values:")
    print("1. Koyeb might not be redeployed")
    print("2. Bot might be caching values")
    print("3. Check Koyeb logs for errors")

print("="*70)
