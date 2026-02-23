

@dp.callback_query(F.data.startswith("terminate_all_"))
async def terminate_all_handler(callback: types.CallbackQuery):
    """Terminate all other devices except current"""
    try:
        account_id = int(callback.data.split("_")[2])
        
        # Get account
        async with async_session() as session:
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found!", show_alert=True)
                return
        
        # Terminate all using Pyrogram
        try:
            from backend.pyrogram_devices import terminate_all_except_current
            api_id = int(os.getenv("API_ID", "0"))
            api_hash = os.getenv("API_HASH", "")
            await terminate_all_except_current(account.session_data, api_id, api_hash)
            
            await callback.answer("✅ All devices terminated!", show_alert=True)
            
            text = "✅ <b>All Other Devices Terminated</b>\n\n"
            text += "All other devices have been logged out.\n\n"
            text += "<i>Only the current device remains active.</i>"
            
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="📱 View Devices", callback_data=f"manage_devices_{account_id}"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Pyrogram error: {e}")
            await callback.answer(f"❌ Failed: {str(e)[:50]}", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Terminate all error: {e}", exc_info=True)
        await callback.answer("❌ Error!", show_alert=True)
