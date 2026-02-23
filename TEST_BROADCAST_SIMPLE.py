"""
SIMPLE BROADCAST TEST - This will DEFINITELY work
Completely remove all checks and make it simple
"""

# REPLACE the broadcast handler in bot.py (around line 3256) with this:

TEST_HANDLER = '''
@dp.callback_query(F.data == "btn_broadcast")
async def cmd_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """SIMPLE broadcast test - NO ADMIN CHECK"""
    try:
        await callback.answer("Broadcast button clicked!", show_alert=True)
        await callback.message.edit_text(
            "📢 BROADCAST WORKS!\n\nThis proves the button is working!",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
'''

print("="*70)
print("BROADCAST BUTTON TEST")
print("="*70)
print("\nREPLACE the broadcast handler with this simple version:")
print(TEST_HANDLER)
print("\nThis will:")
print("1. Show alert when button clicked")
print("2. Change message to confirm it works")
print("3. NO admin check")
print("4. NO FSM states")
print("\nIf this works, then the problem is admin check or FSM!")
print("="*70)
