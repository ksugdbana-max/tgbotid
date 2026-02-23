"""
EMERGENCY BOT DIAGNOSTICS - Check all critical issues
"""
import sys
import os

print("\n" + "="*70)
print("BOT STARTUP DIAGNOSTICS")
print("="*70)

# Check Python version
print(f"\n1. Python Version: {sys.version}")

# Check critical imports
print("\n2. Checking Critical Imports...")
try:
    from aiogram import Bot, Dispatcher
    print("   ✅ aiogram")
except Exception as e:
    print(f"   ❌ aiogram: {e}")

try:
    from sqlalchemy.ext.asyncio import create_async_engine
    print("   ✅ sqlalchemy")
except Exception as e:
    print(f"   ❌ sqlalchemy: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✅ dotenv")
except Exception as e:
    print(f"   ❌ dotenv: {e}")

# Check environment variables
print("\n3. Critical Environment Variables:")
env_vars = ['BOT_TOKEN', 'DATABASE_URL', 'ADMIN_TELEGRAM_ID', 'BASE_WEBHOOK_URL']
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"   ✅ {var}: {value[:30]}...")
    else:
        print(f"   ❌ {var}: NOT SET")

# Try importing bot
print("\n4. Trying to import backend.bot...")
try:
    from backend import bot
    print("   ✅ backend.bot imported successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try importing main
print("\n5. Trying to import backend.main...")
try:
    from backend import main
    print("   ✅ backend.main imported successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)
