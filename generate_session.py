"""
Telegram Session Generator
Simple tool to create session strings for phone numbers
"""

import asyncio
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Your API credentials from .env
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

print("=" * 60)
print("🔐 TELEGRAM SESSION GENERATOR")
print("=" * 60)
print()

if not API_ID or not API_HASH:
    print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH not found in .env")
    exit(1)

print(f"✅ API ID: {API_ID}")
print(f"✅ API Hash: {API_HASH[:10]}...")
print()

# Get phone number from user
phone_number = input("📱 Enter phone number (with country code, e.g., +91 9876543210): ").strip()

if not phone_number.startswith("+"):
    print("⚠️  Adding + to phone number...")
    phone_number = "+" + phone_number

print(f"\n📞 Phone number: {phone_number}")
print("\n" + "=" * 60)
print("⚠️  IMPORTANT INSTRUCTIONS:")
print("=" * 60)
print("1. You will be asked for OTP code from Telegram")
print("2. Check your Telegram app for the code")
print("3. Enter the code when prompted")
print("4. If you have 2FA, enter your password")
print("5. Session string will be generated")
print("=" * 60)
print()

input("Press ENTER to continue...")

async def generate_session():
    """Generate session string for a phone number"""
    
    # Clean phone number for session name
    session_name = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    
    # Create Pyrogram client
    client = Client(
        name=f"session_{session_name}",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone_number,
        in_memory=True  # Don't save .session file
    )
    
    try:
        print("\n🔄 Connecting to Telegram...")
        await client.start()
        
        # Get user info
        me = await client.get_me()
        
        print("\n✅ Login successful!")
        print(f"👤 Name: {me.first_name} {me.last_name or ''}")
        print(f"🆔 User ID: {me.id}")
        print(f"📱 Phone: {me.phone_number}")
        if me.username:
            print(f"👉 Username: @{me.username}")
        
        # Export session string
        session_string = await client.export_session_string()
        
        print("\n" + "=" * 60)
        print("🎉 SESSION GENERATED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("📋 Your session string:")
        print("-" * 60)
        print(session_string)
        print("-" * 60)
        print()
        print("💾 SAVE THIS SESSION STRING TO:")
        print("   - Admin Panel → Accounts → Session Data field")
        print("   - Keep it SECURE (don't share publicly)")
        print()
        
        # Save to file for convenience
        output_file = f"session_{session_name}.txt"
        with open(output_file, "w") as f:
            f.write(f"Phone: {phone_number}\n")
            f.write(f"Name: {me.first_name} {me.last_name or ''}\n")
            f.write(f"Session String:\n{session_string}\n")
        
        print(f"✅ Also saved to: {output_file}")
        print()
        
        await client.stop()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCommon issues:")
        print("- Wrong phone number")
        print("- Incorrect OTP code")
        print("- Wrong 2FA password")
        print("- Phone number already has too many apps")
        print("\nTry again!")

# Run the generator
asyncio.run(generate_session())

print("\n" + "=" * 60)
print("🏁 Session generation complete!")
print("=" * 60)
