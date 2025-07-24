"""
Input Activity Watcher

Monitors keyboard and mouse activity to detect idle periods, activity patterns,
and work rhythm without capturing actual keystrokes or sensitive input data.

Features:
- Idle time detection
- Activity level monitoring
- Work pattern analysis
- Break detection
- Privacy-focused (no keystroke logging)
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import platform

from .observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel, ObserverConfig

# Platform-specific imports for input monitoring
system = platform.system()

if system == "Darwin":  # macOS
    try:
        from Quartz import CGEventSourceSecondsSinceLastEventType, kCGEventSourceStateHIDSystemState
        from Quartz import kCGAnyInputEventType
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        logging.warning("macOS Quartz not available for input monitoring")

elif system == "Windows":
    try:
        import win32api
        import win32con
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logging.warning("Windows win32api not available for input monitoring")

elif system == "Linux":
    try:
        import subprocess
        LINUX_AVAILABLE = True
    except ImportError:
        LINUX_AVAILABLE = False


@dataclass
class ActivityPeriod:
    """Represents a period of user activity or inactivity"""
    start_time: datetime
    end_time: datetime
    is_active: bool
    activity_level: str  # low, medium, high
    total_events: int = 0
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time
    
    @property
    def duration_seconds(self) -> int:
        return int(self.duration.total_seconds())


@dataclass
class WorkSession:
    """Represents a work session with breaks"""
    session_id: str
    start_time: datetime
    end_time: datetime
    active_periods: List[ActivityPeriod]
    break_periods: List[ActivityPeriod]
    
    @property
    def total_duration(self) -> timedelta:
        return self.end_time - self.start_time
    
    @property
    def active_time(self) -> timedelta:
        return sum((period.duration for period in self.active_periods), timedelta())
    
    @property
    def break_time(self) -> timedelta:
        return sum((period.duration for period in self.break_periods), timedelta())
    
    @property
    def productivity_score(self) -> float:
        """Calculate productivity score based on active vs break time"""
        total_seconds = self.total_duration.total_seconds()
        if total_seconds == 0:
            return 0.0
        
        active_seconds = self.active_time.total_seconds()
        return min(1.0, active_seconds / total_seconds)


class InputWatcher:
    """
    Privacy-focused input activity monitor.
    
    Tracks activity patterns without logging actual keystrokes or mouse clicks.
    Focuses on idle detection, activity levels, and work rhythm analysis.
    """
    
    def __init__(self, config: ObserverConfig = None):
        self.config = config or ObserverConfig()
        self.logger = logging.getLogger(__name__)
        
        # Watcher state
        self.is_running = False
        self.last_activity_time = datetime.now()
        self.current_session: Optional[WorkSession] = None
        
        # Activity tracking
        self.activity_periods: List[ActivityPeriod] = []
        self.work_sessions: List[WorkSession] = []
        self.is_currently_idle = False
        self.idle_start_time: Optional[datetime] = None
        
        # Callbacks
        self.observation_callbacks: List[Callable[[ObservationEvent], None]] = []
        
        # Configuration
        self.idle_threshold = self.config.get('observers.input_watcher.idle_threshold', 60)  # seconds
        self.track_activity_patterns = self.config.get('observers.input_watcher.track_keystroke_patterns', False)
        self.poll_interval = 1.0  # Check every second
        
        # Platform detection
        self.system = platform.system()
        self._check_platform_support()
        
        # Activity level thresholds (events per minute)
        self.activity_thresholds = {
            'low': 5,
            'medium': 20,
            'high': 50
        }
    
    def _check_platform_support(self) -> bool:
        """Check if the current platform supports input monitoring"""
        
        if self.system == "Darwin" and not MACOS_AVAILABLE:
            self.logger.error("macOS input monitoring requires Quartz")
            return False
        elif self.system == "Windows" and not WINDOWS_AVAILABLE:
            self.logger.error("Windows input monitoring requires win32api")
            return False
        elif self.system == "Linux" and not LINUX_AVAILABLE:
            self.logger.error("Linux input monitoring requires subprocess support")
            return False
        
        return True
    
    def add_observation_callback(self, callback: Callable[[ObservationEvent], None]):
        """Add callback for input activity observations"""
        self.observation_callbacks.append(callback)
    
    def _get_idle_time_macos(self) -> float:
        """Get idle time on macOS"""
        
        if not MACOS_AVAILABLE:
            return 0.0
        
        try:
            # Get seconds since last input event
            idle_time = CGEventSourceSecondsSinceLastEventType(
                kCGEventSourceStateHIDSystemState,
                kCGAnyInputEventType
            )
            return idle_time
        except Exception as e:
            self.logger.error(f"Error getting idle time on macOS: {e}")
            return 0.0
    
    def _get_idle_time_windows(self) -> float:
        """Get idle time on Windows"""
        
        if not WINDOWS_AVAILABLE:
            return 0.0
        
        try:
            # Get last input info
            last_input_info = win32api.GetLastInputInfo()
            current_time = win32api.GetTickCount()
            
            # Calculate idle time in seconds
            idle_time = (current_time - last_input_info) / 1000.0
            return idle_time
        except Exception as e:
            self.logger.error(f"Error getting idle time on Windows: {e}")
            return 0.0
    
    def _get_idle_time_linux(self) -> float:
        """Get idle time on Linux"""
        
        try:
            # Use xprintidle if available
            result = subprocess.run(['xprintidle'], capture_output=True, text=True)
            if result.returncode == 0:
                # xprintidle returns milliseconds
                idle_ms = int(result.stdout.strip())
                return idle_ms / 1000.0
        except:
            pass
        
        try:
            # Fallback: use xssstate from xscreensaver
            result = subprocess.run(['xssstate', '-i'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse idle time from output
                import re
                match = re.search(r'idle for (\d+) seconds', result.stdout)
                if match:
                    return float(match.group(1))
        except:
            pass
        
        self.logger.warning("No idle time detection method available on Linux")
        return 0.0
    
    def get_idle_time(self) -> float:
        """Get system idle time in seconds"""
        
        if self.system == "Darwin":
            return self._get_idle_time_macos()
        elif self.system == "Windows":
            return self._get_idle_time_windows()
        elif self.system == "Linux":
            return self._get_idle_time_linux()
        else:
            return 0.0
    
    def _determine_activity_level(self, events_per_minute: int) -> str:
        """Determine activity level based on event frequency"""
        
        if events_per_minute >= self.activity_thresholds['high']:
            return 'high'
        elif events_per_minute >= self.activity_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _create_observation_event(self, 
                                event_type: str, 
                                duration: int = 0,
                                metadata: Dict[str, Any] = None) -> ObservationEvent:
        """Create an observation event for input activity"""
        
        return ObservationEvent(
            timestamp=datetime.now(),
            source="input_watcher",
            event_type=event_type,
            app_name="System",
            duration_seconds=duration,
            category=ActivityCategory.SYSTEM,
            metadata={
                'platform': self.system,
                'idle_threshold': self.idle_threshold,
                **(metadata or {})
            }
        )
    
    def _handle_idle_start(self, idle_time: float):
        """Handle the start of an idle period"""
        
        if self.is_currently_idle:
            return
        
        self.is_currently_idle = True
        self.idle_start_time = datetime.now() - timedelta(seconds=idle_time)
        
        # Create idle start event
        event = self._create_observation_event(
            "idle_start",
            metadata={
                'idle_time_seconds': idle_time,
                'last_activity_time': self.last_activity_time.isoformat()
            }
        )
        
        # Notify callbacks
        for callback in self.observation_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in input observation callback: {e}")
        
        self.logger.debug(f"Idle period started (idle for {idle_time:.1f}s)")
    
    def _handle_idle_end(self, idle_duration: int):
        """Handle the end of an idle period"""
        
        if not self.is_currently_idle:
            return
        
        self.is_currently_idle = False
        self.last_activity_time = datetime.now()
        
        # Create idle end event
        event = self._create_observation_event(
            "idle_end",
            duration=idle_duration,
            metadata={
                'idle_duration_seconds': idle_duration,
                'activity_resumed_time': self.last_activity_time.isoformat()
            }
        )
        
        # Create activity period record
        if self.idle_start_time:
            idle_period = ActivityPeriod(
                start_time=self.idle_start_time,
                end_time=datetime.now(),
                is_active=False,
                activity_level='idle'
            )
            self.activity_periods.append(idle_period)
        
        # Notify callbacks
        for callback in self.observation_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in input observation callback: {e}")
        
        self.logger.debug(f"Idle period ended (was idle for {idle_duration}s)")
        self.idle_start_time = None
    
    def _analyze_work_patterns(self):
        """Analyze work patterns from activity periods"""
        
        if len(self.activity_periods) < 2:
            return
        
        # Group periods into work sessions
        # A work session ends after a long break (> 30 minutes idle)
        long_break_threshold = 30 * 60  # 30 minutes
        
        current_session_periods = []
        session_start_time = None
        
        for period in self.activity_periods:
            if session_start_time is None:
                session_start_time = period.start_time
            
            if not period.is_active and period.duration_seconds > long_break_threshold:
                # End current session
                if current_session_periods:
                    session = self._create_work_session(
                        session_start_time,
                        period.start_time,
                        current_session_periods
                    )
                    self.work_sessions.append(session)
                
                # Start new session
                current_session_periods = []
                session_start_time = None
            else:
                current_session_periods.append(period)
        
        # Handle ongoing session
        if current_session_periods and session_start_time:
            session = self._create_work_session(
                session_start_time,
                datetime.now(),
                current_session_periods
            )
            self.current_session = session
    
    def _create_work_session(self, 
                           start_time: datetime, 
                           end_time: datetime,
                           periods: List[ActivityPeriod]) -> WorkSession:
        """Create a work session from activity periods"""
        
        session_id = f"session_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        active_periods = [p for p in periods if p.is_active]
        break_periods = [p for p in periods if not p.is_active]
        
        return WorkSession(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            active_periods=active_periods,
            break_periods=break_periods
        )
    
    async def start_monitoring(self):
        """Start input activity monitoring"""
        
        if not self.config.is_observer_enabled('input_watcher'):
            self.logger.info("Input watcher is disabled in configuration")
            return
        
        if not self._check_platform_support():
            self.logger.error("Platform not supported for input monitoring")
            return
        
        self.is_running = True
        self.last_activity_time = datetime.now()
        
        self.logger.info(f"Starting input activity monitoring on {self.system}")
        self.logger.info(f"Idle threshold: {self.idle_threshold} seconds")
        
        while self.is_running:
            try:
                # Get current idle time
                current_idle_time = self.get_idle_time()
                
                if current_idle_time >= self.idle_threshold:
                    # User is idle
                    if not self.is_currently_idle:
                        self._handle_idle_start(current_idle_time)
                else:
                    # User is active
                    if self.is_currently_idle:
                        # Calculate idle duration
                        if self.idle_start_time:
                            idle_duration = int((datetime.now() - self.idle_start_time).total_seconds())
                            self._handle_idle_end(idle_duration)
                    
                    self.last_activity_time = datetime.now()
                
                # Analyze work patterns periodically
                if len(self.activity_periods) > 0 and len(self.activity_periods) % 10 == 0:
                    self._analyze_work_patterns()
                
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error in input monitoring loop: {e}")
                await asyncio.sleep(self.poll_interval)
        
        self.logger.info("Input activity monitoring stopped")
    
    def stop_monitoring(self):
        """Stop input activity monitoring"""
        self.is_running = False
        
        # Handle final idle period if needed
        if self.is_currently_idle and self.idle_start_time:
            idle_duration = int((datetime.now() - self.idle_start_time).total_seconds())
            self._handle_idle_end(idle_duration)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current input activity status"""
        
        current_idle_time = self.get_idle_time()
        
        return {
            'is_idle': self.is_currently_idle,
            'current_idle_time_seconds': current_idle_time,
            'last_activity_time': self.last_activity_time.isoformat(),
            'idle_threshold_seconds': self.idle_threshold,
            'total_activity_periods': len(self.activity_periods),
            'total_work_sessions': len(self.work_sessions)
        }
    
    def get_activity_summary(self, hours: int = 8) -> Dict[str, Any]:
        """Get summary of activity patterns"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_periods = [
            period for period in self.activity_periods
            if period.start_time >= cutoff_time
        ]
        
        if not recent_periods:
            return {
                'summary': f'No activity data recorded in the last {hours} hours',
                'total_periods': 0,
                'active_time_minutes': 0,
                'idle_time_minutes': 0
            }
        
        # Calculate active vs idle time
        active_periods = [p for p in recent_periods if p.is_active]
        idle_periods = [p for p in recent_periods if not p.is_active]
        
        active_time = sum(p.duration_seconds for p in active_periods)
        idle_time = sum(p.duration_seconds for p in idle_periods)
        total_time = active_time + idle_time
        
        # Calculate break patterns
        short_breaks = len([p for p in idle_periods if p.duration_seconds < 300])  # < 5 min
        medium_breaks = len([p for p in idle_periods if 300 <= p.duration_seconds < 900])  # 5-15 min
        long_breaks = len([p for p in idle_periods if p.duration_seconds >= 900])  # > 15 min
        
        # Current session info
        current_session_info = None
        if self.current_session:
            current_session_info = {
                'session_id': self.current_session.session_id,
                'duration_minutes': int(self.current_session.total_duration.total_seconds() / 60),
                'active_time_minutes': int(self.current_session.active_time.total_seconds() / 60),
                'productivity_score': self.current_session.productivity_score
            }
        
        return {
            'summary': f'{len(recent_periods)} activity periods in {hours} hours',
            'total_periods': len(recent_periods),
            'active_time_minutes': active_time // 60,
            'idle_time_minutes': idle_time // 60,
            'activity_ratio': (active_time / total_time * 100) if total_time > 0 else 0,
            'break_patterns': {
                'short_breaks': short_breaks,
                'medium_breaks': medium_breaks,
                'long_breaks': long_breaks,
                'average_break_minutes': (idle_time // len(idle_periods) // 60) if idle_periods else 0
            },
            'current_session': current_session_info,
            'work_sessions_today': len([s for s in self.work_sessions 
                                      if s.start_time.date() == datetime.now().date()])
        }
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """Generate productivity insights from input patterns"""
        
        if not self.work_sessions and not self.current_session:
            return {'insights': 'No work session data available yet'}
        
        all_sessions = self.work_sessions + ([self.current_session] if self.current_session else [])
        
        if not all_sessions:
            return {'insights': 'No work session data available yet'}
        
        # Calculate productivity metrics
        total_sessions = len(all_sessions)
        avg_productivity = sum(session.productivity_score for session in all_sessions) / total_sessions
        
        # Session length analysis
        session_durations = [session.total_duration.total_seconds() / 3600 for session in all_sessions]  # hours
        avg_session_length = sum(session_durations) / len(session_durations)
        
        # Break pattern analysis
        all_breaks = []
        for session in all_sessions:
            all_breaks.extend(session.break_periods)
        
        if all_breaks:
            avg_break_duration = sum(b.duration_seconds for b in all_breaks) / len(all_breaks) / 60  # minutes
            break_frequency = len(all_breaks) / total_sessions
        else:
            avg_break_duration = 0
            break_frequency = 0
        
        # Generate insights
        insights = []
        
        if avg_productivity > 0.8:
            insights.append("High productivity - maintaining good focus")
        elif avg_productivity < 0.5:
            insights.append("Low productivity - consider reducing distractions")
        
        if avg_session_length > 6:
            insights.append("Very long work sessions - ensure regular breaks")
        elif avg_session_length < 2:
            insights.append("Short work sessions - try time-blocking for longer focus")
        
        if break_frequency < 0.5:
            insights.append("Few breaks taken - regular breaks improve productivity")
        elif break_frequency > 3:
            insights.append("Frequent breaks - check for potential distractions")
        
        if avg_break_duration > 30:
            insights.append("Long breaks - consider shorter, more frequent breaks")
        
        return {
            'average_productivity_score': avg_productivity,
            'average_session_hours': avg_session_length,
            'average_break_minutes': avg_break_duration,
            'breaks_per_session': break_frequency,
            'total_work_sessions': total_sessions,
            'insights': insights,
            'recommendations': self._generate_productivity_recommendations(
                avg_productivity, avg_session_length, break_frequency, avg_break_duration
            )
        }
    
    def _generate_productivity_recommendations(self, 
                                            productivity: float,
                                            session_length: float,
                                            break_frequency: float,
                                            break_duration: float) -> List[str]:
        """Generate productivity recommendations"""
        
        recommendations = []
        
        if productivity < 0.6:
            recommendations.append("Try the Pomodoro Technique: 25min work, 5min break")
        
        if session_length > 4 and break_frequency < 1:
            recommendations.append("Take more regular breaks to maintain focus")
        
        if break_duration > 20:
            recommendations.append("Keep breaks shorter to maintain momentum")
        
        if session_length < 1:
            recommendations.append("Try time-blocking for longer, uninterrupted focus periods")
        
        if break_frequency > 4:
            recommendations.append("Reduce interruptions to maintain deeper focus")
        
        return recommendations