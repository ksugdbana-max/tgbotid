"""
Session Generator Service
Handles Telegram authentication flow in the browser
"""

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid
import asyncio
from typing import Dict, Optional
import logging
import secrets

logger = logging.getLogger(__name__)

class SessionGeneratorService:
    """
    Service to generate Telegram session strings via web interface
    Each login attempt is tracked by a unique session ID
    """
    
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.active_clients: Dict[str, Client] = {}  # session_id -> client
        self.phone_codes: Dict[str, str] = {}  # session_id -> phone_code_hash
        
    async def start_login(self, phone_number: str) -> dict:
        """
        Step 1: Start login process and send OTP
        Returns: { success: bool, session_id: str, message: str }
        """
        try:
            # Generate unique session ID
            session_id = secrets.token_urlsafe(16)
            
            # Create Pyrogram client
            client = Client(
                name=f"web_session_{session_id}",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=phone_number,
                in_memory=True
            )
            
            # Connect and send code
            await client.connect()
            sent_code = await client.send_code(phone_number)
            
            # Store client and code hash
            self.active_clients[session_id] = client
            self.phone_codes[session_id] = sent_code.phone_code_hash
            
            logger.info(f"✅ OTP sent to {phone_number}, session: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "phone_code_hash": sent_code.phone_code_hash,
                "message": f"OTP sent to {phone_number}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start login for {phone_number}: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def verify_otp(self, session_id: str, phone_number: str, otp_code: str) -> dict:
        """
        Step 2: Verify OTP code
        Returns: { success: bool, needs_2fa: bool, session_string: str (if no 2FA) }
        """
        try:
            if session_id not in self.active_clients:
                return {"success": False, "message": "Session expired or invalid"}
            
            client = self.active_clients[session_id]
            phone_code_hash = self.phone_codes[session_id]
            
            try:
                # Try to sign in with OTP
                await client.sign_in(
                    phone_number=phone_number,
                    phone_code_hash=phone_code_hash,
                    phone_code=otp_code
                )
                
                # Success! No 2FA needed
                session_string = await client.export_session_string()
                
                # Cleanup
                await self._cleanup_session(session_id)
                
                logger.info(f"✅ Session generated for {phone_number} (no 2FA)")
                
                return {
                    "success": True,
                    "needs_2fa": False,
                    "session_string": session_string,
                    "message": "Login successful!"
                }
                
            except SessionPasswordNeeded:
                # 2FA is enabled
                logger.info(f"⚠️ 2FA required for {phone_number}")
                return {
                    "success": True,
                    "needs_2fa": True,
                    "message": "2FA password required"
                }
                
            except PhoneCodeInvalid:
                return {
                    "success": False,
                    "message": "Invalid OTP code"
                }
                
        except Exception as e:
            logger.error(f"❌ OTP verification failed: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def verify_2fa(self, session_id: str, password: str) -> dict:
        """
        Step 3: Verify 2FA password (if needed)
        Returns: { success: bool, session_string: str }
        """
        try:
            if session_id not in self.active_clients:
                return {"success": False, "message": "Session expired or invalid"}
            
            client = self.active_clients[session_id]
            
            try:
                # Check 2FA password
                await client.check_password(password)
                
                # Success! Export session
                session_string = await client.export_session_string()
                
                # Cleanup
                await self._cleanup_session(session_id)
                
                logger.info(f"✅ Session generated with 2FA")
                
                return {
                    "success": True,
                    "session_string": session_string,
                    "message": "Login successful!"
                }
                
            except PasswordHashInvalid:
                return {
                    "success": False,
                    "message": "Invalid 2FA password"
                }
                
        except Exception as e:
            logger.error(f"❌ 2FA verification failed: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _cleanup_session(self, session_id: str):
        """Clean up client and temporary data"""
        try:
            if session_id in self.active_clients:
                client = self.active_clients[session_id]
                await client.disconnect()
                del self.active_clients[session_id]
            
            if session_id in self.phone_codes:
                del self.phone_codes[session_id]
                
            logger.info(f"🧹 Cleaned up session {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session: {e}")
    
    async def cleanup_expired_sessions(self):
        """Cleanup sessions older than 10 minutes (call periodically)"""
        # TODO: Add timestamp tracking and cleanup
        pass


# Global instance
_session_generator = None

def get_session_generator():
    """Get or create global session generator instance"""
    global _session_generator
    if _session_generator is None:
        import os
        api_id = int(os.getenv("TELEGRAM_API_ID", 0))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        _session_generator = SessionGeneratorService(api_id, api_hash)
    return _session_generator
