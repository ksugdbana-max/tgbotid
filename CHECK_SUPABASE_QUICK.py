"""
AUTO CHECK SUPABASE - Just shows what's there
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("ERROR: No DATABASE_URL")
    exit(1)

print("\n" + "="*70)
print("SUPABASE DATABASE CHECK")
print("="*70)

conn = psycopg2.connect(database_url)
cur = conn.cursor()

# Check current values
print("\n📋 Current values in Supabase:")
cur.execute("SELECT key, value FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username') ORDER BY key")
rows = cur.fetchall()

if not rows:
    print("  ⚠️ EMPTY - No values set!")
else:
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
print("\n" + "="*70)
