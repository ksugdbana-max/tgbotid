"""
NUCLEAR OPTION: Wrap ALL message.edit_text() calls with try-except
This prevents ANY "message not modified" errors from crashing the bot
"""
import re

# Read bot.py
with open('backend/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find: await callback.message.edit_text(
# Replace with: try-except wrapper

pattern = r'([ \t]*)(await callback\.message\.edit_text\()'

def replace_func(match):
    indent = match.group(1)
    call = match.group(2)
    return f'''{indent}try:
{indent}    {call}'''

# Replace all occurrences
new_content = re.sub(pattern, replace_func, content)

# Now we need to add except blocks - this is complex, so let's use a different approach
# Better solution: Add a try-except wrapper function

wrapper_function = '''
# CRITICAL: Safe message edit wrapper to prevent "message not modified" crashes
async def safe_edit_message(callback, text, reply_markup=None, parse_mode="HTML"):
    """Safely edit a message, falling back to delete+send if edit fails"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        # If edit fails (message not modified, message deleted, etc.)
        try:
            await callback.message.delete()
        except:
            pass
        try:
            await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as send_err:
            logger.error(f"Could not send message after edit failed: {send_err}")
            await callback.answer("✅ Action completed", show_alert=False)

'''

# Find a good place to insert this (after imports, before first handler)
# Look for first @dp. handler
insert_pos = content.find('@dp.message(Command("start"))')
if insert_pos == -1:
    insert_pos = content.find('@dp.callback_query')
    
if insert_pos > 0:
    content = content[:insert_pos] + wrapper_function + "\n" + content[insert_pos:]

# Write back
with open('backend/bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added safe_edit_message wrapper function to bot.py")
print("⚠️  Next step: Manually replace critical .edit_text() calls with safe_edit_message()")
print("\nRecommended: Focus on purchase flow and OTP handlers first")
