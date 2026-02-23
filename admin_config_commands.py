"""
Admin commands for setting channel and owner
Add to bot.py after the /start command
"""

# === ADMIN CONFIG COMMANDS ===

@dp.message(Command("setchannel"))
async def cmd_set_channel(message: types.Message, state: FSMContext):
    """Admin command to set channel link"""
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    
    if message.from_user.id != admin_id:
        await message.answer("❌ This command is admin-only.")
        return
    
    await message.answer(
        "📢 <b>Set Channel Link</b>\n\n"
        "Send your Telegram channel link now.\n\n"
        "Example: <code>https://t.me/yourchannel</code>\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML"
    )
    await state.set_state(AdminConfigStates.waiting_for_channel)


@dp.message(AdminConfigStates.waiting_for_channel)
async def process_channel_link(message: types.Message, state: FSMContext):
    """Process and save channel link"""
    channel_link = message.text.strip()
    
    # Check for cancel
    if channel_link.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Cancelled.")
        return
    
    # Validate
    if not channel_link.startswith("http"):
        await message.answer(
            "❌ <b>Invalid link!</b>\n\n"
            "Channel link must start with https://\n\n" 
            "Try again or send /cancel",
            parse_mode="HTML"
        )
        return
    
    # Check for placeholder
    if "yourchannel" in channel_link.lower():
        await message.answer(
            "❌ <b>Don't use placeholder!</b>\n\n"
            "Enter YOUR actual channel link, not 'yourchannel'\n\n"
            "Try again or send /cancel",
            parse_mode="HTML"
        )
        return
    
    # Save to database
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "bot_channel_link")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = channel_link
        else:
            setting = Settings(key="bot_channel_link", value=channel_link)
            session.add(setting)
        
        await session.commit()
    
    await state.clear()
    await message.answer(
        f"✅ <b>Channel Link Updated!</b>\n\n"
        f"📢 <b>New Value:</b>\n<code>{channel_link}</code>\n\n"
        "Users will now be required to join this channel.",
        parse_mode="HTML"
    )
    logger.info(f"Admin {message.from_user.id} set channel link to: {channel_link}")


@dp.message(Command("setowner"))
async def cmd_set_owner(message: types.Message, state: FSMContext):
    """Admin command to set owner username"""
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    
    if message.from_user.id != admin_id:
        await message.answer("❌ This command is admin-only.")
        return
    
    await message.answer(
        "👤 <b>Set Owner Username</b>\n\n"
        "Send your Telegram username now.\n\n"
        "Example: <code>@yourname</code>\n\n"
        "⚠️ Must start with @\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML"
    )
    await state.set_state(AdminConfigStates.waiting_for_owner)


@dp.message(AdminConfigStates.waiting_for_owner)
async def process_owner_username(message: types.Message, state: FSMContext):
    """Process and save owner username"""
    username = message.text.strip()
    
    # Check for cancel
    if username.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Cancelled.")
        return
    
    # Validate
    if not username.startswith("@"):
        await message.answer(
            "❌ <b>Invalid username!</b>\n\n"
            "Username must start with @\n\n"
            "Example: @yourname\n\n"
            "Try again or send /cancel",
            parse_mode="HTML"
        )
        return
    
    # Check for placeholder
    if "yourusername" in username.lower() or "yourname" in username.lower():
        await message.answer(
            "❌ <b>Don't use placeholder!</b>\n\n"
            "Enter YOUR actual username, not '@yourusername'\n\n"
            "Try again or send /cancel",
            parse_mode="HTML"
        )
        return
    
    # Save to database
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "bot_owner_username")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = username
        else:
            setting = Settings(key="bot_owner_username", value=username)
            session.add(setting)
        
        await session.commit()
    
    await state.clear()
    await message.answer(
        f"✅ <b>Owner Username Updated!</b>\n\n"
        f"👤 <b>New Value:</b> {username}\n\n"
        "This will be shown in the Support menu.",
        parse_mode="HTML"
    )
    logger.info(f"Admin {message.from_user.id} set owner username to: {username}")
