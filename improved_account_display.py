"""
Improved Account Display Handler
Shows all countries with stock count and price in a clean format
"""

# Add this to backend/bot.py (replace existing btn_accounts handler)

@dp.callback_query(F.data == "btn_accounts")
async def process_accounts_button(callback: types.CallbackQuery):
    """Show all countries with their stock and prices"""
    async with async_session() as session:
        # Get all countries
        countries_stmt = select(Country).order_by(Country.name)
        countries_res = await session.execute(countries_stmt)
        countries = countries_res.scalars().all()
        
        if not countries:
            await safe_edit_message(
                callback,
                "❌ <b>No Countries Available</b>\n\n"
                "Please contact admin to add countries.",
            )
            return
        
        # Build message with all countries
        text = "📍 <b>Available Accounts</b>\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for country in countries:
            # Count available stock
            stock_stmt = select(Account).where(
                Account.country_id == country.id,
                Account.is_sold == False,
                Account.type == "ID"
            )
            stock_res = await session.execute(stock_stmt)
            stock_count = len(stock_res.scalars().all())
            
            # Add to message
            text += f"{country.emoji} <b>{country.name}</b>\n"
            text += f"📦 Stock: {stock_count} Pcs | 💰 Price: ₹{country.price:.2f}\n\n"
            
            # Add button only if stock available
            if stock_count > 0:
                builder.row(InlineKeyboardButton(
                    text=f"{country.emoji} {country.name} ({stock_count} available)",
                    callback_data=f"country_{country.id}"
                ))
        
        text += "💡 <i>Select a country to purchase</i>"
        
        # Add back button
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await safe_edit_message(callback, text, reply_markup=builder.as_markup())
