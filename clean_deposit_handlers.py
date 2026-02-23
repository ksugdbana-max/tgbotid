"""
Clean Deposit Handlers - Add to bot.py
Captures: Amount -> UTR -> Screenshot -> Database
"""

# === DEPOSIT FLOW HANDLERS ===

@dp.callback_query(F.data == "btn_deposit")
async def process_deposit_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle deposit button click"""
    try:
        await callback.message.delete()
    except:
        pass
    
    await bot.send_message(
        callback.message.chat.id,
        "💰 <b>Add Balance to Your Account</b>\n\n"
        "Please enter the amount you want to deposit (in ₹):\n\n"
        "Example: 100\n"
        "Minimum: ₹10\n"
        "Maximum: ₹50,000",
        parse_mode="HTML"
    )
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.answer()


@dp.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    """Process deposit amount input"""
    try:
        amount = float(message.text.strip())
        
        if amount < 10:
            await message.answer("❌ Minimum deposit is ₹10. Please try again.")
            return
        
        if amount > 50000:
            await message.answer("❌ Maximum deposit is ₹50,000. Please try again.")
            return
        
        await state.update_data(amount=amount)
        
        # Get UPI ID from settings
        async with async_session() as session:
            upi_stmt = select(Settings).where(Settings.key == "upi_id")
            upi_res = await session.execute(upi_stmt)
            upi_setting = upi_res.scalar_one_or_none()
            upi_id = upi_setting.value if upi_setting else "payment@upi"
        
        await message.answer(
            f"💳 <b>Payment Details</b>\n\n"
            f"Amount to Pay: ₹{amount}\n"
            f"UPI ID: <code>{upi_id}</code>\n\n"
            f"📋 <b>Next Steps:</b>\n"
            f"1️⃣ Send ₹{amount} to the UPI ID above\n"
            f"2️⃣ After payment, enter the UTR/Transaction ID\n\n"
            f"💡 UTR is the 12-digit reference number from your payment",
            parse_mode="HTML"
        )
        
        await message.answer("Please enter your UTR/Transaction ID:")
        await state.set_state(DepositStates.waiting_for_utr)
        
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a valid number.")


@dp.message(DepositStates.waiting_for_utr)
async def process_deposit_utr(message: types.Message, state: FSMContext):
    """Process UTR input - CRITICAL: This saves the UTR"""
    utr = message.text.strip()
    
    if len(utr) < 6:
        await message.answer("❌ UTR seems too short. Please check and try again.")
        return
    
    # CRITICAL: Save UTR in state
    await state.update_data(utr=utr)
    
    await message.answer(
        f"✅ UTR Recorded: <code>{utr}</code>\n\n"
        f"📸 <b>Upload Payment Screenshot</b>\n\n"
        f"Please send a screenshot of your payment confirmation.",
        parse_mode="HTML"
    )
    
    await state.set_state(DepositStates.waiting_for_screenshot)


@dp.message(DepositStates.waiting_for_screenshot)
async def process_deposit_screenshot(message: types.Message, state: FSMContext):
    """Process screenshot and save deposit with UTR"""
    
    if not message.photo:
        await message.answer(
            "❌ Please send a photo/screenshot of your payment.\n\n"
            "💡 Click the attachment icon and select a photo."
        )
        return
    
    # Get state data
    data = await state.get_data()
    amount = data.get('amount')
    utr = data.get('utr')
    
    if not amount or not utr:
        await message.answer("❌ Session expired. Please start over with /start")
        await state.clear()
        return
    
    # Get user
    async with async_session() as session:
        user_stmt = select(User).where(User.telegram_id == message.from_user.id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        if not user:
            await message.answer("❌ User not found. Please use /start first.")
            await state.clear()
            return
        
        # CRITICAL: Create deposit with UTR in upi_ref_id field
        deposit = Deposit(
            user_id=user.id,
            amount=amount,
            upi_ref_id=utr,  # ← THIS IS WHERE UTR IS SAVED
            screenshot_path=f"photo_{message.photo[-1].file_id}",
            status="PENDING"
        )
        
        session.add(deposit)
        await session.commit()
        await session.refresh(deposit)
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Deposit Request Submitted!</b>\n\n"
        f"💰 Amount: ₹{amount}\n"
        f"🔖 UTR: <code>{utr}</code>\n"
        f"📊 Status: Pending Admin Approval\n\n"
        f"⏳ Your deposit will be approved within 24 hours.\n"
        f"You'll be notified once it's approved!",
        reply_markup=InlineKeyboardBuilder()
            .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            .as_markup(),
        parse_mode="HTML"
    )
