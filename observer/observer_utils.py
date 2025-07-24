"""
Observer System Utilities

Shared data structures, utilities, and configuration for the observer system.
Provides privacy controls, activity categorization, and observation events.
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import hashlib
import re


class ActivityCategory(Enum):
    """Categories for observed activities"""
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    ENTERTAINMENT = "entertainment"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    SOCIAL_MEDIA = "social_media"
    SHOPPING = "shopping"
    FINANCE = "finance"
    HEALTH = "health"
    EDUCATION = "education"
    CREATIVE = "creative"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class PrivacyLevel(Enum):
    """Privacy levels for filtering observations"""
    PUBLIC = "public"        # Safe to log and analyze
    SENSITIVE = "sensitive"  # Log with filtering/anonymization
    PRIVATE = "private"      # Don't log at all
    FINANCIAL = "financial"  # Never log financial information


@dataclass
class ObservationEvent:
    """Single observation event from any observer component"""
    timestamp: datetime
    source: str                    # screen_observer, browser_tracker, etc.
    event_type: str               # app_switch, tab_change, idle_start, etc.
    
    # Core data
    app_name: str = ""            # Application name
    window_title: str = ""        # Window title
    url: str = ""                 # URL if browser
    duration_seconds: int = 0     # Duration of activity
    
    # Classification
    category: ActivityCategory = ActivityCategory.UNKNOWN
    subcategory: str = ""         # More specific classification
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    
    # Context
    idle_time: int = 0           # Seconds of idle time before this event
    active_time: int = 0         # Seconds of active time in this session
    session_id: str = ""         # Session identifier
    
    # Metadata
    confidence: float = 1.0      # Confidence in classification (0-1)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.session_id:
            self.session_id = self._generate_session_id()
        
        # Auto-classify if not already classified
        if self.category == ActivityCategory.UNKNOWN:
            self.category = self._auto_classify()
        
        # Auto-determine privacy level
        if self.privacy_level == PrivacyLevel.PUBLIC:
            self.privacy_level = self._determine_privacy_level()
    
    def _generate_session_id(self) -> str:
        """Generate a session ID based on timestamp and app"""
        data = f"{self.timestamp.isoformat()}_{self.app_name}_{self.source}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def _auto_classify(self) -> ActivityCategory:
        """Auto-classify activity based on app name, title, and URL"""
        
        # Combine text for analysis
        text = f"{self.app_name} {self.window_title} {self.url}".lower()
        
        # Development tools
        if any(term in text for term in ['vscode', 'xcode', 'intellij', 'github', 'stackoverflow', 'terminal', 'iterm']):
            return ActivityCategory.DEVELOPMENT
        
        # Communication
        if any(term in text for term in ['slack', 'teams', 'zoom', 'mail', 'gmail', 'outlook', 'whatsapp', 'telegram']):
            return ActivityCategory.COMMUNICATION
        
        # Social Media
        if any(term in text for term in ['facebook', 'twitter', 'instagram', 'linkedin', 'tiktok', 'reddit']):
            return ActivityCategory.SOCIAL_MEDIA
        
        # Entertainment
        if any(term in text for term in ['youtube', 'netflix', 'spotify', 'music', 'twitch', 'video', 'game']):
            return ActivityCategory.ENTERTAINMENT
        
        # Productivity
        if any(term in text for term in ['excel', 'word', 'powerpoint', 'sheets', 'docs', 'notion', 'trello', 'asana']):
            return ActivityCategory.PRODUCTIVITY
        
        # Research
        if any(term in text for term in ['google search', 'wikipedia', 'arxiv', 'scholar', 'research']):
            return ActivityCategory.RESEARCH
        
        # Shopping
        if any(term in text for term in ['amazon', 'ebay', 'shop', 'store', 'cart', 'checkout']):
            return ActivityCategory.SHOPPING
        
        # Finance
        if any(term in text for term in ['bank', 'trading', 'investment', 'crypto', 'wallet', 'payment']):
            return ActivityCategory.FINANCE
        
        # Education
        if any(term in text for term in ['coursera', 'udemy', 'khan', 'course', 'tutorial', 'learning']):
            return ActivityCategory.EDUCATION
        
        # Creative
        if any(term in text for term in ['photoshop', 'sketch', 'figma', 'design', 'creative', 'art']):
            return ActivityCategory.CREATIVE
        
        return ActivityCategory.UNKNOWN
    
    def _determine_privacy_level(self) -> PrivacyLevel:
        """Determine privacy level based on content"""
        
        text = f"{self.app_name} {self.window_title} {self.url}".lower()
        
        # Financial - never log
        if any(term in text for term in ['bank', 'password', 'login', 'credit', 'ssn', 'social security']):
            return PrivacyLevel.FINANCIAL
        
        # Private browsing indicators
        if 'private' in text or 'incognito' in text:
            return PrivacyLevel.PRIVATE
        
        # Sensitive but loggable with filtering
        if any(term in text for term in ['personal', 'medical', 'health', 'private']):
            return PrivacyLevel.SENSITIVE
        
        return PrivacyLevel.PUBLIC
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        
        # Convert enums to strings
        data['category'] = self.category.value
        data['privacy_level'] = self.privacy_level.value
        
        # Convert datetime to ISO string
        data['timestamp'] = self.timestamp.isoformat()
        
        return data
    
    def to_memory_format(self) -> Dict[str, Any]:
        """Convert to format suitable for memory system storage"""
        
        return {
            'event_id': f"{self.source}_{self.session_id}",
            'timestamp': self.timestamp.isoformat(),
            'event_type': 'observation',
            'source': self.source,
            'activity': {
                'app': self.app_name,
                'title': self._sanitize_for_memory(self.window_title),
                'url': self._sanitize_url_for_memory(self.url),
                'category': self.category.value,
                'subcategory': self.subcategory,
                'duration': self.duration_seconds
            },
            'context': {
                'idle_time': self.idle_time,
                'active_time': self.active_time,
                'session_id': self.session_id
            },
            'metadata': {
                'confidence': self.confidence,
                'tags': self.tags,
                'privacy_level': self.privacy_level.value,
                **self.metadata
            }
        }
    
    def _sanitize_for_memory(self, text: str) -> str:
        """Sanitize text for memory storage based on privacy level"""
        
        if self.privacy_level == PrivacyLevel.FINANCIAL:
            return "[FINANCIAL_CONTENT_FILTERED]"
        
        if self.privacy_level == PrivacyLevel.PRIVATE:
            return "[PRIVATE_CONTENT_FILTERED]"
        
        if self.privacy_level == PrivacyLevel.SENSITIVE:
            # Basic anonymization - remove potential personal info
            text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)  # SSN pattern
            text = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', '[CARD]', text)  # Credit card
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)  # Email
        
        return text
    
    def _sanitize_url_for_memory(self, url: str) -> str:
        """Sanitize URL for memory storage"""
        
        if self.privacy_level in [PrivacyLevel.FINANCIAL, PrivacyLevel.PRIVATE]:
            return "[URL_FILTERED]"
        
        if not url:
            return ""
        
        # Remove query parameters that might contain sensitive info
        if '?' in url:
            base_url, params = url.split('?', 1)
            # Keep only safe parameters
            safe_params = []
            for param in params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() not in ['token', 'password', 'key', 'auth', 'secret']:
                        safe_params.append(f"{key}=[PARAM]")
            
            if safe_params:
                return f"{base_url}?{'&'.join(safe_params)}"
            else:
                return base_url
        
        return url
    
    def should_store(self, privacy_settings: Dict[str, Any] = None) -> bool:
        """Determine if this observation should be stored based on privacy settings"""
        
        if privacy_settings is None:
            privacy_settings = {}
        
        # Never store financial information
        if self.privacy_level == PrivacyLevel.FINANCIAL:
            return False
        
        # Check if private content is allowed
        if self.privacy_level == PrivacyLevel.PRIVATE:
            return privacy_settings.get('allow_private', False)
        
        # Check category filters
        blocked_categories = privacy_settings.get('blocked_categories', [])
        if self.category.value in blocked_categories:
            return False
        
        # Check app filters
        blocked_apps = privacy_settings.get('blocked_apps', [])
        if self.app_name.lower() in [app.lower() for app in blocked_apps]:
            return False
        
        # Check URL patterns
        blocked_patterns = privacy_settings.get('blocked_url_patterns', [])
        for pattern in blocked_patterns:
            if re.search(pattern, self.url, re.IGNORECASE):
                return False
        
        return True


class ObserverConfig:
    """Configuration for the observer system"""
    
    def __init__(self, config_path: str = "observer_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        
        default_config = {
            "enabled": True,
            "observers": {
                "screen_observer": {
                    "enabled": True,
                    "poll_interval": 1.0,  # seconds
                    "min_duration": 2      # minimum seconds to record
                },
                "browser_tracker": {
                    "enabled": True,
                    "track_urls": True,
                    "track_tab_switches": True
                },
                "input_watcher": {
                    "enabled": True,
                    "idle_threshold": 60,  # seconds
                    "track_keystroke_patterns": False  # privacy-sensitive
                }
            },
            "privacy": {
                "allow_private": False,
                "blocked_categories": ["finance"],
                "blocked_apps": ["keychain access", "1password"],
                "blocked_url_patterns": [
                    r".*bank.*",
                    r".*password.*",
                    r".*login.*\.aspx"
                ],
                "anonymize_sensitive": True,
                "data_retention_days": 30
            },
            "storage": {
                "local_only": True,
                "encrypt_logs": True,
                "max_log_size_mb": 100
            },
            "analysis": {
                "enable_pattern_detection": True,
                "productivity_analysis": True,
                "anomaly_detection": True,
                "habit_tracking": True
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                return {**default_config, **loaded_config}
        except FileNotFoundError:
            # Save default config
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def is_observer_enabled(self, observer_name: str) -> bool:
        """Check if a specific observer is enabled"""
        return (self.get('enabled', True) and 
                self.get(f'observers.{observer_name}.enabled', True))
    
    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get privacy settings for filtering"""
        return self.get('privacy', {})


class ActivitySession:
    """Represents a continuous session of activity"""
    
    def __init__(self, start_event: ObservationEvent):
        self.session_id = start_event.session_id
        self.start_time = start_event.timestamp
        self.end_time = start_event.timestamp
        self.app_name = start_event.app_name
        self.category = start_event.category
        
        self.events: List[ObservationEvent] = [start_event]
        self.total_duration = 0
        self.idle_time = 0
        self.window_switches = 0
        self.productivity_score = 0.0
    
    def add_event(self, event: ObservationEvent):
        """Add an event to this session"""
        self.events.append(event)
        self.end_time = event.timestamp
        self.total_duration = int((self.end_time - self.start_time).total_seconds())
        
        # Track window switches
        if event.event_type == 'window_switch':
            self.window_switches += 1
        
        # Update idle time
        if event.event_type == 'idle_start':
            self.idle_time += event.duration_seconds
    
    @property
    def duration(self) -> timedelta:
        """Get session duration"""
        return self.end_time - self.start_time
    
    @property
    def active_duration(self) -> int:
        """Get active duration (excluding idle time)"""
        return max(0, self.total_duration - self.idle_time)
    
    def calculate_productivity_score(self) -> float:
        """Calculate a productivity score for this session"""
        
        if self.total_duration == 0:
            return 0.0
        
        score = 0.5  # Base score
        
        # Category bonus/penalty
        category_scores = {
            ActivityCategory.PRODUCTIVITY: 1.0,
            ActivityCategory.DEVELOPMENT: 1.0,
            ActivityCategory.RESEARCH: 0.8,
            ActivityCategory.COMMUNICATION: 0.7,
            ActivityCategory.EDUCATION: 0.9,
            ActivityCategory.ENTERTAINMENT: 0.2,
            ActivityCategory.SOCIAL_MEDIA: 0.1,
        }
        
        category_score = category_scores.get(self.category, 0.5)
        score = score * 0.3 + category_score * 0.7
        
        # Duration factors
        if self.total_duration > 3600:  # > 1 hour
            score *= 1.1  # Bonus for sustained focus
        elif self.total_duration < 300:  # < 5 minutes
            score *= 0.8  # Penalty for brief activities
        
        # Idle time penalty
        if self.total_duration > 0:
            active_ratio = self.active_duration / self.total_duration
            score *= (0.5 + 0.5 * active_ratio)
        
        # Window switching penalty (indicates distraction)
        if self.window_switches > 10:
            score *= 0.9
        
        self.productivity_score = max(0.0, min(1.0, score))
        return self.productivity_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'app_name': self.app_name,
            'category': self.category.value,
            'total_duration': self.total_duration,
            'active_duration': self.active_duration,
            'idle_time': self.idle_time,
            'window_switches': self.window_switches,
            'productivity_score': self.calculate_productivity_score(),
            'event_count': len(self.events)
        }