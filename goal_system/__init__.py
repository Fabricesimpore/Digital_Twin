"""
Goal-Aware Agent System

This module transforms the digital twin from a task executor into a strategic
project management partner that actively helps achieve long-term goals.

Components:
- goal_manager: Core goal definition, decomposition, and tracking
- milestone_tracker: Progress monitoring and deadline management  
- strategic_planner: Adaptive project management and timeline optimization
- goal_reasoner: Goal-aware decision making and priority management
- progress_analyzer: Observer integration for real progress measurement

The Goal-Aware Agent provides:
- Intelligent goal decomposition into actionable milestones
- Adaptive timeline management based on actual work patterns
- Progress tracking using observer data and user feedback
- Strategic guidance and priority recommendations
- Context-aware goal execution integrated with daily workflow
"""

from .goal_manager import GoalManager, Goal, Milestone, GoalStatus
from .strategic_planner import StrategicPlanner, ProjectPlan, TimelineAdaptation
from .goal_reasoner import GoalAwareReasoner, GoalContext

__all__ = [
    'GoalManager', 'Goal', 'Milestone', 'GoalStatus',
    'StrategicPlanner', 'ProjectPlan', 'TimelineAdaptation', 
    'GoalAwareReasoner', 'GoalContext'
]