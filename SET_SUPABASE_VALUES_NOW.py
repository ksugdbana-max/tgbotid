"""
CHECK AND SET SUPABASE VALUES - See what's in database and set YOUR values
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def check_and_set_supabase():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env!")
        return
    
    print("\n" + "="*70)
    print("🔍 CHECKING SUPABASE DATABASE")
    print("="*70)
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Check what's currently there
        print("\n📋 Current values in Supabase:")
        result = conn.execute(text("SELECT key, value FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username') ORDER BY key"))
        rows = result.fetchall()
        
        if not rows:
            print("  ⚠️ NO VALUES FOUND!")
        else:
            for row in rows:
                print(f"  {row[0]}: {row[1]}")
        
        # Get user input
        print("\n" + "="*70)
        print("SET YOUR VALUES NOW:")
        print("="*70)
        
        channel_link = input("\n📢 Enter YOUR channel link (e.g., https://t.me/mychannel): ").strip()
        owner_username = input("👤 Enter YOUR username (e.g., @myname): ").strip()
        
        if not channel_link or not owner_username:
            print("\n❌ Both values required!")
            return
        
        # Delete old values
        print("\n🗑️ Removing old values...")
        conn.execute(text("DELETE FROM settings WHERE key = 'bot_channel_link'"))
        conn.execute(text("DELETE FROM settings WHERE key = 'bot_owner_username'"))
        
        # Insert new values
        print("📝 Inserting YOUR values...")
        conn.execute(text("INSERT INTO settings (key, value) VALUES ('bot_channel_link', :channel)"), {"channel": channel_link})
        conn.execute(text("INSERT INTO settings (key, value) VALUES ('bot_owner_username', :owner)"), {"owner": owner_username})
        
        conn.commit()
        
        # Verify
        print("\n✅ Verifying...")
        result = conn.execute(text("SELECT key, value FROM settings WHERE key IN ('bot_channel_link', 'bot_owner_username') ORDER BY key"))
        rows = result.fetchall()
        
        for row in rows:
            print(f"  ✅ {row[0]}: {row[1]}")
    
    print("\n" + "="*70)
    print("✅ SUPABASE UPDATED!")
    print("="*70)
    print("\n1. Wait 30 seconds for Koyeb to restart")
    print("2. Click 'Support' button")
    print("3. Should show YOUR values!")
    print("\n" + "="*70)

if __name__ == "__main__":
    check_and_set_supabase()
