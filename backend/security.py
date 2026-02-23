"""
Security Module for Session Encryption
Implements AES-256 encryption for Telegram session strings
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SessionEncryption:
    """
    Handles encryption and decryption of sensitive session data
    Uses AES-256 encryption via Fernet (symmetric encryption)
    """
    
    def __init__(self):
        """Initialize encryption with key from environment or generate new one"""
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create a new one"""
        # Check for existing key in environment
        env_key = os.getenv("SESSION_ENCRYPTION_KEY")
        
        if env_key:
            try:
                # Validate the key
                key_bytes = env_key.encode()
                if len(key_bytes) == 44:  # Fernet key is 44 bytes base64
                    logger.info("✅ Using encryption key from environment")
                    return key_bytes
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate new key
        logger.warning("⚠️ No encryption key found - generating new one")
        logger.warning("⚠️ Add this to your .env file:")
        
        new_key = Fernet.generate_key()
        print(f"\n🔐 SESSION_ENCRYPTION_KEY={new_key.decode()}\n")
        
        return new_key
    
    def encrypt_session(self, session_string: str) -> str:
        """
        Encrypt a session string
        Returns: Base64 encoded encrypted data
        """
        try:
            if not session_string:
                return ""
            
            # Convert to bytes
            session_bytes = session_string.encode('utf-8')
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(session_bytes)
            
            # Return as base64 string for database storage
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt_session(self, encrypted_data: str) -> str:
        """
        Decrypt a session string
        Returns: Original session string
        """
        try:
            if not encrypted_data:
                return ""
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            
            # Return as string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def rotate_key(self, old_key: bytes, sessions_to_reencrypt: list):
        """
        Rotate encryption key (re-encrypt all sessions with new key)
        WARNING: This is a sensitive operation!
        """
        logger.info("🔄 Starting key rotation...")
        
        # Create cipher with old key
        old_cipher = Fernet(old_key)
        
        # Generate new key
        new_key = Fernet.generate_key()
        new_cipher = Fernet(new_key)
        
        reencrypted = []
        for encrypted_session in sessions_to_reencrypt:
            try:
                # Decrypt with old key
                decrypted = old_cipher.decrypt(base64.b64decode(encrypted_session))
                # Re-encrypt with new key
                reencrypted_data = new_cipher.encrypt(decrypted)
                reencrypted.append(base64.b64encode(reencrypted_data).decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to rotate session: {e}")
                reencrypted.append(None)
        
        # Update instance key
        self.encryption_key = new_key
        self.cipher = new_cipher
        
        logger.info(f"✅ Key rotation complete. New key: {new_key.decode()}")
        return new_key, reencrypted


class SecurityAudit:
    """
    Audit logging for security-sensitive operations
    """
    
    @staticmethod
    def log_session_access(account_id: int, user_id: int, action: str, ip_address: str = None):
        """Log when someone accesses a session"""
        logger.info(
            f"🔐 SESSION_ACCESS | "
            f"Account: {account_id} | "
            f"User: {user_id} | "
            f"Action: {action} | "
            f"IP: {ip_address or 'Unknown'}"
        )
    
    @staticmethod
    def log_otp_request(phone: str, user_id: int, success: bool):
        """Log OTP requests"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(
            f"📲 OTP_REQUEST | "
            f"Phone: {phone[-4:]} | "  # Only log last 4 digits
            f"User: {user_id} | "
            f"Status: {status}"
        )
    
    @staticmethod
    def log_security_event(event_type: str, details: str, severity: str = "INFO"):
        """Log general security events"""
        logger.warning(f"⚠️ SECURITY | {severity} | {event_type} | {details}")


class RateLimiter:
    """
    Rate limiting for security-sensitive operations
    """
    
    def __init__(self):
        self.attempts = {}  # user_id -> {action -> [(timestamp, count)]}
    
    def check_rate_limit(self, user_id: int, action: str, max_attempts: int = 3, window_seconds: int = 3600) -> bool:
        """
        Check if user has exceeded rate limit
        Returns: True if allowed, False if rate limited
        """
        import time
        current_time = time.time()
        
        if user_id not in self.attempts:
            self.attempts[user_id] = {}
        
        if action not in self.attempts[user_id]:
            self.attempts[user_id][action] = []
        
        # Clean old attempts
        self.attempts[user_id][action] = [
            (ts, count) for ts, count in self.attempts[user_id][action]
            if current_time - ts < window_seconds
        ]
        
        # Count attempts in window
        total_attempts = sum(count for _, count in self.attempts[user_id][action])
        
        if total_attempts >= max_attempts:
            SecurityAudit.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                f"User {user_id} exceeded limit for {action}",
                "WARNING"
            )
            return False
        
        # Add current attempt
        self.attempts[user_id][action].append((current_time, 1))
        return True
    
    def reset_user_limits(self, user_id: int):
        """Reset all limits for a user"""
        if user_id in self.attempts:
            del self.attempts[user_id]


# Global instances
_encryptor = None
_rate_limiter = None

def get_encryptor() -> SessionEncryption:
    """Get global encryption instance"""
    global _encryptor
    if _encryptor is None:
        _encryptor = SessionEncryption()
    return _encryptor

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
