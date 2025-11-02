"""
Telegram Campaign Service - Send DMs to contacts via Telegram User API

Features:
- Connect Telegram account using API ID, API Hash, and phone number
- Discover contacts by phone number
- Send personalized DMs using enriched data
- Rate limiting: max 10 messages per 24 hours, 1 per hour
- Track message history and campaign progress
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telethon import TelegramClient, errors
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TelegramCampaignService:
    """Service for managing Telegram DM campaigns with rate limiting"""
    
    def __init__(self, api_id: str, api_hash: str, phone: str, session_name: str = "leadon_telegram"):
        """
        Initialize Telegram client
        
        Args:
            api_id: Telegram API ID (get from my.telegram.org)
            api_hash: Telegram API Hash
            phone: Phone number with country code (e.g., +1234567890)
            session_name: Session file name for persistent login
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client = None
        
        # Rate limiting
        self.messages_sent_today = 0
        self.last_message_time = None
        self.daily_reset_time = None
        self.MAX_DAILY_MESSAGES = 10
        self.MIN_MESSAGE_INTERVAL = 3600  # 1 hour in seconds
        
    async def connect(self) -> bool:
        """
        Connect to Telegram and authenticate
        
        Returns:
            True if connected successfully
        """
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            
            if await self.client.is_user_authorized():
                logger.info(f"✅ Connected to Telegram as {self.phone}")
                return True
            else:
                logger.error("❌ Failed to authorize Telegram account")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error connecting to Telegram: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram")
    
    def _check_rate_limit(self) -> Dict[str, any]:
        """
        Check if we can send a message based on rate limits
        
        Returns:
            Dict with 'can_send' (bool) and 'reason' (str) if blocked
        """
        now = datetime.now()
        
        # Reset daily counter if 24 hours have passed
        if self.daily_reset_time is None or now >= self.daily_reset_time:
            self.messages_sent_today = 0
            self.daily_reset_time = now + timedelta(days=1)
        
        # Check daily limit
        if self.messages_sent_today >= self.MAX_DAILY_MESSAGES:
            time_until_reset = (self.daily_reset_time - now).total_seconds() / 3600
            return {
                'can_send': False,
                'reason': f'Daily limit reached ({self.MAX_DAILY_MESSAGES} messages). Resets in {time_until_reset:.1f} hours'
            }
        
        # Check hourly limit
        if self.last_message_time:
            time_since_last = (now - self.last_message_time).total_seconds()
            if time_since_last < self.MIN_MESSAGE_INTERVAL:
                wait_time = (self.MIN_MESSAGE_INTERVAL - time_since_last) / 60
                return {
                    'can_send': False,
                    'reason': f'Must wait {wait_time:.1f} minutes before sending next message'
                }
        
        return {'can_send': True}
    
    async def find_contact_by_phone(self, phone: str, first_name: str = "Contact", last_name: str = "") -> Optional[Dict]:
        """
        Try to find a Telegram user by phone number
        
        Args:
            phone: Phone number with country code (e.g., +1234567890)
            first_name: First name for contact (used when adding)
            last_name: Last name for contact
            
        Returns:
            Dict with user info if found, None otherwise
        """
        try:
            # Import contact to check if they have Telegram
            contact = InputPhoneContact(
                client_id=0,
                phone=phone,
                first_name=first_name,
                last_name=last_name
            )
            
            result = await self.client(ImportContactsRequest([contact]))
            
            if result.users:
                user = result.users[0]
                logger.info(f"✅ Found Telegram user: {user.first_name} (@{user.username or 'no username'})")
                return {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': phone,
                    'has_telegram': True
                }
            else:
                logger.info(f"❌ No Telegram account found for {phone}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding contact by phone {phone}: {e}")
            return None
    
    async def send_message(self, user_id: int, message: str) -> Dict[str, any]:
        """
        Send a message to a Telegram user
        
        Args:
            user_id: Telegram user ID
            message: Message text
            
        Returns:
            Dict with 'success' (bool), 'message_id' (int), and 'error' (str) if failed
        """
        # Check rate limits
        rate_check = self._check_rate_limit()
        if not rate_check['can_send']:
            return {
                'success': False,
                'error': rate_check['reason']
            }
        
        try:
            # Send message
            sent_message = await self.client.send_message(user_id, message)
            
            # Update rate limiting counters
            self.messages_sent_today += 1
            self.last_message_time = datetime.now()
            
            logger.info(f"✅ Message sent to user {user_id}")
            return {
                'success': True,
                'message_id': sent_message.id,
                'sent_at': datetime.now().isoformat()
            }
            
        except errors.FloodWaitError as e:
            wait_time = e.seconds / 60
            error_msg = f"Telegram rate limit hit. Must wait {wait_time:.1f} minutes"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
            
        except errors.UserIsBlockedError:
            error_msg = "User has blocked the bot"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    async def send_campaign_message(self, contact: Dict, template: str) -> Dict[str, any]:
        """
        Send a personalized campaign message to a contact
        
        Args:
            contact: Contact dict with 'phone', 'first_name', 'last_name', 'company', etc.
            template: Message template with placeholders like {first_name}, {company}
            
        Returns:
            Dict with campaign result
        """
        # Find contact on Telegram
        telegram_user = await self.find_contact_by_phone(
            contact.get('phone'),
            contact.get('first_name', 'Contact'),
            contact.get('last_name', '')
        )
        
        if not telegram_user:
            return {
                'success': False,
                'contact_phone': contact.get('phone'),
                'error': 'Contact does not have Telegram'
            }
        
        # Personalize message
        personalized_message = template.format(
            first_name=contact.get('first_name', 'there'),
            last_name=contact.get('last_name', ''),
            company=contact.get('company', 'your company'),
            title=contact.get('title', 'your role'),
            **contact  # Allow any other fields from contact
        )
        
        # Send message
        result = await self.send_message(telegram_user['id'], personalized_message)
        result['contact_phone'] = contact.get('phone')
        result['telegram_username'] = telegram_user.get('username')
        
        return result
    
    def get_rate_limit_status(self) -> Dict[str, any]:
        """
        Get current rate limit status
        
        Returns:
            Dict with rate limit info
        """
        now = datetime.now()
        
        # Time until daily reset
        time_until_reset = None
        if self.daily_reset_time:
            time_until_reset = (self.daily_reset_time - now).total_seconds() / 3600
        
        # Time until next message allowed
        time_until_next = 0
        if self.last_message_time:
            time_since_last = (now - self.last_message_time).total_seconds()
            if time_since_last < self.MIN_MESSAGE_INTERVAL:
                time_until_next = (self.MIN_MESSAGE_INTERVAL - time_since_last) / 60
        
        return {
            'messages_sent_today': self.messages_sent_today,
            'daily_limit': self.MAX_DAILY_MESSAGES,
            'messages_remaining': self.MAX_DAILY_MESSAGES - self.messages_sent_today,
            'time_until_daily_reset_hours': time_until_reset,
            'time_until_next_message_minutes': time_until_next,
            'can_send_now': self._check_rate_limit()['can_send']
        }

