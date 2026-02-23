import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from dotenv import load_dotenv
from .database import async_session
from .models import User, Country, Account, Purchase, Deposit, Settings
from .session_manager import get_session_manager_async
from .device_manager import DeviceManager
from sqlalchemy import select, update, func

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Global Error Handler for Maximum Stability ---
@dp.errors()
async def error_handler(event: types.ErrorEvent):
    """
    BULLETPROOF error handler - catches ALL exceptions and prevents bot crashes.
    This ensures the bot NEVER stops working, no matter what error occurs.
    """
    try:
        update = event.update
        exception = event.exception
        logger.error(f"❌ Error handling update {update.update_id if update else 'Unknown'}: {exception}", exc_info=True)
        
        # Try to notify user of error if it's a callback or message update
        try:
            if update:
                chat_id = None
                if update.message:
                    chat_id = update.message.chat.id
                elif update.callback_query:
                    chat_id = update.callback_query.message.chat.id
                
                if chat_id:
                    try:
                        await bot.send_message(
                            chat_id,
                            "⚠️ An error occurred. Please try again or contact support if the issue persists.",
                            reply_markup=get_back_to_main()
                        )
                    except Exception as send_error:
                        logger.error(f"Could not send error message to user: {send_error}")
        except Exception as notify_error:
            logger.error(f"Error in error notification: {notify_error}")
    
    except Exception as handler_error:
        # Even if the error handler itself fails, log it and continue
        logger.critical(f"CRITICAL: Error handler itself failed: {handler_error}", exc_info=True)
    
    # CRITICAL: Always return True to mark error as handled
    # This prevents aiogram from crashing the bot
    return True

# --- FSM States ---
class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_utr = State()
    confirming_utr = State()
    waiting_for_screenshot = State()
    confirming_screenshot = State()

class OxaPayDepositStates(StatesGroup):
    waiting_for_usd_amount = State()
    confirming_usd_amount = State()

class BotSettingsStates(StatesGroup):
    waiting_for_channel_link = State()
    waiting_for_owner_username = State()

class AdminConfigStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_owner = State()

class BroadcastMessageStates(StatesGroup):
    waiting_for_message = State()

# --- Keyboards ---

def get_main_menu(is_admin=False):
    builder = InlineKeyboardBuilder()
    
    # Row 1: Get Account | Profile
    builder.row(
        InlineKeyboardButton(text="🟢 Get Account", callback_data="btn_accounts"),
        InlineKeyboardButton(text="👤 Profile", callback_data="btn_profile")
    )
    
    # Row 2: Deposit | Support
    builder.row(
        InlineKeyboardButton(text="💰 Deposit", callback_data="btn_deposit"),
        InlineKeyboardButton(text="🆘 Support", callback_data="btn_help")
    )
    
    # Row 3: Main Menu
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    if is_admin:
        # Admin-only: Links
        admin_url = os.getenv("ADMIN_WEBAPP_URL", "https://tgbotid-production.up.railway.app")
        builder.row(
            InlineKeyboardButton(text="📊 Admin Web App", web_app=WebAppInfo(url=admin_url)),
            InlineKeyboardButton(text="💳 Payment Settings", web_app=WebAppInfo(url=admin_url + "/settings"))
        )
        # Row 5: Broadcast
        builder.row(
            InlineKeyboardButton(text="📢 Broadcast", callback_data="btn_broadcast")
        )
    
    return builder.as_markup()

def get_back_to_main():
    """Return a simple back to main menu button"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    return builder.as_markup()

async def check_channel_membership(user_id: int) -> bool:
    """Check if user is a member of the required channel"""
    try:
        async with async_session() as session:
            channel_setting = await session.execute(
                select(Settings).where(Settings.key == "bot_channel_link")
            )
            setting = channel_setting.scalar_one_or_none()
            
            if not setting or not setting.value or not str(setting.value).strip():
                return True  # No channel configured
            
            channel_username = setting.value
            if "t.me/" in channel_username:
                channel_username = channel_username.split("t.me/")[-1]
            if not channel_username.startswith("@"):
                channel_username = f"@{channel_username}"
            
            try:
                member = await bot.get_chat_member(channel_username, user_id)
                return member.status in ["creator", "administrator", "member"]
            except:
                return True  # Fail open on error
                
    except Exception as e:
        logger.error(f"Error in check_channel_membership: {e}")
        return True

async def show_force_join_message(message_or_callback, channel_link: str):
    """Show force join message with buttons"""
    text = "🔒 <b>Channel Membership Required</b>\n\n"
    text += "To use this bot, you must join our official channel first!\n\n"
    text += "📢 Click the button below to join, then click 'Check' to verify."
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Join Channel", url=channel_link))
    builder.row(InlineKeyboardButton(text="✅ Check Membership", callback_data="check_membership"))
    
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message_or_callback.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception as e:
        # Ignore "message is not modified" errors as that's expected behavior
        if "message is not modified" not in str(e).lower():
            logger.error(f"Error showing force join message: {e}")


# --- Handlers ---

@dp.startup()
async def on_startup():
    logger.info("Bot started and polling...")


# CRITICAL: Safe message edit wrapper to prevent "message not modified" crashes
async def safe_edit_message(callback, text, reply_markup=None, parse_mode="HTML"):
    """Safely edit a message, falling back to delete+send if edit fails"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        # If edit fails (message not modified, message deleted, etc.)
        try:
            await callback.message.delete()
        except:
            pass
        try:
            await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as send_err:
            logger.error(f"Could not send message after edit failed: {send_err}")
            await callback.answer("✅ Action completed", show_alert=False)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command with force join check"""
    logger.info(f"Received /start from {message.from_user.id}")
    
    # Check channel membership first
    is_member = await check_channel_membership(message.from_user.id)
    
    if not is_member:
        async with async_session() as session:
            channel_setting = await session.execute(
                select(Settings).where(Settings.key == "bot_channel_link")
            )
            setting = channel_setting.scalar_one_or_none()
            channel_link = setting.value if setting else "https://t.me/yourchannel"
        
        await show_force_join_message(message, channel_link)
        return
    
    # User is member, continue with normal start
    is_admin = False
    try:
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            # Check if this telegram ID should be admin
            admin_telegram_id = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
            user_id_str = str(message.from_user.id)
            should_be_admin = admin_telegram_id and user_id_str == admin_telegram_id
            
            logger.info(f"Start Check: User={user_id_str}, AdminEnv={admin_telegram_id}, Match={should_be_admin}")

            if not user:
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    full_name=message.from_user.full_name,
                    is_admin=should_be_admin,
                    balance=0.0 # New users start with 0 balance
                )
                session.add(user)
            elif user.is_admin != should_be_admin:
                # Update admin status if changed
                user.is_admin = should_be_admin
                
            await session.commit()
            is_admin = user.is_admin
            
    except Exception as e:
        logger.error(f"Error in /start handler: {e}")
        # DEBUG: Tell the user what happened so we can diagnose "no reply" issues
        if should_be_admin: # Only show details to admin if possible, or just show everyone for now
             await message.answer(f"⚠️ <b>System Error during Login:</b>\n<code>{str(e)}</code>", parse_mode="HTML")
        # Even if DB fails, we want to try show the menu if possible, or maybe stop here?
    
    # Ensure is_admin has a value even if DB failed (False)
    # If DB failed, this might fail too if get_main_menu relies on DB? No it doesn't.
    try:
        await message.answer(
            f"<b>👋 Hello {message.from_user.full_name}, Welcome to our Premium Store!</b>\n\n"
        "⚡ <b>Instant Delivery | High Quality | 24/7 Support</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛒 <b>Best Place to Buy:</b>\n"
        "• Telegram Accounts (TData/Session)\n"
        "• Fresh & Aged IDs\n"
        "• Bulk Orders Available\n\n"
        "👇 <b>Choose an option below to start:</b>",
        reply_markup=get_main_menu(is_admin=is_admin),
        parse_mode="HTML"
    )
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        # Fallback response if main message fails
        try:
            await message.answer("Welcome! The bot is ready. Type /start to begin.")
        except Exception:
            pass  # If even fallback fails, log it but don't crash

@dp.callback_query(F.data == "check_membership")
async def handle_check_membership(callback: types.CallbackQuery):
    """Handle membership verification check"""
    await callback.answer("Checking membership...")
    
    is_member = await check_channel_membership(callback.from_user.id)
    
    if is_member:
        admin_id = int(os.getenv("ADMIN_ID", "0"))
        is_admin = (callback.from_user.id == admin_id)
        
        text = f"✅ <b>Verified!</b> Welcome to the bot!\n\n"
        text += f"👋 Hello {callback.from_user.first_name}!\n\n"
        text += "Choose an option below:"
        
        await callback.message.edit_text(text, reply_markup=get_main_menu(is_admin), parse_mode="HTML")
    else:
        async with async_session() as session:
            channel_setting = await session.execute(
                select(Settings).where(Settings.key == "bot_channel_link")
            )
            setting = channel_setting.scalar_one_or_none()
            channel_link = setting.value if setting else "https://t.me/yourchannel"
        
        # Explicit feedback: 1. Alert 2. Refresh Message
        await callback.answer("❌ You have NOT joined the channel yet!\n\nPlease join and try again.", show_alert=True)
        
        # Refresh the message to ensure buttons are visible/clickable
        # We delete and resend to make sure it's fresh and at the bottom
        try:
            await callback.message.delete()
        except:
            pass
            
        await show_force_join_message(callback.message, channel_link)

@dp.callback_query(F.data == "btn_deposit")
async def process_deposit_start(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇮🇳 UPI (Manual - INR)", callback_data="btn_deposit_upi_manual"))
    builder.row(InlineKeyboardButton(text="🌐 OxaPay (Crypto - USD)", callback_data="btn_deposit_oxapay"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    await callback.message.edit_text(
        "<b>💸 Deposit Funds</b>\n\n"
        "Choose your deposit method:\n\n"
        "• <b>UPI (Manual)</b> — Pay in ₹ INR, admin verifies UTR\n"
        "• <b>OxaPay (Crypto)</b> — Pay in $ USD, auto-approved instantly",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "btn_deposit_upi_manual")
async def process_deposit_method_upi(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.message.edit_text(
        "<b>💎 Deposit Balance</b>\n\n"
        "Please enter the amount in <b>₹ (INR)</b> you wish to deposit:",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

@dp.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ <b>Invalid Amount!</b> Please enter a numeric value:")
        return
    
    amount = float(message.text)
    await state.update_data(deposit_amount=amount)
    await state.set_state(DepositStates.waiting_for_utr)
    
    async with async_session() as session:
        # Fetch Payment Settings
        upi_res = await session.execute(select(Settings).where(Settings.key == "payment_upi_id"))
        qr_res = await session.execute(select(Settings).where(Settings.key == "payment_qr_image"))
        
        upi_id = upi_res.scalar_one_or_none()
        qr_image = qr_res.scalar_one_or_none()
        
        target_upi_id = upi_id.value if upi_id else "example@upi"
        
        # Check if custom QR image exists
        custom_qr_path = qr_image.value if qr_image else None
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        if custom_qr_path:
            # Check if it's a URL (Supabase) or Local File
            photo_input = None
            if custom_qr_path.startswith("http"):
                photo_input = custom_qr_path
            elif os.path.exists(custom_qr_path):
                photo_input = FSInputFile(custom_qr_path)
            
            if photo_input:
                # Send Custom QR
                text = (
                    f"<b>🏧 Deposit Amount: ₹{amount}</b>\n\n"
                    f"📍 <b>UPI ID:</b> <code>{target_upi_id}</code>\n\n"
                    "📸 <b>Scan the QR Code below to Pay</b>\n\n"
                    "✅ <b>Instructions:</b>\n"
                    "1. Open your UPI app.\n"
                    "2. Scan this QR or pay to the UPI ID.\n"
                    "3. Copy the <b>UTR / Transaction Ref ID</b>.\n\n"
                    "👉 <b>Please enter the UTR / Ref ID here after payment:</b>"
                )
                await message.answer_photo(
                    photo_input,
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
            else:
                 # Fallback if file not found
                 pass # Fall through to dynamic generation logic below? No, duplicate logic.
                 # Let's restructure properly
        
        # If no custom QR or failed path, generate dynamic one
        if not custom_qr_path or (not photo_input):
            # Generate Dynamic QR
            qr_data = f"upi://pay?pa={target_upi_id}&am={amount}&cu=INR&tn=Deposit"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}"

            text = (
                f"<b>🏧 Deposit Amount: ₹{amount}</b>\n\n"
                f"📍 <b>UPI ID:</b> <code>{target_upi_id}</code>\n\n"
                "📸 <b>Scan QR or use the UPI ID above</b>\n\n"
                "✅ <b>Instructions:</b>\n"
                "1. Open your UPI app (PhonePe, GPay, Paytm, etc.)\n"
                "2. Pay the above amount.\n"
                "3. Copy the <b>UTR / Transaction Ref ID</b>.\n\n"
                "👉 <b>Please enter the UTR / Ref ID here after payment:</b>"
            )
            
            await message.answer_photo(
                qr_url,
                caption=text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

@dp.message(DepositStates.waiting_for_utr)
async def process_deposit_utr(message: types.Message, state: FSMContext):
    utr_id = message.text
    if not utr_id or len(utr_id) < 6:
        await message.answer("❌ <b>Invalid UTR!</b>\n\nPlease enter a valid Transaction Ref ID:", reply_markup=get_back_to_main(), parse_mode="HTML")
        return
    
    # Check for duplicate UTR
    async with async_session() as session:
        stmt = select(Deposit).where(Deposit.upi_ref_id == utr_id)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            await message.answer(
                "⚠️ <b>Duplicate UTR Detected!</b>\n\n"
                "This Transaction Ref ID has already been submitted. Please do not submit double UTRs. "
                "If you believe this is an error, please contact support.",
                reply_markup=get_back_to_main(),
                parse_mode="HTML"
            )
            return

    await state.update_data(utr_id=utr_id)
    await state.set_state(DepositStates.confirming_utr)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Confirm UTR", callback_data="confirm_utr"))
    builder.row(InlineKeyboardButton(text="❌ Edit UTR", callback_data="btn_deposit_reenter_amount")) # Simplified backtrack
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))

    await message.answer(
        f"🔎 <b>Review your UTR:</b>\n\n"
        f"<code>{utr_id}</code>\n\n"
        "Is this correct? Click confirm to proceed to the final step.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "confirm_utr", DepositStates.confirming_utr)
async def process_utr_confirmed(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_screenshot)
    await callback.message.edit_text(
        "✅ <b>UTR Confirmed!</b>\n\n"
        "📸 <b>Final Step:</b> Please upload the <b>Payment Screenshot</b> for verification:",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "btn_deposit_reenter_amount", DepositStates.confirming_utr)
async def process_reenter_utr(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_utr)
    await callback.message.edit_text(
        "📝 <b>Re-enter UTR:</b>\n\nPlease send the correct Transaction Ref ID now:",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

@dp.message(DepositStates.waiting_for_screenshot, F.photo)
async def process_deposit_screenshot(message: types.Message, state: FSMContext):
    # Save photo temporarily in state data instead of file immediately to allow confirmation
    photo = message.photo[-1]
    await state.update_data(temp_photo_id=photo.file_id)
    await state.set_state(DepositStates.confirming_screenshot)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Confirm & Submit", callback_data="confirm_deposit"))
    builder.row(InlineKeyboardButton(text="❌ Re-upload Photo", callback_data="reupload_screenshot"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))

    await message.answer(
        "🔎 <b>Is this the correct payment screenshot?</b>\n\n"
        "Click the button below to submit your deposit for admin approval.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "reupload_screenshot", DepositStates.confirming_screenshot)
async def process_reupload_screenshot(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_screenshot)
    await callback.message.edit_text(
        "📸 <b>Please upload the screenshot again:</b>",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "confirm_deposit", DepositStates.confirming_screenshot)
async def process_deposit_final_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("deposit_amount")
    utr_id = data.get("deposit_utr")
    photo_id = data.get("temp_photo_id")
    
    try:
        # We store the Telegram file_id instead of uploading to a bucket.
        # The admin panel will fetch the image via a FastAPI endpoint.
        tg_image_path = f"tg_file_id:{photo_id}"
        
        async with async_session() as session:
            # Get user
            stmt = select(User).where(User.telegram_id == callback.from_user.id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            
            if user:
                deposit = Deposit(
                    user_id=user.id,
                    amount=amount,
                    upi_ref_id=utr_id,
                    screenshot_path=tg_image_path, # Save Telegram format
                    status="PENDING"
                )

                session.add(deposit)
                await session.commit()
                
                # Notify User
                await callback.message.edit_text(
                    "✅ <b>Deposit Submitted!</b>\n\n"
                    f"💰 Amount: ₹{amount}\n"
                    f"🆔 UTR: <code>{utr_id}</code>\n\n"
                    "⏳ Your deposit is pending verification. Please wait for admin approval.",
                    reply_markup=get_back_to_main(),
                    parse_mode="HTML"
                )
                
                # Notify Admin
                admin_id = os.getenv("ADMIN_TELEGRAM_ID")
                if admin_id:
                    try:
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=photo_id,
                            caption=(
                                f"🔔 <b>New Deposit Alert!</b>\n\n"
                                f"👤 User: {callback.from_user.full_name} (@{callback.from_user.username})\n"
                                f"💰 Amount: ₹{amount}\n"
                                f"🆔 UTR: {utr_id}"
                            ),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin: {e}")
            else:
                 await callback.message.edit_text("❌ User not found in database.")
                 
    except Exception as e:
        logger.error(f"Failed to process screenshot: {e}")
        await callback.message.answer(f"❌ Error processing screenshot: {e}")

    await state.clear()

@dp.message(DepositStates.waiting_for_screenshot)
async def process_deposit_screenshot_invalid(message: types.Message):
    await message.answer(
        "⚠️ <b>Not a picture or anything! Only images are allowed.</b>\n\n"
        "Please upload the payment screenshot to proceed:",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

# ============================================================
# OXAPAY DEPOSIT FLOW
# ============================================================

@dp.callback_query(F.data == "btn_deposit_oxapay")
async def process_oxapay_start(callback: types.CallbackQuery, state: FSMContext):
    """Start OxaPay crypto deposit flow"""
    await state.set_state(OxaPayDepositStates.waiting_for_usd_amount)
    
    # Get current exchange rate to show user
    async with async_session() as session:
        rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        rate_res = await session.execute(rate_stmt)
        rate_setting = rate_res.scalar_one_or_none()
        exchange_rate = float(rate_setting.value) if rate_setting else 84.0
    
    await callback.message.edit_text(
        "<b>🌐 OxaPay Crypto Deposit</b>\n\n"
        "Please enter the amount in <b>$ USD</b> you wish to deposit:\n\n"
        f"📊 Current Rate: <b>1 USD = ₹{exchange_rate:.2f} INR</b>\n"
        "⚠️ Minimum deposit: <b>$0.10 USD</b>\n\n"
        "<i>Type the amount in USD (e.g. 5 or 1.50):</i>",
        reply_markup=get_back_to_main(),
        parse_mode="HTML"
    )

@dp.message(OxaPayDepositStates.waiting_for_usd_amount)
async def process_oxapay_amount(message: types.Message, state: FSMContext):
    """Validate and confirm the USD deposit amount"""
    try:
        amount = float(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer(
            "❌ <b>Invalid amount!</b> Please enter a valid number (e.g. 5 or 1.50):",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        return
    
    if amount < 0.10:
        await message.answer(
            "❌ <b>Too small!</b> Minimum deposit is <b>$0.10 USD</b>.\n\nPlease enter a higher amount:",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        return
    
    # Get exchange rate
    async with async_session() as session:
        rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        rate_res = await session.execute(rate_stmt)
        rate_setting = rate_res.scalar_one_or_none()
        exchange_rate = float(rate_setting.value) if rate_setting else 84.0
    
    inr_amount = round(amount * exchange_rate, 2)
    await state.update_data(usd_amount=amount, inr_amount=inr_amount, exchange_rate=exchange_rate)
    await state.set_state(OxaPayDepositStates.confirming_usd_amount)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Confirm & Get Pay Link", callback_data="oxapay_confirm"))
    builder.row(InlineKeyboardButton(text="✏️ Change Amount", callback_data="btn_deposit_oxapay"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    await message.answer(
        f"<b>🔎 Confirm OxaPay Deposit</b>\n\n"
        f"💵 Amount: <b>${amount:.2f} USD</b>\n"
        f"₹ Equivalent: <b>₹{inr_amount:.2f} INR</b>\n"
        f"📊 Rate: 1 USD = ₹{exchange_rate:.2f}\n\n"
        "<i>Confirm to generate your payment link.</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "oxapay_confirm", OxaPayDepositStates.confirming_usd_amount)
async def process_oxapay_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Create OxaPay invoice via backend and send pay link"""
    data = await state.get_data()
    usd_amount = data.get("usd_amount")
    inr_amount = data.get("inr_amount")
    
    await callback.answer("Creating payment link...")
    await callback.message.edit_text(
        "⏳ <b>Generating your payment link...</b>\n\nPlease wait.",
        parse_mode="HTML"
    )
    
    # Get user from DB
    async with async_session() as session:
        user_stmt = select(User).where(User.telegram_id == callback.from_user.id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text(
            "❌ User not found. Please /start the bot first.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Call backend to create OxaPay invoice
    base_url = os.getenv("BASE_WEBHOOK_URL", "http://localhost:8000").rstrip("/")
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{base_url}/api/oxapay/create-invoice",
                json={
                    "usd_amount": usd_amount,
                    "telegram_id": callback.from_user.id,
                    "user_id": user.id
                },
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                result = await resp.json()
    except Exception as e:
        logger.error(f"OxaPay invoice creation error: {e}")
        await callback.message.edit_text(
            "❌ <b>Failed to generate payment link.</b>\n\n"
            "Please try again or use UPI deposit instead.",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    if not result.get("success"):
        await callback.message.edit_text(
            f"❌ <b>OxaPay Error:</b> {result.get('detail', 'Unknown error')}\n\n"
            "Please try again later.",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    pay_link = result["pay_link"]
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Pay with OxaPay", url=pay_link))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    await callback.message.edit_text(
        f"✅ <b>Payment Link Ready!</b>\n\n"
        f"💵 Amount: <b>${usd_amount:.2f} USD</b>\n"
        f"₹ Will Credit: <b>₹{inr_amount:.2f} INR</b>\n\n"
        "👇 <b>Click the button below to pay:</b>\n\n"
        "<i>⚡ Your balance will be credited automatically once payment is confirmed.</i>\n"
        "<i>⏳ Payment link valid for 30 minutes.</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.clear()

@dp.callback_query(F.data == "btn_accounts")
async def process_accounts(callback: types.CallbackQuery):
    """Show available countries with stock counts - OPTIMIZED"""
    await callback.answer()
    
    async with async_session() as session:
        # OPTIMIZED: Single query with JOIN and GROUP BY instead of 64 separate queries
        # This reduces 8+ seconds to milliseconds!
        query = select(
            Country.id,
            Country.name,
            Country.emoji,
            Country.price,
            Country.price_usd,
            func.count(Account.id).label('stock')
        ).outerjoin(
            Account,
            (Account.country_id == Country.id) & 
            (Account.is_sold == False) & 
            (Account.type == 'ID')
        ).group_by(
            Country.id,
            Country.name,
            Country.emoji,
            Country.price,
            Country.price_usd
        ).having(
            func.count(Account.id) > 0
        ).order_by(
            Country.name
        )
        
        result = await session.execute(query)
        countries_with_stock = result.all()
        
        # Get exchange rate for dynamic pricing
        rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        rate_res = await session.execute(rate_stmt)
        rate_setting = rate_res.scalar_one_or_none()
        usd_inr_rate = float(rate_setting.value) if rate_setting else 84.0
    
    if not countries_with_stock:
        await callback.message.edit_text(
            "❌ <b>No accounts available at the moment.</b>\n\n"
            "Please check back later or contact support.",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        return

    builder = InlineKeyboardBuilder()
    for row in countries_with_stock:
        country_id = row.id
        country_name = row.name
        country_emoji = row.emoji
        stock = row.stock
        
        # Calculate dynamic price
        if getattr(row, 'price_usd', 0) > 0:
            effective_price = round(row.price_usd * usd_inr_rate, 2)
        else:
            effective_price = row.price
            
        button_text = f"{country_emoji} {country_name} | ₹{effective_price} | 📦 {stock}"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"country_{country_id}"))
    
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    await callback.message.edit_text(
        "🌐 <b> Select Country to Buy IDs 🛒</b>\n\n"
        f"📊 Exchange Rate: <b>$1 = ₹{usd_inr_rate}</b>\n"
        "✅ Showing Only Countries With Available Stock 📦",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("country_"))
async def process_country_selection(callback: types.CallbackQuery):
    country_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        stmt = select(Country).where(Country.id == country_id)
        result = await session.execute(stmt)
        country = result.scalar_one_or_none()

        if not country:
            await callback.answer("Country not found.")
            return

        # Count available stock for IDs
        stock_stmt = select(Account).where(
            Account.country_id == country_id,
            Account.is_sold == False,
            Account.type == "ID"
        )
        stock_res = await session.execute(stock_stmt)
        available_accounts = stock_res.scalars().all()
        available_stock = len(available_accounts)

        # Get exchange rate
        rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        rate_res = await session.execute(rate_stmt)
        rate_setting = rate_res.scalar_one_or_none()
        usd_inr_rate = float(rate_setting.value) if rate_setting else 84.0

        # Calculate dynamic price
        if country.price_usd > 0:
            effective_price = round(country.price_usd * usd_inr_rate, 2)
            pricing_text = f"₹{effective_price} ($ {country.price_usd})"
        else:
            effective_price = country.price
            pricing_text = f"₹{effective_price}"

        if available_stock == 0:
            text = f"🏴 <b>Country:</b> {country.emoji} {country.name}\n"
            text += f"💵 <b>Price per ID:</b> {pricing_text}\n"
            text += f"📦 <b>Available Stock:</b> {available_stock} IDs\n\n"
            text += "❌ Out of stock. Please check back later."
            
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="btn_accounts"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            return

        # Get first available account to show phone number
        preview_account = available_accounts[0]
        
        # Show confirmation with phone number and disclaimer
        text = f"🏴 <b>Country:</b> {country.emoji} {country.name}\n"
        text += f"💵 <b>Price:</b> {pricing_text}\n"
        text += f"📦 <b>Stock:</b> {available_stock} available\n\n"
        text += "⚠️ <b>IMPORTANT DISCLAIMER:</b>\n"
        text += "• We are NOT responsible for banned/frozen accounts\n"
        text += "• No refunds for account restrictions\n"
        text += "• Use at your own risk\n"
        text += "• Follow Telegram's Terms of Service\n\n"
        text += "✅ <b>Confirm purchase?</b>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="✅ Confirm Purchase",
            callback_data=f"confirm_buy_{country_id}"
        ))
        builder.row(InlineKeyboardButton(
            text="🔙 Back",
            callback_data="btn_accounts"
        ))
        builder.row(InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data="btn_main_menu"
        ))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("confirm_buy_"))
async def confirm_purchase_handler(callback: types.CallbackQuery):
    """CRITICAL HANDLER: Processes account purchases - This was MISSING!"""
    try:
        await callback.answer("Processing purchase...")
        country_id = int(callback.data.split("_")[2])
        
        async with async_session() as session:
            # Get user
            user_stmt = select(User).where(User.telegram_id == callback.from_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                await callback.message.edit_text(
                    "❌ User not found! Please /start the bot first.",
                    reply_markup=get_back_to_main(),
                    parse_mode="HTML"
                )
                return
            
            # Get country and price
            country_stmt = select(Country).where(Country.id == country_id)
            country_result = await session.execute(country_stmt)
            country = country_result.scalar_one_or_none()
            
            if not country:
                await callback.message.edit_text(
                    "❌ Country not found!",
                    reply_markup=get_back_to_main(),
                    parse_mode="HTML"
                )
                return
            
                return

            # Get exchange rate and calculate effective price
            rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
            rate_res = await session.execute(rate_stmt)
            rate_setting = rate_res.scalar_one_or_none()
            usd_inr_rate = float(rate_setting.value) if rate_setting else 84.0
            
            if country.price_usd > 0:
                effective_price = round(country.price_usd * usd_inr_rate, 2)
            else:
                effective_price = country.price

            # Check balance
            if user.balance < effective_price:
                text = f"❌ <b>Insufficient Balance!</b>\n\nRequired: ₹{effective_price}\nYour Balance: ₹{user.balance}\nNeed: ₹{round(effective_price - user.balance, 2)} more\n\n💰 Please add balance first!"
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="➕ Add Balance", callback_data="btn_deposit"))
                builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                return
            
            # Get available account
            account_stmt = select(Account).where(
                Account.country_id == country_id,
                Account.is_sold == False,
                Account.type == "ID"
            ).limit(1)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.message.edit_text(
                    "❌ <b>Out of Stock!</b>\n\nThis account was just sold. Please try another country.",
                    reply_markup=get_back_to_main(),
                    parse_mode="HTML"
                )
                return
            
            # Deduct balance & mark as sold
            user.balance -= effective_price
            account.is_sold = True
            
            # Create purchase record
            purchase = Purchase(
                user_id=user.id,
                account_id=account.id,
                amount=effective_price,
                created_at=datetime.utcnow()
            )
            session.add(purchase)
            await session.commit()
            await session.refresh(user)
            await session.refresh(purchase)
        
        # Show purchase success with OTP button (DELETE+SEND to prevent crash)
        try:
            await callback.message.delete()
        except:
            pass
        
        text = "🎉 <b>Purchase Successful!</b>\n\n"
        text += f"📱 <b>Phone Number:</b> <code>{account.phone_number}</code>\n"
        if account.twofa_password:
            text += f"🔐 <b>2FA Password:</b> <code>{account.twofa_password}</code>\n"
        
        text += f"\n💰 <b>Amount Paid:</b> ₹{effective_price}\n"
        text += f"💵 <b>New Balance:</b> ₹{user.balance}\n\n"
        text += "📋 <b>How to Login:</b>\n"
        text += "1️⃣ Open Telegram app\n"
        text += "2️⃣ Enter the phone number above\n"
        text += "3️⃣ Telegram will ask for OTP\n"
        text += "4️⃣ Click '📲 Get OTP Code' below\n\n"
        text += "✅ Account saved in your purchase history!"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📲 Get OTP Code", callback_data=f"get_otp_{purchase.id}"))
        builder.row(InlineKeyboardButton(text="📱 Manage Devices", callback_data=f"manage_sess_{purchase.id}"))
        builder.row(InlineKeyboardButton(text="📜 My Purchases", callback_data="btn_purchases"))
        builder.row(InlineKeyboardButton(text="🛒 Buy More", callback_data="btn_accounts"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await bot.send_message(
            callback.message.chat.id,
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        logger.info(f"✅ Purchase: User {user.telegram_id} bought {account.phone_number} for ₹{country.price}")
        
        # --- BROMO LOGS CHANNEL BROADCAST ---
        try:
            log_res = await session.execute(select(Settings).where(Settings.key == "log_channel_id"))
            log_setting = log_res.scalar_one_or_none()
            log_channel_id = str(log_setting.value).strip() if log_setting and log_setting.value else None
            
            if log_channel_id:
                owner_res = await session.execute(select(Settings).where(Settings.key == "bot_owner_username"))
                owner_setting = owner_res.scalar_one_or_none()
                owner_username = str(owner_setting.value).strip() if owner_setting and owner_setting.value else os.getenv("BOT_OWNER_USERNAME", "")
                
                # Mask phone number securely
                raw_phone = account.phone_number
                if len(raw_phone) > 7:
                    masked_phone = raw_phone[:4] + "****" + raw_phone[-2:]
                else:
                    masked_phone = raw_phone
                
                # Mask user ID securely
                raw_uid = str(user.telegram_id)
                if len(raw_uid) > 5:
                    masked_uid = raw_uid[:2] + "***" + raw_uid[-3:]
                else:
                    masked_uid = raw_uid
                
                log_text = "🚀 <b>NEW ACCOUNT SOLD!</b>\n\n"
                log_text += f"📁 <b>Category:</b> {country.emoji} {country.name} ({category.name})\n"
                log_text += f"📍 <b>Region:</b> {country.emoji} {country.name}\n"
                log_text += f"📱 <b>Number:</b> <code>{masked_phone}</code>\n"
                log_text += f"👤 <b>User:</b> <code>{masked_uid}</code>\n"
                log_text += "⚡ <b>Status:</b> Verified & Delivered\n"
                
                log_markup = None
                if owner_username:
                    url = f"https://t.me/{owner_username.replace('@', '')}"
                    log_builder = InlineKeyboardBuilder()
                    log_builder.row(InlineKeyboardButton(text="💬 Support / Buy", url=url))
                    log_markup = log_builder.as_markup()
                
                await bot.send_message(
                    chat_id=log_channel_id,
                    text=log_text,
                    reply_markup=log_markup,
                    parse_mode="HTML"
                )
        except Exception as log_err:
            logger.error(f"Failed to send broadcast log to channel: {log_err}")
        # ------------------------------------
        
    except Exception as e:
        logger.error(f"❌ Purchase error: {e}", exc_info=True)
        await callback.message.answer(
            "❌ <b>Purchase Failed!</b>\n\nAn error occurred. Please contact support.",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "btn_profile")
async def process_profile(callback: types.CallbackQuery):
    async with async_session() as session:
        # Get user details
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("User not found.")
            return

        # Calculate Total Spent
        spent_stmt = select(Purchase.amount).where(Purchase.user_id == user.id)
        spent_res = await session.execute(spent_stmt)
        total_spent = sum(spent_res.scalars().all())

        # Calculate Ranking (all users sum of purchases)
        all_users_stmt = select(User.id)
        all_users_res = await session.execute(all_users_stmt)
        all_user_ids = all_users_res.scalars().all()

        rankings = []
        for uid in all_user_ids:
            u_spent_stmt = select(Purchase.amount).where(Purchase.user_id == uid)
            u_spent_res = await session.execute(u_spent_stmt)
            rankings.append((uid, sum(u_spent_res.scalars().all())))
        
        # Sort rankings descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        user_rank = next((i + 1 for i, r in enumerate(rankings) if r[0] == user.id), "N/A")

        text = "👤 <b>Your Profile</b>\n\n"
        text += f"ID: <code>{user.telegram_id}</code>\n"
        text += f"Name: {user.full_name}\n"
        text += f"Username: @{user.username if user.username else 'N/A'}\n"
        text += f"💰 Balance: <b>₹{user.balance}</b>\n"
        text += f"💸 Total Spent: <b>₹{total_spent}</b>\n"
        text += f"🏆 Rank: <b>#{user_rank}</b> in total buyers\n\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📜 Transaction Deposits", callback_data="btn_transactions"))
        builder.row(InlineKeyboardButton(text="🛒 ID Buyed", callback_data="btn_purchases"))
        builder.row(InlineKeyboardButton(text="➕ Add Balance", callback_data="btn_deposit"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "btn_transactions")
async def process_transactions_history(callback: types.CallbackQuery):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        u_res = await session.execute(stmt)
        user = u_res.scalar_one_or_none()
        
        if not user: return
        
        dep_stmt = select(Deposit).where(Deposit.user_id == user.id).order_by(Deposit.created_at.desc()).limit(10)
        dep_res = await session.execute(dep_stmt)
        deposits = dep_res.scalars().all()
        
    text = "📜 <b>Recent Deposits</b>\n\n"
    if not deposits:
        text += "<i>No deposits found.</i>"
    else:
        for d in deposits:
            status_emo = "⏳" if d.status == "PENDING" else "✅" if d.status == "APPROVED" else "❌"
            text += f"{status_emo} ₹{d.amount} | {d.created_at.strftime('%Y-%m-%d')}\n"
            text += f"Ref: <code>{d.upi_ref_id}</code>\n\n"
            
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Back to Profile", callback_data="btn_profile"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "btn_purchases")
async def process_purchase_history(callback: types.CallbackQuery):
    """Show user's purchase history with interactive management buttons"""
    try:
        async with async_session() as session:
            # Get user
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
                await safe_edit_message(callback, text, reply_markup=builder.as_markup())
                return
            
            # Build purchase list
            text = f"📜 <b>My Purchases ({len(purchases)})</b>\n"
            text += "<i>Latest 10 purchases are shown below:</i>\n\n"
            
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
                    emoji = country.emoji if country else "🌍"
                    
                    text += f"{i}. {emoji} <b>{country_name}</b>\n"
                    text += f"   📱 <code>{account.phone_number}</code>\n"
                    text += f"   💰 ₹{purchase.amount} • {purchase.created_at.strftime('%d %b %Y')}\n\n"
            
            # Add control buttons (no individual manage buttons - keep it clean)
            builder.row(InlineKeyboardButton(text="🛒 Buy More", callback_data="btn_accounts"))
            builder.row(InlineKeyboardButton(text="👤 Profile", callback_data="btn_profile"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await safe_edit_message(callback, text, reply_markup=builder.as_markup())
            await callback.answer()
            
    except Exception as e:
        logger.error(f"❌ My purchases error: {e}", exc_info=True)
        await callback.answer("❌ Error loading purchases!", show_alert=True)


@dp.callback_query(F.data == "btn_main_menu")
async def process_main_menu(callback: types.CallbackQuery, state: FSMContext):
    # Clear any FSM state
    await state.clear()
    
    # Check if user is admin
    is_admin = False
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            is_admin = user.is_admin
            
    # FORCE Admin Check from Env Var (Fixes "Missing Admin Panel" bug)
    admin_telegram_id = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
    user_id_str = str(callback.from_user.id)
    
    logger.info(f"Menu Check: User={user_id_str}, AdminEnv={admin_telegram_id}")
    
    if admin_telegram_id and user_id_str == admin_telegram_id:
        is_admin = True
    
    # If message has photo (like QR code), delete it and send new message
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            f"<b><i>Welcome back! 🌟</i></b>\n\n"
            "💠 <b>Select an option below:</b>",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )
    else:
        # Regular text message, can edit
        await callback.message.edit_text(
            f"<b><i>Welcome back! 🌟</i></b>\n\n"
            "💠 <b>Select an option below:</b>",
            reply_markup=get_main_menu(is_admin=is_admin),
            parse_mode="HTML"
        )


@dp.callback_query(F.data.startswith("buy_id_"))
async def process_buy_id(callback: types.CallbackQuery):
    country_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        # Get user
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        # Get country
        stmt = select(Country).where(Country.id == country_id)
        result = await session.execute(stmt)
        country = result.scalar_one_or_none()

        if not user or not country:
            await callback.answer("Error: User or Country not found.")
            return

        if user.balance < country.price:
            await callback.answer(f"Insufficient balance. You need ₹{country.price - user.balance} more.", show_alert=True)
            return

        # Find available account
        stmt = select(Account).where(Account.country_id == country_id, Account.is_sold == False, Account.type == "ID").limit(1)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            await callback.answer("Out of stock for this country.", show_alert=True)
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

        await callback.message.answer(
            f"✅ <b>Purchase Successful!</b>\n\n"
            f"📱 Phone: <code>{account.phone_number}</code>\n"
            f"🔑 Session Data: <code>{account.session_data}</code>\n\n"
            "<i>Keep this safe!</i>",
            parse_mode="HTML"
        )
        await callback.answer("Success!")

@dp.callback_query(F.data == "btn_sessions")
async def process_sessions(callback: types.CallbackQuery):
    async with async_session() as session:
        # Get all countries
        stmt = select(Country)
        result = await session.execute(stmt)
        countries = result.scalars().all()
        
        # Calculate stock for each country (only Sessions)
        countries_with_stock = []
        for country in countries:
            stock_stmt = select(Account).where(
                Account.country_id == country.id,
                Account.is_sold == False,
                Account.type == "Session"
            )
            stock_res = await session.execute(stock_stmt)
            stock_count = len(stock_res.scalars().all())
            
            # Only include countries with available stock
            if stock_count > 0:
                countries_with_stock.append({
                    'country': country,
                    'stock': stock_count
                })

    if not countries_with_stock:
        await callback.message.edit_text(
            "❌ <b>No sessions available at the moment.</b>\n\n"
            "Please check back later or contact support.",
            reply_markup=get_back_to_main(),
            parse_mode="HTML"
        )
        return

    builder = InlineKeyboardBuilder()
    for item in countries_with_stock:
        country = item['country']
        stock = item['stock']
        button_text = f"{country.emoji} {country.name} | 📦 {stock} Sessions"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"session_{country.id}"))
    
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
    
    await callback.message.edit_text(
        "📱 <b>Select a country to buy Sessions:</b>\n\n"
        "Only showing countries with available stock.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("session_"))
async def process_session_country(callback: types.CallbackQuery):
    country_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        stmt = select(Country).where(Country.id == country_id)
        result = await session.execute(stmt)
        country = result.scalar_one_or_none()

        if not country:
            await callback.answer("Country not found.")
            return

        # Count available stock for Sessions
        stock_stmt = select(Account).where(
            Account.country_id == country_id,
            Account.is_sold == False,
            Account.type == "Session"
        )
        stock_res = await session.execute(stock_stmt)
        available_stock = len(stock_res.scalars().all())

        # Show price, stock, and buy button
        text = f"🏴 <b>Country (Session):</b> {country.emoji} {country.name}\n"
        text += f"💵 <b>Price per Session:</b> ₹{country.price}\n"
        text += f"📦 <b>Available Stock:</b> {available_stock} Sessions\n\n"
        
        if available_stock > 0:
            text += "✅ Click below to purchase session."
        else:
            text += "❌ Out of stock. Please check back later."
        
        builder = InlineKeyboardBuilder()
        if available_stock > 0:
            builder.row(InlineKeyboardButton(text="🛒 Buy Session", callback_data=f"buy_sess_{country.id}"))
        builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="btn_sessions"))
        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")



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
            try:
                await callback.message.delete()
            except:
                pass
            await callback.bot.send_message(
                callback.message.chat.id,
                "❌ <b>Error!</b>\n\n"
                "This account doesn't have session data configured.\n"
                "Please contact support.",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )
            return
        
        # Start monitoring
        try:
            logger.info(f"⚡ ATTEMPTING TO START MONITORING FOR {account.phone_number}")
            print(f"⚡ ATTEMPTING TO START MONITORING FOR {account.phone_number}")
            session_mgr = await get_session_manager_async()
            await session_mgr.start_monitoring(
                phone_number=account.phone_number,
                session_string=account.session_data
            )
            
            # Delete the old message and send a new one to avoid "message not modified" error
            try:
                await callback.message.delete()
            except:
                pass  # If delete fails, just continue
            
            # Send new message with OTP waiting screen
            new_message = await callback.bot.send_message(
                callback.message.chat.id,
                "🔄 <b>Starting OTP monitoring...</b>",
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🔙 Back", callback_data=f"manage_sess_{purchase_id}"))
                    .as_markup(),
                parse_mode="HTML"
            )
            
            # Start the OTP waiting loop with new message
            await show_otp_waiting(new_message, account.phone_number, purchase_id)
            
        except Exception as e:
            logger.error(f"Error starting OTP monitoring: {e}")
            # Only show error if it's NOT a "message is not modified" error
            if "message is not modified" not in str(e).lower():
                try:
                    await callback.bot.send_message(
                        callback.message.chat.id,
                        f"❌ <b>Error!</b>\n\n"
                        f"Failed to start OTP monitoring.\n\n"
                        "Please try again or contact support.",
                        reply_markup=InlineKeyboardBuilder()
                            .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                            .as_markup(),
                        parse_mode="HTML"
                    )
                except Exception as send_err:
                    logger.error(f"Could not send error message: {send_err}")
                    await callback.answer("❌ Error occurred. Please try again.", show_alert=True)
            else:
                # Silent ignore for "message is not modified" - it's harmless
                logger.debug(f"Ignoring harmless 'message is not modified' error")


async def show_otp_waiting(message: types.Message, phone_number: str, purchase_id: int, attempt: int = 0):
    """Show OTP waiting screen with manual check button"""
    session_mgr = await get_session_manager_async()
    
    # Check if login successful
    login_status = await session_mgr.check_login_status(phone_number)
    if login_status == "LOGGED_IN":
        await message.edit_text(
            f"🎉 <b>LOGIN DONE SUCCESSFULLY!</b>\n\n"
            f"🙏 <b>Thanks for Purchasing!</b>\n\n"
            f"📱 <b>Phone:</b> <code>{phone_number}</code>\n"
            f"✅ <b>Status:</b> Login Verified\n\n"
            f"🎊 <b>Congratulations!</b>\n"
            f"Your Telegram account is now active and ready to use!\n\n"
            f"💡 <b>Important Notes:</b>\n"
            f"• Account is fully yours now\n"
            f"• Keep your password secure\n"
            f"• Don't share session data\n"
            f"• Follow Telegram's Terms of Service\n\n"
            f"✨ <b>Enjoy your new Telegram account!</b>",
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(text="🛠️ Manage Sessions", callback_data=f"manage_sess_{purchase_id}"))
                .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                .row(InlineKeyboardButton(text="🛍️ Buy More", callback_data="btn_accounts"))
                .as_markup(),
            parse_mode="HTML"
        )
        await session_mgr.stop_monitoring(phone_number)
        return
    
    # Check for OTP (Active Fetch)
    # Using check_latest_otp instead of get_otp to robustly find code even if listener fails
    otp_code = await session_mgr.check_latest_otp(phone_number)
    
    if otp_code:
        # Get 2FA password from database
        async with async_session() as db_session:
            purchase_stmt = select(Purchase).where(Purchase.id == purchase_id)
            purchase_res = await db_session.execute(purchase_stmt)
            purchase = purchase_res.scalar_one_or_none()
            
            twofa_password = None
            if purchase:
                account_stmt = select(Account).where(Account.id == purchase.account_id)
                account_res = await db_session.execute(account_stmt)
                account = account_res.scalar_one_or_none()
                if account:
                    twofa_password = account.twofa_password
        
        # Build message with OTP and optional 2FA password
        text = f"✅ <b>OTP Code Received!</b>\n\n"
        text += f"📱 <b>Phone:</b> <code>{phone_number}</code>\n"
        text += f"🔑 <b>OTP Code:</b> <code>{otp_code}</code>\n"
        
        if twofa_password:
            text += f"🔐 <b>2FA Password:</b> <code>{twofa_password}</code>\n"
        
        text += f"\n📋 <b>Next Steps:</b>\n"
        text += f"1️⃣ Copy the OTP code above\n"
        text += f"2️⃣ Enter it in Telegram app\n"
        
        if twofa_password:
            text += f"3️⃣ Enter the 2FA password when asked\n"
            text += f"4️⃣ Wait for login verification...\n\n"
        else:
            text += f"3️⃣ Wait for login verification...\n\n"
        
        text += f"🔄 <i>Auto-detecting login status...</i>\n"
        text += f"💡 <i>Click 'Resend Code' if needed</i>"
        
        # OTP received, show it with resend and manage devices buttons
        await message.edit_text(
            text,
            reply_markup=InlineKeyboardBuilder()
                .row(InlineKeyboardButton(
                    text="🔄 Resend Code",
                    callback_data=f"resend_otp_{purchase_id}"
                ))
                .row(InlineKeyboardButton(
                    text="🛠️ Manage Devices",
                    callback_data=f"manage_sess_{purchase_id}"
                ))
                .row(InlineKeyboardButton(
                    text="⏹️ Stop Monitoring",
                    callback_data="btn_main_menu"
                ))
                .as_markup(),
            parse_mode="HTML"
        )
        # Continue monitoring for login
        await asyncio.sleep(5)
        await show_otp_waiting(message, phone_number, purchase_id, attempt + 1)
        
    # No OTP yet - show waiting message with manual check button
    # Add timestamp to show it's active
    current_time = datetime.now().strftime("%H:%M:%S")

    # No OTP yet - show waiting message with manual check button
    text = (
        f"⏳ <b>Waiting for your login...</b>\n\n"
        f"📱 <b>Phone:</b> <code>{phone_number}</code>\n\n"
        f"📋 <b>How to Login:</b>\n"
        f"1️⃣ Open <b>Telegram App</b> on your device\n"
        f"2️⃣ Tap '<b>Start Messaging</b>'\n"
        f"3️⃣ Enter this phone: <code>{phone_number}</code>\n"
        f"4️⃣ Request the verification code\n"
        f"5️⃣ Click 'Check for Code' button below!\n\n"
        f"💡 <i>Session monitoring is active</i>\n"
        f"🔄 <i>Auto-checking... ({attempt}/24)</i>\n"
        f"⏱️ <i>Refreshed: {current_time}</i>"
    )
    
    try:
        if attempt == 0:
             await message.edit_text(
                text,
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🔍 Check Code", callback_data=f"check_otp_{purchase_id}"))
                    .row(InlineKeyboardButton(text="🛠️ Manage Devices", callback_data=f"manage_sess_{purchase_id}"))
                    .row(InlineKeyboardButton(text="⏹️ Stop Waiting", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )
        else:
            await message.edit_text(
                text,
                reply_markup=InlineKeyboardBuilder()
                    .row(InlineKeyboardButton(text="🔍 Check Code", callback_data=f"check_otp_{purchase_id}"))
                    .row(InlineKeyboardButton(text="🛠️ Manage Devices", callback_data=f"manage_sess_{purchase_id}"))
                    .row(InlineKeyboardButton(text="⏹️ Stop Waiting", callback_data="btn_main_menu"))
                    .as_markup(),
                parse_mode="HTML"
            )
    except Exception as e:
        # Ignore "message is not modified" errors
        if "message is not modified" not in str(e).lower():
             logger.error(f"Error editing message: {e}")
    
    # Continue monitoring for 2 minutes (24 * 5s = 120s)
    if attempt < 24:
        await asyncio.sleep(5)
        await show_otp_waiting(message, phone_number, purchase_id, attempt + 1)
    else:
         await message.edit_text(
            f"❌ <b>Timeout!</b>\n\n"
            f"We waited 2 minutes but didn't receive the code.\n"
            f"Please try again or contact support.",
            reply_markup=InlineKeyboardBuilder()
                 .row(InlineKeyboardButton(text="🔄 Try Again", callback_data=f"get_otp_{purchase_id}"))
                 .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
                 .as_markup(),
            parse_mode="HTML"
        )



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
        
        # Clear OTP cache and FORCE ACTIVE CHECK
        session_mgr = await get_session_manager_async()
        session_mgr.clear_otp(account.phone_number)
        
        await callback.answer("Checking for new code...")
        
        # Active check to get the new code immediately
        await session_mgr.check_latest_otp(account.phone_number)
        
        # Call show_otp_waiting with error handling
        try:
            await show_otp_waiting(callback.message, account.phone_number, purchase_id)
        except Exception as e:
            # Silently ignore "message is not modified" errors
            if "message is not modified" not in str(e).lower():
                logger.error(f"Error in resend OTP: {e}")
                await callback.answer("❌ Error checking code. Please try again.", show_alert=True)
            else:
                logger.debug("Ignoring harmless 'message is not modified' error in resend_otp")
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
        
        # Check if monitoring is active
        session_mgr = await get_session_manager_async()
        login_status = await session_mgr.check_login_status(account.phone_number)
        
        if login_status == "NOT_MONITORING":
            await callback.answer("Reconnecting session...")
            try:
                # Restart monitoring
                await session_mgr.start_monitoring(
                    phone_number=account.phone_number,
                    session_string=account.session_data
                )
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Failed to restart monitoring: {e}")
                await callback.answer("Failed to reconnect session")
                return

        # FORCE ACTIVE CHECK: actively fetch history from 777000
        await callback.answer("Checking Telegram messages...")
        await session_mgr.check_latest_otp(account.phone_number)
        
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

# --- Device Management Handlers ---

@dp.callback_query(F.data.startswith("manage_sess_"))
async def process_manage_session(callback: types.CallbackQuery):
    """List active sessions for a purchase"""
    purchase_id = int(callback.data.split("_")[2])
    
    await callback.message.edit_text("🔄 <b>Connecting to Telegram...</b>\n\nPlease wait while we fetch active sessions...", parse_mode="HTML")
    
    async with async_session() as session:
        # Get Purchase -> Account -> Session String
        stmt = select(Purchase).where(Purchase.id == purchase_id)
        res = await session.execute(stmt)
        purchase = res.scalar_one_or_none()
        
        if not purchase:
            await callback.message.edit_text("❌ Purchase not found.", reply_markup=get_back_to_main())
            return
            
        stmt_acc = select(Account).where(Account.id == purchase.account_id)
        res_acc = await session.execute(stmt_acc)
        account = res_acc.scalar_one_or_none()
        
        if not account or not account.session_data:
            await callback.message.edit_text("❌ No session data found for this account.", reply_markup=get_back_to_main())
            return

        try:
            dm = DeviceManager()
            sessions = await dm.get_active_sessions(account.session_data)
            
            if not sessions:
                await callback.message.edit_text("❌ No active sessions found (weird).", reply_markup=get_back_to_main())
                return
                
            text = f"📱 <b>Active Sessions for {account.phone_number}</b>\n\n"
            text += "<i>Tap 🛑 Logout to remove any device below.</i>\n\n"
            
            for sess in sessions:
                # Mark current session (Bot)
                is_current = sess.get("is_current", False)
                status_icon = "🟢" if is_current else "⚪"
                device_name = f"{sess['device_model']} ({sess['platform']})"
                
                text += f"{status_icon} {device_name}"
                if is_current:
                    text += " (Current)"
                text += f"\n   └ IP: {sess['ip']}\n\n"

            text += f"💡 <i>Logout other devices to secure your account</i>\n"
            
            builder = InlineKeyboardBuilder()
            # Add Logout buttons for other sessions
            for sess in sessions:
                if not sess.get("is_current", False):
                    builder.row(InlineKeyboardButton(
                        text=f"🛑 Logout: {sess['device_model'][:15]}",
                        callback_data=f"kill_sess_{purchase_id}_{sess['hash']}"
                    ))

            builder.row(InlineKeyboardButton(text="📨 Get OTP Code", callback_data=f"get_otp_{purchase_id}")) # RESTORED: OTP ON MANUAL REQUEST
            builder.row(InlineKeyboardButton(text="🔄 Refresh Sessions", callback_data=f"manage_sess_{purchase_id}"))
            builder.row(InlineKeyboardButton(text="🔙 Back to Purchases", callback_data="btn_purchases"))
            builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Error managing sessions: {e}")
            await callback.message.edit_text(
                f"❌ <b>Error fetching sessions</b>\n\n{str(e)}",
                reply_markup=get_back_to_main(),
                parse_mode="HTML"
            )

@dp.callback_query(F.data.startswith("kill_sess_"))
async def process_kill_session(callback: types.CallbackQuery):
    """Terminate a session"""
    parts = callback.data.split("_")
    purchase_id = int(parts[2])
    session_hash = int(parts[3])
    
    await callback.answer("Logging out device...", show_alert=False)
    
    async with async_session() as session:
        # Get Account
        stmt = select(Purchase).where(Purchase.id == purchase_id)
        res = await session.execute(stmt)
        purchase = res.scalar_one_or_none()
        
        if not purchase: return
        
        stmt_acc = select(Account).where(Account.id == purchase.account_id)
        res_acc = await session.execute(stmt_acc)
        account = res_acc.scalar_one_or_none()
        
        if not account: return

        try:
            dm = DeviceManager()
            success = await dm.terminate_session(account.session_data, session_hash)
            
            if success:
                await callback.answer("✅ Device logged out successfully!", show_alert=True)
                # Refresh list
                await process_manage_session(callback)
            else:
                await callback.answer("❌ Failed to logout device.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error killing session: {e}")
            
            # Check if it's Telegram's "fresh login" security restriction
            error_msg = str(e).lower()
            if "fresh_reset_authorisation_forbidden" in error_msg or "logged-in recently" in error_msg:
                await callback.answer(
                    "🔒 Security Restriction\n\n"
                    "Telegram doesn't allow logging out other devices for 24 hours after a fresh login.\n\n"
                    "⏰ Please try again tomorrow!",
                    show_alert=True
                )
            else:
                await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
"""

Complete Deposit Flow for Telegram Bot

Handles: Amount   ->  UTR   ->  Screenshot   ->  Admin Approval

"""



# Add this to backend/bot.py after the DepositStates class definition



# Deposit Flow Handlers





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

        

        # Store amount in state

        await state.update_data(amount=amount)

        

        # Get payment settings from database

        async with async_session() as session:

            # Get UPI ID from settings

            upi_stmt = select(Settings).where(Settings.key == "upi_id")

            upi_res = await session.execute(upi_stmt)

            upi_setting = upi_res.scalar_one_or_none()

            upi_id = upi_setting.value if upi_setting else "Not configured"

        

        await message.answer(

            f"💰 <b>Payment Details</b>\n\n"

            f"Amount to Pay: ₹ {amount}\n"

            f"UPI ID: <code>{upi_id}</code>\n\n"

            f"✅ <b>Next Steps:</b>\n"

            f"1. Send ₹ {amount} to the UPI ID above\n"

            f"2. After payment, enter the UTR/Transaction ID\n\n"

            f"💰 UTR is the 12-digit reference number from your payment",

            parse_mode="HTML"

        )

        

        await message.answer(

            "Please enter your UTR/Transaction ID:",

            parse_mode="HTML"

        )

        

        await state.set_state(DepositStates.waiting_for_utr)

        

    except ValueError:

        await message.answer("❌ Invalid amount. Please enter a valid number.")





@dp.message(DepositStates.waiting_for_utr)

async def process_deposit_utr(message: types.Message, state: FSMContext):

    """Process UTR input"""

    utr = message.text.strip()

    

    # Validate UTR format (usually 12 digits)

    if len(utr) < 6:

        await message.answer("❌ UTR seems too short. Please check and try again.")

        return

    

    # Store UTR in state

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

    """Process screenshot upload"""

    

    if not message.photo:

        await message.answer(

            "❌ Please send a photo/screenshot of your payment.\n\n"

            "💰 Click the attachment icon and select a photo."

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

        

        # Create deposit record

        deposit = Deposit(

            user_id=user.id,

            amount=amount,

            upi_ref_id=utr,  #    THIS IS THE UTR FIELD

            screenshot_path=f"photo_{message.photo[-1].file_id}",

            status="PENDING"

        )

        

        session.add(deposit)

        await session.commit()

        await session.refresh(deposit)

    

    await state.clear()

    

    await message.answer(

        f"✅ <b>Deposit Request Submitted!</b>\n\n"

        f"💰 Amount: ₹ {amount}\n"

        f"🆔 UTR: <code>{utr}</code>\n"

        f"⏳ Status: Pending Admin Approval\n\n"

        f" Your deposit will be approved within 24 hours.\n"

        f"You'll be notified once it's approved!",

        reply_markup=InlineKeyboardBuilder()

            .row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))

            .as_markup(),

        parse_mode="HTML"

    )

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

        text = "📸 <b>Available Accounts</b>\n\n"

        

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

            text += f"📦 Stock: {stock_count} Pcs | 💰 Price: ₹ {country.price:.2f}\n\n"

            

            # Add button only if stock available

            if stock_count > 0:

                builder.row(InlineKeyboardButton(

                    text=f"{country.emoji} {country.name} ({stock_count} available)",

                    callback_data=f"country_{country.id}"

                ))

        

        text += "💰 <i>Select a country to purchase</i>"

        

        # Add back button

        builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))

        

        await safe_edit_message(callback, text, reply_markup=builder.as_markup())

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

            await message.answer("R Minimum deposit is  10. Please try again.")

            return

        

        if amount > 50000:

            await message.answer("R Maximum deposit is  50,000. Please try again.")

            return

        

        await state.update_data(amount=amount)

        

        # Get UPI ID from settings

        async with async_session() as session:

            upi_stmt = select(Settings).where(Settings.key == "upi_id")

            upi_res = await session.execute(upi_stmt)

            upi_setting = upi_res.scalar_one_or_none()

            upi_id = upi_setting.value if upi_setting else "payment@upi"

        

        await message.answer(

            f"x  <b>Payment Details</b>\n\n"

            f"Amount to Pay:  {amount}\n"

            f"UPI ID: <code>{upi_id}</code>\n\n"

            f"x 9  <b>Next Steps:</b>\n"

            f"1 Send  {amount} to the UPI ID above\n"

            f"2 After payment, enter the UTR/Transaction ID\n\n"

            f"x  UTR is the 12-digit reference number from your payment",

            parse_mode="HTML"

        )

        

        await message.answer("Please enter your UTR/Transaction ID:")

        await state.set_state(DepositStates.waiting_for_utr)

        

    except ValueError:

        await message.answer("R Invalid amount. Please enter a valid number.")





@dp.message(DepositStates.waiting_for_utr)

async def process_deposit_utr(message: types.Message, state: FSMContext):

    """Process UTR input - CRITICAL: This saves the UTR"""

    utr = message.text.strip()

    

    if len(utr) < 6:

        await message.answer("R UTR seems too short. Please check and try again.")

        return

    

    # CRITICAL: Save UTR in state

    await state.update_data(utr=utr)

    

    await message.answer(

        f"S&  UTR Recorded: <code>{utr}</code>\n\n"

        f"x  <b>Upload Payment Screenshot</b>\n\n"

        f"Please send a screenshot of your payment confirmation.",

        parse_mode="HTML"

    )

    

    await state.set_state(DepositStates.waiting_for_screenshot)





@dp.message(DepositStates.waiting_for_screenshot)

async def process_deposit_screenshot(message: types.Message, state: FSMContext):

    """Process screenshot and save deposit with UTR"""

    

    if not message.photo:

        await message.answer(

            "R Please send a photo/screenshot of your payment.\n\n"

            "x  Click the attachment icon and select a photo."

        )

        return

    

    # Get state data

    data = await state.get_data()

    amount = data.get('amount')

    utr = data.get('utr')

    

    if not amount or not utr:

        await message.answer("R Session expired. Please start over with /start")

        await state.clear()

        return

    

    # Get user

    async with async_session() as session:

        user_stmt = select(User).where(User.telegram_id == message.from_user.id)

        user_res = await session.execute(user_stmt)

        user = user_res.scalar_one_or_none()

        

        if not user:

            await message.answer("R User not found. Please use /start first.")

            await state.clear()

            return

        

        # CRITICAL: Create deposit with UTR in upi_ref_id field

        deposit = Deposit(

            user_id=user.id,

            amount=amount,

            upi_ref_id=utr,  #    THIS IS WHERE UTR IS SAVED

            screenshot_path=f"photo_{message.photo[-1].file_id}",

            status="PENDING"

        )

        

        session.add(deposit)

        await session.commit()

        await session.refresh(deposit)

    

    await state.clear()

    

    await message.answer(

        f"S&  <b>Deposit Request Submitted!</b>\n\n"

        f"x  Amount:  {amount}\n"

        f"x   UTR: <code>{utr}</code>\n"

        f"x ` Status: Pending Admin Approval\n\n"

        f" Your deposit will be approved within 24 hours.\n"

        f"You'll be notified once it's approved!",

        reply_markup=InlineKeyboardBuilder()

            .row(InlineKeyboardButton(text="x Main Menu", callback_data="btn_main_menu"))

            .as_markup(),

        parse_mode="HTML"

    )




# === SESSION MANAGEMENT HANDLERS ===












# === SUPPORT & BROADCAST HANDLERS ===

@dp.callback_query(F.data == "btn_help")
async def process_help_button(callback: types.CallbackQuery):
    """Handle support button - BULLETPROOF version with full error handling"""
    try:
        # STEP 1: Try to get from ENVIRONMENT VARIABLES (Koyeb)
        channel_link = os.getenv("BOT_CHANNEL_LINK", "").strip()
        owner_username = os.getenv("BOT_OWNER_USERNAME", "").strip()
        
        logger.info(f"🔍 ENV CHECK - Channel: '{channel_link}', Owner: '{owner_username}'")
        
        # STEP 2: If not in env vars, try database as fallback
        if not channel_link or not owner_username:
            logger.warning("⚠️ Environment variables not set, checking database...")
            try:
                async with async_session() as session:
                    if not channel_link:
                        chan_stmt = select(Settings).where(Settings.key == "bot_channel_link")
                        chan_res = await session.execute(chan_stmt)
                        chan_setting = chan_res.scalar_one_or_none()
                        if chan_setting and chan_setting.value:
                            channel_link = str(chan_setting.value).strip()
                            logger.info(f"📊 Found channel in database: {channel_link}")
                    
                    if not owner_username:
                        owner_stmt = select(Settings).where(Settings.key == "bot_owner_username")
                        owner_res = await session.execute(owner_stmt)
                        owner_setting = owner_res.scalar_one_or_none()
                        if owner_setting and owner_setting.value:
                            owner_username = str(owner_setting.value).strip()
                            logger.info(f"📊 Found owner in database: {owner_username}")
            except Exception as db_error:
                logger.error(f"❌ Database error in support handler: {db_error}")
                # Continue anyway with whatever values we have
        else:
            logger.info("✅ Using values from ENVIRONMENT VARIABLES!")
        
        # STEP 3: Build response
        if channel_link or owner_username:
            text = "🆘 <b>Support & Contact</b>\n\n"
            
            if channel_link:
                text += f"📢 <b>Official Channel:</b>\n{channel_link}\n\n"
            
            if owner_username:
                text += f"👤 <b>Contact Support:</b>\n{owner_username}\n\n"
            
            text += "We're here to help! 💙"
        else:
            # If neither is set anywhere
            text = (
                "🆘 <b>Support</b>\n\n"
                "⚠️ Support contact information not configured.\n\n"
                "Admin: Set BOT_CHANNEL_LINK and BOT_OWNER_USERNAME\n"
                "in Koyeb environment variables."
            )
            logger.error("❌ NO SUPPORT INFO FOUND - Not in env vars OR database!")
        
        # STEP 4: Send response with error handling
        try:
            keyboard = InlineKeyboardBuilder()
            keyboard.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            await callback.answer()
            logger.info("✅ Support handler completed successfully")
        except Exception as send_error:
            logger.error(f"❌ Error sending support message: {send_error}")
            # Try to at least answer the callback to prevent timeout
            try:
                await callback.answer("❌ Error displaying support info", show_alert=True)
            except:
                pass  # If even this fails, just log it
                
    except Exception as e:
        # ULTIMATE FALLBACK - catch ANY error
        logger.error(f"❌ CRITICAL ERROR in support handler: {e}", exc_info=True)
        try:
            # Try to send a simple error message
            await callback.answer("❌ Support temporarily unavailable", show_alert=True)
        except:
            pass  # If this fails too, bot won't crash

# Broadcast States (defined locally to avoid import issues)
class BroadcastMessageStates(StatesGroup):
    waiting_for_message = State()

@dp.callback_query(F.data == "btn_broadcast")
async def process_broadcast_button(callback: types.CallbackQuery, state: FSMContext):
    """Admin clicked Broadcast button"""
    admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    
    if callback.from_user.id != admin_id:
        await callback.answer("❌ Admin only!", show_alert=True)
        return

    await callback.bot.send_message(
        callback.message.chat.id,
        "📢 <b>Broadcast Message</b>\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "💡 <i>You can send text, photos, or videos.</i>\n"
        "⚠️ <i>This will be sent to ALL users in the database.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().row(
            InlineKeyboardButton(text="❌ Cancel", callback_data="btn_main_menu")
        ).as_markup()
    )
    
    # Set state for waiting for broadcast message
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
                    message.html_text if hasattr(message, 'html_text') else message.text,
                    parse_mode="HTML"
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
            
            # Update status for large broadcasts (every 10 users)
            if success_count % 10 == 0:
                try:
                    await status_msg.edit_text(
                        f"📤 <b>Broadcasting...</b>\n\n"
                        f"✅ Sent: {success_count}\n"
                        f"❌ Failed: {failed_count}\n"
                        f"⏳ Remaining: {len(users) - success_count - failed_count}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass  # Ignore "message is not modified"
            
            # Respect Telegram's broadcast limits (~30 msg/sec)
            await asyncio.sleep(0.05)
            
        except TelegramForbiddenError:
            logger.error(f"🚫 User {user.telegram_id} blocked the bot")
            failed_count += 1
        except TelegramRetryAfter as e:
            logger.warning(f"⏳ Rate limited. Waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            # Re-attempt once after retry delay
            try:
                if message.text:
                    await bot.send_message(user.telegram_id, message.html_text if hasattr(message, 'html_text') else message.text, parse_mode="HTML")
                elif message.photo:
                    await bot.send_photo(user.telegram_id, message.photo[-1].file_id, caption=message.caption or "")
                success_count += 1
            except Exception:
                failed_count += 1
        except TelegramAPIError as e:
            if "chat not found" in str(e).lower() or "user is deactivated" in str(e).lower():
                logger.warning(f"🗑️ User {user.telegram_id} deleted chat or is deactivated")
            else:
                logger.error(f"❌ Telegram API Error for {user.telegram_id}: {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"❓ Unexpected failure for {user.telegram_id}: {e}")
            failed_count += 1
    
    # Final status
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"Total users: {len(users)}\n"
        f"✅ Successfully sent: {success_count}\n"
        f"❌ Failed/Skipped: {failed_count}\n\n"
        f"💡 <i>Includes users who blocked bot or deleted chat.</i>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("terminate_device_"))
async def terminate_device_handler(callback: types.CallbackQuery):
    """Terminate a specific device session"""
    try:
        parts = callback.data.split("_")
        account_id = int(parts[2])
        session_hash = int(parts[3])
        
        # Get account
        async with async_session() as session:
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("❌ Account not found!", show_alert=True)
                return
        
        # Terminate using Pyrogram
        try:
            from backend.pyrogram_devices import terminate_session
            api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            await terminate_session(account.session_data, api_id, api_hash, session_hash)
        except Exception as e:
            logger.error(f"Pyrogram error: {e}")
            await callback.answer(f"❌ Failed: {str(e)[:50]}", show_alert=True)
            return
        
        await callback.answer("âœ… Device terminated!", show_alert=True)
        
        text = f"âœ… <b>Device Terminated</b>\n\n"
        text += f"The device has been logged out successfully.\n\n"
        text += "<i>It will no longer have access to this account.</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="ðŸ“± View Devices", callback_data=f"manage_devices_{account_id}"))
        builder.row(InlineKeyboardButton(text="ðŸ  Main Menu", callback_data="btn_main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"âŒ Terminate device error: {e}", exc_info=True)
        await callback.answer("âŒ Error terminating device!", show_alert=True)


@dp.callback_query(F.data.startswith("terminate_all_"))
async def terminate_all_handler(callback: types.CallbackQuery):
    """Terminate all other devices except current"""
    try:
        account_id = int(callback.data.split("_")[2])
        
        # Get account
        async with async_session() as session:
            account_stmt = select(Account).where(Account.id == account_id)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()
            
            if not account:
                await callback.answer("âŒ Account not found!", show_alert=True)
                return
        
        # Terminate all using Pyrogram
        try:
            from backend.pyrogram_devices import terminate_all_except_current
            api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            await terminate_all_except_current(account.session_data, api_id, api_hash)
            
            await callback.answer("âœ… All devices terminated!", show_alert=True)
            
            text = "âœ… <b>All Other Devices Terminated</b>\n\n"
            text += "All other devices have been logged out.\n\n"
            text += "<i>Only the current device remains active.</i>"
            
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="ðŸ“± View Devices", callback_data=f"manage_devices_{account_id}"))
            builder.row(InlineKeyboardButton(text="ðŸ  Main Menu", callback_data="btn_main_menu"))
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Pyrogram error: {e}")
            await callback.answer(f"âŒ Failed: {str(e)[:50]}", show_alert=True)
        
    except Exception as e:
        logger.error(f"âŒ Terminate all error: {e}", exc_info=True)
        await callback.answer("âŒ Error!", show_alert=True)
# === ADMIN CONFIG COMMANDS REMOVED ===
# Support values now configured via environment variables on Koyeb:
# Set these in Koyeb Environment Variables:
# - BOT_CHANNEL_LINK=https://t.me/yourchannel
# - BOT_OWNER_USERNAME=@yourusername


