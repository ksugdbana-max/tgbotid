
# --- OTP & Purchase Handlers (appended to bot.py) ---

@dp.callback_query(F.data.startswith("buy_id_"))
async def process_buy_id_or_session(callback: types.CallbackQuery):
    """Handle purchasing both IDs and Sessions"""
    country_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Get user
        user_stmt = select(User).where(User.telegram_id == callback.from_user.id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        # Get country
        country_stmt = select(Country).where(Country.id == country_id)
        country_res = await session.execute(country_stmt)
        country = country_res.scalar_one_or_none()
        
        if not user or not country:
            await callback.answer("Error: User or country not found")
            return
        
        # Check if user has sufficient balance
        if user.balance < country.price:
            await callback.message.edit_text(
                f"❌ <b>Insufficient Balance!</b>\\n\\n"
                f"💰 Your Balance: ₹{user.balance}\\n"
                f"💵 Required: ₹{country.price}\\n"
                f"💸 Short by: ₹{country.price - user.balance}\\n\\n"
                "Please deposit to continue.",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="💰 Deposit", callback_data="btn_deposit"))
                    .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )
            return
        
        # Find available account
        account_stmt = select(Account).where(
            Account.country_id == country_id,
            Account.is_sold == False,
            Account.type == "ID"
        ).limit(1)
        account_res = await session.execute(account_stmt)
        account = account_res.scalar_one_or_none()
        
        if not account:
            await callback.message.edit_text(
                "❌ <b>Out of Stock!</b>\\n\\n"
                f"Sorry, no {country.name} IDs available right now.",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🔙 Back", callback_data="btn_accounts"))
                    .as_markup(),
                parse_mode="HTML"
            )
            return
        
        # Process purchase
        user.balance -= country.price
        account.is_sold = True
        
        purchase = Purchase(
            user_id=user.id,
            account_id=account.id,
            amount=country.price
        )
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        
        # Show purchase success with OTP button
        await callback.message.edit_text(
            f"✅ <b>Purchase Successful!</b>\\n\\n"
            f"📱 <b>Your Telegram ID:</b>\\n"
            f"<code>{account.phone_number}</code>\\n\\n"
            f"💰 <b>Paid:</b> ₹{country.price}\\n"
            f"💳 <b>Remaining Balance:</b> ₹{user.balance}\\n\\n"
            f"📋 <b>How to Login:</b>\\n"
            f"1. Open Telegram app\\n"
            f"2. Enter the phone number above\\n"
            f"3. Telegram will ask for OTP\\n"
            f"4. Click 'Get OTP Code' below\\n"
            f"5. We'll send you the code instantly!\\n\\n"
            f"👇 <b>Ready to receive OTP?</b>",
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(
                    text="📲 Get OTP Code",
                    callback_data=f"get_otp_{purchase.id}"
                ))
                .row(InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data="btn_main_menu"
                ))
                .as_markup(),
            parse_mode="HTML"
        )


@dp.callback_query(F.data.startswith("get_otp_"))
async def process_get_otp(callback: types.CallbackQuery):
    """Start OTP monitoring for a purchase"""
    purchase_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Get purchase details
        purchase_stmt = select(Purchase).where(Purchase.id == purchase_id)
        purchase_res = await session.execute(purchase_stmt)
        purchase = purchase_res.scalar_one_or_none()
        
        if not purchase:
            await callback.answer("Purchase not found")
            return
        
        # Get account
        account_stmt = select(Account).where(Account.id == purchase.account_id)
        account_res = await session.execute(account_stmt)
        account = account_res.scalar_one_or_none()
        
        if not account or not account.session_data:
            await callback.message.edit_text(
                "❌ <b>Error!</b>\\n\\n"
                "This account doesn't have session data configured.\\n"
                "Please contact support.",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )
            return
        
        # Start monitoring
        try:
            session_mgr = get_session_manager()
            await session_mgr.start_monitoring(
                phone_number=account.phone_number,
                session_string=account.session_data
            )
            
            # Start the OTP waiting loop
            await show_otp_waiting(callback.message, account.phone_number, purchase_id)
            
        except Exception as e:
            logger.error(f"Error starting OTP monitoring: {e}")
            await callback.message.edit_text(
                f"❌ <b>Error!</b>\\n\\n"
                f"Failed to start OTP monitoring: {str(e)}\\n\\n"
                "Please contact support.",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )


async def show_otp_waiting(message, phone_number, purchase_id, attempt=0):
    """Auto-refreshing OTP display with login detection"""
    session_mgr = get_session_manager()
    
    # Check if login successful
    login_status = await session_mgr.check_login_status(phone_number)
    if login_status == "LOGGED_IN":
        await message.edit_text(
            f"🎉 <b>LOGIN SUCCESSFUL!</b>\\n\\n"
            f"📱 Phone: <code>{phone_number}</code>\\n"
            f"✅ You are now logged in to Telegram!\\n\\n"
            f"💡 <b>Account is now yours!</b>\\n"
            f"You can now use this account freely.\\n\\n"
            f"⚠️ <i>Note: Don't share your session/password with anyone.</i>",
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                .as_markup(),
            parse_mode="HTML"
        )
        await session_mgr.stop_monitoring(phone_number)
        return
    
    # Check for OTP
    otp_code = session_mgr.get_otp(phone_number)
    
    if otp_code:
        # OTP received, show it
        await message.edit_text(
            f"✅ <b>OTP Code Received!</b>\\n\\n"
            f"📱 Phone: <code>{phone_number}</code>\\n"
            f"🔑 OTP: <code>{otp_code}</code>\\n\\n"
            f"📋 <b>Next Steps:</b>\\n"
            f"1. Enter this code in Telegram\\n"
            f"2. Wait for login confirmation...\\n\\n"
            f"🔄 <i>Monitoring login status...</i>",
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(
                    text="🔄 Resend OTP",
                    callback_data=f"resend_otp_{purchase_id}"
                ))
                .row(InlineKeyboardButton(
                    text="⏹️ Stop",
                    callback_data="btn_main_menu"
                ))
                .as_markup(),
            parse_mode="HTML"
        )
        # Continue monitoring for login
        await asyncio.sleep(5)
        await show_otp_waiting(message, phone_number, purchase_id, attempt + 1)
        
    elif attempt < 24:  # 2 minutes total (24 * 5 sec = 120 sec)
        # Silently wait for OTP without showing instructions
        await asyncio.sleep(5)
        await show_otp_waiting(message, phone_number, purchase_id, attempt + 1)
    else:
        # Timeout
        await message.edit_text(
            f"⏱️ <b>Request Timed Out</b>\\n\\n"
            f"📱 Phone: <code>{phone_number}</code>\\n\\n"
            f"No OTP received in 2 minutes.\\n\\n"
            f"💡 Try again or contact support if issue persists.",
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(
                    text="🔄 Try Again",
                    callback_data=f"get_otp_{purchase_id}"
                ))
                .row(InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data="btn_main_menu"
                ))
                .as_markup(),
            parse_mode="HTML"
        )
        await session_mgr.stop_monitoring(phone_number)


@dp.callback_query(F.data.startswith("resend_otp_"))
async def process_resend_otp(callback: types.CallbackQuery):
    """Resend OTP request (clears cache and restarts monitoring)"""
    purchase_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        purchase_stmt = select(Purchase).where(Purchase.id == purchase_id)
        purchase_res = await session.execute(purchase_stmt)
        purchase = purchase_res.scalar_one_or_none()
        
        if not purchase:
            await callback.answer("Purchase not found")
            return
        
        account_stmt = select(Account).where(Account.id == purchase.account_id)
        account_res = await session.execute(account_stmt)
        account = account_res.scalar_one_or_none()
        
        if not account:
            await callback.answer("Account not found")
            return
        
        # Clear OTP cache and restart monitoring
        session_mgr = get_session_manager()
        session_mgr.clear_otp(account.phone_number)
        
        await callback.message.edit_text(
            f"🔄 <b>Restarting OTP monitoring...</b>\\n\\n"
            f"📱 Phone: <code>{account.phone_number}</code>\\n\\n"
            f"Please request a new code from Telegram.",
            parse_mode="HTML"
        )
        
        await asyncio.sleep(2)
        await show_otp_waiting(callback.message, account.phone_number, purchase_id)
