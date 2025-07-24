"""
Google Calendar API Integration for Digital Twin

This tool provides intelligent calendar management with memory integration:
- Reading and analyzing calendar events
- Creating and managing events with context awareness
- Learning scheduling patterns and preferences
- Intelligent conflict detection and resolution
- Integration with email and task management

The tool learns from the twin's memory system to:
- Remember preferred meeting times and patterns
- Learn optimal scheduling strategies
- Track meeting outcomes and effectiveness
- Build context about recurring meetings and relationships
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os.path


@dataclass
class CalendarEvent:
    """Structured representation of a calendar event"""
    event_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    creator: str = ""
    is_recurring: bool = False
    status: str = "confirmed"  # confirmed, tentative, cancelled
    meeting_link: str = ""
    calendar_id: str = "primary"
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []
    
    @property
    def duration(self) -> timedelta:
        """Get event duration"""
        return self.end_time - self.start_time
    
    @property
    def is_today(self) -> bool:
        """Check if event is today"""
        return self.start_time.date() == datetime.now().date()
    
    @property
    def is_tomorrow(self) -> bool:
        """Check if event is tomorrow"""
        tomorrow = datetime.now().date() + timedelta(days=1)
        return self.start_time.date() == tomorrow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for memory storage"""
        return {
            'event_id': self.event_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location': self.location,
            'attendees': self.attendees,
            'creator': self.creator,
            'is_recurring': self.is_recurring,
            'status': self.status,
            'meeting_link': self.meeting_link,
            'duration_minutes': int(self.duration.total_seconds() / 60)
        }
    
    def conflicts_with(self, other: 'CalendarEvent') -> bool:
        """Check if this event conflicts with another"""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


@dataclass
class SchedulingAnalysis:
    """Analysis of scheduling patterns and preferences"""
    preferred_times: List[str]  # ["9:00 AM", "2:00 PM"]
    preferred_days: List[str]   # ["Monday", "Wednesday"]
    average_meeting_length: int  # minutes
    common_meeting_types: Dict[str, int]
    busy_periods: List[Tuple[datetime, datetime]]
    free_periods: List[Tuple[datetime, datetime]]
    scheduling_conflicts: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'preferred_times': self.preferred_times,
            'preferred_days': self.preferred_days,
            'average_meeting_length': self.average_meeting_length,
            'common_meeting_types': self.common_meeting_types,
            'scheduling_conflicts': self.scheduling_conflicts,
            'busy_periods': [
                (start.isoformat(), end.isoformat()) 
                for start, end in self.busy_periods
            ],
            'free_periods': [
                (start.isoformat(), end.isoformat())
                for start, end in self.free_periods
            ]
        }


class CalendarTool:
    """
    Google Calendar integration tool for the digital twin.
    
    Provides intelligent calendar management with memory integration:
    - Smart event creation and management
    - Conflict detection and resolution
    - Pattern learning from scheduling behavior
    - Integration with twin's reasoning and memory systems
    """
    
    # Calendar API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self,
                 credentials_file: str = "calendar_credentials.json",
                 token_file: str = "calendar_token.pickle"):
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        # Calendar state
        self.event_cache: Dict[str, CalendarEvent] = {}
        self.scheduling_patterns: Dict[str, Any] = {}
        
        # Learning and optimization
        self.preferred_times: List[str] = []
        self.conflict_history: List[Dict[str, Any]] = []
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize Calendar service
        self._initialize_calendar_service()
    
    def _initialize_calendar_service(self):
        """Initialize the Google Calendar API service"""
        
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
                    self.logger.error(f"Calendar credentials file not found: {self.credentials_file}")
                    self.logger.info("Please download credentials from Google Cloud Console")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Calendar service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Calendar service: {e}")
            self.service = None
    
    async def get_upcoming_events(self, 
                                 days_ahead: int = 7, 
                                 limit: int = 50) -> List[CalendarEvent]:
        """Get upcoming calendar events"""
        
        if not self.service:
            self.logger.error("Calendar service not available")
            return []
        
        try:
            # Calculate time range
            now = datetime.now(timezone.utc)
            end_time = now + timedelta(days=days_ahead)
            
            # Get events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            calendar_events = []
            for event in events:
                calendar_event = self._parse_calendar_event(event)
                if calendar_event:
                    calendar_events.append(calendar_event)
                    self.event_cache[calendar_event.event_id] = calendar_event
            
            self.logger.info(f"Retrieved {len(calendar_events)} upcoming events")
            return calendar_events
            
        except HttpError as error:
            self.logger.error(f"Failed to get upcoming events: {error}")
            return []
    
    def _parse_calendar_event(self, event_data: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Parse Google Calendar event data into CalendarEvent object"""
        
        try:
            event_id = event_data['id']
            title = event_data.get('summary', 'No Title')
            description = event_data.get('description', '')
            
            # Parse start and end times
            start_data = event_data['start']
            end_data = event_data['end']
            
            if 'dateTime' in start_data:
                # Timed event
                start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            else:
                # All-day event
                start_time = datetime.fromisoformat(start_data['date'] + 'T00:00:00+00:00')
                end_time = datetime.fromisoformat(end_data['date'] + 'T23:59:59+00:00')
            
            # Extract other details
            location = event_data.get('location', '')
            creator = event_data.get('creator', {}).get('email', '')
            status = event_data.get('status', 'confirmed')
            
            # Extract attendees
            attendees = []
            if 'attendees' in event_data:
                attendees = [
                    attendee.get('email', '') 
                    for attendee in event_data['attendees']
                ]
            
            # Check for meeting link
            meeting_link = ""
            if 'hangoutLink' in event_data:
                meeting_link = event_data['hangoutLink']
            elif 'location' in event_data and 'meet.google.com' in event_data['location']:
                meeting_link = event_data['location']
            
            # Check if recurring
            is_recurring = 'recurrence' in event_data
            
            return CalendarEvent(
                event_id=event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendees=attendees,
                creator=creator,
                is_recurring=is_recurring,
                status=status,
                meeting_link=meeting_link
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse calendar event: {e}")
            return None
    
    async def create_event(self,
                          title: str,
                          start_time: datetime,
                          duration: timedelta,
                          description: str = "",
                          location: str = "",
                          attendees: List[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """Create a new calendar event"""
        
        if not self.service:
            return {"success": False, "error": "Calendar service not available"}
        
        context = kwargs.get('_context', {})
        
        try:
            # Calculate end time
            end_time = start_time + duration
            
            # Check for conflicts
            conflicts = await self._check_conflicts(start_time, end_time)
            if conflicts:
                self.logger.warning(f"Scheduling conflict detected: {len(conflicts)} overlapping events")
                # Could suggest alternative times here
            
            # Build event data
            event_data = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if location:
                event_data['location'] = location
            
            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            # Parse created event
            calendar_event = self._parse_calendar_event(created_event)
            if calendar_event:
                self.event_cache[calendar_event.event_id] = calendar_event
            
            # Learn from this scheduling
            await self._learn_from_scheduling(calendar_event, context)
            
            self.logger.info(f"Created calendar event: {title}")
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'title': title,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'conflicts_detected': len(conflicts),
                'event_url': created_event.get('htmlLink', '')
            }
            
        except HttpError as error:
            self.logger.error(f"Failed to create calendar event: {error}")
            return {
                'success': False,
                'error': str(error),
                'title': title
            }
    
    async def _check_conflicts(self, start_time: datetime, end_time: datetime) -> List[CalendarEvent]:
        """Check for scheduling conflicts"""
        
        # Get events in the time range
        events = await self.get_events_in_range(start_time, end_time)
        
        conflicts = []
        for event in events:
            if event.start_time < end_time and event.end_time > start_time:
                conflicts.append(event)
        
        return conflicts
    
    async def get_events_in_range(self, start_time: datetime, end_time: datetime) -> List[CalendarEvent]:
        """Get events in a specific time range"""
        
        if not self.service:
            return []
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            calendar_events = []
            for event in events:
                calendar_event = self._parse_calendar_event(event)
                if calendar_event:
                    calendar_events.append(calendar_event)
            
            return calendar_events
            
        except HttpError as error:
            self.logger.error(f"Failed to get events in range: {error}")
            return []
    
    async def find_free_time(self,
                            duration: timedelta,
                            days_ahead: int = 7,
                            preferred_times: List[str] = None) -> List[Tuple[datetime, datetime]]:
        """Find free time slots for scheduling"""
        
        # Get existing events
        events = await self.get_upcoming_events(days_ahead)
        
        # Define working hours (can be made configurable)
        work_start = 9  # 9 AM
        work_end = 17   # 5 PM
        
        # Use preferred times if provided, otherwise use learned patterns
        if not preferred_times:
            preferred_times = self.preferred_times or ['10:00', '14:00', '15:00']
        
        free_slots = []
        
        # Check each day
        for day_offset in range(days_ahead):
            check_date = datetime.now().date() + timedelta(days=day_offset)
            
            # Skip weekends (can be made configurable)
            if check_date.weekday() >= 5:
                continue
            
            # Get events for this day
            day_start = datetime.combine(check_date, datetime.min.time().replace(hour=work_start))
            day_end = datetime.combine(check_date, datetime.min.time().replace(hour=work_end))
            
            day_events = [e for e in events if e.start_time.date() == check_date]
            day_events.sort(key=lambda x: x.start_time)
            
            # Find gaps
            current_time = day_start
            
            for event in day_events:
                # Check gap before this event
                if event.start_time > current_time + duration:
                    gap_start = current_time
                    gap_end = event.start_time
                    
                    # Check if gap is long enough
                    if gap_end - gap_start >= duration:
                        free_slots.append((gap_start, gap_end))
                
                current_time = max(current_time, event.end_time)
            
            # Check gap after last event
            if day_end > current_time + duration:
                free_slots.append((current_time, day_end))
        
        # Sort by preferred times
        def time_preference_score(slot):
            start_time = slot[0]
            hour_str = start_time.strftime('%H:%M')
            
            if hour_str in preferred_times:
                return 0  # Highest preference
            
            # Score based on how close to preferred times
            hour = start_time.hour
            preferred_hours = [int(t.split(':')[0]) for t in preferred_times]
            
            if preferred_hours:
                min_diff = min(abs(hour - ph) for ph in preferred_hours)
                return min_diff
            
            return 10  # Default score
        
        free_slots.sort(key=time_preference_score)
        
        return free_slots[:10]  # Return top 10 options
    
    async def _learn_from_scheduling(self, event: CalendarEvent, context: Dict[str, Any]):
        """Learn patterns from scheduling behavior"""
        
        if not event:
            return
        
        # Learn preferred times
        hour_str = event.start_time.strftime('%H:%M')
        if hour_str not in self.preferred_times:
            self.preferred_times.append(hour_str)
        
        # Keep only recent preferences
        if len(self.preferred_times) > 20:
            self.preferred_times = self.preferred_times[-20:]
        
        # Learn meeting duration patterns
        duration_minutes = int(event.duration.total_seconds() / 60)
        
        if 'meeting_durations' not in self.scheduling_patterns:
            self.scheduling_patterns['meeting_durations'] = []
        
        self.scheduling_patterns['meeting_durations'].append(duration_minutes)
        
        # Learn attendee patterns
        attendee_count = len(event.attendees)
        if 'attendee_counts' not in self.scheduling_patterns:
            self.scheduling_patterns['attendee_counts'] = []
        
        self.scheduling_patterns['attendee_counts'].append(attendee_count)
        
        # Learn day-of-week preferences
        day_name = event.start_time.strftime('%A')
        if 'preferred_days' not in self.scheduling_patterns:
            self.scheduling_patterns['preferred_days'] = {}
        
        if day_name not in self.scheduling_patterns['preferred_days']:
            self.scheduling_patterns['preferred_days'][day_name] = 0
        
        self.scheduling_patterns['preferred_days'][day_name] += 1
        
        self.logger.info(f"Updated scheduling patterns from event: {event.title}")
    
    async def get_todays_schedule(self) -> Dict[str, Any]:
        """Get today's schedule summary"""
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        events = await self.get_events_in_range(today_start, today_end)
        
        if not events:
            return {
                'summary': 'No events scheduled for today',
                'event_count': 0,
                'total_meeting_time': 0,
                'next_event': None
            }
        
        # Sort by start time
        events.sort(key=lambda x: x.start_time)
        
        # Calculate total meeting time
        total_minutes = sum(int(event.duration.total_seconds() / 60) for event in events)
        
        # Find next event
        now = datetime.now()
        next_event = None
        for event in events:
            if event.start_time > now:
                next_event = event
                break
        
        # Create summary
        event_descriptions = []
        for event in events:
            time_str = event.start_time.strftime('%H:%M')
            duration_str = f"{int(event.duration.total_seconds() / 60)}min"
            event_descriptions.append(f"{time_str}: {event.title} ({duration_str})")
        
        summary = f"Today's schedule: {len(events)} events, {total_minutes} minutes total"
        
        return {
            'summary': summary,
            'event_count': len(events),
            'total_meeting_time': total_minutes,
            'events': [event.to_dict() for event in events],
            'event_descriptions': event_descriptions,
            'next_event': next_event.to_dict() if next_event else None
        }
    
    async def get_tomorrows_schedule(self) -> Dict[str, Any]:
        """Get tomorrow's schedule summary"""
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
        
        events = await self.get_events_in_range(tomorrow_start, tomorrow_end)
        
        if not events:
            return {
                'summary': 'No events scheduled for tomorrow',
                'event_count': 0,
                'total_meeting_time': 0,
                'first_event': None
            }
        
        # Sort by start time
        events.sort(key=lambda x: x.start_time)
        
        total_minutes = sum(int(event.duration.total_seconds() / 60) for event in events)
        
        summary = f"Tomorrow's schedule: {len(events)} events, {total_minutes} minutes total"
        
        return {
            'summary': summary,
            'event_count': len(events),
            'total_meeting_time': total_minutes,
            'events': [event.to_dict() for event in events],
            'first_event': events[0].to_dict() if events else None
        }
    
    async def suggest_meeting_time(self,
                                  duration_minutes: int,
                                  attendees: List[str] = None,
                                  days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Suggest optimal meeting times"""
        
        duration = timedelta(minutes=duration_minutes)
        free_slots = await self.find_free_time(duration, days_ahead)
        
        suggestions = []
        for start_time, end_time in free_slots[:5]:  # Top 5 suggestions
            # Calculate preference score
            hour = start_time.hour
            day_name = start_time.strftime('%A')
            
            # Base score
            score = 50
            
            # Preferred time bonus
            if f"{hour:02d}:00" in self.preferred_times:
                score += 30
            
            # Preferred day bonus
            day_prefs = self.scheduling_patterns.get('preferred_days', {})
            if day_name in day_prefs:
                day_score = day_prefs[day_name]
                score += min(20, day_score * 2)
            
            # Avoid very early or very late
            if hour < 8 or hour > 18:
                score -= 20
            
            # Prefer certain times
            if hour in [10, 14, 15]:  # 10 AM, 2 PM, 3 PM
                score += 10
            
            suggestions.append({
                'start_time': start_time.isoformat(),
                'end_time': (start_time + duration).isoformat(),
                'day': day_name,
                'time_str': start_time.strftime('%A, %B %d at %I:%M %p'),
                'preference_score': score,
                'available_duration': int((end_time - start_time).total_seconds() / 60)
            })
        
        # Sort by preference score
        suggestions.sort(key=lambda x: x['preference_score'], reverse=True)
        
        return suggestions
    
    def get_scheduling_insights(self) -> Dict[str, Any]:
        """Get insights about scheduling patterns"""
        
        insights = {
            'preferred_times': self.preferred_times[-10:] if self.preferred_times else [],
            'total_events_processed': len(self.event_cache),
            'scheduling_patterns': self.scheduling_patterns.copy()
        }
        
        # Calculate average meeting duration
        if 'meeting_durations' in self.scheduling_patterns:
            durations = self.scheduling_patterns['meeting_durations']
            if durations:
                insights['average_meeting_duration'] = sum(durations) / len(durations)
        
        # Most common day
        if 'preferred_days' in self.scheduling_patterns:
            day_prefs = self.scheduling_patterns['preferred_days']
            if day_prefs:
                most_common_day = max(day_prefs.items(), key=lambda x: x[1])
                insights['most_common_day'] = most_common_day[0]
        
        return insights
    
    async def update_event(self,
                          event_id: str,
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event"""
        
        if not self.service:
            return {"success": False, "error": "Calendar service not available"}
        
        try:
            # Get existing event
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Apply updates
            for key, value in updates.items():
                if key == 'title':
                    existing_event['summary'] = value
                elif key == 'description':
                    existing_event['description'] = value
                elif key == 'start_time':
                    existing_event['start'] = {
                        'dateTime': value.isoformat(),
                        'timeZone': 'UTC'
                    }
                elif key == 'end_time':
                    existing_event['end'] = {
                        'dateTime': value.isoformat(),
                        'timeZone': 'UTC'
                    }
                elif key == 'location':
                    existing_event['location'] = value
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event
            ).execute()
            
            # Update cache
            calendar_event = self._parse_calendar_event(updated_event)
            if calendar_event:
                self.event_cache[event_id] = calendar_event
            
            self.logger.info(f"Updated calendar event: {event_id}")
            
            return {
                'success': True,
                'event_id': event_id,
                'updates_applied': list(updates.keys())
            }
            
        except HttpError as error:
            self.logger.error(f"Failed to update calendar event: {error}")
            return {
                'success': False,
                'error': str(error),
                'event_id': event_id
            }
    
    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        
        if not self.service:
            return {"success": False, "error": "Calendar service not available"}
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Remove from cache
            if event_id in self.event_cache:
                del self.event_cache[event_id]
            
            self.logger.info(f"Deleted calendar event: {event_id}")
            
            return {
                'success': True,
                'event_id': event_id,
                'message': 'Event deleted successfully'
            }
            
        except HttpError as error:
            self.logger.error(f"Failed to delete calendar event: {error}")
            return {
                'success': False,
                'error': str(error),
                'event_id': event_id
            }