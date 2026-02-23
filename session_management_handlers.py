# Session Management and My Purchases Handlers
# Add these after the confirm_purchase_handler

@dp.callback_query(F.data.startswith("manage_session_"))
async def manage_session_handler(callback: types.CallbackQuery):
    """Show session management options - Get OTP code"""
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
            
            # Get purchase and account
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
        
        # Show session management options
        text = f"🔑 <b>Manage Session</b>\n\n"
        text += f"📱 <b>Phone:</b> <code>{account.phone_number}</code>\n"
        if account.twofa_password:
            text += f"🔐 <b>2FA:</b> <code>{account.twofa_password}</code>\n"
        
        text += f"\n💡 <b>What would you like to do?</b>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📨 Get OTP Code", callback_data=f"get_otp_{account_id}"))
        builder.row(InlineKeyboardButton(text="📋 View Full Session", callback_data=f"view_session_{account_id}"))
        builder.row(InlineKeyboardButton(text="🔄 Retry Login", callback_data=f"retry_login_{account_id}"))
        builder.row(InlineKeyboardButton(text="🔙 Back to Purchases", callback_data="btn_my_purchases"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Manage session error: {e}", exc_info=True)
        await callback.answer("❌ Error loading session!", show_alert=True)


@dp.callback_query(F.data == "btn_my_purchases")
async def show_my_purchases(callback: types.CallbackQuery):
    """Show user's purchase history"""
    try:
        async with async_session() as session:
            user_stmt = select(User).where(User.telegram_id == callback.from_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                await callback.answer("❌ User not found!", show_alert=True)
                return
            
            # Get all purchases
            purchases_stmt = select(Purchase).where(Purchase.user_id == user.id).order_by(Purchase.created_at.desc())
            purchases_result = await session.execute(purchases_stmt)
            purchases = purchases_result.scalars().all()
            
            if not purchases:
                text = "📜 <b>My Purchases</b>\n\n❌ You haven't made any purchases yet!\n\n🛒 Browse countries to buy accounts."
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🟢 Get Account", callback_data="btn_accounts"))
                builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                return
            
            # Build purchase list
            text = f"📜 <b>My Purchases ({len(purchases)})</b>\n\n"
            
            builder = InlineKeyboardBuilder()
            for i, purchase in enumerate(purchases[:10], 1):  # Show latest 10
                # Get account details
                account_stmt = select(Account).where(Account.id == purchase.account_id)
                account_result = await session.execute(account_stmt)
                account = account_result.scalar_one_or_none()
                
                if account:
                    # Get country
                    country_stmt = select(Country).where(Country.id == account.country_id)
                    country_result = await session.execute(country_stmt)
                    country = country_result.scalar_one_or_none()
                    
                    country_name = country.name if country else "Unknown"
                    flag = country.flag if country else "🌍"
                    
                    text += f"{i}. {flag} <b>{country_name}</b>\n"
                    text += f"   📱 <code>{account.phone_number}</code>\n"
                    text += f"   💰 ₹{purchase.amount} • {purchase.created_at.strftime('%d %b %Y')}\n\n"
                    
                    # Add button for each purchase
                    builder.row(InlineKeyboardButton(
                        text=f"{flag} {country_name} - {account.phone_number[-4:]}",
                        callback_data=f"manage_session_{account.id}"
                    ))
            
            # Add control buttons
            builder.row(InlineKeyboardButton(text="🛒 Buy More", callback_data="btn_accounts"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ My purchases error: {e}", exc_info=True)
        await callback.answer("❌ Error loading purchases!", show_alert=True)


@dp.callback_query(F.data.startswith("get_otp_"))
async def get_otp_code(callback: types.CallbackQuery):
    """Request OTP code for the account"""
    await callback.answer("📨 Requesting OTP code...", show_alert=False)
    
    # TODO: Implement OTP request logic via Pyrogram
    text = "📨 <b>OTP Requested</b>\n\n"
    text += "⏳ Waiting for OTP code...\n\n"
    text += "<i>Note: This feature requires the session to be active.</i>"
    
    await callback.message.edit_text(text, parse_mode="HTML")


@dp.callback_query(F.data.startswith("view_session_"))
async def view_full_session(callback: types.CallbackQuery):
    """View the full session string/code"""
    try:
        account_id = int(callback.data.split("_")[2])
        
        async with async_session() as session:
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found!", show_alert=True)
                return
            
            text = f"📋 <b>Full Session Data</b>\n\n"
            text += f"📱 <b>Phone:</b> <code>{account.phone_number}</code>\n\n"
            
            if account.session_data:
                text += f"<b>Session String:</b>\n<code>{account.session_data}</code>\n\n"
                text += "<i>Copy this code to login elsewhere</i>"
            else:
                text += "❌ No session data available"
            
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔙 Back", callback_data=f"manage_session_{account_id}"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ View session error: {e}", exc_info=True)
        await callback.answer("❌ Error loading session!", show_alert=True)


@dp.callback_query(F.data.startswith("retry_login_"))
async def retry_login(callback: types.CallbackQuery):
    """Retry login instructions"""
    await callback.answer("🔄 Retry login...")
    
    text = "🔄 <b>Retry Login Guide</b>\n\n"
    text += "1️⃣ Use the phone number provided\n"
    text += "2️⃣ Enter the 2FA password if prompted\n"
    text += "3️⃣ Request OTP code via 'Get OTP Code'\n"
    text += "4️⃣ Enter the OTP when it arrives\n\n"
    text += "💡 <i>Need help? Contact support!</i>"
    
    await callback.message.edit_text(text, parse_mode="HTML")
