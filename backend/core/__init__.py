"""
Core backend components for Digital Twin
"""

from .action_classifier import ActionClassifier, CriticalityLevel, ActionType
from .hitl_engine import HITLEngine, ApprovalStatus, ApprovalRequest
from .alert_dispatcher import AlertDispatcher, AlertChannel
from .feedback_tracker import FeedbackTracker, FeedbackEntry
from .realtime_memory_streamer import MemoryStreamer, RealTimeObserver, MemoryUpdate
from .twin_decision_loop import TwinDecisionLoop

# Validation and utility modules
from .env_validator import EnvValidator, validate_environment
from .config_validator import ConfigValidator, validate_all_configs
from .safe_imports import (
    safe_import_twilio, 
    safe_import_plyer, 
    safe_import_numpy,
    safe_import_tabulate
)

__all__ = [
    # Core components
    'ActionClassifier', 'CriticalityLevel', 'ActionType',
    'HITLEngine', 'ApprovalStatus', 'ApprovalRequest', 
    'AlertDispatcher', 'AlertChannel',
    'FeedbackTracker', 'FeedbackEntry',
    'MemoryStreamer', 'RealTimeObserver', 'MemoryUpdate',
    'TwinDecisionLoop',
    
    # Validation utilities
    'EnvValidator', 'validate_environment',
    'ConfigValidator', 'validate_all_configs',
    'safe_import_twilio', 'safe_import_plyer', 
    'safe_import_numpy', 'safe_import_tabulate'
]