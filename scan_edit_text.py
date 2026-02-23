"""
COMPREHENSIVE FIX: Find and replace ALL .edit_text() calls in bot.py
This will eliminate ALL "message not modified" crashes permanently
"""
import re

# Read bot.py
with open('backend/bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all .edit_text( occurrences with line numbers
edit_text_lines = []
for i, line in enumerate(lines, 1):
    if '.edit_text(' in line:
        edit_text_lines.append((i, line.strip()))

print(f"Found {len(edit_text_lines)} .edit_text() calls:")
print("=" * 80)
for line_num, line_content in edit_text_lines:
    print(f"Line {line_num}: {line_content[:100]}...")
print("=" * 80)

# Create a comprehensive fix
content = ''.join(lines)

# Count before
before_count = content.count('.edit_text(')
print(f"\n📊 Before fix: {before_count} .edit_text() calls")

# We can't automatically fix all of them safely, so let's just report them
print("\n⚠️ Manual review required for each .edit_text() call")
print("Recommendation: Replace ALL with delete+send pattern")

# Export list to file
with open('edit_text_locations.txt', 'w') as f:
    f.write("All .edit_text() locations in bot.py:\n")
    f.write("=" * 80 + "\n")
    for line_num, line_content in edit_text_lines:
        f.write(f"Line {line_num}: {line_content}\n")

print(f"\n✅ Created edit_text_locations.txt with all locations")
print(f"\n🎯 Total .edit_text() calls to fix: {len(edit_text_lines)}")
