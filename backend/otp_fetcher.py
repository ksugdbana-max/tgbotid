"""
Real OTP code fetching using Pyrogram
"""
import logging
import re
from pyrogram import Client
from pyrogram.raw.functions.messages import GetHistory
from pyrogram.raw.types import InputPeerUser
from pyrogram.errors import RPCError

logger = logging.getLogger(__name__)

async def get_latest_otp_code(session_string: str, api_id: int, api_hash: str):
    """
    Get the latest OTP/login code from Telegram's service messages
    Returns the code string or None
    """
    try:
        async with Client(
            "temp_session",
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            in_memory=True
        ) as client:
            # Get messages from Telegram service notifications (777000)
            async for message in client.get_chat_history(777000, limit=5):
                if message.text:
                    # Look for login code pattern
                    # Telegram sends codes like: "Login code: 12345" or just "12345"
                    match = re.search(r'(\d{5,6})', message.text)
                    if match:
                        code = match.group(1)
                        logger.info(f"✅ Found OTP code: {code}")
                        return code
            
            logger.warning("No OTP code found in recent messages")
            return None
            
    except RPCError as e:
        logger.error(f"Pyrogram error getting OTP: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting OTP code: {e}")
        return None


async def request_login_code(phone_number: str, api_id: int, api_hash: str):
    """
    Request a new login code for a phone number
    This creates a temporary client to trigger code sending
    """
    try:
        # Create temporary client
        client = Client(
            "code_request",
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            in_memory=True
        )
        
        # This will trigger code sending
        await client.connect()
        code_hash = await client.send_code(phone_number)
        await client.disconnect()
        
        logger.info(f"✅ Login code requested for {phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error requesting login code: {e}")
        return False
