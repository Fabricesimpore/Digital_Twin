"""
Twilio Voice API Integration for Digital Twin

This tool provides real voice communication capabilities:
- Making phone calls with intelligent message delivery
- Text-to-speech for natural voice synthesis
- Call recording and transcription for learning
- Voice-based reminders and notifications
- Integration with twin's memory for personalized communication

The tool learns from the twin's memory system to:
- Remember successful call patterns and timing
- Learn optimal message delivery styles
- Track call outcomes and effectiveness
- Build context about voice communication preferences
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

try:
    from twilio.rest import Client
    from twilio.twiml import VoiceResponse
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class CallRecord:
    """Record of a phone call made by the twin"""
    call_sid: str
    recipient: str
    message_type: str
    message_content: str
    call_duration: int  # seconds
    call_status: str    # completed, busy, no-answer, failed
    timestamp: datetime
    cost: float = 0.0
    recording_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for memory storage"""
        return {
            'call_sid': self.call_sid,
            'recipient': self.recipient,
            'message_type': self.message_type,
            'message_content': self.message_content,
            'call_duration': self.call_duration,
            'call_status': self.call_status,
            'timestamp': self.timestamp.isoformat(),
            'cost': self.cost,
            'recording_url': self.recording_url
        }


@dataclass
class VoiceMessage:
    """Structured voice message for delivery"""
    message_type: str      # reminder, update, notification, personal
    content: str          # What to say
    urgency: str         # low, medium, high, urgent
    personalization: Dict[str, Any]  # Personal touches for the recipient
    estimated_duration: int  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_type': self.message_type,
            'content': self.content,
            'urgency': self.urgency,
            'personalization': self.personalization,
            'estimated_duration': self.estimated_duration
        }


class VoiceTool:
    """
    Twilio Voice integration tool for the digital twin.
    
    Provides intelligent voice communication with memory integration:
    - Smart call scheduling and execution
    - Personalized message delivery
    - Learning from call outcomes
    - Integration with twin's reasoning and memory systems
    """
    
    def __init__(self,
                 account_sid: str = None,
                 auth_token: str = None,
                 from_number: str = None):
        
        # Twilio credentials
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_FROM_NUMBER')
        
        # Initialize Twilio client
        if TWILIO_AVAILABLE and self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
        
        # Call tracking
        self.call_history: Dict[str, CallRecord] = {}
        self.message_templates: Dict[str, str] = {}
        
        # Voice preferences learned from memory
        self.voice_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize message templates and voice patterns
        self._initialize_message_templates()
        self._initialize_voice_patterns()
        
        if not self.client:
            self.logger.warning("Twilio credentials not provided - voice functionality disabled")
    
    def _initialize_message_templates(self):
        """Initialize default message templates"""
        
        self.message_templates = {
            'task_reminder': (
                "Hi, this is your digital assistant calling with a reminder. "
                "You asked me to remind you about: {task_description}. "
                "The deadline is {deadline}. "
                "Would you like me to reschedule this reminder or mark it as complete? "
                "I'll wait for your response."
            ),
            'meeting_reminder': (
                "Hello, this is your digital assistant. "
                "You have a meeting coming up: {meeting_title} "
                "scheduled for {meeting_time} with {attendees}. "
                "The meeting is in {time_until} minutes. "
                "Don't forget to join at {meeting_link} if it's virtual."
            ),
            'daily_update': (
                "Good {time_of_day}! This is your daily update. "
                "Today you have {event_count} events scheduled, "
                "including {important_events}. "
                "Your priority tasks are: {priority_tasks}. "
                "You have {unread_emails} unread emails, "
                "{urgent_count} of which are marked urgent. "
                "Have a productive day!"
            ),
            'urgent_notification': (
                "This is an urgent notification from your digital assistant. "
                "{urgent_message} "
                "This requires your immediate attention. "
                "Please respond when you receive this message."
            ),
            'general_notification': (
                "Hi, this is your digital assistant calling with an update. "
                "{message_content} "
                "Let me know if you need any follow-up actions."
            ),
            'check_in': (
                "Hi, this is your digital assistant checking in. "
                "How are things going with {context}? "
                "Based on your schedule, you should be {expected_activity} right now. "
                "Is there anything I can help you with?"
            )
        }
        
        self.logger.info(f"Initialized {len(self.message_templates)} voice message templates")
    
    def _initialize_voice_patterns(self):
        """Initialize voice communication patterns"""
        
        # Default patterns - these will be learned and updated over time
        self.voice_patterns = {
            'optimal_call_times': {
                'weekday_morning': {'start': 9, 'end': 11, 'success_rate': 0.7},
                'weekday_afternoon': {'start': 14, 'end': 16, 'success_rate': 0.8},
                'weekday_evening': {'start': 18, 'end': 20, 'success_rate': 0.6},
                'weekend': {'start': 10, 'end': 18, 'success_rate': 0.5}
            },
            'message_effectiveness': {
                'task_reminder': {'avg_response_rate': 0.8, 'optimal_length': 45},
                'meeting_reminder': {'avg_response_rate': 0.9, 'optimal_length': 30},
                'daily_update': {'avg_response_rate': 0.6, 'optimal_length': 60},
                'urgent_notification': {'avg_response_rate': 0.95, 'optimal_length': 20}
            },
            'personalization_preferences': {
                'formality_level': 'medium',
                'use_name': True,
                'include_context': True,
                'wait_for_response': True
            }
        }
    
    async def make_call(self,
                       recipient: str,
                       message_type: str = "general",
                       message_content: str = "",
                       context: Dict[str, Any] = None,
                       **kwargs) -> Dict[str, Any]:
        """Make a phone call with intelligent message delivery"""
        
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not initialized - check credentials',
                'recipient': recipient
            }
        
        if not self.from_number:
            return {
                'success': False,
                'error': 'Twilio from_number not configured',
                'recipient': recipient
            }
        
        # Get context from previous steps if available (twin controller integration)
        if '_context' in kwargs:
            step_context = kwargs['_context']
            
            # Check if we have task results from previous step
            if 'step_0_result' in step_context and message_type == 'task_reminder':
                tasks = step_context['step_0_result']
                if isinstance(tasks, dict) and 'tasks' in tasks:
                    message_content = self._format_task_reminder_message(tasks['tasks'])
        
        try:
            # Generate personalized message
            voice_message = await self._generate_voice_message(
                message_type, message_content, context or {}
            )
            
            # Check if this is an optimal time to call
            timing_analysis = self._analyze_call_timing()
            
            self.logger.info(f"Making call to {recipient}: {message_type}")
            self.logger.info(f"Timing analysis: {timing_analysis}")
            
            # Create TwiML for the call
            twiml = self._create_twiml_response(voice_message)
            
            # Make the call
            call = self.client.calls.create(
                twiml=twiml,
                to=recipient,
                from_=self.from_number,
                record=True,  # Record for learning
                timeout=30,   # Ring for 30 seconds
                status_callback_event=['completed', 'answered', 'busy'],
                status_callback_method='POST'
            )
            
            # Create call record
            call_record = CallRecord(
                call_sid=call.sid,
                recipient=recipient,
                message_type=message_type,
                message_content=voice_message.content,
                call_duration=0,  # Will be updated when call completes
                call_status='initiated',
                timestamp=datetime.now()
            )
            
            self.call_history[call.sid] = call_record
            
            # Learn from this call attempt
            await self._learn_from_call_attempt(call_record, context or {})
            
            return {
                'success': True,
                'call_sid': call.sid,
                'recipient': recipient,
                'message_type': message_type,
                'estimated_duration': voice_message.estimated_duration,
                'timing_analysis': timing_analysis,
                'message': f"Call initiated to {recipient}"
            }
            
        except TwilioException as e:
            self.logger.error(f"Twilio error making call: {e}")
            return {
                'success': False,
                'error': f'Twilio error: {str(e)}',
                'recipient': recipient,
                'message_type': message_type
            }
        except Exception as e:
            self.logger.error(f"Unexpected error making call: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'recipient': recipient
            }
    
    def _format_task_reminder_message(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks into a speakable message"""
        if not tasks:
            return "You have no pending tasks at the moment. Enjoy your free time!"
        
        message = f"You have {len(tasks)} tasks to complete. "
        
        # Group by priority
        high_priority = [t for t in tasks if t.get('priority') == 'high']
        normal_priority = [t for t in tasks if t.get('priority') != 'high']
        
        if high_priority:
            message += f"High priority tasks: "
            for task in high_priority[:3]:  # Limit to top 3
                message += f"{task.get('title', 'Untitled task')}. "
                if task.get('deadline'):
                    message += f"Due {task['deadline']}. "
        
        if normal_priority and len(message) < 500:  # Keep message reasonable length
            message += f"Other tasks include: "
            for task in normal_priority[:2]:
                message += f"{task.get('title', 'Untitled task')}. "
        
        return message
    
    async def _generate_voice_message(self,
                                     message_type: str,
                                     content: str,
                                     context: Dict[str, Any]) -> VoiceMessage:
        """Generate a personalized voice message"""
        
        # Get template for message type
        template = self.message_templates.get(message_type, self.message_templates['general_notification'])
        
        # Extract personalization context
        personalization = {
            'recipient_name': context.get('recipient_name', 'there'),
            'time_of_day': self._get_time_of_day_greeting(),
            'urgency_modifier': self._get_urgency_modifier(context.get('urgency', 'medium'))
        }
        
        # Build message content based on type
        if message_type == 'task_reminder':
            message_content = template.format(
                task_description=content or "your scheduled task",
                deadline=context.get('deadline', 'soon'),
                **personalization
            )
        elif message_type == 'meeting_reminder':
            message_content = template.format(
                meeting_title=context.get('meeting_title', 'your meeting'),
                meeting_time=context.get('meeting_time', 'the scheduled time'),
                attendees=context.get('attendees', 'other participants'),
                time_until=context.get('time_until', '15'),
                meeting_link=context.get('meeting_link', 'the meeting location'),
                **personalization
            )
        elif message_type == 'daily_update':
            message_content = template.format(
                event_count=context.get('event_count', 0),
                important_events=context.get('important_events', 'your scheduled meetings'),
                priority_tasks=context.get('priority_tasks', 'your pending tasks'),
                unread_emails=context.get('unread_emails', 0),
                urgent_count=context.get('urgent_count', 0),
                **personalization
            )
        elif message_type == 'urgent_notification':
            message_content = template.format(
                urgent_message=content or "There is an urgent matter that needs your attention",
                **personalization
            )
        else:
            # General message or use provided content
            if content:
                message_content = content
            else:
                message_content = template.format(
                    message_content="I have an update for you",
                    **personalization
                )
        
        # Apply personalization preferences
        message_content = self._apply_personalization(message_content, context)
        
        # Estimate speaking duration (average 150 words per minute)
        word_count = len(message_content.split())
        estimated_duration = int((word_count / 150) * 60) + 10  # Add 10 seconds buffer
        
        return VoiceMessage(
            message_type=message_type,
            content=message_content,
            urgency=context.get('urgency', 'medium'),
            personalization=personalization,
            estimated_duration=estimated_duration
        )
    
    def _get_time_of_day_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "evening"  # Late night, still use evening
    
    def _get_urgency_modifier(self, urgency: str) -> str:
        """Get urgency modifier for message tone"""
        modifiers = {
            'low': 'when you have a moment',
            'medium': 'at your convenience',
            'high': 'soon',
            'urgent': 'immediately'
        }
        return modifiers.get(urgency, 'at your convenience')
    
    def _apply_personalization(self, message: str, context: Dict[str, Any]) -> str:
        """Apply personalization preferences to message"""
        
        prefs = self.voice_patterns.get('personalization_preferences', {})
        
        # Adjust formality
        formality = prefs.get('formality_level', 'medium')
        if formality == 'high':
            message = message.replace("Hi,", "Good day,")
            message = message.replace("Thanks", "Thank you")
        elif formality == 'low':
            message = message.replace("Good day,", "Hey,")
            message = message.replace("This is your digital assistant", "It's me, your assistant")
        
        # Add context if preferred
        if prefs.get('include_context', True) and context.get('current_activity'):
            activity = context['current_activity']
            message += f" I know you're currently {activity}, so I'll keep this brief."
        
        return message
    
    def _create_twiml_response(self, voice_message: VoiceMessage) -> str:
        """Create TwiML response for the call"""
        
        response = VoiceResponse()
        
        # Add a pause to let the person answer
        response.pause(length=1)
        
        # Say the message
        response.say(
            voice_message.content,
            voice='Polly.Joanna',  # Use Amazon Polly voice
            language='en-US'
        )
        
        # If it's an interactive message, gather response
        if voice_message.message_type in ['task_reminder', 'check_in']:
            gather = response.gather(
                num_digits=1,
                timeout=10,
                action='/voice/handle_response',
                method='POST'
            )
            gather.say(
                "Press 1 if this is complete, 2 to snooze for 1 hour, or 3 to speak with me.",
                voice='Polly.Joanna'
            )
            
            # If no response, leave a polite message
            response.say(
                "I didn't hear a response. I'll check back with you later. Have a great day!",
                voice='Polly.Joanna'
            )
        else:
            # Non-interactive message
            response.pause(length=2)
            response.say(
                "That's all for now. Have a great day!",
                voice='Polly.Joanna'
            )
        
        return str(response)
    
    def _analyze_call_timing(self) -> Dict[str, Any]:
        """Analyze if current time is optimal for calling"""
        
        now = datetime.now()
        hour = now.hour
        day_name = now.strftime('%A')
        is_weekend = now.weekday() >= 5
        
        # Get timing patterns
        timing_patterns = self.voice_patterns.get('optimal_call_times', {})
        
        # Determine current period
        if is_weekend:
            current_period = 'weekend'
            optimal_range = timing_patterns.get('weekend', {})
        elif 9 <= hour <= 11:
            current_period = 'weekday_morning'
            optimal_range = timing_patterns.get('weekday_morning', {})
        elif 14 <= hour <= 16:
            current_period = 'weekday_afternoon'
            optimal_range = timing_patterns.get('weekday_afternoon', {})
        elif 18 <= hour <= 20:
            current_period = 'weekday_evening'
            optimal_range = timing_patterns.get('weekday_evening', {})
        else:
            current_period = 'off_hours'
            optimal_range = {'success_rate': 0.3}
        
        # Calculate timing score
        success_rate = optimal_range.get('success_rate', 0.5)
        
        if success_rate >= 0.8:
            timing_quality = 'excellent'
        elif success_rate >= 0.6:
            timing_quality = 'good'
        elif success_rate >= 0.4:
            timing_quality = 'fair'
        else:
            timing_quality = 'poor'
        
        return {
            'current_period': current_period,
            'timing_quality': timing_quality,
            'expected_success_rate': success_rate,
            'hour': hour,
            'day': day_name,
            'is_weekend': is_weekend,
            'recommendation': 'proceed' if success_rate >= 0.5 else 'consider_rescheduling'
        }
    
    async def _learn_from_call_attempt(self, call_record: CallRecord, context: Dict[str, Any]):
        """Learn from call attempt for future optimization"""
        
        # Update timing patterns based on this attempt
        timing_analysis = self._analyze_call_timing()
        current_period = timing_analysis['current_period']
        
        # This would be updated when we get the call completion webhook
        # For now, we track the attempt
        if current_period not in self.voice_patterns.get('call_attempts', {}):
            if 'call_attempts' not in self.voice_patterns:
                self.voice_patterns['call_attempts'] = {}
            self.voice_patterns['call_attempts'][current_period] = {'total': 0, 'successful': 0}
        
        self.voice_patterns['call_attempts'][current_period]['total'] += 1
        
        self.logger.info(f"Logged call attempt for learning: {call_record.message_type} at {current_period}")
    
    async def handle_call_completion(self, call_sid: str, call_status: str, call_duration: int = 0):
        """Handle call completion for learning and analytics"""
        
        if call_sid not in self.call_history:
            self.logger.warning(f"Unknown call SID in completion handler: {call_sid}")
            return
        
        call_record = self.call_history[call_sid]
        call_record.call_status = call_status
        call_record.call_duration = call_duration
        
        # Learn from the outcome
        success = call_status in ['completed', 'answered']
        
        # Update timing success rates
        timing_analysis = self._analyze_call_timing()
        current_period = timing_analysis['current_period']
        
        if 'call_attempts' in self.voice_patterns and current_period in self.voice_patterns['call_attempts']:
            if success:
                self.voice_patterns['call_attempts'][current_period]['successful'] += 1
            
            # Recalculate success rate
            attempts = self.voice_patterns['call_attempts'][current_period]
            new_success_rate = attempts['successful'] / attempts['total']
            
            # Update optimal call times
            if current_period in self.voice_patterns['optimal_call_times']:
                old_rate = self.voice_patterns['optimal_call_times'][current_period]['success_rate']
                # Use exponential moving average
                alpha = 0.2
                self.voice_patterns['optimal_call_times'][current_period]['success_rate'] = (
                    alpha * new_success_rate + (1 - alpha) * old_rate
                )
        
        # Update message effectiveness
        message_type = call_record.message_type
        if message_type in self.voice_patterns.get('message_effectiveness', {}):
            effectiveness = self.voice_patterns['message_effectiveness'][message_type]
            
            # Update response rate (simplified)
            if success:
                effectiveness['avg_response_rate'] = min(1.0, effectiveness['avg_response_rate'] * 1.1)
            else:
                effectiveness['avg_response_rate'] = max(0.1, effectiveness['avg_response_rate'] * 0.9)
        
        self.logger.info(f"Updated learning from call completion: {call_status} for {message_type}")
    
    async def get_call_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent calling activity"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_calls = [
            call for call in self.call_history.values()
            if call.timestamp >= cutoff_date
        ]
        
        if not recent_calls:
            return {
                'summary': f'No calls made in the last {days} days',
                'total_calls': 0,
                'successful_calls': 0,
                'success_rate': 0.0
            }
        
        # Calculate statistics
        total_calls = len(recent_calls)
        successful_calls = len([c for c in recent_calls if c.call_status in ['completed', 'answered']])
        success_rate = successful_calls / total_calls if total_calls > 0 else 0
        
        # Group by message type
        by_type = {}
        for call in recent_calls:
            msg_type = call.message_type
            if msg_type not in by_type:
                by_type[msg_type] = {'count': 0, 'successful': 0}
            by_type[msg_type]['count'] += 1
            if call.call_status in ['completed', 'answered']:
                by_type[msg_type]['successful'] += 1
        
        # Calculate total duration and cost
        total_duration = sum(call.call_duration for call in recent_calls)
        total_cost = sum(call.cost for call in recent_calls)
        
        return {
            'summary': f'{total_calls} calls made in {days} days, {success_rate:.1%} success rate',
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'success_rate': success_rate,
            'total_duration_minutes': total_duration // 60,
            'total_cost': total_cost,
            'by_message_type': {
                msg_type: {
                    'count': stats['count'],
                    'success_rate': stats['successful'] / stats['count'] if stats['count'] > 0 else 0
                }
                for msg_type, stats in by_type.items()
            },
            'recent_calls': [call.to_dict() for call in recent_calls[-5:]]  # Last 5 calls
        }
    
    def get_voice_insights(self) -> Dict[str, Any]:
        """Get insights about voice communication patterns"""
        
        return {
            'total_calls_made': len(self.call_history),
            'message_templates': len(self.message_templates),
            'learned_patterns': {
                'optimal_call_times': self.voice_patterns.get('optimal_call_times', {}),
                'message_effectiveness': self.voice_patterns.get('message_effectiveness', {}),
                'personalization_preferences': self.voice_patterns.get('personalization_preferences', {})
            },
            'voice_patterns_learned': len(self.voice_patterns)
        }
    
    async def test_voice_capability(self) -> Dict[str, Any]:
        """Test voice capability without making actual calls"""
        
        # Test message generation
        test_message = await self._generate_voice_message(
            'task_reminder',
            'Test your digital twin setup',
            {'deadline': 'today', 'urgency': 'medium'}
        )
        
        # Test timing analysis
        timing = self._analyze_call_timing()
        
        # Test TwiML generation
        twiml = self._create_twiml_response(test_message)
        
        return {
            'voice_tool_ready': self.client is not None,
            'credentials_configured': bool(self.account_sid and self.auth_token and self.from_number),
            'test_message': test_message.to_dict(),
            'timing_analysis': timing,
            'twiml_generated': len(twiml) > 0,
            'message_templates_loaded': len(self.message_templates),
            'voice_patterns_initialized': len(self.voice_patterns)
        }