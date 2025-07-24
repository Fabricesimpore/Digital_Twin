"""
Alert Dispatcher - Fixed version with proper error handling
"""
import os
import re
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path
import logging

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException, TwilioRestException
    from twilio.twiml.voice_response import VoiceResponse
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False
    Client = None
    TwilioException = Exception
    TwilioRestException = Exception
    VoiceResponse = None

try:
    import plyer
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

from abc import ABC, abstractmethod


class AlertChannel(ABC):
    """Abstract base class for alert channels"""
    
    @abstractmethod
    async def send(self, message: str, request_id: str) -> bool:
        """Send alert through this channel"""
        pass


class TwilioSMSChannel(AlertChannel):
    """SMS alerts via Twilio with proper error handling"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.logger = logging.getLogger(f"{__name__}.TwilioSMS")
        
        if not HAS_TWILIO:
            raise ImportError("Twilio package not installed. Run: pip install twilio")
        
        # Validate credentials format
        if not self._validate_credentials(account_sid, auth_token, from_number, to_number):
            raise ValueError("Invalid Twilio credentials or phone numbers")
        
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number
        
        # Test credentials
        if not self._test_credentials():
            raise ValueError("Twilio credentials validation failed")
        
    def _validate_credentials(self, account_sid: str, auth_token: str, 
                            from_number: str, to_number: str) -> bool:
        """Validate credential formats"""
        try:
            # Validate SID format (starts with AC, 34 chars total)
            if not re.match(r'^AC[a-f0-9]{32}$', account_sid):
                self.logger.error("Invalid Account SID format")
                return False
            
            # Validate token format (32 chars)
            if len(auth_token) != 32:
                self.logger.error("Invalid Auth Token format")
                return False
            
            # Validate phone number formats
            phone_pattern = r'^\+1[0-9]{10}$'
            if not re.match(phone_pattern, from_number):
                self.logger.error(f"Invalid from_number format: {from_number}")
                return False
            
            if not re.match(phone_pattern, to_number):
                self.logger.error(f"Invalid to_number format: {to_number}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Credential validation error: {e}")
            return False
    
    def _test_credentials(self) -> bool:
        """Test credentials with a minimal API call"""
        try:
            # Test with account fetch (minimal cost)
            account = self.client.api.account.fetch()
            self.logger.info(f"Twilio validated: {account.friendly_name}")
            return True
            
        except TwilioRestException as e:
            self.logger.error(f"Twilio REST error: {e.msg} (Code: {e.code})")
            return False
        except TwilioException as e:
            self.logger.error(f"Twilio error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Credential test failed: {e}")
            return False
    
    async def send(self, message: str, request_id: str) -> bool:
        """Send SMS with retry and timeout"""
        max_retries = 3
        timeout_seconds = 30
        
        for attempt in range(max_retries):
            try:
                # Add request ID for easy response
                full_message = f"{message}\n\nID: {request_id[:8]}"
                
                # Execute in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                message_obj = await asyncio.wait_for(
                    loop.run_in_executor(None, self._send_sms_sync, full_message),
                    timeout=timeout_seconds
                )
                
                self.logger.info(f"SMS sent successfully: {message_obj.sid}")
                return True
                
            except asyncio.TimeoutError:
                self.logger.warning(f"SMS timeout on attempt {attempt + 1}")
            except TwilioRestException as e:
                self.logger.error(f"Twilio REST error: {e.msg} (Code: {e.code})")
                if e.code in [20003, 20005]:  # Authentication errors - don't retry
                    break
            except TwilioException as e:
                self.logger.error(f"Twilio error: {e}")
            except Exception as e:
                self.logger.error(f"SMS send error: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def _send_sms_sync(self, message: str):
        """Synchronous SMS send for thread executor"""
        return self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=self.to_number
        )


class TwilioCallChannel(AlertChannel):
    """Phone call alerts via Twilio with proper error handling"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, 
                 to_number: str, webhook_url: str):
        self.logger = logging.getLogger(f"{__name__}.TwilioCall")
        
        if not HAS_TWILIO:
            raise ImportError("Twilio package not installed")
        
        # Validate webhook URL
        if not webhook_url.startswith('https://'):
            raise ValueError("Webhook URL must use HTTPS")
        
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number
        self.webhook_url = webhook_url
        
    async def send(self, message: str, request_id: str) -> bool:
        """Make phone call with error handling"""
        try:
            # Create TwiML
            response = VoiceResponse()
            response.say(f"Digital Twin alert: {message}", voice='alice')
            
            gather = response.gather(
                num_digits=1,
                action=f"{self.webhook_url}/response/{request_id}",
                method='POST',
                timeout=10
            )
            gather.say("Press 1 to approve, 2 to deny, or 3 to defer.")
            
            # Save TwiML
            twiml_path = Path(f"backend/data/calls/{request_id}.xml")
            twiml_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(twiml_path, 'w') as f:
                f.write(str(response))
            
            # Make call
            loop = asyncio.get_event_loop()
            call = await asyncio.wait_for(
                loop.run_in_executor(None, self._make_call_sync, request_id),
                timeout=30
            )
            
            self.logger.info(f"Call initiated: {call.sid}")
            return True
            
        except asyncio.TimeoutError:
            self.logger.error("Call initiation timeout")
            return False
        except TwilioRestException as e:
            self.logger.error(f"Twilio call error: {e.msg} (Code: {e.code})")
            return False
        except Exception as e:
            self.logger.error(f"Call error: {e}")
            return False
    
    def _make_call_sync(self, request_id: str):
        """Synchronous call creation"""
        return self.client.calls.create(
            url=f"{self.webhook_url}/twiml/{request_id}",
            to=self.to_number,
            from_=self.from_number,
            timeout=20,
            record=False
        )


class DesktopNotificationChannel(AlertChannel):
    """Desktop notifications with fallback"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Desktop")
        
    async def send(self, message: str, request_id: str) -> bool:
        """Send desktop notification with fallback"""
        if not HAS_PLYER:
            self.logger.warning("Plyer not available, using console fallback")
            print(f"🔔 ALERT: {message} (ID: {request_id[:8]})")
            return True
        
        try:
            plyer.notification.notify(
                title="🤖 Digital Twin Alert",
                message=f"{message}\n\nID: {request_id[:8]}",
                timeout=15,
                app_name="Digital Twin"
            )
            return True
            
        except Exception as e:
            self.logger.warning(f"Desktop notification failed: {e}, using console")
            print(f"🔔 ALERT: {message} (ID: {request_id[:8]})")
            return True  # Console fallback always works


class AlertDispatcher:
    """Enhanced alert dispatcher with proper error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Dispatcher")
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
        # Setup channels from environment
        self._setup_from_env()
    
    def _setup_from_env(self):
        """Setup channels with validation"""
        # Always add desktop notifications
        self.channels['notification'] = DesktopNotificationChannel()
        self.logger.info("Desktop notification channel configured")
        
        # Twilio SMS
        try:
            if self._has_twilio_env():
                self.channels['sms'] = TwilioSMSChannel(
                    account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
                    auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
                    from_number=os.getenv('TWILIO_PHONE_NUMBER'),
                    to_number=os.getenv('USER_PHONE_NUMBER')
                )
                self.logger.info("SMS channel configured successfully")
                
                # Add call channel if webhook URL provided
                webhook_url = os.getenv('TWILIO_WEBHOOK_URL')
                if webhook_url:
                    self.channels['call'] = TwilioCallChannel(
                        account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
                        auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
                        from_number=os.getenv('TWILIO_PHONE_NUMBER'),
                        to_number=os.getenv('USER_PHONE_NUMBER'),
                        webhook_url=webhook_url
                    )
                    self.logger.info("Call channel configured successfully")
                    
        except Exception as e:
            self.logger.error(f"Failed to setup Twilio channels: {e}")
            self.logger.info("Continuing with desktop notifications only")
    
    def _has_twilio_env(self) -> bool:
        """Check if all required Twilio env vars are set"""
        required_vars = [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN', 
            'TWILIO_PHONE_NUMBER',
            'USER_PHONE_NUMBER'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            self.logger.warning(f"Missing Twilio env vars: {missing}")
            return False
        return True
    
    async def send_alert(self, message: str, request_id: str, 
                        channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """Send alert with comprehensive error handling"""
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        
        # Send to each channel with individual error handling
        for channel_name in channels:
            if channel_name not in self.channels:
                self.logger.warning(f"Channel '{channel_name}' not configured")
                results[channel_name] = False
                continue
            
            channel = self.channels[channel_name]
            try:
                success = await channel.send(message, request_id)
                results[channel_name] = success
                
            except Exception as e:
                self.logger.error(f"Unexpected error in channel {channel_name}: {e}")
                results[channel_name] = False
        
        # Log alert
        self._log_alert(message, request_id, results)
        return results
    
    async def send_sms(self, message: str, request_id: str) -> bool:
        """Send SMS with fallback to notification"""
        results = await self.send_alert(message, request_id, ['sms'])
        success = results.get('sms', False)
        
        # Fallback to notification if SMS fails
        if not success and 'notification' in self.channels:
            self.logger.info("SMS failed, falling back to notification")
            fallback_results = await self.send_alert(message, request_id, ['notification'])
            return fallback_results.get('notification', False)
        
        return success
    
    async def send_call(self, message: str, request_id: str) -> bool:
        """Make phone call with SMS fallback"""
        results = await self.send_alert(message, request_id, ['call'])
        success = results.get('call', False)
        
        # Fallback to SMS if call fails
        if not success and 'sms' in self.channels:
            self.logger.info("Call failed, falling back to SMS")
            return await self.send_sms(message, request_id)
        
        return success
    
    async def send_notification(self, message: str, request_id: str) -> bool:
        """Send desktop notification (always available)"""
        results = await self.send_alert(message, request_id, ['notification'])
        return results.get('notification', False)
    
    def _log_alert(self, message: str, request_id: str, results: Dict[str, bool]):
        """Log alert to history"""
        alert_log = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'message': message[:100],  # Truncate for storage
            'results': results,
            'success': any(results.values())
        }
        
        self.alert_history.append(alert_log)
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    def get_channel_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed channel status"""
        status = {}
        
        for name, channel in self.channels.items():
            status[name] = {
                'configured': True,
                'type': type(channel).__name__,
                'available': True
            }
        
        # Check for missing channels
        all_channels = ['sms', 'call', 'notification']
        for channel in all_channels:
            if channel not in status:
                status[channel] = {
                    'configured': False,
                    'reason': 'Missing configuration or credentials'
                }
        
        return status


if __name__ == "__main__":
    async def test_dispatcher():
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        dispatcher = AlertDispatcher()
        
        # Check status
        status = dispatcher.get_channel_status()
        print("Channel Status:")
        for channel, info in status.items():
            print(f"  {channel}: {info}")
        
        # Test alert
        if dispatcher.channels:
            results = await dispatcher.send_alert(
                "Test alert from enhanced dispatcher",
                "test-123",
                ['notification']
            )
            print(f"\nTest results: {results}")
    
    asyncio.run(test_dispatcher())