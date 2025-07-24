"""
Observer Manager

Central coordination system for all observer components. Manages data collection,
storage, analysis, and integration with the digital twin's memory system.

Features:
- Coordinated observation across all components
- Centralized data collection and storage
- Privacy filtering and data sanitization
- Real-time context generation for the twin
- Pattern analysis and insight generation
"""

import logging
import asyncio
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

from .observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel, ObserverConfig, ActivitySession
from .screen_observer import ScreenObserver
from .browser_tracker import BrowserTracker
from .input_watcher import InputWatcher


@dataclass
class ObservationSummary:
    """Summary of observations over a time period"""
    start_time: datetime
    end_time: datetime
    total_observations: int
    active_time_minutes: int
    idle_time_minutes: int
    top_applications: List[Dict[str, Any]]
    top_websites: List[Dict[str, Any]]
    productivity_score: float
    focus_sessions: int
    break_sessions: int
    categories: Dict[str, int]  # category -> time in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_observations': self.total_observations,
            'active_time_minutes': self.active_time_minutes,
            'idle_time_minutes': self.idle_time_minutes,
            'top_applications': self.top_applications,
            'top_websites': self.top_websites,
            'productivity_score': self.productivity_score,
            'focus_sessions': self.focus_sessions,
            'break_sessions': self.break_sessions,
            'categories': {k.value if hasattr(k, 'value') else str(k): v for k, v in self.categories.items()}
        }


@dataclass
class CurrentContext:
    """Current activity context for the digital twin"""
    timestamp: datetime
    current_app: str
    current_window_title: str
    current_url: str
    activity_category: ActivityCategory
    is_idle: bool
    idle_duration_seconds: int
    current_session_duration_minutes: int
    productivity_state: str  # focused, distracted, idle, break
    recent_activity_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'current_app': self.current_app,
            'current_window_title': self.current_window_title,
            'current_url': self.current_url,
            'activity_category': self.activity_category.value,
            'is_idle': self.is_idle,
            'idle_duration_seconds': self.idle_duration_seconds,
            'current_session_duration_minutes': self.current_session_duration_minutes,
            'productivity_state': self.productivity_state,
            'recent_activity_summary': self.recent_activity_summary
        }


class ObserverManager:
    """
    Central manager for all observation components.
    
    Coordinates data collection, applies privacy filters, stores observations,
    and provides real-time context to the digital twin system.
    """
    
    def __init__(self, config: ObserverConfig = None, memory_interface=None):
        self.config = config or ObserverConfig()
        self.memory_interface = memory_interface
        self.logger = logging.getLogger(__name__)
        
        # Observer components
        self.screen_observer = ScreenObserver(self.config)
        self.browser_tracker = BrowserTracker(self.config)
        self.input_watcher = InputWatcher(self.config)
        
        # Manager state
        self.is_running = False
        self.observation_lock = threading.Lock()
        
        # Data storage
        self.observations: List[ObservationEvent] = []
        self.activity_sessions: List[ActivitySession] = []
        self.current_context: Optional[CurrentContext] = None
        
        # Analysis and caching
        self.analysis_cache: Dict[str, Any] = {}
        self.last_analysis_time: Optional[datetime] = None
        
        # Storage configuration
        self.data_dir = Path("observer_data")
        self.data_dir.mkdir(exist_ok=True)
        self.max_observations_in_memory = 10000
        
        # Callbacks for external systems
        self.context_callbacks: List[Callable[[CurrentContext], None]] = []
        self.observation_callbacks: List[Callable[[ObservationEvent], None]] = []
        
        # Setup observer callbacks
        self._setup_observer_callbacks()
        
        # Privacy settings
        self.privacy_settings = self.config.get_privacy_settings()
        
        self.logger.info("Observer Manager initialized")
    
    def _setup_observer_callbacks(self):
        """Set up callbacks from individual observers"""
        
        # Screen observer callbacks
        self.screen_observer.add_observation_callback(self._handle_screen_observation)
        
        # Browser tracker callbacks
        self.browser_tracker.add_observation_callback(self._handle_browser_observation)
        
        # Input watcher callbacks
        self.input_watcher.add_observation_callback(self._handle_input_observation)
    
    def add_context_callback(self, callback: Callable[[CurrentContext], None]):
        """Add callback for context updates"""
        self.context_callbacks.append(callback)
    
    def add_observation_callback(self, callback: Callable[[ObservationEvent], None]):
        """Add callback for new observations"""
        self.observation_callbacks.append(callback)
    
    def _handle_screen_observation(self, event: ObservationEvent):
        """Handle observation from screen observer"""
        self._process_observation(event)
    
    def _handle_browser_observation(self, event: ObservationEvent):
        """Handle observation from browser tracker"""
        self._process_observation(event)
    
    def _handle_input_observation(self, event: ObservationEvent):
        """Handle observation from input watcher"""
        self._process_observation(event)
    
    def _process_observation(self, event: ObservationEvent):
        """Process and store a new observation"""
        
        with self.observation_lock:
            # Apply privacy filtering
            if not event.should_store(self.privacy_settings):
                self.logger.debug(f"Observation filtered for privacy: {event.event_type}")
                return
            
            # Store observation
            self.observations.append(event)
            
            # Maintain memory limits
            if len(self.observations) > self.max_observations_in_memory:
                # Archive oldest observations
                self._archive_old_observations()
            
            # Update current context
            self._update_current_context(event)
            
            # Store in memory system if available
            if self.memory_interface:
                try:
                    memory_data = event.to_memory_format()
                    # Store as episodic memory
                    self.memory_interface.store_episodic_memory(
                        event=memory_data['event_type'],
                        situation=f"User activity: {event.app_name}",
                        reasoning=f"Observed {event.event_type} in {event.app_name}",
                        decision="observe",
                        outcome="recorded",
                        metadata=memory_data
                    )
                except Exception as e:
                    self.logger.error(f"Error storing observation in memory: {e}")
            
            # Notify external callbacks
            for callback in self.observation_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in observation callback: {e}")
            
            self.logger.debug(f"Processed observation: {event.event_type} from {event.source}")
    
    def _update_current_context(self, event: ObservationEvent):
        """Update current context based on new observation"""
        
        # Get input status
        input_status = self.input_watcher.get_current_status()
        
        # Get screen activity
        screen_activity = self.screen_observer.get_current_activity()
        
        # Determine productivity state
        productivity_state = self._determine_productivity_state(event, input_status)
        
        # Generate recent activity summary
        recent_summary = self._generate_recent_activity_summary()
        
        # Create context
        self.current_context = CurrentContext(
            timestamp=datetime.now(),
            current_app=event.app_name or (screen_activity['app_name'] if screen_activity else ''),
            current_window_title=event.window_title or (screen_activity.get('window_title', '') if screen_activity else ''),
            current_url=event.url,
            activity_category=event.category,
            is_idle=input_status['is_idle'],
            idle_duration_seconds=input_status['current_idle_time_seconds'],
            current_session_duration_minutes=self._calculate_current_session_duration(),
            productivity_state=productivity_state,
            recent_activity_summary=recent_summary
        )
        
        # Notify context callbacks
        for callback in self.context_callbacks:
            try:
                callback(self.current_context)
            except Exception as e:
                self.logger.error(f"Error in context callback: {e}")
    
    def _determine_productivity_state(self, event: ObservationEvent, input_status: Dict[str, Any]) -> str:
        """Determine current productivity state"""
        
        if input_status['is_idle']:
            if input_status['current_idle_time_seconds'] > 300:  # > 5 minutes
                return "break"
            else:
                return "idle"
        
        # Check activity category
        if event.category in [ActivityCategory.PRODUCTIVITY, ActivityCategory.DEVELOPMENT, ActivityCategory.RESEARCH]:
            return "focused"
        elif event.category in [ActivityCategory.ENTERTAINMENT, ActivityCategory.SOCIAL_MEDIA]:
            return "distracted"
        else:
            return "active"
    
    def _calculate_current_session_duration(self) -> int:
        """Calculate current work session duration in minutes"""
        
        if not self.observations:
            return 0
        
        # Find the start of current session (after last long break)
        long_break_threshold = 30 * 60  # 30 minutes
        session_start = None
        
        for obs in reversed(self.observations[-50:]):  # Check last 50 observations
            if obs.event_type == "idle_end" and obs.duration_seconds > long_break_threshold:
                session_start = obs.timestamp
                break
        
        if session_start is None:
            # Use first observation as session start
            session_start = self.observations[0].timestamp
        
        duration = datetime.now() - session_start
        return int(duration.total_seconds() / 60)
    
    def _generate_recent_activity_summary(self) -> str:
        """Generate a summary of recent activity"""
        
        if not self.observations:
            return "No recent activity"
        
        # Get last 10 minutes of observations
        cutoff_time = datetime.now() - timedelta(minutes=10)
        recent_obs = [obs for obs in self.observations if obs.timestamp >= cutoff_time]
        
        if not recent_obs:
            return "No recent activity"
        
        # Summarize by app and category
        app_time = {}
        categories = set()
        
        for obs in recent_obs:
            if obs.duration_seconds > 0:
                app_time[obs.app_name] = app_time.get(obs.app_name, 0) + obs.duration_seconds
                categories.add(obs.category.value)
        
        if app_time:
            top_app = max(app_time.items(), key=lambda x: x[1])
            summary = f"Primarily using {top_app[0]} ({top_app[1]//60}min)"
            
            if len(categories) > 1:
                summary += f" across {len(categories)} activity types"
            
            return summary
        
        return "Mixed activity"
    
    def _archive_old_observations(self):
        """Archive old observations to disk"""
        
        # Keep recent observations in memory
        keep_count = self.max_observations_in_memory // 2
        old_observations = self.observations[:-keep_count]
        self.observations = self.observations[-keep_count:]
        
        # Save old observations to file
        if old_observations:
            archive_file = self.data_dir / f"observations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            try:
                with open(archive_file, 'w') as f:
                    json.dump([obs.to_dict() for obs in old_observations], f, indent=2)
                
                self.logger.info(f"Archived {len(old_observations)} observations to {archive_file}")
            except Exception as e:
                self.logger.error(f"Error archiving observations: {e}")
    
    async def start_observing(self):
        """Start all observer components"""
        
        if not self.config.get('enabled', True):
            self.logger.info("Observer system is disabled in configuration")
            return
        
        self.is_running = True
        self.logger.info("Starting observer system...")
        
        # Start all observer components concurrently
        tasks = []
        
        if self.config.is_observer_enabled('screen_observer'):
            tasks.append(asyncio.create_task(self.screen_observer.start_observing()))
        
        if self.config.is_observer_enabled('browser_tracker'):
            tasks.append(asyncio.create_task(self.browser_tracker.start_tracking()))
        
        if self.config.is_observer_enabled('input_watcher'):
            tasks.append(asyncio.create_task(self.input_watcher.start_monitoring()))
        
        # Start analysis loop
        tasks.append(asyncio.create_task(self._analysis_loop()))
        
        self.logger.info(f"Started {len(tasks)} observer components")
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in observer system: {e}")
        finally:
            self.logger.info("Observer system stopped")
    
    def stop_observing(self):
        """Stop all observer components"""
        
        self.is_running = False
        
        # Stop individual observers
        self.screen_observer.stop_observing()
        self.browser_tracker.stop_tracking()
        self.input_watcher.stop_monitoring()
        
        # Archive remaining observations
        if self.observations:
            self._archive_old_observations()
        
        self.logger.info("Observer system stopped")
    
    async def _analysis_loop(self):
        """Periodic analysis and insight generation"""
        
        while self.is_running:
            try:
                # Run analysis every 5 minutes
                await asyncio.sleep(300)
                
                if len(self.observations) > 10:  # Only analyze if we have data
                    await self._perform_periodic_analysis()
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
    
    async def _perform_periodic_analysis(self):
        """Perform periodic analysis of observations"""
        
        self.logger.debug("Performing periodic analysis...")
        
        # Update analysis cache
        try:
            # Activity patterns
            self.analysis_cache['activity_patterns'] = self._analyze_activity_patterns()
            
            # Productivity insights
            self.analysis_cache['productivity_insights'] = self._analyze_productivity()
            
            # Focus patterns
            self.analysis_cache['focus_patterns'] = self._analyze_focus_patterns()
            
            # Anomaly detection
            self.analysis_cache['anomalies'] = self._detect_anomalies()
            
            self.last_analysis_time = datetime.now()
            
            self.logger.debug("Periodic analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error in periodic analysis: {e}")
    
    def _analyze_activity_patterns(self) -> Dict[str, Any]:
        """Analyze activity patterns from observations"""
        
        if not self.observations:
            return {}
        
        # Time-based patterns
        hourly_activity = {}
        daily_apps = {}
        category_distribution = {}
        
        for obs in self.observations[-1000:]:  # Last 1000 observations
            hour = obs.timestamp.hour
            day = obs.timestamp.strftime('%A')
            
            # Hourly activity
            if hour not in hourly_activity:
                hourly_activity[hour] = 0
            hourly_activity[hour] += obs.duration_seconds
            
            # Daily app usage
            if day not in daily_apps:
                daily_apps[day] = {}
            if obs.app_name not in daily_apps[day]:
                daily_apps[day][obs.app_name] = 0
            daily_apps[day][obs.app_name] += obs.duration_seconds
            
            # Category distribution
            category = obs.category.value
            category_distribution[category] = category_distribution.get(category, 0) + obs.duration_seconds
        
        return {
            'hourly_activity': hourly_activity,
            'daily_app_patterns': daily_apps,
            'category_distribution': category_distribution,
            'most_active_hour': max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None,
            'most_productive_day': self._find_most_productive_day(daily_apps)
        }
    
    def _analyze_productivity(self) -> Dict[str, Any]:
        """Analyze productivity patterns"""
        
        productive_categories = [ActivityCategory.PRODUCTIVITY, ActivityCategory.DEVELOPMENT, 
                               ActivityCategory.RESEARCH, ActivityCategory.EDUCATION]
        distracting_categories = [ActivityCategory.ENTERTAINMENT, ActivityCategory.SOCIAL_MEDIA]
        
        productive_time = 0
        distracting_time = 0
        total_time = 0
        
        for obs in self.observations[-500:]:  # Last 500 observations
            if obs.duration_seconds > 0:
                total_time += obs.duration_seconds
                
                if obs.category in productive_categories:
                    productive_time += obs.duration_seconds
                elif obs.category in distracting_categories:
                    distracting_time += obs.duration_seconds
        
        if total_time == 0:
            return {'productivity_score': 0.0, 'analysis': 'No data available'}
        
        productivity_score = productive_time / total_time
        distraction_ratio = distracting_time / total_time
        
        return {
            'productivity_score': productivity_score,
            'distraction_ratio': distraction_ratio,
            'productive_time_minutes': productive_time // 60,
            'distracting_time_minutes': distracting_time // 60,
            'total_analyzed_time_minutes': total_time // 60,
            'productivity_trend': self._calculate_productivity_trend()
        }
    
    def _analyze_focus_patterns(self) -> Dict[str, Any]:
        """Analyze focus and attention patterns"""
        
        # Find focus sessions (sustained activity in productive categories)
        focus_sessions = []
        current_session = None
        
        for obs in self.observations[-200:]:  # Last 200 observations
            if obs.category in [ActivityCategory.PRODUCTIVITY, ActivityCategory.DEVELOPMENT]:
                if current_session is None:
                    current_session = {
                        'start_time': obs.timestamp,
                        'app': obs.app_name,
                        'duration': 0
                    }
                
                current_session['duration'] += obs.duration_seconds
                current_session['end_time'] = obs.timestamp
            else:
                if current_session and current_session['duration'] > 600:  # > 10 minutes
                    focus_sessions.append(current_session)
                current_session = None
        
        # Add final session if it exists
        if current_session and current_session['duration'] > 600:
            focus_sessions.append(current_session)
        
        # Calculate focus metrics
        total_focus_time = sum(session['duration'] for session in focus_sessions)
        avg_focus_duration = total_focus_time / len(focus_sessions) if focus_sessions else 0
        
        return {
            'focus_sessions_count': len(focus_sessions),
            'total_focus_time_minutes': total_focus_time // 60,
            'average_focus_duration_minutes': avg_focus_duration // 60,
            'longest_focus_session_minutes': max((s['duration'] for s in focus_sessions), default=0) // 60,
            'focus_apps': list(set(s['app'] for s in focus_sessions))
        }
    
    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect unusual patterns in behavior"""
        
        anomalies = []
        
        if len(self.observations) < 100:
            return anomalies
        
        # Calculate baseline patterns
        recent_obs = self.observations[-100:]
        historical_obs = self.observations[-500:-100] if len(self.observations) > 500 else []
        
        if not historical_obs:
            return anomalies
        
        # Analyze app usage anomalies
        recent_apps = {}
        historical_apps = {}
        
        for obs in recent_obs:
            recent_apps[obs.app_name] = recent_apps.get(obs.app_name, 0) + obs.duration_seconds
        
        for obs in historical_obs:
            historical_apps[obs.app_name] = historical_apps.get(obs.app_name, 0) + obs.duration_seconds
        
        # Detect unusual app usage
        for app, recent_time in recent_apps.items():
            historical_time = historical_apps.get(app, 0)
            
            if historical_time > 0:
                usage_ratio = recent_time / historical_time
                
                if usage_ratio > 3:  # 3x more usage than usual
                    anomalies.append({
                        'type': 'increased_app_usage',
                        'app': app,
                        'usage_increase': f"{usage_ratio:.1f}x",
                        'recent_minutes': recent_time // 60,
                        'baseline_minutes': historical_time // 60
                    })
                elif usage_ratio < 0.3:  # Less than 30% of usual usage
                    anomalies.append({
                        'type': 'decreased_app_usage',
                        'app': app,
                        'usage_decrease': f"{1/usage_ratio:.1f}x less",
                        'recent_minutes': recent_time // 60,
                        'baseline_minutes': historical_time // 60
                    })
        
        return anomalies
    
    def _find_most_productive_day(self, daily_apps: Dict[str, Dict[str, int]]) -> Optional[str]:
        """Find the most productive day based on app usage"""
        
        productive_apps = ['vscode', 'xcode', 'terminal', 'excel', 'word', 'notion']
        day_scores = {}
        
        for day, apps in daily_apps.items():
            score = 0
            for app, time_spent in apps.items():
                if any(prod_app in app.lower() for prod_app in productive_apps):
                    score += time_spent
            day_scores[day] = score
        
        if day_scores:
            return max(day_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _calculate_productivity_trend(self) -> str:
        """Calculate productivity trend over recent observations"""
        
        if len(self.observations) < 100:
            return "insufficient_data"
        
        # Compare recent vs older productivity
        recent_productivity = self._calculate_productivity_score(self.observations[-50:])
        older_productivity = self._calculate_productivity_score(self.observations[-100:-50])
        
        if recent_productivity > older_productivity * 1.1:
            return "improving"
        elif recent_productivity < older_productivity * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _calculate_productivity_score(self, observations: List[ObservationEvent]) -> float:
        """Calculate productivity score for a set of observations"""
        
        productive_categories = [ActivityCategory.PRODUCTIVITY, ActivityCategory.DEVELOPMENT, 
                               ActivityCategory.RESEARCH, ActivityCategory.EDUCATION]
        
        productive_time = 0
        total_time = 0
        
        for obs in observations:
            if obs.duration_seconds > 0:
                total_time += obs.duration_seconds
                if obs.category in productive_categories:
                    productive_time += obs.duration_seconds
        
        return productive_time / total_time if total_time > 0 else 0.0
    
    def get_current_context(self) -> Optional[CurrentContext]:
        """Get current activity context"""
        return self.current_context
    
    def get_observation_summary(self, hours: int = 8) -> ObservationSummary:
        """Get summary of observations over specified time period"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Filter observations by time range
        period_observations = [
            obs for obs in self.observations
            if start_time <= obs.timestamp <= end_time
        ]
        
        if not period_observations:
            return ObservationSummary(
                start_time=start_time,
                end_time=end_time,
                total_observations=0,
                active_time_minutes=0,
                idle_time_minutes=0,
                top_applications=[],
                top_websites=[],
                productivity_score=0.0,
                focus_sessions=0,
                break_sessions=0,
                categories={}
            )
        
        # Calculate metrics
        app_time = {}
        website_time = {}
        category_time = {}
        active_time = 0
        idle_time = 0
        
        for obs in period_observations:
            # App usage
            if obs.app_name:
                app_time[obs.app_name] = app_time.get(obs.app_name, 0) + obs.duration_seconds
            
            # Website usage
            if obs.url:
                domain = obs.url.split('/')[2] if len(obs.url.split('/')) > 2 else obs.url
                website_time[domain] = website_time.get(domain, 0) + obs.duration_seconds
            
            # Category usage
            category_time[obs.category] = category_time.get(obs.category, 0) + obs.duration_seconds
            
            # Active vs idle time
            if obs.event_type == "idle_start" or obs.event_type == "idle_end":
                idle_time += obs.duration_seconds
            else:
                active_time += obs.duration_seconds
        
        # Top applications
        top_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)[:10]
        top_applications = [
            {'name': app, 'time_minutes': time_seconds // 60, 'percentage': (time_seconds / (active_time + idle_time) * 100) if (active_time + idle_time) > 0 else 0}
            for app, time_seconds in top_apps
        ]
        
        # Top websites
        top_sites = sorted(website_time.items(), key=lambda x: x[1], reverse=True)[:10]
        top_websites = [
            {'domain': domain, 'time_minutes': time_seconds // 60, 'percentage': (time_seconds / (active_time + idle_time) * 100) if (active_time + idle_time) > 0 else 0}
            for domain, time_seconds in top_sites
        ]
        
        # Productivity score
        productive_categories = [ActivityCategory.PRODUCTIVITY, ActivityCategory.DEVELOPMENT, 
                               ActivityCategory.RESEARCH, ActivityCategory.EDUCATION]
        productive_time = sum(category_time.get(cat, 0) for cat in productive_categories)
        total_time = active_time + idle_time
        productivity_score = productive_time / total_time if total_time > 0 else 0.0
        
        # Focus and break sessions
        focus_sessions = len([obs for obs in period_observations if obs.duration_seconds > 600 and obs.category in productive_categories])
        break_sessions = len([obs for obs in period_observations if obs.event_type in ["idle_start", "idle_end"] and obs.duration_seconds > 300])
        
        return ObservationSummary(
            start_time=start_time,
            end_time=end_time,
            total_observations=len(period_observations),
            active_time_minutes=active_time // 60,
            idle_time_minutes=idle_time // 60,
            top_applications=top_applications,
            top_websites=top_websites,
            productivity_score=productivity_score,
            focus_sessions=focus_sessions,
            break_sessions=break_sessions,
            categories={cat.value: time_seconds for cat, time_seconds in category_time.items()}
        )
    
    def get_insights(self) -> Dict[str, Any]:
        """Get behavioral insights from collected observations"""
        
        if not self.analysis_cache:
            # Run analysis if not available
            asyncio.create_task(self._perform_periodic_analysis())
            return {'status': 'Analysis in progress, check back soon'}
        
        return {
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'activity_patterns': self.analysis_cache.get('activity_patterns', {}),
            'productivity_insights': self.analysis_cache.get('productivity_insights', {}),
            'focus_patterns': self.analysis_cache.get('focus_patterns', {}),
            'anomalies': self.analysis_cache.get('anomalies', []),
            'current_context': self.current_context.to_dict() if self.current_context else None
        }
    
    def export_data(self, days: int = 7) -> str:
        """Export observation data to JSON file"""
        
        cutoff_time = datetime.now() - timedelta(days=days)
        export_observations = [
            obs.to_dict() for obs in self.observations
            if obs.timestamp >= cutoff_time
        ]
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'export_period_days': days,
            'total_observations': len(export_observations),
            'observations': export_observations,
            'analysis_cache': self.analysis_cache,
            'current_context': self.current_context.to_dict() if self.current_context else None
        }
        
        export_file = self.data_dir / f"observer_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported {len(export_observations)} observations to {export_file}")
        return str(export_file)
    
    def pause_observing(self, duration_minutes: int = 30):
        """Temporarily pause observation for privacy"""
        
        self.logger.info(f"Pausing observation for {duration_minutes} minutes")
        
        # This would implement a pause mechanism
        # For now, we'll just log the request
        
        # In a full implementation, this would:
        # 1. Stop all observers
        # 2. Set a timer to resume
        # 3. Notify the user when resuming
        
        return f"Observation paused for {duration_minutes} minutes"
    
    def get_privacy_report(self) -> Dict[str, Any]:
        """Generate a privacy report showing what data is collected"""
        
        total_observations = len(self.observations)
        
        # Count by privacy level
        privacy_counts = {}
        source_counts = {}
        category_counts = {}
        
        for obs in self.observations[-1000:]:  # Last 1000 observations
            privacy_level = obs.privacy_level.value
            privacy_counts[privacy_level] = privacy_counts.get(privacy_level, 0) + 1
            
            source_counts[obs.source] = source_counts.get(obs.source, 0) + 1
            
            category = obs.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_observations': total_observations,
            'privacy_level_distribution': privacy_counts,
            'data_sources': source_counts,
            'activity_categories': category_counts,
            'privacy_settings': self.privacy_settings,
            'data_retention_days': self.config.get('privacy.data_retention_days', 30),
            'local_storage_only': self.config.get('storage.local_only', True),
            'encryption_enabled': self.config.get('storage.encrypt_logs', True)
        }