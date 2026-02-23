# Broadcast handlers to add at the end of bot.py
# Add these BEFORE the /setchannel and /setowner commands

# === BROADCAST HANDLERS ===

@dp.callback_query(F.data == "btn_broadcast")
async def cmd_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Admin broadcast button handler"""
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    
    if callback.from_user.id != admin_id:
        await callback.answer("❌ Admin only!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "You can send:\n"
        "• Text messages\n"
        "• Photos with captions\n"
        "• Videos with captions\n"
        "• Documents\n\n"
        "Send /cancel to abort.",
        reply_markup=InlineKeyboardBuilder()
            .row(InlineKeyboardButton(text="❌ Cancel", callback_data="btn_main_menu"))
            .as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastMessageStates.waiting_for_message)
    await callback.answer()


@dp.message(BroadcastMessageStates.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    """Send broadcast message to all users"""
    await state.clear()
    
    # Get all users
    async with async_session() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
    
    if not users:
        await message.answer("❌ No users found in database.")
        return
    
    # Status message
    status_msg = await message.answer(
        f"📤 <b>Broadcasting...</b>\n\nTotal users: {len(users)}",
        parse_mode="HTML"
    )
    
    success_count = 0
    failed_count = 0
    
    # Send to all users
    for user in users:
        try:
            # Send message based on type
            if message.text:
                await bot.send_message(
                    user.telegram_id,
                    message.text,
                    parse_mode=message.html_text if hasattr(message, 'html_text') else None
                )
            elif message.photo:
                await bot.send_photo(
                    user.telegram_id,
                    message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            elif message.video:
                await bot.send_video(
                    user.telegram_id,
                    message.video.file_id,
                    caption=message.caption or ""
                )
            elif message.document:
                await bot.send_document(
                    user.telegram_id,
                    message.document.file_id,
                    caption=message.caption or ""
                )
            else:
                # Skip unsupported message types
                continue
            
            success_count += 1
            
            # Update every 10 users
            if success_count % 10 == 0:
                try:
                    await status_msg.edit_text(
                        f"📤 <b>Broadcasting...</b>\n\n"
                        f"✅ Sent: {success_count}\n"
                        f"❌ Failed: {failed_count}\n"
                        f"⏳ Remaining: {len(users) - success_count - failed_count}",
                        parse_mode="HTML"
                    )
                except:
                    pass  # Ignore "message not modified" errors
            
            # Delay to avoid rate limits (Telegram allows ~30 messages/second)
            await asyncio.sleep(0.04)
            
        except Exception as e:
            logger.error(f"Broadcast failed to {user.telegram_id}: {e}")
            failed_count += 1
    
    # Final status
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"Total users: {len(users)}\n"
        f"✅ Successfully sent: {success_count}\n"
        f"❌ Failed: {failed_count}\n\n"
        f"💡 <i>Users who blocked the bot were skipped.</i>",
        parse_mode="HTML"
    )
