"""
Goal Management System

Core system for defining, decomposing, and tracking goals with intelligent
milestone generation and progress monitoring.

Features:
- Hierarchical goal structure with sub-goals and milestones
- Intelligent goal decomposition using AI reasoning
- Progress tracking with multiple measurement methods
- Deadline management with adaptive scheduling
- Integration with observer system for automatic progress detection
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from pathlib import Path


class GoalStatus(Enum):
    """Status of a goal or milestone"""
    DRAFT = "draft"           # Goal defined but not started
    ACTIVE = "active"         # Currently working on this goal
    PAUSED = "paused"         # Temporarily paused
    COMPLETED = "completed"   # Successfully achieved
    CANCELLED = "cancelled"   # No longer pursuing
    OVERDUE = "overdue"       # Past deadline without completion


class GoalType(Enum):
    """Type of goal for different management approaches"""
    PROJECT = "project"       # Discrete project with clear end
    HABIT = "habit"          # Ongoing behavioral change
    LEARNING = "learning"     # Skill acquisition or knowledge
    CREATIVE = "creative"     # Creative or artistic endeavor
    CAREER = "career"        # Professional development
    HEALTH = "health"        # Health and wellness
    PERSONAL = "personal"    # Personal development


class MeasurementType(Enum):
    """How progress is measured"""
    BINARY = "binary"         # Done or not done
    PERCENTAGE = "percentage"  # 0-100% completion
    QUANTITY = "quantity"     # Numeric count (pages written, hours practiced)
    MILESTONE = "milestone"   # Progress through defined milestones
    BEHAVIORAL = "behavioral" # Tracked through observer system


@dataclass
class Milestone:
    """A specific milestone within a goal"""
    id: str
    title: str
    description: str
    goal_id: str
    
    # Timeline
    target_date: datetime
    estimated_effort_hours: float
    actual_effort_hours: float = 0.0
    
    # Progress tracking
    status: GoalStatus = GoalStatus.DRAFT
    progress_percentage: float = 0.0
    measurement_type: MeasurementType = MeasurementType.BINARY
    
    # Dependencies and ordering
    depends_on: List[str] = field(default_factory=list)  # Other milestone IDs
    priority: int = 1  # 1 (highest) to 5 (lowest)
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    completion_date: Optional[datetime] = None
    
    # Context and learning
    success_criteria: List[str] = field(default_factory=list)
    obstacles_encountered: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"milestone_{uuid.uuid4().hex[:8]}"
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue"""
        return (self.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED] and 
                datetime.now() > self.target_date)
    
    @property
    def days_until_deadline(self) -> int:
        """Days until target date (negative if overdue)"""
        return (self.target_date - datetime.now()).days
    
    def mark_completed(self, completion_notes: str = ""):
        """Mark milestone as completed"""
        self.status = GoalStatus.COMPLETED
        self.completion_date = datetime.now()
        self.progress_percentage = 100.0
        self.last_updated = datetime.now()
        
        if completion_notes:
            self.lessons_learned.append(f"Completed: {completion_notes}")
    
    def update_progress(self, progress: float, notes: str = ""):
        """Update milestone progress"""
        self.progress_percentage = max(0.0, min(100.0, progress))
        self.last_updated = datetime.now()
        
        if progress >= 100.0:
            self.mark_completed(notes)
        elif notes:
            self.lessons_learned.append(f"Progress update: {notes}")
    
    def add_obstacle(self, obstacle: str):
        """Record an obstacle encountered"""
        self.obstacles_encountered.append(f"{datetime.now().isoformat()}: {obstacle}")
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'goal_id': self.goal_id,
            'target_date': self.target_date.isoformat(),
            'estimated_effort_hours': self.estimated_effort_hours,
            'actual_effort_hours': self.actual_effort_hours,
            'status': self.status.value,
            'progress_percentage': self.progress_percentage,
            'measurement_type': self.measurement_type.value,
            'depends_on': self.depends_on,
            'priority': self.priority,
            'created_date': self.created_date.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'success_criteria': self.success_criteria,
            'obstacles_encountered': self.obstacles_encountered,
            'lessons_learned': self.lessons_learned
        }


@dataclass
class Goal:
    """A high-level goal with intelligent decomposition and tracking"""
    id: str
    title: str
    description: str
    goal_type: GoalType
    
    # Timeline
    target_date: datetime
    created_date: datetime = field(default_factory=datetime.now)
    estimated_duration_weeks: float = 4.0
    
    # Progress and status
    status: GoalStatus = GoalStatus.DRAFT
    progress_percentage: float = 0.0
    measurement_type: MeasurementType = MeasurementType.MILESTONE
    
    # Goal hierarchy
    parent_goal_id: Optional[str] = None
    sub_goal_ids: List[str] = field(default_factory=list)
    milestone_ids: List[str] = field(default_factory=list)
    
    # Motivation and context
    motivation: str = ""
    success_vision: str = ""
    impact_areas: List[str] = field(default_factory=list)  # work, personal, health, etc.
    
    # Adaptive management
    priority: int = 3  # 1 (highest) to 5 (lowest)
    energy_level_required: str = "medium"  # low, medium, high
    preferred_work_times: List[str] = field(default_factory=list)  # morning, afternoon, evening
    
    # Learning and adaptation
    success_metrics: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    
    # Observer integration
    related_apps: List[str] = field(default_factory=list)  # Apps associated with this goal
    activity_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"goal_{uuid.uuid4().hex[:8]}"
    
    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        return (self.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED] and 
                datetime.now() > self.target_date)
    
    @property
    def days_until_deadline(self) -> int:
        """Days until target date (negative if overdue)"""
        return (self.target_date - datetime.now()).days
    
    @property
    def weeks_remaining(self) -> float:
        """Weeks remaining until deadline"""
        return self.days_until_deadline / 7.0
    
    def calculate_progress_from_milestones(self, milestones: List[Milestone]) -> float:
        """Calculate overall progress from milestone completion"""
        
        goal_milestones = [m for m in milestones if m.goal_id == self.id]
        
        if not goal_milestones:
            return self.progress_percentage
        
        # Weighted progress by milestone priority
        total_weight = 0
        weighted_progress = 0
        
        for milestone in goal_milestones:
            weight = 6 - milestone.priority  # Higher priority = more weight
            total_weight += weight
            weighted_progress += milestone.progress_percentage * weight
        
        return weighted_progress / total_weight if total_weight > 0 else 0.0
    
    def get_next_milestones(self, milestones: List[Milestone], limit: int = 3) -> List[Milestone]:
        """Get next milestones to work on"""
        
        goal_milestones = [m for m in milestones if m.goal_id == self.id]
        
        # Filter available milestones (not completed, dependencies met)
        available = []
        for milestone in goal_milestones:
            if milestone.status in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]:
                continue
            
            # Check if dependencies are met
            dependencies_met = True
            for dep_id in milestone.depends_on:
                dep_milestone = next((m for m in milestones if m.id == dep_id), None)
                if not dep_milestone or dep_milestone.status != GoalStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                available.append(milestone)
        
        # Sort by priority and deadline
        available.sort(key=lambda m: (m.priority, m.target_date))
        
        return available[:limit]
    
    def add_related_app(self, app_name: str):
        """Add an app that's related to working on this goal"""
        if app_name not in self.related_apps:
            self.related_apps.append(app_name)
    
    def update_from_observer_data(self, activity_data: Dict[str, Any]):
        """Update goal based on observer system data"""
        
        # Track time spent in related apps
        for app_name, time_spent in activity_data.get('app_usage', {}).items():
            if app_name in self.related_apps:
                if 'app_time_tracking' not in self.activity_patterns:
                    self.activity_patterns['app_time_tracking'] = {}
                
                self.activity_patterns['app_time_tracking'][app_name] = (
                    self.activity_patterns['app_time_tracking'].get(app_name, 0) + time_spent
                )
        
        # Update preferred work times based on when goal-related work happens
        productive_hours = activity_data.get('productive_hours', [])
        if productive_hours:
            self.activity_patterns['productive_hours'] = productive_hours
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'goal_type': self.goal_type.value,
            'target_date': self.target_date.isoformat(),
            'created_date': self.created_date.isoformat(),
            'estimated_duration_weeks': self.estimated_duration_weeks,
            'status': self.status.value,
            'progress_percentage': self.progress_percentage,
            'measurement_type': self.measurement_type.value,
            'parent_goal_id': self.parent_goal_id,
            'sub_goal_ids': self.sub_goal_ids,
            'milestone_ids': self.milestone_ids,
            'motivation': self.motivation,
            'success_vision': self.success_vision,
            'impact_areas': self.impact_areas,
            'priority': self.priority,
            'energy_level_required': self.energy_level_required,
            'preferred_work_times': self.preferred_work_times,
            'success_metrics': self.success_metrics,
            'risk_factors': self.risk_factors,
            'mitigation_strategies': self.mitigation_strategies,
            'lessons_learned': self.lessons_learned,
            'related_apps': self.related_apps,
            'activity_patterns': self.activity_patterns
        }


class GoalManager:
    """
    Central manager for goal-aware intelligence.
    
    Handles goal definition, decomposition, tracking, and adaptive management
    with integration to the observer system and AI reasoning.
    """
    
    def __init__(self, storage_dir: str = "goal_data", ai_interface=None):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.ai_interface = ai_interface
        self.logger = logging.getLogger(__name__)
        
        # Goal storage
        self.goals: Dict[str, Goal] = {}
        self.milestones: Dict[str, Milestone] = {}
        
        # Load existing data
        self._load_goals()
        self._load_milestones()
        
        self.logger.info(f"GoalManager initialized with {len(self.goals)} goals and {len(self.milestones)} milestones")
    
    def create_goal(self,
                   title: str,
                   description: str,
                   target_date: datetime,
                   goal_type: GoalType = GoalType.PROJECT,
                   **kwargs) -> Goal:
        """Create a new goal with intelligent setup"""
        
        goal = Goal(
            id="",  # Will be auto-generated
            title=title,
            description=description,
            goal_type=goal_type,
            target_date=target_date,
            **kwargs
        )
        
        self.goals[goal.id] = goal
        self._save_goals()
        
        self.logger.info(f"Created new goal: {goal.title} (ID: {goal.id})")
        
        # Trigger intelligent decomposition
        if self.ai_interface:
            asyncio.create_task(self._decompose_goal_intelligently(goal))
        
        return goal
    
    async def _decompose_goal_intelligently(self, goal: Goal):
        """Use AI to intelligently decompose goal into milestones"""
        
        try:
            decomposition_prompt = f"""
Break down this goal into specific, actionable milestones:

Goal: {goal.title}
Description: {goal.description}
Target Date: {goal.target_date.strftime('%Y-%m-%d')}
Duration: {goal.estimated_duration_weeks} weeks
Type: {goal.goal_type.value}

Create 3-7 milestones that:
1. Are specific and measurable
2. Build logically toward the goal
3. Have realistic time estimates
4. Account for dependencies
5. Include success criteria

Format as JSON array with fields: title, description, estimated_effort_hours, success_criteria, priority (1-5)
"""
            
            # This would call the AI interface to generate milestones
            # For now, we'll create a basic structure
            milestones_data = await self._get_ai_milestone_suggestions(decomposition_prompt)
            
            for i, milestone_data in enumerate(milestones_data):
                milestone = Milestone(
                    id="",  # Auto-generated
                    title=milestone_data['title'],
                    description=milestone_data['description'],
                    goal_id=goal.id,
                    target_date=self._calculate_milestone_date(goal, i, len(milestones_data)),
                    estimated_effort_hours=milestone_data.get('estimated_effort_hours', 8),
                    priority=milestone_data.get('priority', 3),
                    success_criteria=milestone_data.get('success_criteria', [])
                )
                
                self.milestones[milestone.id] = milestone
                goal.milestone_ids.append(milestone.id)
            
            self._save_goals()
            self._save_milestones()
            
            self.logger.info(f"Generated {len(milestones_data)} milestones for goal: {goal.title}")
            
        except Exception as e:
            self.logger.error(f"Error in intelligent goal decomposition: {e}")
    
    async def _get_ai_milestone_suggestions(self, prompt: str) -> List[Dict[str, Any]]:
        """Get AI-generated milestone suggestions"""
        
        # Placeholder for AI integration
        # In practice, this would call the twin's reasoning system
        return [
            {
                "title": "Initial setup and planning",
                "description": "Set up project structure and create detailed plan",
                "estimated_effort_hours": 4,
                "success_criteria": ["Project structure created", "Timeline defined"],
                "priority": 1
            },
            {
                "title": "Core implementation phase 1",
                "description": "Implement primary functionality",
                "estimated_effort_hours": 16,
                "success_criteria": ["Core features working", "Basic testing complete"],
                "priority": 1
            },
            {
                "title": "Testing and refinement",
                "description": "Comprehensive testing and bug fixes",
                "estimated_effort_hours": 8,
                "success_criteria": ["All tests passing", "Performance acceptable"],
                "priority": 2
            }
        ]
    
    def _calculate_milestone_date(self, goal: Goal, milestone_index: int, total_milestones: int) -> datetime:
        """Calculate target date for milestone based on goal timeline"""
        
        total_days = (goal.target_date - goal.created_date).days
        milestone_spacing = total_days / total_milestones
        
        milestone_date = goal.created_date + timedelta(days=milestone_spacing * (milestone_index + 1))
        
        return milestone_date
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals"""
        return [goal for goal in self.goals.values() if goal.status == GoalStatus.ACTIVE]
    
    def get_overdue_items(self) -> Dict[str, List[Union[Goal, Milestone]]]:
        """Get overdue goals and milestones"""
        
        overdue_goals = [goal for goal in self.goals.values() if goal.is_overdue]
        overdue_milestones = [milestone for milestone in self.milestones.values() if milestone.is_overdue]
        
        return {
            'goals': overdue_goals,
            'milestones': overdue_milestones
        }
    
    def get_next_actions(self, limit: int = 5) -> List[Milestone]:
        """Get next actions across all active goals"""
        
        next_actions = []
        
        for goal in self.get_active_goals():
            goal_next = goal.get_next_milestones(list(self.milestones.values()), limit=2)
            next_actions.extend(goal_next)
        
        # Sort by priority and deadline
        next_actions.sort(key=lambda m: (m.priority, m.target_date))
        
        return next_actions[:limit]
    
    def update_progress_from_observer(self, observer_data: Dict[str, Any]):
        """Update goal progress based on observer system data"""
        
        for goal in self.get_active_goals():
            goal.update_from_observer_data(observer_data)
        
        # Auto-detect progress in goal-related activities
        app_usage = observer_data.get('app_usage', {})
        
        for goal in self.get_active_goals():
            for app_name in goal.related_apps:
                if app_name in app_usage:
                    time_spent = app_usage[app_name]
                    
                    # Simple heuristic: significant time in goal-related app = progress
                    if time_spent > 1800:  # 30 minutes
                        self._auto_update_milestone_progress(goal, app_name, time_spent)
    
    def _auto_update_milestone_progress(self, goal: Goal, app_name: str, time_spent: int):
        """Auto-update milestone progress based on observed activity"""
        
        active_milestones = [
            self.milestones[mid] for mid in goal.milestone_ids
            if mid in self.milestones and self.milestones[mid].status == GoalStatus.ACTIVE
        ]
        
        if active_milestones:
            # Update the highest priority active milestone
            milestone = min(active_milestones, key=lambda m: m.priority)
            
            # Estimate progress based on time spent (rough heuristic)
            estimated_progress = (time_spent / 3600) / milestone.estimated_effort_hours * 100
            
            new_progress = min(milestone.progress_percentage + estimated_progress, 100.0)
            milestone.update_progress(
                new_progress, 
                f"Auto-updated from {app_name} activity ({time_spent//60} minutes)"
            )
    
    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get goal by ID"""
        return self.goals.get(goal_id)
    
    def get_milestone_by_id(self, milestone_id: str) -> Optional[Milestone]:
        """Get milestone by ID"""
        return self.milestones.get(milestone_id)
    
    def get_goal_summary(self) -> Dict[str, Any]:
        """Get summary of all goals"""
        
        total_goals = len(self.goals)
        active_goals = len(self.get_active_goals())
        completed_goals = len([g for g in self.goals.values() if g.status == GoalStatus.COMPLETED])
        overdue_items = self.get_overdue_items()
        
        return {
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'overdue_goals': len(overdue_items['goals']),
            'overdue_milestones': len(overdue_items['milestones']),
            'next_actions': len(self.get_next_actions()),
            'completion_rate': (completed_goals / total_goals * 100) if total_goals > 0 else 0
        }
    
    def _save_goals(self):
        """Save goals to storage"""
        goals_file = self.storage_dir / "goals.json"
        
        with open(goals_file, 'w') as f:
            json.dump([goal.to_dict() for goal in self.goals.values()], f, indent=2)
    
    def _save_milestones(self):
        """Save milestones to storage"""
        milestones_file = self.storage_dir / "milestones.json"
        
        with open(milestones_file, 'w') as f:
            json.dump([milestone.to_dict() for milestone in self.milestones.values()], f, indent=2)
    
    def _load_goals(self):
        """Load goals from storage"""
        goals_file = self.storage_dir / "goals.json"
        
        if goals_file.exists():
            try:
                with open(goals_file, 'r') as f:
                    goals_data = json.load(f)
                
                for goal_data in goals_data:
                    # Convert back to Goal object
                    goal = Goal(
                        id=goal_data['id'],
                        title=goal_data['title'],
                        description=goal_data['description'],
                        goal_type=GoalType(goal_data['goal_type']),
                        target_date=datetime.fromisoformat(goal_data['target_date']),
                        created_date=datetime.fromisoformat(goal_data['created_date']),
                        estimated_duration_weeks=goal_data['estimated_duration_weeks'],
                        status=GoalStatus(goal_data['status']),
                        progress_percentage=goal_data['progress_percentage'],
                        measurement_type=MeasurementType(goal_data['measurement_type']),
                        parent_goal_id=goal_data.get('parent_goal_id'),
                        sub_goal_ids=goal_data.get('sub_goal_ids', []),
                        milestone_ids=goal_data.get('milestone_ids', []),
                        motivation=goal_data.get('motivation', ''),
                        success_vision=goal_data.get('success_vision', ''),
                        impact_areas=goal_data.get('impact_areas', []),
                        priority=goal_data.get('priority', 3),
                        energy_level_required=goal_data.get('energy_level_required', 'medium'),
                        preferred_work_times=goal_data.get('preferred_work_times', []),
                        success_metrics=goal_data.get('success_metrics', []),
                        risk_factors=goal_data.get('risk_factors', []),
                        mitigation_strategies=goal_data.get('mitigation_strategies', []),
                        lessons_learned=goal_data.get('lessons_learned', []),
                        related_apps=goal_data.get('related_apps', []),
                        activity_patterns=goal_data.get('activity_patterns', {})
                    )
                    
                    self.goals[goal.id] = goal
                
            except Exception as e:
                self.logger.error(f"Error loading goals: {e}")
    
    def _load_milestones(self):
        """Load milestones from storage"""
        milestones_file = self.storage_dir / "milestones.json"
        
        if milestones_file.exists():
            try:
                with open(milestones_file, 'r') as f:
                    milestones_data = json.load(f)
                
                for milestone_data in milestones_data:
                    milestone = Milestone(
                        id=milestone_data['id'],
                        title=milestone_data['title'],
                        description=milestone_data['description'],
                        goal_id=milestone_data['goal_id'],
                        target_date=datetime.fromisoformat(milestone_data['target_date']),
                        estimated_effort_hours=milestone_data['estimated_effort_hours'],
                        actual_effort_hours=milestone_data.get('actual_effort_hours', 0.0),
                        status=GoalStatus(milestone_data['status']),
                        progress_percentage=milestone_data['progress_percentage'],
                        measurement_type=MeasurementType(milestone_data['measurement_type']),
                        depends_on=milestone_data.get('depends_on', []),
                        priority=milestone_data.get('priority', 1),
                        created_date=datetime.fromisoformat(milestone_data['created_date']),
                        last_updated=datetime.fromisoformat(milestone_data['last_updated']),
                        completion_date=datetime.fromisoformat(milestone_data['completion_date']) if milestone_data.get('completion_date') else None,
                        success_criteria=milestone_data.get('success_criteria', []),
                        obstacles_encountered=milestone_data.get('obstacles_encountered', []),
                        lessons_learned=milestone_data.get('lessons_learned', [])
                    )
                    
                    self.milestones[milestone.id] = milestone
                
            except Exception as e:
                self.logger.error(f"Error loading milestones: {e}")


# Import asyncio for async operations
import asyncio