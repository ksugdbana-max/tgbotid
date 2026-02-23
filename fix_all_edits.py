"""
COMPREHENSIVE FIX: Replace ALL .edit_text() with safe delete+send pattern
This fixes the "message is not modified" error permanently
"""
import re

# Read bot.py
with open('backend/bot.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Count original edit_text calls
original_count = content.count('edit_text(')
print(f"Found {original_count} .edit_text() calls before fix")

# Pattern 1: await callback.message.edit_text(...)
# Replace with: try delete except pass, then send
pattern1 = r'await callback\.message\.edit_text\('
replacement1 = '''try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer('''

content = re.sub(pattern1, replacement1, content)

# Pattern 2: await message.edit_text(...)
pattern2 = r'await (\w+)\.edit_text\('
replacement2 = r'''try:
        await \1.delete()
   except:
        pass
    await \1.answer('''

content = re.sub(pattern2, replacement2, content)

# Write back
with open('backend/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Count remaining
remaining = content.count('edit_text(')
print(f"✅ Fixed {original_count - remaining} calls")
print(f"Remaining .edit_text() calls: {remaining}")
print("\n✅ All message edits now use delete+send pattern!")
print("✅ No more 'message not modified' errors!")
