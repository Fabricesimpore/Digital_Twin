"""
Digital Twin Observer System

This module provides passive behavior learning capabilities for the digital twin.
It observes user activities across applications, websites, and input patterns
to build a comprehensive understanding of behavior and work patterns.

Components:
- screen_observer: Tracks active windows and applications
- browser_tracker: Monitors web browsing activity
- input_watcher: Observes keyboard/mouse activity and idle time
- observer_manager: Central coordination and data collection
- observer_utils: Shared utilities and data structures

Privacy & Security:
- All observation data is stored locally by default
- User-configurable privacy filters
- Encrypted storage options
- Pause/resume controls for temporary privacy
"""

from .observer_manager import ObserverManager
from .observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel

__all__ = ['ObserverManager', 'ObservationEvent', 'ActivityCategory', 'PrivacyLevel']