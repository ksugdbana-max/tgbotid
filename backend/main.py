from fastapi import FastAPI, Depends, HTTPException, status, Body, Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import init_db, async_session
from .bot import bot, dp
from .models import User, Country, Account, Purchase, Deposit, Settings
from aiogram.types import Update
from .session_manager import get_session_manager
from .session_generator_service import get_session_generator, get_session_generator_async
from sqlalchemy import select, update, delete
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import os
import base64
from fastapi import UploadFile, File, Form
import aiohttp # For webhook setup in startup event
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Schemas ---
class CountryCreate(BaseModel):
    name: str
    emoji: str
    price: float = 0.0
    price_usd: float = 0.0

class AccountCreate(BaseModel):
    country_id: int
    phone_number: str
    session_data: str
    type: str = "ID"
    twofa_password: str | None = None

class DepositUpdate(BaseModel):
    status: str # APPROVED, REJECTED

class LoginRequest(BaseModel):
    password: str

class BalanceAdjustment(BaseModel):
    amount: float
    reason: str  # "admin_add" or "admin_deduct"

# Webhook Configuration
WEBHOOK_PATH = "/webhook"
# BASE_WEBHOOK_URL must be set as environment variable on Koyeb
# Example: BASE_WEBHOOK_URL=https://your-app-name.koyeb.app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    await init_db()
    
    # Set Webhook on Startup with error handling
    try:
        base_url = os.getenv("BASE_WEBHOOK_URL")
        
        if not base_url:
            print("❌ ERROR: BASE_WEBHOOK_URL environment variable not set!", flush=True)
            print("   Set it on Railway to your app URL (e.g., https://your-app.up.railway.app)", flush=True)
        else:
            # Smart URL construction: don't double append /webhook
            if base_url.endswith("/webhook"):
                webhook_url = base_url
            else:
                webhook_url = f"{base_url.rstrip('/')}/webhook"
            
            print(f"🔄 Setting webhook to: {webhook_url}", flush=True)
            
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
            
            # Verify Webhook
            info = await bot.get_webhook_info()
            print(f"✅ Webhook set successfully!", flush=True)
            print(f"   URL: {info.url}", flush=True)
            print(f"   Pending updates: {info.pending_update_count}", flush=True)
            
            if info.last_error_message:
                print(f"⚠️ Last webhook error: {info.last_error_message}", flush=True)
                print(f"   Error date: {info.last_error_date}", flush=True)
            
    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}", flush=True)
        print(f"   Bot will continue but webhook may not work!", flush=True)
    
    yield
    
    # Delete Webhook on Shutdown
    try:
        await bot.delete_webhook()
    except:
        pass
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Add CORS Middleware - allow all origins (auth is token-based, not cookie-based)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "webhook", "service": "Telegram Bot Backend"}


# === CRITICAL: WEBHOOK ENDPOINT ===

@app.post(WEBHOOK_PATH)
async def webhook_handler(update: dict):
    """Receive and process Telegram updates"""
    try:
        telegram_update = Update(**update)
        await dp.feed_update(bot=bot, update=telegram_update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return {"ok": False}


@app.post("/api/fix-webhook")
async def fix_webhook_endpoint():
    """
    Manual webhook fix endpoint for admin panel
    Deletes old webhook and sets new one
    """
    try:
        import os
        import aiohttp
        import asyncio
        import logging
        
        logger = logging.getLogger(__name__)
        
        bot_token = os.getenv("BOT_TOKEN")
        base_url = os.getenv("BASE_WEBHOOK_URL")
        
        if not base_url:
            logger.error("❌ BASE_WEBHOOK_URL not set in environment!")
            return {"success": False, "error": "BASE_WEBHOOK_URL not configured"}
        
        # Smart URL construction
        if base_url.endswith("/webhook"):
            webhook_url = base_url
        else:
            webhook_url = f"{base_url.rstrip('/')}/webhook"
            
        logger.info(f"🔧 Admin requested webhook fix to: {webhook_url}")
        
        async with aiohttp.ClientSession() as session:
            # Delete old webhook
            delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            async with session.post(delete_url, json={"drop_pending_updates": True}) as response:
                delete_result = await response.json()
                logger.info(f"🗑️ Webhook deleted: {delete_result.get('ok', False)}")
            
            # Wait for Telegram to process
            await asyncio.sleep(2)
            
            # Set new webhook
            set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            webhook_data = {
                "url": webhook_url,
                "drop_pending_updates": True,
                "max_connections": 100,
                "allowed_updates": ["message", "callback_query"]
            }
            
            async with session.post(set_url, json=webhook_data) as response:
                set_result = await response.json()
                
                if set_result.get('ok'):
                    # Verify webhook
                    verify_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                    async with session.get(verify_url) as verify_response:
                        verify_data = await verify_response.json()
                        webhook_info = verify_data.get('result', {})
                        
                        logger.info(f"✅ Webhook fixed and verified: {webhook_url}")
                        
                        return {
                            "success": True,
                            "message": "Webhook fixed successfully!",
                            "webhook_info": {
                                "url": webhook_info.get('url'),
                                "pending_updates": webhook_info.get('pending_update_count', 0),
                                "max_connections": webhook_info.get('max_connections', 0)
                            }
                        }
                else:
                    logger.error(f"❌ Failed to set webhook: {set_result}")
                    return {
                        "success": False,
                        "message": f"Failed to set webhook: {set_result.get('description', 'Unknown error')}"
                    }
                    
    except Exception as e:
        logger.error(f"❌ Webhook fix error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.get("/health")
@app.head("/health")  # Support HEAD requests for UptimeRobot
async def detailed_health():
    """Detailed health check with database and webhook verification"""
    health_status = {"status": "healthy", "checks": {}}
    
    # Check database connection
    try:
        async with async_session() as session:
            await session.execute(select(User).limit(1))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)[:100]}"
    
    # Check webhook
    try:
        info = await bot.get_webhook_info()
        health_status["checks"]["webhook"] = {
            "url": info.url,
            "pending_updates": info.pending_update_count
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["webhook"] = f"error: {str(e)[:100]}"
    
    return health_status

# Removed duplicate middleware - handled at top level

# Add timeout middleware for request protection
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import logging

# Get logger for middleware
middleware_logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to prevent requests from hanging indefinitely.
    Adds timeout protection to all HTTP requests.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            # Set timeout for request processing (30 seconds max)
            response = await asyncio.wait_for(call_next(request), timeout=30.0)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except asyncio.TimeoutError:
            middleware_logger.error(f"Request timeout: {request.url.path}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=504,
                content={"detail": "Request processing timeout. Please try again."}
            )
        except Exception as e:
            middleware_logger.error(f"Request error: {e}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Please try again."}
            )

app.add_middleware(TimeoutMiddleware)


# Removed duplicate webhook - handled at line 117

# Removed duplicate middleware - handled at top level

# Admin API and Frontend serving below

@app.post("/api/login")
async def login(request: LoginRequest):
    """Admin login endpoint - reads password from ADMIN_PASSWORD or ADMIN_TOKEN env var"""
    try:
        # Get admin password from environment variable (support both names)
        admin_password = os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_TOKEN") or "admin123"
        
        logger.info(f"🔐 Login attempt received.")
        
        # Check password
        if request.password == admin_password:
            logger.info("✅ Login successful!")
            # Create a simple token (in production, use proper JWT)
            token = "admin_token_" + str(hash(admin_password))
            return {"token": token, "success": True}
        else:
            logger.warning("❌ Login failed - incorrect password")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

# COMPATIBILITY: Also support /admin/login endpoint (frontend uses this)
@app.post("/admin/login")
async def admin_login(request: LoginRequest):
    """Admin login - compatibility endpoint, calls main login function"""
    return await login(request)

class TelegramAuthRequest(BaseModel):
    init_data: str  # Raw initData string from window.Telegram.WebApp.initDataUnsafe

@app.post("/admin/telegram-login")
async def telegram_login(request: TelegramAuthRequest):
    """Auto-login for Telegram Mini App - validates initData and checks admin status"""
    import hmac, hashlib, json
    try:
        bot_token = os.getenv("BOT_TOKEN", "")
        admin_telegram_id = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
        if not bot_token:
            raise HTTPException(status_code=500, detail="Bot token not configured")

        # Parse the initData string
        from urllib.parse import parse_qs, unquote
        params = {}
        for part in request.init_data.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[k] = unquote(v)

        received_hash = params.pop("hash", "")
        if not received_hash:
            raise HTTPException(status_code=401, detail="Missing hash in initData")

        # Validate HMAC
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(received_hash, expected_hash):
            raise HTTPException(status_code=401, detail="Invalid initData signature")

        # Parse user info
        user_data = json.loads(params.get("user", "{}"))
        telegram_id = str(user_data.get("id", ""))

        if not telegram_id:
            raise HTTPException(status_code=401, detail="No user info in initData")

        # Check if this is the admin
        if telegram_id != admin_telegram_id:
            raise HTTPException(status_code=403, detail="Not authorized as admin")

        # Issue token
        admin_password = os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_TOKEN") or "admin123"
        token = "admin_token_" + str(hash(admin_password))
        logger.info(f"✅ Telegram auto-login successful for admin {telegram_id}")
        return {"token": token, "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin API Routes ---

@app.get("/admin/countries")
async def get_countries():
    async with async_session() as session:
        result = await session.execute(select(Country))
        return result.scalars().all()

@app.post("/admin/countries")
async def create_country(country: CountryCreate):
    async with async_session() as session:
        db_country = Country(**country.model_dump())
        session.add(db_country)
        await session.commit()
        return db_country

@app.delete("/admin/countries/{country_id}")
async def delete_country(country_id: int):
    async with async_session() as session:
        await session.execute(delete(Country).where(Country.id == country_id))
        await session.commit()
        return {"message": "Country deleted"}

class CountryUpdate(BaseModel):
    price: Optional[float] = None
    price_usd: Optional[float] = None

@app.put("/admin/countries/{country_id}")
async def update_country(country_id: int, update_data: CountryUpdate):
    async with async_session() as session:
        result = await session.execute(select(Country).where(Country.id == country_id))
        db_country = result.scalar_one_or_none()
        if not db_country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        if update_data.price is not None:
            db_country.price = update_data.price
        if update_data.price_usd is not None:
            db_country.price_usd = update_data.price_usd
            
        await session.commit()
        await session.refresh(db_country)
        return db_country

@app.get("/admin/accounts")
async def get_accounts():
    async with async_session() as session:
        result = await session.execute(select(Account))
        return result.scalars().all()

@app.post("/admin/accounts")
async def add_account(account: AccountCreate):
    async with async_session() as session:
        # REMOVED duplicate check - allows restocking same number after sold
        
        db_account = Account(
            country_id=account.country_id,
            phone_number=account.phone_number,
            session_data=account.session_data,
            type=account.type,
            twofa_password=account.twofa_password,
            is_sold=False  # Explicitly ensure new accounts are available
        )
        session.add(db_account)
        await session.commit()
        await session.refresh(db_account)
        return db_account

@app.get("/admin/stats")
async def get_admin_stats():
    """Get dashboard statistics using efficient SQL aggregations"""
    async with async_session() as session:
        # Use SQL COUNT instead of loading all users into memory
        from sqlalchemy import func
        
        # Total Users - use COUNT
        users_count = await session.scalar(select(func.count(User.id)))
        
        # Total Sales - use SUM aggregation
        total_sales_result = await session.scalar(select(func.sum(Purchase.amount)))
        total_sales = total_sales_result if total_sales_result else 0
        
        # Pending Deposits - use COUNT with filter
        pending_count = await session.scalar(
            select(func.count(Deposit.id)).where(Deposit.status == "PENDING")
        )
        
        return {
            "total_users": users_count or 0,
            "total_sales": float(total_sales),
            "pending_deposits": pending_count or 0
        }

@app.get("/admin/settings/payment")
async def get_payment_settings():
    """Fetch current payment settings and bot config"""
    async with async_session() as session:
        upi_res = await session.execute(select(Settings).where(Settings.key == "payment_upi_id"))
        qr_res = await session.execute(select(Settings).where(Settings.key == "payment_qr_image"))
        channel_res = await session.execute(select(Settings).where(Settings.key == "bot_channel_link"))
        owner_res = await session.execute(select(Settings).where(Settings.key == "bot_owner_username"))
        
        upi_id = upi_res.scalar_one_or_none()
        qr_image = qr_res.scalar_one_or_none()
        channel_link = channel_res.scalar_one_or_none()
        owner_username = owner_res.scalar_one_or_none()
        
        return {
            "upi_id": upi_id.value if upi_id else "",
            "qr_image": qr_image.value if qr_image else "",
            "channel_link": channel_link.value if channel_link else "",
            "owner_username": owner_username.value if owner_username else ""
        }

@app.post("/admin/settings/payment")
async def update_payment_settings(
    upi_id: str = Form(""),
    qr_image: UploadFile = File(None),
    channel_link: str = Form(""),
    owner_username: str = Form("")
):
    """Update payment settings and bot configuration"""
    async with async_session() as session:
        # Update or create UPI ID
        upi_stmt = select(Settings).where(Settings.key == "payment_upi_id")
        upi_res = await session.execute(upi_stmt)
        upi_setting = upi_res.scalar_one_or_none()
        
        if upi_setting:
            upi_setting.value = upi_id
        else:
            session.add(Settings(key="payment_upi_id", value=upi_id))
        
        # Update or create channel link
        channel_stmt = select(Settings).where(Settings.key == "bot_channel_link")
        channel_res = await session.execute(channel_stmt)
        channel_setting = channel_res.scalar_one_or_none()
        
        if channel_setting:
            channel_setting.value = channel_link
        else:
            session.add(Settings(key="bot_channel_link", value=channel_link))
        
        # Update or create owner username
        owner_stmt = select(Settings).where(Settings.key == "bot_owner_username")
        owner_res = await session.execute(owner_stmt)
        owner_setting = owner_res.scalar_one_or_none()
        
        if owner_setting:
            owner_setting.value = owner_username
        else:
            session.add(Settings(key="bot_owner_username", value=owner_username))
        
        # Handle QR image upload if provided
        if qr_image and qr_image.filename:
            contents = await qr_image.read()
            base64_encoded = base64.b64encode(contents).decode('utf-8')
            data_uri = f"data:{qr_image.content_type};base64,{base64_encoded}"
            
            qr_stmt = select(Settings).where(Settings.key == "payment_qr_image")
            qr_res = await session.execute(qr_stmt)
            qr_setting = qr_res.scalar_one_or_none()
            
            if qr_setting:
                qr_setting.value = data_uri
            else:
                session.add(Settings(key="payment_qr_image", value=data_uri))
        
        await session.commit()
        return {"status": "success"}

@app.get("/admin/deposits")
async def get_deposits():
    async with async_session() as session:
        result = await session.execute(select(Deposit).order_by(Deposit.created_at.desc()))
        return result.scalars().all()

from fastapi.responses import StreamingResponse
import io

@app.get("/admin/deposits/photo/{file_id}")
async def get_deposit_photo(file_id: str):
    """Serve Telegram photo by file_id without downloading locally"""
    try:
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        if hasattr(downloaded_file, 'getvalue'):
            file_bytes = downloaded_file.getvalue()
        else:
            downloaded_file.seek(0)
            file_bytes = downloaded_file.read()
            
        return StreamingResponse(io.BytesIO(file_bytes), media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Error serving deposit photo: {e}")
        raise HTTPException(status_code=404, detail="Photo not found")


@app.patch("/admin/deposits/{deposit_id}")
async def update_deposit(deposit_id: int, update_data: DepositUpdate):
    async with async_session() as session:
        stmt = select(Deposit).where(Deposit.id == deposit_id)
        result = await session.execute(stmt)
        deposit = result.scalar_one_or_none()
        
        if not deposit:
            raise HTTPException(status_code=404, detail="Deposit not found")
        
        deposit.status = update_data.status
        
        if update_data.status == "APPROVED":
            # Add balance to user
            user_stmt = select(User).where(User.id == deposit.user_id)
            user_res = await session.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if user:
                user.balance += deposit.amount
                # Notify user via bot
                try:
                    await bot.send_message(
                        user.telegram_id, 
                        f"<i>✅ Your deposit of ₹{deposit.amount} has been approved! Your new balance is ₹{user.balance}.</i>",
                        parse_mode="HTML"
                    )
                except:
                    pass
        elif update_data.status == "REJECTED":
            # Notify user about rejection with Contact Owner button
            user_stmt = select(User).where(User.id == deposit.user_id)
            user_res = await session.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if user:
                try:
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    from aiogram.utils.keyboard import InlineKeyboardBuilder
                    
                    builder = InlineKeyboardBuilder()
                    builder.row(InlineKeyboardButton(text="📞 Contact Owner", url="https://t.me/akhilportal"))
                    
                    await bot.send_message(
                        user.telegram_id,
                        f"<i>❌ Your deposit of ₹{deposit.amount} was rejected.\n\n"
                        "Please contact the owner if you think this is a mistake.</i>",
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )
                except:
                    pass
        
        await session.commit()
        return deposit

@app.post("/admin/users/{user_id}/adjust-balance")
async def adjust_user_balance(user_id: int, adjustment: BalanceAdjustment):
    async with async_session() as session:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update balance
        old_balance = user.balance
        user.balance += adjustment.amount
        new_balance = user.balance
        
        await session.commit()
        
        # Send notification to user via bot
        try:
            if adjustment.reason == "admin_add":
                message = (
                    f"✅ <b>Balance Credited</b>\n\n"
                    f"💰 Amount: ₹{abs(adjustment.amount)}\n"
                    f"📊 Previous Balance: ₹{old_balance}\n"
                    f"💵 New Balance: ₹{new_balance}\n\n"
                    f"<i>Balance added by admin</i>"
                )
            elif adjustment.reason == "admin_deduct":
                message = (
                    f"⚠️ <b>Balance Debited</b>\n\n"
                    f"💰 Amount: ₹{abs(adjustment.amount)}\n"
                    f"📊 Previous Balance: ₹{old_balance}\n"
                    f"💵 New Balance: ₹{new_balance}\n\n"
                    f"<i>Balance deducted by admin</i>"
                )
            else:
                message = (
                    f"💳 <b>Balance Updated</b>\n\n"
                    f"💰 Change: ₹{adjustment.amount}\n"
                    f"📊 Previous Balance: ₹{old_balance}\n"
                    f"💵 New Balance: ₹{new_balance}"
                )
            
            await bot.send_message(
                user.telegram_id,
                message,
                parse_mode="HTML"
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send notification: {e}")
        
        return {"status": "success", "user": user, "new_balance": new_balance}


@app.get("/admin/users")
async def get_users():
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()

@app.get("/admin/users/{user_id}")
async def get_user_details(user_id: int):
    async with async_session() as session:
        # Get user
        user_stmt = select(User).where(User.id == user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get purchases
        pur_stmt = select(Purchase).where(Purchase.user_id == user_id).order_by(Purchase.created_at.desc())
        pur_res = await session.execute(pur_stmt)
        purchases = pur_res.scalars().all()
        
        # Get deposits
        dep_stmt = select(Deposit).where(Deposit.user_id == user_id).order_by(Deposit.created_at.desc())
        dep_res = await session.execute(dep_stmt)
        deposits = dep_res.scalars().all()
        
        return {
            "user": user,
            "purchases": purchases,
            "deposits": deposits
        }

# --- Session Testing & OTP Monitoring Endpoints ---

@app.post("/admin/test-session/{account_id}")
async def test_session(account_id: int):
    """Test if a Telegram session is still active"""
    async with async_session() as session:
        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if not account.session_data:
            return {
                "success": False,
                "status": "NO_SESSION",
                "message": "No session data available for this account"
            }
        
        try:
            session_mgr = get_session_manager()
            result = await session_mgr.test_session(
                phone_number=account.phone_number,
                session_string=account.session_data
            )
            
            # Update account with test result
            if result["success"]:
                account.session_status = "ACTIVE"
                account.last_health_check = datetime.now()
                account.health_check_message = f"Active - {result['user_info']['first_name']}"
            else:
                account.session_status = "ERROR"
                account.health_check_message = result.get("message", "Unknown error")
            
            await session.commit()
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "ERROR",
                "message": str(e)
            }

@app.post("/admin/start-otp-monitor/{account_id}")
async def start_otp_monitoring(account_id: int):
    """Start listening for OTP codes on a specific account"""
    async with async_session() as session:
        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if not account.session_data:
            raise HTTPException(status_code=400, detail="No session data available")
        
        try:
            session_mgr = get_session_manager()
            await session_mgr.start_monitoring(
                phone_number=account.phone_number,
                session_string=account.session_data
            )
            return {"success": True, "message": f"Monitoring started for {account.phone_number}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/stop-otp-monitor/{account_id}")
async def stop_otp_monitoring(account_id: int):
    """Stop listening for OTP codes"""
    async with async_session() as session:
        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        try:
            session_mgr = get_session_manager()
            await session_mgr.stop_monitoring(account.phone_number)
            return {"success": True, "message": "Monitoring stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/otp-monitor/live")
async def get_live_otp_codes():
    """Get all active OTP monitoring sessions and recent codes"""
    try:
        session_mgr = get_session_manager()
        active_phones = session_mgr.get_all_active_phones()
        
        # Get recent OTPs (last 5 minutes)
        recent_otps = []
        for phone in active_phones:
            otp = session_mgr.get_otp(phone)
            if otp:
                recent_otps.append({
                    "phone": phone,
                    "code": otp,
                    "time_ago": "Just now"
                })
        
        return {
            "active_sessions": session_mgr.get_active_sessions_count(),
            "otps": recent_otps,
            "pending_requests": 0  # TODO: Track pending requests
        }
    except Exception as e:
        return {
            "active_sessions": 0,
            "otps": [],
            "pending_requests": 0,
            "error": str(e)
        }

# --- Session Generator Endpoints ---

class SessionStartRequest(BaseModel):
    phone_number: str

class SessionVerifyOTPRequest(BaseModel):
    session_id: str
    phone_number: str
    otp_code: str

class SessionVerify2FARequest(BaseModel):
    session_id: str
    password: str

@app.post("/admin/session/start")
async def start_session_generation(req: SessionStartRequest):
    """Start Telegram login and send OTP"""
    try:
        generator = await get_session_generator_async()
        result = await generator.start_login(req.phone_number)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/admin/session/verify-otp")
async def verify_session_otp(req: SessionVerifyOTPRequest):
    """Verify OTP code and check for 2FA"""
    try:
        generator = await get_session_generator_async()
        result = await generator.verify_otp(
            session_id=req.session_id,
            phone_number=req.phone_number,
            otp_code=req.otp_code
        )
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/admin/session/verify-2fa")
async def verify_session_2fa(req: SessionVerify2FARequest):
    """Verify 2FA password"""
    try:
        generator = await get_session_generator_async()
        result = await generator.verify_2fa(req.session_id, req.password)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/admin/settings/telegram-api")
async def get_telegram_api_settings():
    """Get stored TELEGRAM_API_ID and TELEGRAM_API_HASH from database"""
    async with async_session() as session:
        api_id_stmt = select(Settings).where(Settings.key == "telegram_api_id")
        api_hash_stmt = select(Settings).where(Settings.key == "telegram_api_hash")
        api_id_res = await session.execute(api_id_stmt)
        api_hash_res = await session.execute(api_hash_stmt)
        api_id_setting = api_id_res.scalar_one_or_none()
        api_hash_setting = api_hash_res.scalar_one_or_none()
        return {
            "api_id": api_id_setting.value if api_id_setting else os.getenv("TELEGRAM_API_ID", ""),
            "api_hash": api_hash_setting.value if api_hash_setting else os.getenv("TELEGRAM_API_HASH", "")
        }

class TelegramApiCredentials(BaseModel):
    api_id: str
    api_hash: str

@app.post("/admin/settings/telegram-api")
async def set_telegram_api_settings(data: TelegramApiCredentials):
    """Save TELEGRAM_API_ID and TELEGRAM_API_HASH to database"""
    if not data.api_id or not data.api_hash:
        raise HTTPException(status_code=400, detail="Both API ID and API Hash are required")
    async with async_session() as session:
        for key, value in [("telegram_api_id", data.api_id), ("telegram_api_hash", data.api_hash)]:
            stmt = select(Settings).where(Settings.key == key)
            res = await session.execute(stmt)
            setting = res.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                session.add(Settings(key=key, value=value))
        await session.commit()
    os.environ["TELEGRAM_API_ID"] = data.api_id
    os.environ["TELEGRAM_API_HASH"] = data.api_hash
    logger.info(f"✅ Telegram API credentials updated via admin panel")
    return {"success": True, "message": "Telegram API credentials saved successfully"}

@app.get("/admin/deposits/enhanced")
async def get_deposits_enhanced():
    """Return all deposits with joined user info, payment method, and OxaPay fields"""
    async with async_session() as session:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Deposit).options(joinedload(Deposit.user)).order_by(Deposit.created_at.desc())
        )
        deposits = result.scalars().all()
        return [
            {
                "id": d.id,
                "amount": d.amount,
                "upi_ref_id": d.upi_ref_id,
                "screenshot_path": d.screenshot_path,
                "status": d.status,
                "payment_method": getattr(d, 'payment_method', 'UPI'),
                "oxapay_order_id": getattr(d, 'oxapay_order_id', None),
                "created_at": d.created_at,
                "user": {
                    "id": d.user.id,
                    "telegram_id": d.user.telegram_id,
                    "username": d.user.username,
                    "full_name": d.user.full_name
                }
            }
            for d in deposits
        ]

# ============================================================
# EXCHANGE RATE ENDPOINTS
# ============================================================

class ExchangeRateUpdate(BaseModel):
    rate: float  # e.g. 84.50 meaning 1 USD = 84.50 INR

@app.get("/admin/settings/exchange-rate")
async def get_exchange_rate():
    """Get the current USD to INR exchange rate from settings"""
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        return {"rate": float(setting.value) if setting else 84.0}

@app.post("/admin/settings/exchange-rate")
async def set_exchange_rate(data: ExchangeRateUpdate):
    """Set the USD to INR exchange rate in settings"""
    if data.rate <= 0:
        raise HTTPException(status_code=400, detail="Rate must be a positive number")
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(data.rate)
        else:
            session.add(Settings(key="usd_inr_rate", value=str(data.rate)))
        await session.commit()
        logger.info(f"✅ Exchange rate updated: 1 USD = {data.rate} INR")
        return {"success": True, "rate": data.rate}

# ============================================================
# OXAPAY ENDPOINTS
# ============================================================

import httpx

class OxaPayInvoiceRequest(BaseModel):
    usd_amount: float
    telegram_id: int
    user_id: int

class OxaPayWebhookPayload(BaseModel):
    status: str = ""
    trackId: str = ""
    orderId: str = ""
    amount: float = 0.0
    currency: str = ""
    payAmount: float = 0.0
    payCurrency: str = ""
    payDate: str = ""
    merchant: str = ""

@app.post("/api/oxapay/create-invoice")
async def create_oxapay_invoice(req: OxaPayInvoiceRequest):
    """Create an OxaPay payment invoice. Min $0.10 USD."""
    if req.usd_amount < 0.10:
        raise HTTPException(status_code=400, detail="Minimum deposit amount is $0.10 USD")

    oxapay_key = os.getenv("OXAPAY_API_KEY", "")
    if not oxapay_key:
        raise HTTPException(status_code=500, detail="OxaPay API key not configured")

    base_url = os.getenv("BASE_WEBHOOK_URL", "").rstrip("/")
    callback_url = f"{base_url}/api/oxapay/webhook"

    # Get current exchange rate to calculate INR equivalent
    async with async_session() as session:
        rate_stmt = select(Settings).where(Settings.key == "usd_inr_rate")
        rate_res = await session.execute(rate_stmt)
        rate_setting = rate_res.scalar_one_or_none()
        exchange_rate = float(rate_setting.value) if rate_setting else 84.0

    inr_amount = round(req.usd_amount * exchange_rate, 2)

    payload = {
        "merchant": oxapay_key,
        "amount": req.usd_amount,
        "currency": "USD",
        "lifeTime": 30,
        "callbackUrl": callback_url,
        "description": f"Deposit for Telegram user {req.telegram_id}",
        "orderId": f"tg_{req.user_id}_{req.telegram_id}"
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.oxapay.com/merchants/request",
                json=payload
            )
            data = response.json()

        if data.get("result") != 100:
            logger.error(f"OxaPay error: {data}")
            raise HTTPException(status_code=502, detail=f"OxaPay error: {data.get('message', 'Unknown')}")

        track_id = data["trackId"]
        pay_link = data["payLink"]

        # Create a PENDING deposit record immediately
        async with async_session() as session:
            user_stmt = select(User).where(User.id == req.user_id)
            user_res = await session.execute(user_stmt)
            user = user_res.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            deposit = Deposit(
                user_id=req.user_id,
                amount=inr_amount,
                upi_ref_id=None,
                screenshot_path=None,
                status="PENDING",
                payment_method="OXAPAY",
                oxapay_order_id=str(track_id)
            )
            session.add(deposit)
            await session.commit()

        logger.info(f"✅ OxaPay invoice created: trackId={track_id}, USD={req.usd_amount}, INR={inr_amount}")
        return {
            "success": True,
            "track_id": track_id,
            "pay_link": pay_link,
            "usd_amount": req.usd_amount,
            "inr_amount": inr_amount,
            "exchange_rate": exchange_rate
        }

    except httpx.RequestError as e:
        logger.error(f"OxaPay network error: {e}")
        raise HTTPException(status_code=502, detail="Could not connect to OxaPay. Try again.")


@app.post("/api/oxapay/webhook")
async def oxapay_webhook(request: Request):
    """OxaPay calls this endpoint when a payment is confirmed. Auto-approves the deposit."""
    try:
        body = await request.json()
        logger.info(f"📩 OxaPay Webhook received: {body}")

        status = body.get("status", "")
        track_id = str(body.get("trackId", ""))

        # Only process confirmed payments
        if status != "Paid":
            logger.info(f"OxaPay webhook ignored (status={status})")
            return {"status": "ignored"}

        if not track_id:
            logger.warning("OxaPay webhook: missing trackId")
            return {"status": "error", "detail": "missing trackId"}

        async with async_session() as session:
            # Find the deposit by OxaPay trackId
            dep_stmt = select(Deposit).where(Deposit.oxapay_order_id == track_id)
            dep_res = await session.execute(dep_stmt)
            deposit = dep_res.scalar_one_or_none()

            if not deposit:
                logger.warning(f"OxaPay webhook: no deposit found for trackId={track_id}")
                return {"status": "not_found"}

            if deposit.status == "APPROVED":
                logger.info(f"OxaPay webhook: deposit {deposit.id} already approved")
                return {"status": "already_approved"}

            # Get user
            user_stmt = select(User).where(User.id == deposit.user_id)
            user_res = await session.execute(user_stmt)
            user = user_res.scalar_one_or_none()

            if not user:
                logger.error(f"OxaPay webhook: user not found for deposit {deposit.id}")
                return {"status": "user_not_found"}

            # AUTO-APPROVE: Credit balance
            old_balance = user.balance
            user.balance += deposit.amount
            deposit.status = "APPROVED"
            await session.commit()

            logger.info(f"✅ OxaPay deposit auto-approved: user={user.telegram_id}, INR={deposit.amount}, new_balance={user.balance}")

            # Notify user on Telegram
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"✅ <b>OxaPay Deposit Approved!</b>\n\n"
                    f"💰 Amount Credited: <b>₹{deposit.amount:.2f}</b>\n"
                    f"📊 Previous Balance: ₹{old_balance:.2f}\n"
                    f"💵 New Balance: <b>₹{user.balance:.2f}</b>\n\n"
                    f"<i>Payment verified automatically via OxaPay</i>",
                    parse_mode="HTML"
                )
            except Exception as notify_err:
                logger.warning(f"Could not notify user: {notify_err}")

            return {"status": "approved"}

    except Exception as e:
        logger.error(f"OxaPay webhook error: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}

# --- Serve Frontend ---
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # API routes are NOT caught here by default if they match specifically
    # But we want to ensure any non-api/non-admin-api route serves index.html
    if full_path.startswith("admin/"): # This matches frontend routes like /admin/users
        index_file = os.path.join(dist_path, "index.html")
        return FileResponse(index_file)
    
    # Static files check
    file_path = os.path.join(dist_path, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Root or other SPA routes
    index_file = os.path.join(dist_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    return {"error": "Frontend not found"}

if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

# Mount uploads directory for payment screenshots
uploads_path = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
"""

Add Account Creation Endpoint

This creates the missing /admin/accounts POST endpoint

"""



# Add this code to backend/main.py



from pydantic import BaseModel



class AccountCreate(BaseModel):

    country_id: int

    phone_number: str

    session_data: str

    type: str = "ID"

    twofa_password: str = None



@app.post("/admin/accounts")

async def create_account(account: AccountCreate):

    """Create a new account - allows duplicates after sold"""

    async with async_session() as session:

        # Create new account (no duplicate check - allows restocking)

        new_account = Account(

            country_id=account.country_id,

            phone_number=account.phone_number,

            session_data=account.session_data,

            type=account.type,

            twofa_password=account.twofa_password,

            is_sold=False

        )

        

        session.add(new_account)

        await session.commit()

        await session.refresh(new_account)

        

        return {

            "success": True,

            "message": "Account added successfully",

            "account": {

                "id": new_account.id,

                "phone_number": new_account.phone_number,

                "country_id": new_account.country_id

            }

        }

