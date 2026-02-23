"""
SET YOUR VALUES IN SUPABASE NOW
Channel: https://t.me/akhilportal
Username: @akhilescrow
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("ERROR: No DATABASE_URL")
    exit(1)

# Your values
CHANNEL = "https://t.me/akhilportal"
USERNAME = "@akhilescrow"

print("\n" + "="*70)
print("SETTING YOUR VALUES IN SUPABASE")
print("="*70)
print(f"Channel: {CHANNEL}")
print(f"Username: {USERNAME}")

engine = create_engine(database_url, pool_pre_ping=True)

with engine.begin() as conn:
    # Delete old values
    print("\n🗑️ Removing old values...")
    conn.execute(text("DELETE FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username')"))
    
    # Insert YOUR values
    print("📝 Inserting YOUR values...")
    conn.execute(text("INSERT INTO settings (key, value) VALUES ('bot_channel_link', :channel)"), {"channel": CHANNEL})
    conn.execute(text("INSERT INTO settings (key, value) VALUES ('bot_owner_username', :owner)"), {"owner": USERNAME})
    
    # Verify
    print("\n✅ Verifying...")
    result = conn.execute(text("SELECT key, value FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username') ORDER BY key"))
    rows = result.fetchall()
    
    for row in rows:
        print(f"  ✅ {row[0]}: {row[1]}")

print("\n" + "="*70)
print("✅ SUPABASE UPDATED SUCCESSFULLY!")
print("="*70)
print("\nNow:")
print("1. Wait 30 seconds (Koyeb restarts automatically)")
print("2. Click 'Support' button in bot")
print("3. Should show YOUR channel and username!")
print("\n" + "="*70)
