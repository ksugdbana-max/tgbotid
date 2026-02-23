"""
Emergency fix: Define safe_send BEFORE it's used in handlers
Currently safe_send might be undefined when btn_accounts tries to call it
"""

# The issue: safe_send is not defined early enough in bot.py
# Need to move it right after error handler, before any handlers that use it

print("""
SOLUTION:
Move safe_send helper function to line ~72 (right after error_handler)
Before all the keyboard functions and handlers

This ensures it's available when btn_accounts and other handlers try to use it.
""")
