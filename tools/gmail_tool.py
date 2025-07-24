"""
Gmail API Integration for Digital Twin

This tool provides real Gmail integration with intelligent email handling:
- Reading and analyzing incoming emails
- Composing and sending emails with your communication style
- Managing email threads and conversations
- Learning from email patterns and responses
- Smart email categorization and prioritization

The tool integrates with the twin's memory system to:
- Remember communication patterns with different people
- Learn effective email styles and responses
- Track email-based task creation and follow-ups
- Build relationship context from email history
"""

import base64
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os.path


@dataclass
class EmailMessage:
    """Structured representation of an email message"""
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: datetime
    is_unread: bool = False
    labels: List[str] = None
    attachments: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.attachments is None:
            self.attachments = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for memory storage"""
        return {
            'message_id': self.message_id,
            'thread_id': self.thread_id, 
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'timestamp': self.timestamp.isoformat(),
            'is_unread': self.is_unread,
            'labels': self.labels,
            'attachments': self.attachments
        }


@dataclass
class EmailAnalysis:
    """Analysis of an email for intelligent handling"""
    urgency_level: str  # "low", "medium", "high", "urgent"
    category: str       # "meeting", "task", "update", "question", "social"
    sentiment: str      # "positive", "neutral", "negative"
    requires_response: bool
    suggested_actions: List[str]
    key_entities: List[str]  # People, dates, projects mentioned
    estimated_response_time: int  # Minutes needed to respond properly
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'urgency_level': self.urgency_level,
            'category': self.category,
            'sentiment': self.sentiment,
            'requires_response': self.requires_response,
            'suggested_actions': self.suggested_actions,
            'key_entities': self.key_entities,
            'estimated_response_time': self.estimated_response_time
        }


class GmailTool:
    """
    Gmail integration tool for the digital twin.
    
    Provides intelligent email handling with memory integration:
    - Smart email reading and analysis
    - Context-aware email composition
    - Learning from email patterns
    - Integration with twin's memory and reasoning
    """
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, 
                 credentials_file: str = "gmail_credentials.json",
                 token_file: str = "gmail_token.pickle"):
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        # Email handling state
        self.processed_emails: set = set()
        self.email_cache: Dict[str, EmailMessage] = {}
        
        # Communication patterns learned from memory
        self.communication_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gmail service
        self._initialize_gmail_service()
    
    def _initialize_gmail_service(self):
        """Initialize the Gmail API service with authentication"""
        
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    self.logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                    self.logger.info("Please download credentials from Google Cloud Console")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            self.service = None
    
    async def get_unread_emails(self, limit: int = 10) -> List[EmailMessage]:
        """Get unread emails for processing"""
        
        if not self.service:
            self.logger.error("Gmail service not available")
            return []
        
        try:
            # Search for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            email_messages = []
            for message in messages:
                email_msg = await self._get_email_details(message['id'])
                if email_msg:
                    email_messages.append(email_msg)
            
            self.logger.info(f"Retrieved {len(email_messages)} unread emails")
            return email_messages
            
        except HttpError as error:
            self.logger.error(f"Failed to get unread emails: {error}")
            return []
    
    async def _get_email_details(self, message_id: str) -> Optional[EmailMessage]:
        """Get detailed email information"""
        
        if message_id in self.email_cache:
            return self.email_cache[message_id]
        
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            # Extract email details
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            sender = header_dict.get('From', 'Unknown')
            recipient = header_dict.get('To', 'Unknown')
            subject = header_dict.get('Subject', 'No Subject')
            date_str = header_dict.get('Date', '')
            
            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                timestamp = parsedate_to_datetime(date_str)
            except:
                timestamp = datetime.now()
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            # Check if unread
            is_unread = 'UNREAD' in message.get('labelIds', [])
            
            # Get labels
            labels = message.get('labelIds', [])
            
            email_msg = EmailMessage(
                message_id=message_id,
                thread_id=message.get('threadId', ''),
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                timestamp=timestamp,
                is_unread=is_unread,
                labels=labels
            )
            
            # Cache the email
            self.email_cache[message_id] = email_msg
            
            return email_msg
            
        except HttpError as error:
            self.logger.error(f"Failed to get email details for {message_id}: {error}")
            return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail API payload"""
        
        body = ""
        
        if 'parts' in payload:
            # Multi-part email
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        # Could parse HTML here, for now just decode
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            # Single part email
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body.strip()
    
    async def analyze_email(self, email: EmailMessage) -> EmailAnalysis:
        """Analyze an email for intelligent handling"""
        
        # Simple analysis - in production, you'd use more sophisticated NLP
        
        # Determine urgency
        urgency_keywords = {
            'urgent': ['urgent', 'asap', 'immediately', 'emergency'],
            'high': ['important', 'priority', 'deadline', 'today'],
            'medium': ['please', 'need', 'should', 'when possible'],
            'low': ['fyi', 'info', 'whenever', 'no rush']
        }
        
        urgency_level = "medium"  # default
        email_text = (email.subject + " " + email.body).lower()
        
        for level, keywords in urgency_keywords.items():
            if any(keyword in email_text for keyword in keywords):
                urgency_level = level
                break
        
        # Determine category
        category_keywords = {
            'meeting': ['meeting', 'call', 'zoom', 'conference', 'discuss'],
            'task': ['task', 'todo', 'action', 'complete', 'finish'],
            'update': ['update', 'status', 'progress', 'report'],
            'question': ['question', 'help', 'how', 'what', 'why', '?'],
            'social': ['hi', 'hello', 'thanks', 'congratulations']
        }
        
        category = "update"  # default
        for cat, keywords in category_keywords.items():
            if any(keyword in email_text for keyword in keywords):
                category = cat
                break
        
        # Determine if response is needed
        requires_response = (
            '?' in email_text or
            'please' in email_text or
            'need' in email_text or
            category in ['question', 'task', 'meeting']
        )
        
        # Suggest actions
        suggested_actions = []
        if category == 'meeting':
            suggested_actions.extend(['schedule_meeting', 'check_calendar'])
        if category == 'task':
            suggested_actions.extend(['create_task', 'set_reminder'])
        if requires_response:
            suggested_actions.append('compose_response')
        
        # Extract key entities (simplified)
        key_entities = self._extract_entities(email_text)
        
        # Estimate response time
        time_map = {'urgent': 5, 'high': 30, 'medium': 120, 'low': 480}
        estimated_time = time_map.get(urgency_level, 120)
        
        # Sentiment analysis (very basic)
        positive_words = ['thank', 'great', 'excellent', 'good', 'happy']
        negative_words = ['problem', 'issue', 'concern', 'sorry', 'wrong']
        
        positive_count = sum(1 for word in positive_words if word in email_text)
        negative_count = sum(1 for word in negative_words if word in email_text)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return EmailAnalysis(
            urgency_level=urgency_level,
            category=category,
            sentiment=sentiment,
            requires_response=requires_response,
            suggested_actions=suggested_actions,
            key_entities=key_entities,
            estimated_response_time=estimated_time
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from email text (simplified)"""
        
        entities = []
        
        # Look for dates
        import re
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(today|tomorrow|next week)\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Look for times
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(am|pm)?\b',
            r'\b\d{1,2}\s*(am|pm)\b'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend([match[0] if isinstance(match, tuple) else match for match in matches])
        
        return entities[:5]  # Return top 5 entities
    
    async def compose_email(self,
                           recipient: str,
                           subject: str,
                           body: str,
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compose and send an email"""
        
        if not self.service:
            return {"success": False, "error": "Gmail service not available"}
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = recipient
            message['subject'] = subject
            
            # Get sender email
            profile = self.service.users().getProfile(userId='me').execute()
            sender_email = profile['emailAddress']
            message['from'] = sender_email
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Email sent successfully to {recipient}")
            
            return {
                'success': True,
                'message_id': send_result['id'],
                'recipient': recipient,
                'subject': subject,
                'timestamp': datetime.now().isoformat()
            }
            
        except HttpError as error:
            self.logger.error(f"Failed to send email: {error}")
            return {
                'success': False,
                'error': str(error),
                'recipient': recipient,
                'subject': subject
            }
    
    async def send_email(self, 
                        recipient: str, 
                        subject: str, 
                        body: str,
                        **kwargs) -> Dict[str, Any]:
        """Send email - interface for twin controller"""
        
        context = kwargs.get('_context', {})
        
        # Apply communication patterns if available
        enhanced_body = await self._enhance_email_with_patterns(
            recipient, subject, body, context
        )
        
        result = await self.compose_email(recipient, subject, enhanced_body, context)
        
        # Learn from this composition
        if result['success']:
            await self._learn_from_email_composition(recipient, subject, enhanced_body, context)
        
        return result
    
    async def _enhance_email_with_patterns(self,
                                          recipient: str,
                                          subject: str, 
                                          body: str,
                                          context: Dict[str, Any]) -> str:
        """Enhance email composition with learned patterns"""
        
        # Check if we have communication patterns for this recipient
        recipient_domain = recipient.split('@')[-1] if '@' in recipient else 'unknown'
        
        patterns = self.communication_patterns.get(recipient, {})
        domain_patterns = self.communication_patterns.get(recipient_domain, {})
        
        enhanced_body = body
        
        # Apply formality level
        formality = patterns.get('formality', domain_patterns.get('formality', 'medium'))
        
        if formality == 'high':
            if not enhanced_body.startswith(('Dear', 'Hello')):
                enhanced_body = f"Dear {recipient.split('@')[0]},\n\n{enhanced_body}"
            if not enhanced_body.endswith(('Sincerely', 'Best regards')):
                enhanced_body = f"{enhanced_body}\n\nBest regards"
        elif formality == 'low':
            if not enhanced_body.startswith(('Hi', 'Hey')):
                enhanced_body = f"Hi {recipient.split('@')[0]},\n\n{enhanced_body}"
            if not enhanced_body.endswith(('Thanks', 'Cheers')):
                enhanced_body = f"{enhanced_body}\n\nThanks"
        
        # Apply typical response patterns
        if 'typical_closings' in patterns:
            closings = patterns['typical_closings']
            if closings and not any(closing in enhanced_body for closing in closings):
                enhanced_body = f"{enhanced_body}\n\n{closings[0]}"
        
        return enhanced_body
    
    async def _learn_from_email_composition(self,
                                           recipient: str,
                                           subject: str,
                                           body: str,
                                           context: Dict[str, Any]):
        """Learn patterns from email composition"""
        
        # Extract patterns from this composition
        if recipient not in self.communication_patterns:
            self.communication_patterns[recipient] = {
                'email_count': 0,
                'avg_length': 0,
                'common_subjects': [],
                'formality': 'medium',
                'typical_closings': []
            }
        
        patterns = self.communication_patterns[recipient]
        patterns['email_count'] += 1
        
        # Update average length
        body_length = len(body.split())
        patterns['avg_length'] = (
            (patterns['avg_length'] * (patterns['email_count'] - 1) + body_length) / 
            patterns['email_count']
        )
        
        # Track subject patterns
        if subject not in patterns['common_subjects']:
            patterns['common_subjects'].append(subject)
            # Keep only recent subjects
            if len(patterns['common_subjects']) > 10:
                patterns['common_subjects'] = patterns['common_subjects'][-10:]
        
        # Detect formality level
        formal_indicators = ['dear', 'sincerely', 'best regards', 'yours truly']
        informal_indicators = ['hi', 'hey', 'thanks', 'cheers']
        
        body_lower = body.lower()
        formal_count = sum(1 for indicator in formal_indicators if indicator in body_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in body_lower)
        
        if formal_count > informal_count:
            patterns['formality'] = 'high'
        elif informal_count > formal_count:
            patterns['formality'] = 'low'
        
        self.logger.info(f"Updated communication patterns for {recipient}")
    
    async def get_recent_emails(self, 
                               days: int = 7, 
                               limit: int = 50) -> List[EmailMessage]:
        """Get recent emails for analysis"""
        
        if not self.service:
            return []
        
        try:
            # Calculate date range
            after_date = datetime.now() - timedelta(days=days)
            after_str = after_date.strftime('%Y/%m/%d')
            
            results = self.service.users().messages().list(
                userId='me',
                q=f'after:{after_str}',
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            email_messages = []
            for message in messages:
                email_msg = await self._get_email_details(message['id'])
                if email_msg:
                    email_messages.append(email_msg)
            
            return email_messages
            
        except HttpError as error:
            self.logger.error(f"Failed to get recent emails: {error}")
            return []
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read"""
        
        if not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            # Update cache
            if message_id in self.email_cache:
                self.email_cache[message_id].is_unread = False
            
            return True
            
        except HttpError as error:
            self.logger.error(f"Failed to mark email as read: {error}")
            return False
    
    def get_communication_insights(self) -> Dict[str, Any]:
        """Get insights about communication patterns"""
        
        total_emails = len(self.email_cache)
        unread_count = sum(1 for email in self.email_cache.values() if email.is_unread)
        
        # Analyze senders
        senders = {}
        for email in self.email_cache.values():
            sender = email.sender
            if sender not in senders:
                senders[sender] = 0
            senders[sender] += 1
        
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_emails_processed': total_emails,
            'unread_emails': unread_count,
            'top_senders': top_senders,
            'communication_patterns': len(self.communication_patterns),
            'patterns_learned': {
                recipient: {
                    'email_count': patterns['email_count'],
                    'formality': patterns['formality'],
                    'avg_length': int(patterns['avg_length'])
                }
                for recipient, patterns in self.communication_patterns.items()
            }
        }
    
    async def smart_email_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get intelligent summary of recent emails"""
        
        recent_emails = await self.get_unread_emails(limit)
        
        if not recent_emails:
            return {
                'summary': 'No unread emails',
                'urgent_count': 0,
                'action_required': 0,
                'total_unread': 0
            }
        
        # Analyze all emails
        analyses = []
        for email in recent_emails:
            analysis = await self.analyze_email(email)
            analyses.append((email, analysis))
        
        # Categorize
        urgent_emails = [ea for ea in analyses if ea[1].urgency_level in ['urgent', 'high']]
        action_required = [ea for ea in analyses if ea[1].requires_response]
        
        # Create summary
        summary_parts = []
        
        if urgent_emails:
            summary_parts.append(f"{len(urgent_emails)} urgent emails")
        
        if action_required:
            summary_parts.append(f"{len(action_required)} requiring response")
        
        categories = {}
        for _, analysis in analyses:
            cat = analysis.category
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            summary_parts.append(f"mostly {top_category[0]} emails")
        
        summary = "Recent emails: " + ", ".join(summary_parts) if summary_parts else "Recent emails processed"
        
        return {
            'summary': summary,
            'urgent_count': len(urgent_emails),
            'action_required': len(action_required),
            'total_unread': len(recent_emails),
            'categories': categories,
            'urgent_emails': [
                {
                    'sender': email.sender,
                    'subject': email.subject,
                    'urgency': analysis.urgency_level
                }
                for email, analysis in urgent_emails
            ]
        }