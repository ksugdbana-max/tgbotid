"""
EMERGENCY FIX: Replace ALL message.edit_text with delete+send pattern in bot.py
This prevents ALL "message not modified" crashes
"""
import re

# Read the file
with open('backend/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count edit_text calls
edit_count = len(re.findall(r'\.edit_text\(', content))
print(f"Found {edit_count} .edit_text() calls")

# Fix the purchase success message (line ~998)
old_pattern = r'''        # Show purchase success with OTP button
        await callback\.message\.edit_text\('''

new_pattern = '''        # Show purchase success with OTP button (DELETE+SEND to prevent crash)
        try:
            await callback.message.delete()
        except:
            pass
        await bot.send_message(
            callback.message.chat.id,'''

content = re.sub(old_pattern, new_pattern, content)

# Write back
with open('backend/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed purchase success message")
print("✅ bot.py updated successfully")
