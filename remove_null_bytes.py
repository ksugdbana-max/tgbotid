"""
EMERGENCY FIX: Remove null bytes from corrupted files
This is why all Koyeb deployments are failing!
"""

import os

files_to_fix = ['backend/bot.py', 'backend/main.py']

for filepath in files_to_fix:
    print(f"\nFixing {filepath}...")
    
    # Read with error handling
    with open(filepath, 'rb') as f:
        content_bytes = f.read()
    
    # Remove null bytes
    cleaned_bytes = content_bytes.replace(b'\x00', b'')
    
    # Count removed
    null_count = len(content_bytes) - len(cleaned_bytes)
    
    # Write back
    with open(filepath, 'wb') as f:
        f.write(cleaned_bytes)
    
    print(f"✅ Removed {null_count} null bytes from {filepath}")

print("\n✅ All files cleaned!")
print("✅ Files should now compile without errors!")
