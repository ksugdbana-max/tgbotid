# Handler for manual OTP check
@dp.callback_query(F.data.startswith("check_otp_"))
async def handle_check_otp(callback: types.CallbackQuery):
    purchase_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Get purchase and account
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
        
        await callback.answer("Checking for codes...")
        await show_otp_waiting(callback.message, account.phone_number, purchase_id)

# Handler for login status check
@dp.callback_query(F.data.startswith("check_login_"))
async def handle_check_login(callback: types.CallbackQuery):
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
        
        await callback.answer("Checking login status...")
        await show_otp_waiting(callback.message, account.phone_number, purchase_id)
