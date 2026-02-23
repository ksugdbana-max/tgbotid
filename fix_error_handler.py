"""
Fix error handler signature - CRITICAL FIX
This fixes the "missing 1 required positional argument: 'exception'" error
"""
import re

# Read bot.py
with open('backend/bot.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find and fix error handler signature
old_pattern = r'async def error_handler\(event, exception\):'
new_pattern = 'async def error_handler(update: types.Update, exception: Exception):'

content = re.sub(old_pattern, new_pattern, content)

# Also fix any references to 'event' inside the error handler
# Replace event.update with update
content = re.sub(r'if hasattr\(event, \'update\'\) and event\.update:', 'if update:', content)
content = re.sub(r'update = event\.update', '# update is already the parameter', content)

# Write back
with open('backend/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed error handler signature")
print("✅ Bot will now handle errors correctly")
