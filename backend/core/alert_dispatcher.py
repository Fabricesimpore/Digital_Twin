"""
Alert Dispatcher - Sends alerts via SMS, phone calls, and notifications
"""
import os
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import json
from pathlib import Path
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import plyer  # For desktop notifications
from abc import ABC, abstractmethod


class AlertChannel(ABC):
    """Abstract base class for alert channels"""
    
    @abstractmethod
    async def send(self, message: str, request_id: str) -> bool:
        """Send alert through this channel"""
        pass


class TwilioSMSChannel(AlertChannel):
    """SMS alerts via Twilio"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number
        
    async def send(self, message: str, request_id: str) -> bool:
        """Send SMS alert"""
        try:
            # Add request ID to message for easy response
            full_message = f"{message}\n\nRequest ID: {request_id[:8]}"
            
            # Send SMS
            message = self.client.messages.create(
                body=full_message,
                from_=self.from_number,
                to=self.to_number
            )
            
            print(f"SMS sent: {message.sid}")
            return True
            
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False


class TwilioCallChannel(AlertChannel):
    """Phone call alerts via Twilio"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str, webhook_url: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_number = to_number
        self.webhook_url = webhook_url
        
    async def send(self, message: str, request_id: str) -> bool:
        """Make phone call alert"""
        try:
            # Create TwiML for the call
            response = VoiceResponse()
            response.say(message, voice='alice')
            
            # Add gather for user response
            gather = response.gather(
                num_digits=1,
                action=f"{self.webhook_url}/response/{request_id}",
                method='POST'
            )
            gather.say("Press 1 to approve, 2 to deny, or 3 to defer this action.")
            
            # Save TwiML for webhook
            twiml_path = Path(f"backend/data/calls/{request_id}.xml")
            twiml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(twiml_path, 'w') as f:
                f.write(str(response))
            
            # Make the call
            call = self.client.calls.create(
                url=f"{self.webhook_url}/twiml/{request_id}",
                to=self.to_number,
                from_=self.from_number
            )
            
            print(f"Call initiated: {call.sid}")
            return True
            
        except Exception as e:
            print(f"Error making call: {e}")
            return False


class DesktopNotificationChannel(AlertChannel):
    """Desktop notifications"""
    
    async def send(self, message: str, request_id: str) -> bool:
        """Send desktop notification"""
        try:
            plyer.notification.notify(
                title="Digital Twin Alert",
                message=f"{message}\n\nID: {request_id[:8]}",
                timeout=10
            )
            return True
        except Exception as e:
            print(f"Error sending desktop notification: {e}")
            return False


class EmailChannel(AlertChannel):
    """Email alerts (placeholder for future implementation)"""
    
    async def send(self, message: str, request_id: str) -> bool:
        """Send email alert"""
        # TODO: Implement email sending
        print(f"Email alert (not implemented): {message}")
        return True


class AlertDispatcher:
    """Dispatches alerts through multiple channels"""
    
    def __init__(self):
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.config_path = Path("backend/config/alert_config.json")
        self._load_config()
        
    def _load_config(self):
        """Load alert configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self._setup_channels(config)
        else:
            print("No alert config found, using environment variables")
            self._setup_from_env()
    
    def _setup_from_env(self):
        """Setup channels from environment variables"""
        # Twilio SMS
        if all(os.getenv(k) for k in ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'USER_PHONE_NUMBER']):
            self.channels['sms'] = TwilioSMSChannel(
                account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
                auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
                from_number=os.getenv('TWILIO_PHONE_NUMBER'),
                to_number=os.getenv('USER_PHONE_NUMBER')
            )
            print("SMS channel configured")
        
        # Twilio Call
        webhook_url = os.getenv('TWILIO_WEBHOOK_URL')
        if webhook_url and 'sms' in self.channels:
            self.channels['call'] = TwilioCallChannel(
                account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
                auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
                from_number=os.getenv('TWILIO_PHONE_NUMBER'),
                to_number=os.getenv('USER_PHONE_NUMBER'),
                webhook_url=webhook_url
            )
            print("Call channel configured")
        
        # Desktop notifications (always available)
        self.channels['notification'] = DesktopNotificationChannel()
        print("Desktop notification channel configured")
    
    def _setup_channels(self, config: Dict[str, Any]):
        """Setup channels from config"""
        # Setup each configured channel
        for channel_name, channel_config in config.get('channels', {}).items():
            if not channel_config.get('enabled', False):
                continue
                
            channel_type = channel_config.get('type')
            
            if channel_type == 'twilio_sms':
                self.channels[channel_name] = TwilioSMSChannel(
                    account_sid=channel_config['account_sid'],
                    auth_token=channel_config['auth_token'],
                    from_number=channel_config['from_number'],
                    to_number=channel_config['to_number']
                )
            elif channel_type == 'twilio_call':
                self.channels[channel_name] = TwilioCallChannel(
                    account_sid=channel_config['account_sid'],
                    auth_token=channel_config['auth_token'],
                    from_number=channel_config['from_number'],
                    to_number=channel_config['to_number'],
                    webhook_url=channel_config['webhook_url']
                )
            elif channel_type == 'desktop':
                self.channels[channel_name] = DesktopNotificationChannel()
            elif channel_type == 'email':
                self.channels[channel_name] = EmailChannel()
    
    async def send_alert(self, message: str, request_id: str, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Send alert through specified channels
        
        Args:
            message: Alert message
            request_id: Request ID
            channels: List of channel names to use (None = all channels)
            
        Returns:
            Dict of channel name to success status
        """
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        tasks = []
        
        # Create tasks for each channel
        for channel_name in channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                task = asyncio.create_task(channel.send(message, request_id))
                tasks.append((channel_name, task))
        
        # Wait for all tasks
        for channel_name, task in tasks:
            try:
                results[channel_name] = await task
            except Exception as e:
                print(f"Error in channel {channel_name}: {e}")
                results[channel_name] = False
        
        # Log alert
        self._log_alert(message, request_id, results)
        
        return results
    
    async def send_sms(self, message: str, request_id: str) -> bool:
        """Send SMS alert"""
        if 'sms' in self.channels:
            results = await self.send_alert(message, request_id, ['sms'])
            return results.get('sms', False)
        return False
    
    async def send_call(self, message: str, request_id: str) -> bool:
        """Make phone call alert"""
        if 'call' in self.channels:
            results = await self.send_alert(message, request_id, ['call'])
            return results.get('call', False)
        return False
    
    async def send_notification(self, message: str, request_id: str) -> bool:
        """Send desktop notification"""
        if 'notification' in self.channels:
            results = await self.send_alert(message, request_id, ['notification'])
            return results.get('notification', False)
        return False
    
    def _log_alert(self, message: str, request_id: str, results: Dict[str, bool]):
        """Log alert to history"""
        alert_log = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'message': message,
            'results': results,
            'success': any(results.values())
        }
        
        self.alert_history.append(alert_log)
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def get_channel_status(self) -> Dict[str, str]:
        """Get status of all channels"""
        return {
            name: "configured" if name in self.channels else "not configured"
            for name in ['sms', 'call', 'notification', 'email']
        }


# Example configuration file format
EXAMPLE_CONFIG = {
    "channels": {
        "sms": {
            "type": "twilio_sms",
            "enabled": True,
            "account_sid": "your_account_sid",
            "auth_token": "your_auth_token",
            "from_number": "+1234567890",
            "to_number": "+0987654321"
        },
        "call": {
            "type": "twilio_call",
            "enabled": True,
            "account_sid": "your_account_sid",
            "auth_token": "your_auth_token",
            "from_number": "+1234567890",
            "to_number": "+0987654321",
            "webhook_url": "https://your-webhook-url.com"
        },
        "notification": {
            "type": "desktop",
            "enabled": True
        },
        "email": {
            "type": "email",
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your_email@gmail.com",
            "password": "your_app_password",
            "from_email": "your_email@gmail.com",
            "to_email": "recipient@example.com"
        }
    },
    "preferences": {
        "high_priority_channels": ["call", "sms", "notification"],
        "medium_priority_channels": ["sms", "notification"],
        "low_priority_channels": ["notification"]
    }
}


if __name__ == "__main__":
    # Example usage
    async def test_dispatcher():
        dispatcher = AlertDispatcher()
        
        # Check channel status
        print("Channel status:", dispatcher.get_channel_status())
        
        # Send test alert
        if dispatcher.channels:
            results = await dispatcher.send_alert(
                "Test alert from Digital Twin",
                "test-request-123",
                ['notification']  # Only desktop notification for testing
            )
            print(f"Alert results: {results}")
    
    # Run test
    asyncio.run(test_dispatcher())