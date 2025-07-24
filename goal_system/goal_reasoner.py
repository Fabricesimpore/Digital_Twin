"""
Goal-Aware Reasoning System

Integrates goals into the digital twin's reasoning process, making every
decision context-aware of current goals, priorities, and strategic objectives.

Features:
- Goal-informed decision making for all twin interactions
- Priority-based task and action recommendations
- Strategic context injection into conversations
- Goal progress consideration in daily planning
- Automatic goal relevance detection for requests
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .goal_manager import Goal, Milestone, GoalStatus, GoalType, GoalManager
from .strategic_planner import StrategicPlanner, ProjectPlan, TimelineStatus


class GoalRelevance(Enum):
    """How relevant a request/decision is to goals"""
    HIGHLY_RELEVANT = "highly_relevant"    # Directly advances a goal
    MODERATELY_RELEVANT = "moderately_relevant"  # Indirectly related
    TANGENTIALLY_RELEVANT = "tangentially_relevant"  # Loosely related
    NOT_RELEVANT = "not_relevant"          # No relation to goals


@dataclass
class GoalContext:
    """Context about goals for reasoning"""
    active_goals: List[Goal]
    urgent_milestones: List[Milestone]
    overdue_items: Dict[str, List]
    next_actions: List[Milestone]
    current_priorities: List[str]
    goal_relevance: GoalRelevance
    relevant_goal_ids: List[str]
    strategic_recommendations: List[str]
    
    def to_reasoning_prompt(self) -> str:
        """Convert to text for AI reasoning"""
        
        context_text = "CURRENT GOALS CONTEXT:\n\n"
        
        # Active goals
        if self.active_goals:
            context_text += "Active Goals:\n"
            for goal in self.active_goals[:3]:  # Top 3
                progress = f"{goal.progress_percentage:.1f}%"
                deadline = goal.target_date.strftime('%Y-%m-%d')
                context_text += f"• {goal.title} ({progress} complete, due {deadline})\n"
            context_text += "\n"
        
        # Urgent items
        if self.urgent_milestones:
            context_text += "Urgent Milestones:\n"
            for milestone in self.urgent_milestones[:3]:
                days_left = milestone.days_until_deadline
                context_text += f"• {milestone.title} (due in {days_left} days)\n"
            context_text += "\n"
        
        # Next actions
        if self.next_actions:
            context_text += "Next Actions:\n"
            for action in self.next_actions[:3]:
                context_text += f"• {action.title}\n"
            context_text += "\n"
        
        # Current priorities
        if self.current_priorities:
            context_text += f"Current Priorities: {', '.join(self.current_priorities)}\n\n"
        
        # Strategic recommendations
        if self.strategic_recommendations:
            context_text += "Strategic Recommendations:\n"
            for rec in self.strategic_recommendations[:2]:
                context_text += f"• {rec}\n"
        
        return context_text


class GoalAwareReasoner:
    """
    Goal-aware reasoning system that integrates strategic objectives
    into every decision made by the digital twin.
    """
    
    def __init__(self, goal_manager: GoalManager, strategic_planner: StrategicPlanner):
        self.goal_manager = goal_manager
        self.strategic_planner = strategic_planner
        self.logger = logging.getLogger(__name__)
        
        # Context caching
        self._context_cache = None
        self._context_cache_time = None
        self._cache_duration = timedelta(minutes=5)
    
    def get_goal_context(self, request_text: str = "", force_refresh: bool = False) -> GoalContext:
        """Get current goal context for reasoning"""
        
        # Check cache validity
        if (not force_refresh and 
            self._context_cache and 
            self._context_cache_time and 
            datetime.now() - self._context_cache_time < self._cache_duration):
            
            # Update relevance for new request
            if request_text:
                self._context_cache.goal_relevance, self._context_cache.relevant_goal_ids = self._assess_goal_relevance(request_text)
            
            return self._context_cache
        
        # Build fresh context
        active_goals = self.goal_manager.get_active_goals()
        overdue_items = self.goal_manager.get_overdue_items()
        next_actions = self.goal_manager.get_next_actions(limit=5)
        
        # Get urgent milestones (due within 7 days)
        urgent_milestones = []
        for milestone in self.goal_manager.milestones.values():
            if (milestone.status == GoalStatus.ACTIVE and 
                0 <= milestone.days_until_deadline <= 7):
                urgent_milestones.append(milestone)
        
        urgent_milestones.sort(key=lambda m: m.days_until_deadline)
        
        # Determine current priorities
        current_priorities = self._determine_current_priorities(active_goals, urgent_milestones)
        
        # Get strategic recommendations
        strategic_recommendations = []
        for goal in active_goals[:2]:  # Top 2 goals
            recommendations = self.strategic_planner.get_strategic_recommendations(goal.id)
            strategic_recommendations.extend(recommendations[:2])  # Top 2 per goal
        
        # Assess relevance to current request
        goal_relevance = GoalRelevance.NOT_RELEVANT
        relevant_goal_ids = []
        
        if request_text:
            goal_relevance, relevant_goal_ids = self._assess_goal_relevance(request_text)
        
        # Create context
        context = GoalContext(
            active_goals=active_goals,
            urgent_milestones=urgent_milestones,
            overdue_items=overdue_items,
            next_actions=next_actions,
            current_priorities=current_priorities,
            goal_relevance=goal_relevance,
            relevant_goal_ids=relevant_goal_ids,
            strategic_recommendations=strategic_recommendations[:4]  # Limit to 4
        )
        
        # Cache the context
        self._context_cache = context
        self._context_cache_time = datetime.now()
        
        return context
    
    def _determine_current_priorities(self, active_goals: List[Goal], urgent_milestones: List[Milestone]) -> List[str]:
        """Determine what should be prioritized right now"""
        
        priorities = []
        
        # Overdue items are highest priority
        for milestone in urgent_milestones:
            if milestone.days_until_deadline < 0:
                priorities.append(f"OVERDUE: {milestone.title}")
        
        # Urgent items (next 3 days)
        for milestone in urgent_milestones:
            if 0 <= milestone.days_until_deadline <= 3:
                priorities.append(f"URGENT: {milestone.title}")
        
        # High priority goals
        high_priority_goals = [g for g in active_goals if g.priority <= 2]
        for goal in high_priority_goals[:2]:
            priorities.append(f"High Priority Goal: {goal.title}")
        
        return priorities[:5]  # Limit to top 5
    
    def _assess_goal_relevance(self, request_text: str) -> Tuple[GoalRelevance, List[str]]:
        """Assess how relevant a request is to current goals"""
        
        if not request_text:
            return GoalRelevance.NOT_RELEVANT, []
        
        request_lower = request_text.lower()
        relevant_goals = []
        max_relevance = GoalRelevance.NOT_RELEVANT
        
        active_goals = self.goal_manager.get_active_goals()
        
        for goal in active_goals:
            relevance_score = 0
            
            # Direct goal title mention
            if goal.title.lower() in request_lower:
                relevance_score += 10
            
            # Goal keywords in request
            goal_keywords = goal.title.lower().split() + goal.description.lower().split()
            for keyword in goal_keywords:
                if len(keyword) > 3 and keyword in request_lower:
                    relevance_score += 2
            
            # Related apps mentioned
            for app in goal.related_apps:
                if app.lower() in request_lower:
                    relevance_score += 3
            
            # Goal type relevance
            type_keywords = {
                GoalType.PROJECT: ['project', 'build', 'create', 'develop', 'launch'],
                GoalType.LEARNING: ['learn', 'study', 'practice', 'skill', 'course'],
                GoalType.CREATIVE: ['design', 'write', 'create', 'art', 'creative'],
                GoalType.CAREER: ['work', 'career', 'job', 'professional'],
                GoalType.HEALTH: ['health', 'fitness', 'exercise', 'wellness'],
                GoalType.HABIT: ['habit', 'routine', 'daily', 'practice']
            }
            
            goal_type_keywords = type_keywords.get(goal.goal_type, [])
            for keyword in goal_type_keywords:
                if keyword in request_lower:
                    relevance_score += 1
            
            # Assess relevance level
            if relevance_score >= 8:
                goal_relevance = GoalRelevance.HIGHLY_RELEVANT
                relevant_goals.append(goal.id)
            elif relevance_score >= 4:
                goal_relevance = GoalRelevance.MODERATELY_RELEVANT
                relevant_goals.append(goal.id)
            elif relevance_score >= 1:
                goal_relevance = GoalRelevance.TANGENTIALLY_RELEVANT
                relevant_goals.append(goal.id)
            
            # Track highest relevance found
            if goal_relevance.value == 'highly_relevant':
                max_relevance = GoalRelevance.HIGHLY_RELEVANT
            elif goal_relevance.value == 'moderately_relevant' and max_relevance != GoalRelevance.HIGHLY_RELEVANT:
                max_relevance = GoalRelevance.MODERATELY_RELEVANT
            elif goal_relevance.value == 'tangentially_relevant' and max_relevance == GoalRelevance.NOT_RELEVANT:
                max_relevance = GoalRelevance.TANGENTIALLY_RELEVANT
        
        return max_relevance, relevant_goals
    
    def enhance_reasoning_prompt(self, base_prompt: str, request_text: str = "") -> str:
        """Enhance a reasoning prompt with goal context"""
        
        goal_context = self.get_goal_context(request_text)
        
        # Add goal context to prompt
        enhanced_prompt = f"{base_prompt}\n\n{goal_context.to_reasoning_prompt()}"
        
        # Add relevance-specific instructions
        if goal_context.goal_relevance == GoalRelevance.HIGHLY_RELEVANT:
            enhanced_prompt += "\nIMPORTANT: This request is directly related to active goals. Prioritize actions that advance these goals.\n"
        elif goal_context.goal_relevance == GoalRelevance.MODERATELY_RELEVANT:
            enhanced_prompt += "\nNOTE: This request may relate to your goals. Consider how your response can support goal progress.\n"
        
        # Add priority reminders
        if goal_context.current_priorities:
            enhanced_prompt += f"\nCURRENT PRIORITIES: {', '.join(goal_context.current_priorities[:3])}\n"
        
        return enhanced_prompt
    
    def get_goal_informed_recommendations(self, request_text: str) -> List[str]:
        """Get recommendations that consider current goals"""
        
        goal_context = self.get_goal_context(request_text)
        recommendations = []
        
        # Urgent milestone reminders
        if goal_context.urgent_milestones:
            milestone = goal_context.urgent_milestones[0]
            days_left = milestone.days_until_deadline
            
            if days_left < 0:
                recommendations.append(f"⚠️ OVERDUE: {milestone.title} was due {abs(days_left)} days ago")
            elif days_left <= 3:
                recommendations.append(f"🚨 URGENT: {milestone.title} is due in {days_left} days")
        
        # Next action suggestions
        if goal_context.next_actions:
            action = goal_context.next_actions[0]
            recommendations.append(f"📋 Next Action: Consider working on '{action.title}'")
        
        # Goal progress opportunities
        if goal_context.goal_relevance in [GoalRelevance.HIGHLY_RELEVANT, GoalRelevance.MODERATELY_RELEVANT]:
            for goal_id in goal_context.relevant_goal_ids[:2]:
                goal = self.goal_manager.get_goal_by_id(goal_id)
                if goal:
                    recommendations.append(f"🎯 Goal Connection: This could advance '{goal.title}' ({goal.progress_percentage:.1f}% complete)")
        
        # Strategic recommendations
        if goal_context.strategic_recommendations:
            recommendations.append(f"💡 Strategic Tip: {goal_context.strategic_recommendations[0]}")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def should_proactively_mention_goals(self, current_activity: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Determine if goals should be proactively mentioned"""
        
        goal_context = self.get_goal_context()
        
        # Always mention overdue items
        if goal_context.overdue_items['milestones']:
            overdue_milestone = goal_context.overdue_items['milestones'][0]
            return True, f"Reminder: {overdue_milestone.title} is overdue"
        
        # Mention urgent items
        if goal_context.urgent_milestones:
            urgent = goal_context.urgent_milestones[0]
            if urgent.days_until_deadline <= 1:
                return True, f"Urgent: {urgent.title} is due tomorrow"
        
        # Mention goal-related activity
        if current_activity:
            current_app = current_activity.get('current_app', '')
            
            for goal in goal_context.active_goals:
                if current_app in goal.related_apps:
                    next_milestones = goal.get_next_milestones(
                        list(self.goal_manager.milestones.values()), 
                        limit=1
                    )
                    
                    if next_milestones:
                        milestone = next_milestones[0]
                        return True, f"I see you're working in {current_app}. Don't forget about '{milestone.title}' for your {goal.title} goal"
        
        return False, ""
    
    def get_daily_goal_briefing(self) -> str:
        """Generate a daily briefing focused on goals"""
        
        goal_context = self.get_goal_context(force_refresh=True)
        
        briefing = "📅 **Daily Goal Briefing**\n\n"
        
        # Urgent items
        if goal_context.urgent_milestones:
            briefing += "🚨 **Urgent Today:**\n"
            for milestone in goal_context.urgent_milestones[:3]:
                days_left = milestone.days_until_deadline
                urgency = "OVERDUE" if days_left < 0 else f"{days_left} days left"
                briefing += f"• {milestone.title} ({urgency})\n"
            briefing += "\n"
        
        # Active goals progress
        if goal_context.active_goals:
            briefing += "🎯 **Active Goals:**\n"
            for goal in goal_context.active_goals[:3]:
                progress = f"{goal.progress_percentage:.1f}%"
                briefing += f"• {goal.title} - {progress} complete\n"
            briefing += "\n"
        
        # Recommended actions
        if goal_context.next_actions:
            briefing += "📋 **Recommended Actions:**\n"
            for action in goal_context.next_actions[:3]:
                briefing += f"• {action.title}\n"
            briefing += "\n"
        
        # Strategic recommendations
        if goal_context.strategic_recommendations:
            briefing += "💡 **Strategic Focus:**\n"
            for rec in goal_context.strategic_recommendations[:2]:
                briefing += f"• {rec}\n"
        
        return briefing
    
    def get_goal_aware_task_prioritization(self, tasks: List[str]) -> List[Tuple[str, int, str]]:
        """Prioritize tasks based on goal alignment"""
        
        goal_context = self.get_goal_context()
        prioritized_tasks = []
        
        for task in tasks:
            relevance, relevant_goals = self._assess_goal_relevance(task)
            
            # Base priority
            priority = 5  # Default low priority
            reason = "General task"
            
            # Boost priority based on goal relevance
            if relevance == GoalRelevance.HIGHLY_RELEVANT:
                priority = 1
                goal_titles = [self.goal_manager.get_goal_by_id(gid).title for gid in relevant_goals[:2]]
                reason = f"Directly advances: {', '.join(goal_titles)}"
            elif relevance == GoalRelevance.MODERATELY_RELEVANT:
                priority = 2
                reason = "Supports active goals"
            elif relevance == GoalRelevance.TANGENTIALLY_RELEVANT:
                priority = 3
                reason = "Loosely related to goals"
            
            # Check for urgent milestone keywords
            for milestone in goal_context.urgent_milestones:
                if any(word in task.lower() for word in milestone.title.lower().split()):
                    priority = 1
                    reason = f"Urgent milestone: {milestone.title}"
                    break
            
            prioritized_tasks.append((task, priority, reason))
        
        # Sort by priority (1 = highest)
        prioritized_tasks.sort(key=lambda x: x[1])
        
        return prioritized_tasks
    
    def update_goal_progress_from_completion(self, completed_task: str, time_spent_hours: float = 0):
        """Update goal progress when a task is completed"""
        
        relevance, relevant_goal_ids = self._assess_goal_relevance(completed_task)
        
        if relevance in [GoalRelevance.HIGHLY_RELEVANT, GoalRelevance.MODERATELY_RELEVANT]:
            for goal_id in relevant_goal_ids:
                goal = self.goal_manager.get_goal_by_id(goal_id)
                if goal:
                    # Find active milestones for this goal
                    active_milestones = [
                        self.goal_manager.get_milestone_by_id(mid) 
                        for mid in goal.milestone_ids
                        if (mid in self.goal_manager.milestones and 
                            self.goal_manager.milestones[mid].status == GoalStatus.ACTIVE)
                    ]
                    
                    if active_milestones:
                        # Update the highest priority milestone
                        milestone = min(active_milestones, key=lambda m: m.priority)
                        
                        # Estimate progress boost
                        progress_boost = min(20.0, time_spent_hours / milestone.estimated_effort_hours * 100)
                        new_progress = min(milestone.progress_percentage + progress_boost, 100.0)
                        
                        milestone.update_progress(
                            new_progress,
                            f"Auto-updated from completed task: {completed_task}"
                        )
                        
                        # Update actual effort
                        milestone.actual_effort_hours += time_spent_hours
                        
                        self.logger.info(f"Updated milestone '{milestone.title}' progress to {new_progress:.1f}%")
                        
                        # Update strategic plan
                        self.strategic_planner.update_plan_from_progress(goal_id)