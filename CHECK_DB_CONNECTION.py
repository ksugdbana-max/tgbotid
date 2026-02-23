"""
CHECK: Which database is bot actually using?
This will show if bot is connected to Supabase or local DB
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("DATABASE CONNECTION CHECK")
print("="*70)

database_url = os.getenv("DATABASE_URL")
supabase_url = os.getenv("SUPABASE_URL")

print(f"\nDATABASE_URL: {database_url[:50] if database_url else 'NOT SET'}...")
print(f"SUPABASE_URL: {supabase_url[:50] if supabase_url else 'NOT SET'}...")

if database_url:
    if "supabase" in database_url.lower():
        print("\n✅ Bot IS using Supabase!")
    else:
        print("\n❌ Bot is using LOCAL database!")
        print("   This is why commands don't update!")
else:
    print("\n❌ DATABASE_URL not set!")

print("\n" + "="*70)
print("SOLUTION:")
print("="*70)
if database_url and "supabase" not in database_url.lower():
    print("\n1. Make sure DATABASE_URL in .env points to Supabase")
    print("2. Or set it on Koyeb environment variables")
    print("3. Restart/redeploy bot")
elif not database_url:
    print("\n1. Add DATABASE_URL to .env file")
    print("2. Point it to your Supabase database")
    print("3. Restart bot")
else:
    print("\n✅ Connection looks correct!")
    print("Issue might be elsewhere - check if commands are working")

print("="*70)
