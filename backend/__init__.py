"""
Digital Twin Backend - Phase 8: Real-Time Intelligence with Human-in-the-Loop
"""

__version__ = "0.8.0"
__author__ = "Digital Twin Project"

# Make core components easily importable
from .core.twin_decision_loop import TwinDecisionLoop
from .core.action_classifier import ActionClassifier, CriticalityLevel
from .core.hitl_engine import HITLEngine, ApprovalStatus
from .core.alert_dispatcher import AlertDispatcher
from .core.feedback_tracker import FeedbackTracker
from .core.realtime_memory_streamer import MemoryStreamer, RealTimeObserver

__all__ = [
    'TwinDecisionLoop',
    'ActionClassifier', 
    'CriticalityLevel',
    'HITLEngine',
    'ApprovalStatus', 
    'AlertDispatcher',
    'FeedbackTracker',
    'MemoryStreamer',
    'RealTimeObserver'
]