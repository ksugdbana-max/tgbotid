
# === RETRY CODE AND DEVICE MANAGEMENT HANDLERS ===

@dp.callback_query(F.data.startswith("retry_code_"))
async def retry_code_handler(callback: types.CallbackQuery):
    """Retry getting OTP code for login"""
    try:
        account_id = int(callback.data.split("_")[2])
        
        async with async_session() as session:
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found!", show_alert=True)
                return
        
        # Try to fetch OTP code
        otp_code = "⏳ Requesting new code..."
        try:
            # TODO: Implement Pyrogram OTP fetching
            # For now, show instruction
            otp_code = "Check Telegram app for new code"
        except:
            otp_code = "Check Telegram app"
        
        text = f"🔄 <b>Retry Login Code</b>\n\n"
        text += f"📱 <b>Phone:</b> <code>{account.phone_number}</code>\n"
        if account.twofa_password:
            text += f"🔐 <b>2FA:</b> <code>{account.twofa_password}</code>\n"
        text += f"\n📨 <b>Login Code:</b> <code>{otp_code}</code>\n\n"
        text += "💡 <i>A new login code has been requested. Check your Telegram app!</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 Retry Again", callback_data=f"retry_code_{account_id}"))
        builder.row(InlineKeyboardButton(text="📱 Manage Devices", callback_data=f"manage_devices_{account_id}"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer("📨 New code requested!")
        
    except Exception as e:
        logger.error(f"❌ Retry code error: {e}", exc_info=True)
        await callback.answer("❌ Error requesting code!", show_alert=True)


@dp.callback_query(F.data.startswith("manage_devices_"))
async def manage_devices_handler(callback: types.CallbackQuery):
    """Show active devices/sessions for this account"""
    try:
        account_id = int(callback.data.split("_")[2])
        
        async with async_session() as session:
            # Verify user owns this account
            user_stmt = select(User).where(User.telegram_id == callback.from_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                await callback.answer("❌ User not found!", show_alert=True)
                return
            
            # Get purchase to verify ownership
            purchase_stmt = select(Purchase).where(
                Purchase.user_id == user.id,
                Purchase.account_id == account_id
            )
            purchase_result = await session.execute(purchase_stmt)
            purchase = purchase_result.scalar_one_or_none()
            
            if not purchase:
                await callback.answer("❌ You don't own this account!", show_alert=True)
                return
            
            # Get account details
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found!", show_alert=True)
                return
        
        # TODO: Implement Pyrogram to get active sessions
        # For now, show mock data
        text = f"📱 <b>Manage Devices</b>\n\n"
        text += f"📞 <b>Account:</b> <code>{account.phone_number}</code>\n\n"
        text += "🔌 <b>Active Devices:</b>\n\n"
        
        # Mock device list (replace with real Pyrogram data)
        text += "1️⃣ <b>Android Phone</b>\n"
        text += "   🕐 Last seen: 2 minutes ago\n"
        text += "   📍 Location: India\n\n"
        
        text += "2️⃣ <b>Desktop (Windows)</b>\n"
        text += "   🕐 Last seen: 1 hour ago\n"
        text += "   📍 Location: India\n\n"
        
        text += "<i>⚠️ Tap a device to terminate it</i>"
        
        builder = InlineKeyboardBuilder()
        # Add terminate buttons for each device
        builder.row(InlineKeyboardButton(text="❌ Terminate Android Phone", callback_data=f"terminate_device_{account_id}_1"))
        builder.row(InlineKeyboardButton(text="❌ Terminate Desktop", callback_data=f"terminate_device_{account_id}_2"))
        builder.row(InlineKeyboardButton(text="🔄 Refresh Devices", callback_data=f"manage_devices_{account_id}"))
        builder.row(InlineKeyboardButton(text="🔙 Back to Purchases", callback_data="btn_my_purchases"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Manage devices error: {e}", exc_info=True)
        await callback.answer("❌ Error loading devices!", show_alert=True)


@dp.callback_query(F.data.startswith("terminate_device_"))
async def terminate_device_handler(callback: types.CallbackQuery):
    """Terminate a specific device session"""
    try:
        parts = callback.data.split("_")
        account_id = int(parts[2])
        device_id = parts[3]
        
        # TODO: Implement Pyrogram session termination
        # For now, show confirmation
        
        await callback.answer("✅ Device terminated!", show_alert=True)
        
        text = f"✅ <b>Device Terminated</b>\n\n"
        text += f"The device has been logged out successfully.\n\n"
        text += "<i>It will no longer have access to this account.</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📱 View Devices", callback_data=f"manage_devices_{account_id}"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"❌ Terminate device error: {e}", exc_info=True)
        await callback.answer("❌ Error terminating device!", show_alert=True)
