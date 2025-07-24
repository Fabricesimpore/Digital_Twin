"""
Strategic Planner for Goal-Aware Agent

Provides adaptive project management, timeline optimization, and strategic
guidance based on behavioral patterns from the observer system.

Features:
- Dynamic timeline adjustment based on actual progress
- Resource allocation and capacity planning
- Risk assessment and mitigation strategies
- Strategic recommendations based on behavioral data
- Integration with observer system for real-time adaptation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

from .goal_manager import Goal, Milestone, GoalStatus, GoalType


class TimelineStatus(Enum):
    """Status of project timeline"""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    AHEAD = "ahead"
    CRITICAL = "critical"


class ResourceType(Enum):
    """Types of resources for project planning"""
    TIME = "time"
    ENERGY = "energy"
    FOCUS = "focus"
    TOOLS = "tools"
    KNOWLEDGE = "knowledge"


@dataclass
class TimelineAdaptation:
    """Represents a timeline adjustment recommendation"""
    milestone_id: str
    original_date: datetime
    recommended_date: datetime
    reason: str
    confidence: float  # 0-1
    impact_on_goal: str  # low, medium, high
    
    @property
    def days_adjustment(self) -> int:
        """Days being added or removed from timeline"""
        return (self.recommended_date - self.original_date).days


@dataclass
class ProjectPlan:
    """Strategic project plan with adaptive management"""
    goal_id: str
    created_date: datetime
    last_updated: datetime
    
    # Timeline analysis
    original_timeline_weeks: float
    current_timeline_weeks: float
    timeline_status: TimelineStatus
    completion_probability: float  # 0-1
    
    # Resource planning
    estimated_total_hours: float
    hours_completed: float
    hours_remaining: float
    weekly_capacity_hours: float
    
    # Risk assessment
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    success_blockers: List[str] = field(default_factory=list)
    
    # Behavioral insights
    optimal_work_schedule: Dict[str, Any] = field(default_factory=dict)
    productivity_patterns: Dict[str, Any] = field(default_factory=dict)
    focus_recommendations: List[str] = field(default_factory=list)
    
    # Adaptations
    timeline_adaptations: List[TimelineAdaptation] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Overall project progress percentage"""
        if self.estimated_total_hours == 0:
            return 0.0
        return (self.hours_completed / self.estimated_total_hours) * 100
    
    @property
    def projected_completion_date(self) -> datetime:
        """Projected completion date based on current progress"""
        if self.weekly_capacity_hours == 0 or self.hours_remaining == 0:
            return datetime.now()
        
        weeks_remaining = self.hours_remaining / self.weekly_capacity_hours
        return datetime.now() + timedelta(weeks=weeks_remaining)


class StrategicPlanner:
    """
    Strategic planning system for goal-aware project management.
    
    Integrates with observer system to provide data-driven timeline
    adjustments, resource planning, and strategic recommendations.
    """
    
    def __init__(self, goal_manager, observer_manager=None):
        self.goal_manager = goal_manager
        self.observer_manager = observer_manager
        self.logger = logging.getLogger(__name__)
        
        # Planning data
        self.project_plans: Dict[str, ProjectPlan] = {}
        
        # Behavioral analysis cache
        self.productivity_analysis_cache = {}
        self.last_analysis_update = None
    
    def create_project_plan(self, goal: Goal, milestones: List[Milestone]) -> ProjectPlan:
        """Create a strategic project plan for a goal"""
        
        # Calculate timeline estimates
        total_hours = sum(m.estimated_effort_hours for m in milestones)
        completed_hours = sum(m.actual_effort_hours for m in milestones)
        remaining_hours = total_hours - completed_hours
        
        # Estimate weekly capacity based on behavioral data
        weekly_capacity = self._estimate_weekly_capacity(goal)
        
        # Calculate timeline
        original_weeks = (goal.target_date - goal.created_date).days / 7
        current_weeks = remaining_hours / weekly_capacity if weekly_capacity > 0 else 0
        
        # Assess timeline status
        timeline_status = self._assess_timeline_status(goal, current_weeks, original_weeks)
        
        # Calculate completion probability
        completion_prob = self._calculate_completion_probability(goal, milestones)
        
        plan = ProjectPlan(
            goal_id=goal.id,
            created_date=datetime.now(),
            last_updated=datetime.now(),
            original_timeline_weeks=original_weeks,
            current_timeline_weeks=current_weeks,
            timeline_status=timeline_status,
            completion_probability=completion_prob,
            estimated_total_hours=total_hours,
            hours_completed=completed_hours,
            hours_remaining=remaining_hours,
            weekly_capacity_hours=weekly_capacity
        )
        
        # Add behavioral insights
        self._add_behavioral_insights(plan, goal)
        
        # Generate risk assessment
        self._assess_project_risks(plan, goal, milestones)
        
        # Generate timeline adaptations if needed
        if timeline_status in [TimelineStatus.BEHIND, TimelineStatus.CRITICAL]:
            plan.timeline_adaptations = self._generate_timeline_adaptations(goal, milestones, plan)
        
        self.project_plans[goal.id] = plan
        
        self.logger.info(f"Created strategic plan for goal: {goal.title}")
        return plan
    
    def _estimate_weekly_capacity(self, goal: Goal) -> float:
        """Estimate weekly time capacity for goal-related work"""
        
        if not self.observer_manager:
            # Default estimate
            return 10.0  # 10 hours per week
        
        # Get behavioral data from observer
        try:
            insights = self.observer_manager.get_insights()
            
            # Look for productivity patterns
            productivity_data = insights.get('productivity_insights', {})
            
            # Base capacity on observed productive time
            daily_productive_hours = productivity_data.get('average_focus_duration_minutes', 120) / 60
            working_days_per_week = 5  # Assume 5-day work week
            
            # Factor in goal type
            goal_factor = {
                GoalType.PROJECT: 1.0,
                GoalType.LEARNING: 0.7,  # Learning typically gets less time
                GoalType.CREATIVE: 0.8,
                GoalType.HABIT: 0.3,      # Habits need less dedicated time
                GoalType.CAREER: 0.6,
                GoalType.HEALTH: 0.4,
                GoalType.PERSONAL: 0.5
            }.get(goal.goal_type, 0.7)
            
            estimated_capacity = daily_productive_hours * working_days_per_week * goal_factor
            
            # Cap at reasonable limits
            return max(2.0, min(40.0, estimated_capacity))
            
        except Exception as e:
            self.logger.error(f"Error estimating capacity: {e}")
            return 10.0
    
    def _assess_timeline_status(self, goal: Goal, current_weeks: float, original_weeks: float) -> TimelineStatus:
        """Assess current timeline status"""
        
        if current_weeks <= original_weeks * 0.8:
            return TimelineStatus.AHEAD
        elif current_weeks <= original_weeks:
            return TimelineStatus.ON_TRACK
        elif current_weeks <= original_weeks * 1.2:
            return TimelineStatus.AT_RISK
        elif current_weeks <= original_weeks * 1.5:
            return TimelineStatus.BEHIND
        else:
            return TimelineStatus.CRITICAL
    
    def _calculate_completion_probability(self, goal: Goal, milestones: List[Milestone]) -> float:
        """Calculate probability of goal completion by target date"""
        
        factors = []
        
        # Progress factor
        progress = goal.calculate_progress_from_milestones(milestones)
        progress_factor = min(progress / 100.0 * 2, 1.0)  # Progress contributes up to 1.0
        factors.append(progress_factor)
        
        # Timeline factor
        days_remaining = goal.days_until_deadline
        if days_remaining > 0:
            timeline_factor = min(days_remaining / 30, 1.0)  # More time = higher probability
        else:
            timeline_factor = 0.1  # Already overdue
        factors.append(timeline_factor)
        
        # Milestone dependency factor
        blocked_milestones = 0
        total_milestones = len(milestones)
        
        for milestone in milestones:
            if milestone.goal_id == goal.id and milestone.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]:
                # Check if dependencies are blocking
                for dep_id in milestone.depends_on:
                    dep_milestone = next((m for m in milestones if m.id == dep_id), None)
                    if not dep_milestone or dep_milestone.status != GoalStatus.COMPLETED:
                        blocked_milestones += 1
                        break
        
        if total_milestones > 0:
            dependency_factor = 1.0 - (blocked_milestones / total_milestones * 0.5)
        else:
            dependency_factor = 0.5
        factors.append(dependency_factor)
        
        # Behavioral pattern factor (if observer data available)
        if self.observer_manager:
            try:
                insights = self.observer_manager.get_insights()
                productivity_score = insights.get('productivity_insights', {}).get('productivity_score', 0.5)
                behavioral_factor = productivity_score
                factors.append(behavioral_factor)
            except:
                pass
        
        # Calculate weighted average
        return sum(factors) / len(factors)
    
    def _add_behavioral_insights(self, plan: ProjectPlan, goal: Goal):
        """Add behavioral insights to project plan"""
        
        if not self.observer_manager:
            return
        
        try:
            insights = self.observer_manager.get_insights()
            
            # Optimal work schedule
            activity_patterns = insights.get('activity_patterns', {})
            most_active_hour = activity_patterns.get('most_active_hour')
            
            if most_active_hour:
                plan.optimal_work_schedule = {
                    'peak_hours': [most_active_hour, most_active_hour + 1],
                    'recommended_schedule': f"Work on {goal.title} during {most_active_hour}:00-{most_active_hour+2}:00"
                }
            
            # Productivity patterns
            productivity_insights = insights.get('productivity_insights', {})
            plan.productivity_patterns = {
                'productivity_score': productivity_insights.get('productivity_score', 0.5),
                'productivity_trend': productivity_insights.get('productivity_trend', 'stable'),
                'distraction_ratio': productivity_insights.get('distraction_ratio', 0.3)
            }
            
            # Focus recommendations
            focus_patterns = insights.get('focus_patterns', {})
            avg_focus_duration = focus_patterns.get('average_focus_duration_minutes', 45)
            
            plan.focus_recommendations = [
                f"Based on your patterns, work in {avg_focus_duration}-minute focused sessions",
                "Take breaks when productivity score drops below 60%",
                f"Schedule {goal.title} work during your peak hours: {most_active_hour}:00-{most_active_hour+2}:00" if most_active_hour else ""
            ]
            
            # Filter out empty recommendations
            plan.focus_recommendations = [r for r in plan.focus_recommendations if r]
            
        except Exception as e:
            self.logger.error(f"Error adding behavioral insights: {e}")
    
    def _assess_project_risks(self, plan: ProjectPlan, goal: Goal, milestones: List[Milestone]):
        """Assess and document project risks"""
        
        # Timeline risks
        if plan.timeline_status in [TimelineStatus.BEHIND, TimelineStatus.CRITICAL]:
            plan.risk_factors.append("Timeline at risk - may miss target date")
            plan.mitigation_strategies.append("Consider reducing scope or extending deadline")
        
        # Capacity risks
        if plan.weekly_capacity_hours < 5:
            plan.risk_factors.append("Low weekly capacity may slow progress")
            plan.mitigation_strategies.append("Block dedicated time slots for goal work")
        
        # Dependency risks
        blocked_count = 0
        for milestone in milestones:
            if milestone.goal_id == goal.id:
                for dep_id in milestone.depends_on:
                    dep_milestone = next((m for m in milestones if m.id == dep_id), None)
                    if dep_milestone and dep_milestone.status != GoalStatus.COMPLETED:
                        blocked_count += 1
        
        if blocked_count > 0:
            plan.risk_factors.append(f"{blocked_count} milestones blocked by dependencies")
            plan.mitigation_strategies.append("Prioritize completing dependency milestones")
        
        # Behavioral risks
        if self.observer_manager:
            try:
                insights = self.observer_manager.get_insights()
                productivity_score = insights.get('productivity_insights', {}).get('productivity_score', 0.5)
                
                if productivity_score < 0.4:
                    plan.risk_factors.append("Low productivity patterns may impact progress")
                    plan.mitigation_strategies.append("Focus on productivity optimization and distraction reduction")
                
                distraction_ratio = insights.get('productivity_insights', {}).get('distraction_ratio', 0.3)
                if distraction_ratio > 0.4:
                    plan.risk_factors.append("High distraction levels detected")
                    plan.mitigation_strategies.append("Consider using focus tools or blocking distracting websites")
                    
            except Exception as e:
                self.logger.error(f"Error assessing behavioral risks: {e}")
        
        # Success blockers
        overdue_milestones = [m for m in milestones if m.goal_id == goal.id and m.is_overdue]
        if overdue_milestones:
            plan.success_blockers.append(f"{len(overdue_milestones)} overdue milestones need immediate attention")
    
    def _generate_timeline_adaptations(self, goal: Goal, milestones: List[Milestone], plan: ProjectPlan) -> List[TimelineAdaptation]:
        """Generate timeline adaptation recommendations"""
        
        adaptations = []
        goal_milestones = [m for m in milestones if m.goal_id == goal.id]
        
        # Calculate delay needed based on current capacity
        weeks_behind = max(0, plan.current_timeline_weeks - plan.original_timeline_weeks)
        days_behind = int(weeks_behind * 7)
        
        # Suggest pushing back non-critical milestones
        for milestone in goal_milestones:
            if milestone.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]:
                # Lower priority milestones can be delayed more
                delay_factor = (6 - milestone.priority) / 5  # Priority 1 = 0, Priority 5 = 0.8
                suggested_delay = int(days_behind * delay_factor)
                
                if suggested_delay > 0:
                    new_date = milestone.target_date + timedelta(days=suggested_delay)
                    
                    adaptation = TimelineAdaptation(
                        milestone_id=milestone.id,
                        original_date=milestone.target_date,
                        recommended_date=new_date,
                        reason=f"Adjust for capacity constraints (Priority {milestone.priority})",
                        confidence=0.7,
                        impact_on_goal="medium" if milestone.priority <= 2 else "low"
                    )
                    
                    adaptations.append(adaptation)
        
        return adaptations
    
    def update_plan_from_progress(self, goal_id: str):
        """Update project plan based on actual progress"""
        
        if goal_id not in self.project_plans:
            return
        
        plan = self.project_plans[goal_id]
        goal = self.goal_manager.get_goal_by_id(goal_id)
        milestones = [self.goal_manager.get_milestone_by_id(mid) for mid in goal.milestone_ids]
        milestones = [m for m in milestones if m is not None]
        
        # Recalculate progress
        plan.hours_completed = sum(m.actual_effort_hours for m in milestones)
        plan.hours_remaining = plan.estimated_total_hours - plan.hours_completed
        
        # Update timeline assessment
        current_weeks = plan.hours_remaining / plan.weekly_capacity_hours if plan.weekly_capacity_hours > 0 else 0
        plan.current_timeline_weeks = current_weeks
        plan.timeline_status = self._assess_timeline_status(goal, current_weeks, plan.original_timeline_weeks)
        
        # Recalculate completion probability
        plan.completion_probability = self._calculate_completion_probability(goal, milestones)
        
        # Update timestamp
        plan.last_updated = datetime.now()
        
        self.logger.info(f"Updated project plan for goal: {goal.title}")
    
    def get_strategic_recommendations(self, goal_id: str) -> List[str]:
        """Get strategic recommendations for a goal"""
        
        if goal_id not in self.project_plans:
            return ["Create a project plan first"]
        
        plan = self.project_plans[goal_id]
        goal = self.goal_manager.get_goal_by_id(goal_id)
        recommendations = []
        
        # Timeline recommendations
        if plan.timeline_status == TimelineStatus.BEHIND:
            recommendations.append("Consider extending timeline or reducing scope")
            recommendations.append("Focus on highest priority milestones first")
        elif plan.timeline_status == TimelineStatus.CRITICAL:
            recommendations.append("URGENT: Major timeline adjustment needed")
            recommendations.append("Consider breaking goal into smaller, achievable parts")
        
        # Capacity recommendations
        if plan.weekly_capacity_hours < 5:
            recommendations.append("Schedule more dedicated time for this goal")
            recommendations.append("Consider time-blocking specific hours for focused work")
        
        # Progress recommendations
        if plan.progress_percentage < 25 and plan.completion_probability < 0.6:
            recommendations.append("Re-evaluate goal feasibility with current approach")
            recommendations.append("Consider getting help or learning new skills")
        
        # Behavioral recommendations
        if plan.productivity_patterns.get('distraction_ratio', 0) > 0.4:
            recommendations.append("Address distractions during goal work sessions")
            recommendations.append("Use focus tools or apps to maintain concentration")
        
        # Add focus recommendations from behavioral analysis
        recommendations.extend(plan.focus_recommendations)
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def get_next_week_plan(self, goal_id: str) -> Dict[str, Any]:
        """Generate next week's plan for a goal"""
        
        goal = self.goal_manager.get_goal_by_id(goal_id)
        if not goal:
            return {}
        
        plan = self.project_plans.get(goal_id)
        next_milestones = goal.get_next_milestones(
            list(self.goal_manager.milestones.values()), 
            limit=3
        )
        
        # Calculate recommended time allocation
        total_available_hours = plan.weekly_capacity_hours if plan else 10
        
        weekly_plan = {
            'goal_title': goal.title,
            'available_hours': total_available_hours,
            'recommended_milestones': [],
            'schedule_suggestions': [],
            'focus_tips': []
        }
        
        # Allocate time to milestones
        for i, milestone in enumerate(next_milestones):
            hours_needed = min(milestone.estimated_effort_hours * 0.3, total_available_hours * 0.4)
            
            weekly_plan['recommended_milestones'].append({
                'title': milestone.title,
                'recommended_hours': hours_needed,
                'priority': milestone.priority,
                'deadline': milestone.target_date.strftime('%Y-%m-%d')
            })
        
        # Schedule suggestions based on behavioral data
        if plan and plan.optimal_work_schedule:
            peak_hours = plan.optimal_work_schedule.get('peak_hours', [14, 15])
            weekly_plan['schedule_suggestions'] = [
                f"Schedule goal work during peak hours: {peak_hours[0]}:00-{peak_hours[-1]}:00",
                "Break work into focused sessions with regular breaks",
                f"Aim for {total_available_hours:.1f} hours total this week"
            ]
        
        # Focus tips
        if plan:
            weekly_plan['focus_tips'] = plan.focus_recommendations
        
        return weekly_plan
    
    def get_all_project_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries of all project plans"""
        
        summaries = []
        
        for goal_id, plan in self.project_plans.items():
            goal = self.goal_manager.get_goal_by_id(goal_id)
            
            if goal:
                summary = {
                    'goal_id': goal_id,
                    'title': goal.title,
                    'progress_percentage': plan.progress_percentage,
                    'timeline_status': plan.timeline_status.value,
                    'completion_probability': plan.completion_probability,
                    'weeks_remaining': plan.current_timeline_weeks,
                    'next_milestone': None,
                    'risk_level': len(plan.risk_factors)
                }
                
                # Get next milestone
                next_milestones = goal.get_next_milestones(
                    list(self.goal_manager.milestones.values()), 
                    limit=1
                )
                
                if next_milestones:
                    summary['next_milestone'] = {
                        'title': next_milestones[0].title,
                        'deadline': next_milestones[0].target_date.strftime('%Y-%m-%d'),
                        'days_remaining': next_milestones[0].days_until_deadline
                    }
                
                summaries.append(summary)
        
        return summaries