"""
SIMPLE CHECK - What's in Supabase right now?
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Parse Supabase URL
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("ERROR: DATABASE_URL not in .env!")
    exit(1)

print("\n" + "="*70)
print("CHECKING SUPABASE VALUES")
print("="*70)

# Connect using psycopg2 (simpler)
conn = psycopg2.connect(database_url)
cur = conn.cursor()

# Check current values
print("\n📋 Current values:")
cur.execute("SELECT key, value FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username') ORDER BY key")
rows = cur.fetchall()

if not rows:
    print("  ⚠️ NO VALUES in database!")
else:
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

# Get user input to set
print("\n" + "="*70)
print("SET VALUES:")
channel = input("Channel link (https://t.me/...): ").strip()
owner = input("Owner username (@...): ").strip()

if channel and owner:
    # Delete old
    cur.execute("DELETE FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username')")
    
    # Insert new
    cur.execute("INSERT INTO settings (key, value) VALUES ('bot_channel_link', %s)", (channel,))
    cur.execute("INSERT INTO settings (key, value) VALUES ('bot_owner_username', %s)", (owner,))
    
    conn.commit()
    
    print("\n✅ SAVED TO SUPABASE!")
    print(f"  Channel: {channel}")
    print(f"  Owner: {owner}")
else:
    print("\n❌ Cancelled")

cur.close()
conn.close()

print("\n" + "="*70)
print("Wait 30 seconds, then test Support button!")
print("="*70)
