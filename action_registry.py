"""
Universal Action Registry for Digital Twin System

This module provides a comprehensive action registry that standardizes how
the digital twin system handles all types of actions across different domains:

- Communication (calls, emails, messages)
- Calendar/Scheduling (meetings, reminders, events)
- Task Management (todos, projects, deadlines)
- File/Document Operations (create, edit, organize)
- External Integrations (APIs, services, automations)
- System Operations (backup, optimize, maintain)

The registry provides:
1. Universal ActionPlan structure for all action types
2. Standardized action validation and execution
3. Memory-aware action optimization
4. Cross-platform action compatibility
5. Extensible action type definitions
"""

from typing import Dict, List, Any, Optional, Union, Callable, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import logging


class ActionCategory(Enum):
    """Categories of actions the twin can perform"""
    COMMUNICATION = "communication"
    SCHEDULING = "scheduling"
    TASK_MANAGEMENT = "task_management"
    FILE_OPERATIONS = "file_operations"
    RESEARCH = "research"
    AUTOMATION = "automation"
    SYSTEM = "system"
    PERSONAL = "personal"
    LEARNING = "learning"
    ANALYSIS = "analysis"


class ActionComplexity(Enum):
    """Complexity levels for actions"""
    SIMPLE = "simple"          # Single tool, single step
    MODERATE = "moderate"      # Multiple steps, single domain
    COMPLEX = "complex"        # Multiple tools, multiple domains
    WORKFLOW = "workflow"      # Multi-step process with dependencies


class ActionUrgency(Enum):
    """Urgency levels for action execution"""
    LOW = "low"               # Can be delayed, background processing
    NORMAL = "normal"         # Standard processing
    HIGH = "high"            # Prioritized execution
    URGENT = "urgent"        # Immediate execution required
    CRITICAL = "critical"    # System-critical, highest priority


@dataclass
class ActionParameter:
    """Definition of an action parameter"""
    name: str
    type_hint: str  # "str", "int", "datetime", "list", etc.
    description: str
    required: bool = True
    default_value: Any = None
    validation_rule: Optional[str] = None  # Regex or validation function name
    
    def validate(self, value: Any) -> bool:
        """Validate parameter value"""
        # Basic type validation (simplified)
        if self.required and value is None:
            return False
        
        # Additional validation logic would go here
        return True


@dataclass 
class ActionDefinition:
    """Complete definition of an action type"""
    action_id: str
    name: str
    description: str
    category: ActionCategory
    complexity: ActionComplexity
    
    # Execution details
    tool_requirements: List[str]  # Required tools
    parameters: List[ActionParameter]
    estimated_duration: timedelta
    
    # Behavioral hints
    typical_contexts: List[str]  # When this action is commonly used
    success_patterns: List[str]  # What makes this action successful
    failure_patterns: List[str]  # Common failure modes
    
    # Memory integration
    memory_importance: float = 0.7  # How important to remember (0-1)
    learns_from_outcomes: bool = True
    creates_follow_up_actions: bool = False
    
    # Optimization
    can_be_batched: bool = False  # Can multiple instances be batched
    can_be_scheduled: bool = True
    requires_human_confirmation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'action_id': self.action_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'complexity': self.complexity.value,
            'tool_requirements': self.tool_requirements,
            'parameters': [
                {
                    'name': p.name,
                    'type_hint': p.type_hint,
                    'description': p.description,
                    'required': p.required,
                    'default_value': p.default_value
                }
                for p in self.parameters
            ],
            'estimated_duration': self.estimated_duration.total_seconds(),
            'typical_contexts': self.typical_contexts,
            'success_patterns': self.success_patterns,
            'failure_patterns': self.failure_patterns,
            'memory_importance': self.memory_importance,
            'learns_from_outcomes': self.learns_from_outcomes
        }


@dataclass
class UniversalActionPlan:
    """
    Enhanced ActionPlan that works across all domains and tools.
    
    This extends the basic ActionPlan with:
    - Rich action definitions
    - Memory-aware optimization
    - Cross-domain orchestration
    - Learning integration
    """
    
    # Core identification
    plan_id: str
    action_definition: ActionDefinition
    
    # Request context
    original_request: str
    request_context: Dict[str, Any]
    
    # Execution parameters
    parameters: Dict[str, Any]  # Actual parameter values
    urgency: ActionUrgency = ActionUrgency.NORMAL
    complexity_override: Optional[ActionComplexity] = None
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Memory integration
    memory_context: List[str] = field(default_factory=list)  # Relevant memory IDs
    lessons_to_apply: List[str] = field(default_factory=list)
    expected_learning: str = ""  # What we expect to learn
    
    # Dependencies and workflow
    prerequisite_actions: List[str] = field(default_factory=list)  # Action IDs that must complete first
    follow_up_actions: List[str] = field(default_factory=list)     # Actions to trigger after
    parent_workflow: Optional[str] = None  # If part of larger workflow
    
    # Execution tracking
    status: str = "planned"  # planned, validated, executing, completed, failed
    execution_attempts: int = 0
    last_attempt: Optional[datetime] = None
    
    # Results and learning
    actual_duration: Optional[timedelta] = None
    satisfaction_score: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
    outcome_summary: str = ""
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "digital_twin"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and transmission"""
        return {
            'plan_id': self.plan_id,
            'action_definition': self.action_definition.to_dict(),
            'original_request': self.original_request,
            'request_context': self.request_context,
            'parameters': self.parameters,
            'urgency': self.urgency.value,
            'complexity_override': self.complexity_override.value if self.complexity_override else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'memory_context': self.memory_context,
            'lessons_to_apply': self.lessons_to_apply,
            'expected_learning': self.expected_learning,
            'prerequisite_actions': self.prerequisite_actions,
            'follow_up_actions': self.follow_up_actions,
            'status': self.status,
            'execution_attempts': self.execution_attempts,
            'satisfaction_score': self.satisfaction_score,
            'lessons_learned': self.lessons_learned,
            'outcome_summary': self.outcome_summary,
            'created_at': self.created_at.isoformat()
        }
    
    def get_complexity(self) -> ActionComplexity:
        """Get effective complexity (override or definition)"""
        return self.complexity_override or self.action_definition.complexity
    
    def is_ready_to_execute(self) -> bool:
        """Check if all prerequisites are met"""
        if self.prerequisite_actions:
            # Would need to check if prerequisite actions are completed
            # For now, assume they're ready
            pass
        
        if self.scheduled_time and self.scheduled_time > datetime.now():
            return False
        
        return self.status == "validated"
    
    def estimate_completion_time(self) -> datetime:
        """Estimate when this action will complete"""
        base_duration = self.action_definition.estimated_duration
        
        # Adjust based on complexity and urgency
        if self.get_complexity() == ActionComplexity.COMPLEX:
            base_duration *= 1.5
        elif self.get_complexity() == ActionComplexity.WORKFLOW:
            base_duration *= 2.0
        
        if self.urgency == ActionUrgency.URGENT:
            base_duration *= 0.8  # Faster execution under urgency
        
        start_time = self.scheduled_time or datetime.now()
        return start_time + base_duration


class UniversalActionRegistry:
    """
    Central registry for all action types and their definitions.
    
    This provides:
    1. Standardized action definitions across all domains
    2. Memory-enhanced action optimization
    3. Cross-tool action orchestration
    4. Learning-based action improvement
    """
    
    def __init__(self):
        self.action_definitions: Dict[str, ActionDefinition] = {}
        self.action_templates: Dict[str, Dict[str, Any]] = {}
        self.success_patterns: Dict[str, List[str]] = {}
        self.failure_patterns: Dict[str, List[str]] = {}
        
        # Performance tracking
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Learning integration
        self.optimization_cache: Dict[str, Any] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize with core action definitions
        self._initialize_core_actions()
    
    def _initialize_core_actions(self):
        """Initialize the registry with core action definitions"""
        
        # Communication Actions
        self.register_action(ActionDefinition(
            action_id="make_phone_call",
            name="Make Phone Call",
            description="Make a phone call to communicate with someone",
            category=ActionCategory.COMMUNICATION,
            complexity=ActionComplexity.SIMPLE,
            tool_requirements=["voice"],
            parameters=[
                ActionParameter("recipient", "str", "Phone number or contact name", required=True),
                ActionParameter("message_type", "str", "Type of message to deliver", required=False, default_value="general"),
                ActionParameter("callback_time", "datetime", "When to make the call", required=False)
            ],
            estimated_duration=timedelta(minutes=5),
            typical_contexts=["reminder", "update", "notification", "urgent_communication"],
            success_patterns=["clear message delivery", "recipient available", "message understood"],
            failure_patterns=["recipient unavailable", "technical issues", "unclear message"],
            memory_importance=0.8,
            learns_from_outcomes=True
        ))
        
        self.register_action(ActionDefinition(
            action_id="send_email",
            name="Send Email",
            description="Send an email message",
            category=ActionCategory.COMMUNICATION,
            complexity=ActionComplexity.SIMPLE,
            tool_requirements=["gmail"],
            parameters=[
                ActionParameter("recipient", "str", "Email address", required=True),
                ActionParameter("subject", "str", "Email subject", required=True),
                ActionParameter("body", "str", "Email content", required=True),
                ActionParameter("attachments", "list", "File attachments", required=False)
            ],
            estimated_duration=timedelta(minutes=2),
            typical_contexts=["formal_communication", "document_sharing", "updates", "requests"],
            success_patterns=["clear subject line", "structured content", "appropriate tone"],
            failure_patterns=["unclear subject", "missing information", "wrong recipient"],
            memory_importance=0.7
        ))
        
        # Scheduling Actions
        self.register_action(ActionDefinition(
            action_id="create_calendar_event",
            name="Create Calendar Event",
            description="Create a new calendar event or meeting",
            category=ActionCategory.SCHEDULING,
            complexity=ActionComplexity.MODERATE,
            tool_requirements=["calendar"],
            parameters=[
                ActionParameter("title", "str", "Event title", required=True),
                ActionParameter("start_time", "datetime", "Event start time", required=True),
                ActionParameter("duration", "timedelta", "Event duration", required=True),
                ActionParameter("attendees", "list", "List of attendees", required=False),
                ActionParameter("location", "str", "Event location", required=False),
                ActionParameter("description", "str", "Event description", required=False)
            ],
            estimated_duration=timedelta(minutes=3),
            typical_contexts=["meeting_scheduling", "appointment_booking", "reminder_setting"],
            success_patterns=["clear title", "appropriate time", "relevant attendees"],
            failure_patterns=["scheduling conflicts", "missing attendees", "unclear purpose"],
            creates_follow_up_actions=True  # Might create reminder actions
        ))
        
        # Task Management Actions
        self.register_action(ActionDefinition(
            action_id="create_task",
            name="Create Task",
            description="Create a new task or todo item",
            category=ActionCategory.TASK_MANAGEMENT,
            complexity=ActionComplexity.SIMPLE,
            tool_requirements=["task_manager"],
            parameters=[
                ActionParameter("title", "str", "Task title", required=True),
                ActionParameter("description", "str", "Task description", required=False),
                ActionParameter("priority", "str", "Task priority (low/medium/high)", required=False, default_value="medium"),
                ActionParameter("deadline", "datetime", "Task deadline", required=False),
                ActionParameter("project", "str", "Associated project", required=False)
            ],
            estimated_duration=timedelta(minutes=1),
            typical_contexts=["task_planning", "reminder_creation", "project_management"],
            success_patterns=["clear title", "appropriate priority", "realistic deadline"],
            failure_patterns=["vague description", "unrealistic deadline", "missing context"]
        ))
        
        # Research Actions
        self.register_action(ActionDefinition(
            action_id="web_research",
            name="Web Research",
            description="Research information on the web",
            category=ActionCategory.RESEARCH,
            complexity=ActionComplexity.MODERATE,
            tool_requirements=["web_browser"],
            parameters=[
                ActionParameter("query", "str", "Search query", required=True),
                ActionParameter("focus_area", "str", "Specific area to focus on", required=False),
                ActionParameter("depth", "str", "Research depth (quick/thorough)", required=False, default_value="quick"),
                ActionParameter("sources", "list", "Preferred sources", required=False)
            ],
            estimated_duration=timedelta(minutes=10),
            typical_contexts=["information_gathering", "fact_checking", "planning_support"],
            success_patterns=["specific queries", "reliable sources", "comprehensive results"],
            failure_patterns=["vague queries", "unreliable sources", "information overload"],
            can_be_batched=True  # Multiple research queries can be batched
        ))
        
        # System Actions
        self.register_action(ActionDefinition(
            action_id="system_backup",
            name="System Backup",
            description="Backup digital twin system state",
            category=ActionCategory.SYSTEM,
            complexity=ActionComplexity.COMPLEX,
            tool_requirements=["system"],
            parameters=[
                ActionParameter("backup_type", "str", "Type of backup (full/incremental)", required=False, default_value="incremental"),
                ActionParameter("location", "str", "Backup location", required=False),
                ActionParameter("encryption", "bool", "Encrypt backup", required=False, default_value=True)
            ],
            estimated_duration=timedelta(minutes=15),
            typical_contexts=["maintenance", "data_protection", "system_updates"],
            success_patterns=["regular_schedule", "verified_backup", "secure_storage"],
            failure_patterns=["corrupted_backup", "insufficient_space", "access_denied"],
            memory_importance=0.9,
            requires_human_confirmation=True
        ))
        
        self.logger.info(f"Initialized action registry with {len(self.action_definitions)} core actions")
    
    def register_action(self, action_def: ActionDefinition):
        """Register a new action definition"""
        self.action_definitions[action_def.action_id] = action_def
        
        # Initialize tracking
        self.execution_stats[action_def.action_id] = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_duration": action_def.estimated_duration.total_seconds(),
            "success_rate": 0.0,
            "last_executed": None
        }
        
        self.logger.info(f"Registered action: {action_def.name} ({action_def.action_id})")
    
    def get_action_definition(self, action_id: str) -> Optional[ActionDefinition]:
        """Get action definition by ID"""
        return self.action_definitions.get(action_id)
    
    def find_actions_by_category(self, category: ActionCategory) -> List[ActionDefinition]:
        """Find all actions in a category"""
        return [
            action_def for action_def in self.action_definitions.values()
            if action_def.category == category
        ]
    
    def find_actions_by_context(self, context: str) -> List[ActionDefinition]:
        """Find actions suitable for a given context"""
        matching_actions = []
        
        for action_def in self.action_definitions.values():
            if any(context.lower() in typical_context.lower() 
                   for typical_context in action_def.typical_contexts):
                matching_actions.append(action_def)
        
        return matching_actions
    
    def create_action_plan(self,
                          action_id: str,
                          original_request: str,
                          parameters: Dict[str, Any],
                          context: Dict[str, Any] = None,
                          urgency: ActionUrgency = ActionUrgency.NORMAL,
                          memory_context: List[str] = None) -> Optional[UniversalActionPlan]:
        """Create a new action plan"""
        
        action_def = self.get_action_definition(action_id)
        if not action_def:
            self.logger.error(f"Unknown action ID: {action_id}")
            return None
        
        # Validate parameters
        validation_errors = self._validate_parameters(action_def, parameters)
        if validation_errors:
            self.logger.error(f"Parameter validation failed: {validation_errors}")
            return None
        
        import uuid
        plan_id = str(uuid.uuid4())
        
        plan = UniversalActionPlan(
            plan_id=plan_id,
            action_definition=action_def,
            original_request=original_request,
            request_context=context or {},
            parameters=parameters,
            urgency=urgency,
            memory_context=memory_context or [],
            status="planned"
        )
        
        # Apply memory-based optimizations
        self._apply_memory_optimizations(plan)
        
        # Set estimated completion
        plan.estimated_completion = plan.estimate_completion_time()
        
        self.logger.info(f"Created action plan: {action_def.name} ({plan_id})")
        
        return plan
    
    def _validate_parameters(self, action_def: ActionDefinition, parameters: Dict[str, Any]) -> List[str]:
        """Validate action parameters"""
        errors = []
        
        for param_def in action_def.parameters:
            param_value = parameters.get(param_def.name)
            
            if param_def.required and param_value is None:
                errors.append(f"Required parameter '{param_def.name}' is missing")
            
            if param_value is not None and not param_def.validate(param_value):
                errors.append(f"Parameter '{param_def.name}' validation failed")
        
        return errors
    
    def _apply_memory_optimizations(self, plan: UniversalActionPlan):
        """Apply memory-based optimizations to action plan"""
        
        action_id = plan.action_definition.action_id
        
        # Apply successful patterns from memory
        if action_id in self.success_patterns:
            plan.lessons_to_apply.extend(self.success_patterns[action_id])
        
        # Adjust based on historical performance
        if action_id in self.execution_stats:
            stats = self.execution_stats[action_id]
            
            # Adjust estimated duration based on actual performance
            if stats["total_executions"] > 5:
                historical_duration = timedelta(seconds=stats["average_duration"])
                plan.action_definition.estimated_duration = historical_duration
        
        # Set expected learning based on action definition
        if plan.action_definition.learns_from_outcomes:
            plan.expected_learning = f"Optimize {plan.action_definition.name} execution patterns"
    
    def update_execution_stats(self, 
                              action_id: str, 
                              success: bool, 
                              duration: timedelta,
                              satisfaction: float = None):
        """Update execution statistics for learning"""
        
        if action_id not in self.execution_stats:
            return
        
        stats = self.execution_stats[action_id]
        
        # Update counts
        stats["total_executions"] += 1
        if success:
            stats["successful_executions"] += 1
        
        # Update success rate
        stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        
        # Update average duration (weighted average)
        current_avg = stats["average_duration"]
        new_duration = duration.total_seconds()
        
        # Use exponential moving average
        alpha = 0.2  # Learning rate
        stats["average_duration"] = alpha * new_duration + (1 - alpha) * current_avg
        
        stats["last_executed"] = datetime.now().isoformat()
        
        self.logger.info(f"Updated stats for {action_id}: success_rate={stats['success_rate']:.2f}")
    
    def get_recommended_actions(self, 
                               context: str, 
                               category: ActionCategory = None,
                               max_complexity: ActionComplexity = None) -> List[ActionDefinition]:
        """Get recommended actions for a context"""
        
        # Start with context-based matches
        recommended = self.find_actions_by_context(context)
        
        # Filter by category if specified
        if category:
            recommended = [a for a in recommended if a.category == category]
        
        # Filter by complexity if specified
        if max_complexity:
            complexity_order = [ActionComplexity.SIMPLE, ActionComplexity.MODERATE, 
                              ActionComplexity.COMPLEX, ActionComplexity.WORKFLOW]
            max_level = complexity_order.index(max_complexity)
            recommended = [a for a in recommended 
                          if complexity_order.index(a.complexity) <= max_level]
        
        # Sort by success rate and memory importance
        def score_action(action_def):
            stats = self.execution_stats.get(action_def.action_id, {})
            success_rate = stats.get("success_rate", 0.5)  # Default neutral
            memory_importance = action_def.memory_importance
            
            return success_rate * 0.7 + memory_importance * 0.3
        
        recommended.sort(key=score_action, reverse=True)
        
        return recommended[:5]  # Top 5 recommendations
    
    def export_registry(self, filepath: str = None) -> str:
        """Export the complete action registry"""
        
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"action_registry_export_{timestamp}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "action_definitions": {
                action_id: action_def.to_dict()
                for action_id, action_def in self.action_definitions.items()
            },
            "execution_stats": self.execution_stats,
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported action registry to {filepath}")
        
        return filepath
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        
        total_actions = len(self.action_definitions)
        categories = {}
        complexities = {}
        
        for action_def in self.action_definitions.values():
            # Count by category
            cat = action_def.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            # Count by complexity
            comp = action_def.complexity.value
            complexities[comp] = complexities.get(comp, 0) + 1
        
        # Calculate overall success rate
        total_executions = sum(stats["total_executions"] for stats in self.execution_stats.values())
        total_successes = sum(stats["successful_executions"] for stats in self.execution_stats.values())
        overall_success_rate = total_successes / max(1, total_executions)
        
        return {
            "total_actions": total_actions,
            "categories": categories,
            "complexities": complexities,
            "execution_stats": {
                "total_executions": total_executions,
                "overall_success_rate": overall_success_rate,
                "most_used_actions": sorted(
                    [(aid, stats["total_executions"]) for aid, stats in self.execution_stats.items()],
                    key=lambda x: x[1], reverse=True
                )[:5]
            }
        }


# Global registry instance
global_action_registry = UniversalActionRegistry()