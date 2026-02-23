"""
Device Session Management Handlers for Telegram Bot

This module contains handlers for managing active Telegram device sessions.
Users can view their active devices and terminate unwanted sessions.
"""

from aiogram import types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import logging
from .database import async_session
from .models import Purchase, Account
from .device_manager import DeviceManager
from sqlalchemy import select

logger = logging.getLogger(__name__)


def register_session_handlers(dp):
    """Register device session management handlers"""
    
    @dp.callback_query(F.data.startswith("manage_sess_"))
    async def show_device_sessions(callback: types.CallbackQuery):
        """Show active device sessions with terminate buttons"""
        purchase_id = int(callback.data.split("_")[2])
        
        async with async_session() as session:
            purchase_stmt = select(Purchase).where(Purchase.id == purchase_id)
            purchase_res = await session.execute(purchase_stmt)
            purchase = purchase_res.scalar_one_or_none()
            
            if not purchase:
                await callback.answer("❌ Purchase not found", show_alert=True)
                return
            
            account_stmt = select(Account).where(Account.id == purchase.account_id)
            account_res = await session.execute(account_stmt)
            account = account_res.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found", show_alert=True)
                return
        
        try:
            device_mgr = DeviceManager()
            devices = await device_mgr.get_active_sessions(account.session_data)
            
            if not devices:
                await callback.message.edit_text(
                    f"🔐 <b>Session Management</b>\n\n"
                    f"📱 <b>Phone:</b> <code>{account.phone_number}</code>\n\n"
                    f"ℹ️ No active devices found.",
                    reply_markup=InlineKeyboardBuilder()
                        .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                        .as_markup(),
                    parse_mode="HTML"
                )
                return
            
            text = f"🔐 <b>Session Management</b>\n\n"
            text += f"📱 <b>Phone:</b> <code>{account.phone_number}</code>\n\n"
            text += f"📊 <b>Active Devices ({len(devices)}):</b>\n\n"
            
            builder = InlineKeyboardBuilder()
            
            for idx, device in enumerate(devices, 1):
                device_name = device.get('device_model', 'Unknown Device')
                platform = device.get('platform', '')
                app_name = device.get('app_name', '')
                is_current = device.get('is_current', False)
                
                text += f"{idx}. <b>{device_name}</b>\n"
                text += f"   📱 {app_name} on {platform}\n"
                if is_current:
                    text += f"   🟢 Current Session\n"
                text += f"\n"
                
                if not is_current:
                    hash_id = device.get('hash')
                    builder.row(InlineKeyboardButton(
                        text=f"❌ Terminate {device_name[:20]}",
                        callback_data=f"term_sess_{purchase_id}_{hash_id}"
                    ))
            
            if len(devices) > 1:
                builder.row(InlineKeyboardButton(
                    text="⚠️ Terminate All Other Sessions",
                    callback_data=f"term_all_{purchase_id}"
                ))
            
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error getting device sessions: {e}")
            await callback.answer(f"❌ Error: {str(e)}", show_alert=True)

    
    @dp.callback_query(F.data.startswith("term_sess_"))
    async def terminate_device_session(callback: types.CallbackQuery):
        """Terminate a specific device session"""
        parts = callback.data.split("_")
        purchase_id = int(parts[2])
        session_hash = int(parts[3])
        
        async with async_session() as session:
            purchase_stmt = select(Purchase).where(Purchase.id == purchase_id)
            purchase_res = await session.execute(purchase_stmt)
            purchase = purchase_res.scalar_one_or_none()
            
            if not purchase:
                await callback.answer("❌ Purchase not found", show_alert=True)
                return
            
            account_stmt = select(Account).where(Account.id == purchase.account_id)
            account_res = await session.execute(account_stmt)
            account = account_res.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found", show_alert=True)
                return
        
        try:
            device_mgr = DeviceManager()
            success = await device_mgr.terminate_session(account.session_data, session_hash)
            
            if success:
                await callback.answer("✅ Device session terminated!", show_alert=True)
                await show_device_sessions(callback)
            else:
                await callback.answer("❌ Failed to terminate session", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error terminating session: {e}")
            await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
