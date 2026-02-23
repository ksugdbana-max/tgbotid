"""
Broadcast feature for admin to send messages to all users
"""
import os
import asyncio
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from .database import async_session
from .models import User

logger = logging.getLogger(__name__)

class BroadcastStates(StatesGroup):
    waiting_for_message = State()

def register_broadcast_handlers(dp, bot):
    """Register broadcast handlers with the dispatcher"""
    
    @dp.message(Command("broadcast"))
    async def cmd_broadcast(message: types.Message, state: FSMContext):
        """Admin-only broadcast command"""
        admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
        
        if message.from_user.id != admin_id:
            await message.answer("❌ This command is admin-only.")
            return
        
        await message.answer(
            "📢 <b>Broadcast Message</b>\n\n"
            "Send the message you want to broadcast to all users.\n\n"
            "💡 <i>You can send text, photos, or videos.</i>\n"
            "⚠️ <i>This will be sent to ALL users in the database.</i>",
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.waiting_for_message)
    
    @dp.message(BroadcastStates.waiting_for_message)
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
                if message.text:
                    await bot.send_message(user.telegram_id, message.text)
                elif message.photo:
                    await bot.send_photo(
                        user.telegram_id,
                        message.photo[-1].file_id,
                        caption=message.caption
                    )
                elif message.video:
                    await bot.send_video(
                        user.telegram_id,
                        message.video.file_id,
                        caption=message.caption
                    )
                elif message.document:
                    await bot.send_document(
                        user.telegram_id,
                        message.document.file_id,
                        caption=message.caption
                    )
                
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
                
                # Delay to avoid rate limits
                await asyncio.sleep(0.05)
                
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
