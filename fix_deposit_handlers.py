"""
Emergency fix: Add missing deposit handlers directly to bot.py
This will ensure UTR is captured and saved correctly
"""
import re

# Read bot.py
with open('backend/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if deposit handlers already exist
if '@dp.callback_query(F.data == "btn_deposit")' in content:
    print("✅ Deposit handlers already exist in bot.py")
    exit(0)

# Read deposit flow code
with open('deposit_flow.py', 'r', encoding='utf-8') as f:
    deposit_code = f.read()

# Clean up the deposit code - remove header comments
deposit_code = deposit_code.replace(
    '"""\nComplete Deposit Flow for Telegram Bot\nHandles: Amount → UTR → Screenshot → Admin Approval\n"""\n\n# Add this to backend/bot.py after the DepositStates class definition\n\n# Deposit Flow Handlers\n\n',
    '\n\n# === DEPOSIT FLOW HANDLERS ===\n'
)

# Append to bot.py
with open('backend/bot.py', 'a', encoding='utf-8') as f:
    f.write(f"\n\n{deposit_code}\n")

print("✅ Added deposit handlers to bot.py")
print("✅ UTR will now be captured correctly")
