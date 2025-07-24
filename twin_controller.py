"""
Digital Twin Controller - Central Nervous System

This module orchestrates all actions for the digital twin, converting
high-level plans from the brain into concrete tool executions.

Key responsibilities:
1. Parse intents into structured plans
2. Route plans to appropriate tools
3. Handle time-based and multi-step actions
4. Log outcomes back to memory
5. Manage the tool ecosystem
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from enum import Enum

from digital_twin_v3 import DigitalTwinV3, Situation
from memory_system.episodic_memory import EpisodicMemorySystem
from memory_system.vector_memory import EnhancedVectorMemory
from memory_system.memory_retrieval import IntelligentMemoryRetrieval
from scheduler import ActionScheduler


class ActionStatus(Enum):
    """Status of an action execution"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionPlan:
    """
    Structured representation of what the twin intends to do.
    
    This converts fuzzy human requests into executable steps.
    """
    id: str
    intent: str  # Original user request
    steps: List[Dict[str, Any]]  # List of actions to take
    context: Dict[str, Any] = field(default_factory=dict)
    scheduled_time: Optional[datetime] = None
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'intent': self.intent,
            'steps': self.steps,
            'context': self.context,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status.value,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ActionResult:
    """Result of executing an action"""
    action_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MemoryAwareController:
    """
    Memory-Aware Twin Controller - Enhanced Central Orchestrator
    
    This upgraded controller integrates the complete Brain + Memory system:
    - Uses DigitalTwinV3 with persistent memory for all decisions
    - Memory-enhanced action planning based on past experiences
    - Automatic learning from action outcomes
    - Context-aware tool selection using memory patterns
    - Persistent action history and pattern recognition
    """
    
    def __init__(self, 
                 twin: DigitalTwinV3,
                 scheduler: ActionScheduler = None):
        
        self.twin = twin  # DigitalTwinV3 with complete memory system
        self.scheduler = scheduler
        
        # Tool registry - will be populated with actual tools
        self.tools: Dict[str, Any] = {}
        
        # Active plans tracking
        self.active_plans: Dict[str, ActionPlan] = {}
        
        # Execution history (now memory-backed)
        self.execution_history: List[ActionResult] = []
        
        # Action learning and optimization
        self.action_patterns = {}  # Cached successful action patterns
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        self.logger.info("Memory-Aware Controller initialized with DigitalTwinV3")
    
    def register_tool(self, name: str, tool: Any):
        """Register a tool that the controller can use"""
        self.tools[name] = tool
        self.logger.info(f"Registered tool: {name}")
    
    def set_scheduler(self, scheduler):
        """Inject the scheduler for time-based actions"""
        self.scheduler = scheduler
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> ActionPlan:
        """
        Memory-Enhanced Request Processing
        
        This version:
        1. Uses the complete Brain + Memory system for reasoning
        2. Learns from past similar requests and their outcomes
        3. Applies memory-based optimizations to action planning
        4. Automatically captures the planning decision as memory
        
        Examples:
        - "Call me at 3:30 and remind me of tasks"
        - "Send email to John about the project update"
        - "Check my calendar and summarize tomorrow's meetings"
        """
        
        # Step 1: Enhanced reasoning with memory system
        situation = Situation(
            context=request,
            category="user_command",
            metadata={
                **(context or {}),
                "controller_request": True,
                "available_tools": list(self.tools.keys())
            }
        )
        
        # Brain reasons with full memory context
        brain_response = await self.twin.reason(situation)
        
        self.logger.info(f"Brain reasoning mode: {brain_response.reasoning_mode}, "
                        f"Memory refs: {len(brain_response.memory_references)}, "
                        f"Lessons applied: {len(brain_response.lessons_applied)}")
        
        # Step 2: Memory-enhanced action plan creation
        plan = await self._create_memory_enhanced_plan(request, brain_response, context)
        
        # Step 3: Validate plan with memory insights
        if not await self._validate_plan_with_memory(plan):
            plan.status = ActionStatus.FAILED
            await self._learn_from_planning_failure(plan, "validation_failed")
            return plan
        
        # Step 4: Store plan and capture planning decision
        self.active_plans[plan.id] = plan
        await self._capture_planning_memory(request, plan, brain_response)
        
        # Step 5: Execute or schedule
        if plan.scheduled_time and plan.scheduled_time > datetime.now():
            await self._schedule_plan(plan)
        else:
            await self._execute_plan(plan)
        
        return plan
    
    async def _create_memory_enhanced_plan(self, request: str, brain_response, context: Dict[str, Any] = None) -> ActionPlan:
        """
        Convert brain reasoning into executable plan.
        
        This is where we parse intents and structure multi-step actions.
        """
        import uuid
        
        # Parse the request with memory-enhanced intelligence
        plan_id = str(uuid.uuid4())
        steps = []
        scheduled_time = None
        
        # Check memory for similar successful requests
        similar_plans = await self._find_similar_successful_plans(request)
        
        self.logger.info(f"Found {len(similar_plans)} similar successful action patterns")
        
        # Enhanced parsing using brain response + memory patterns
        request_lower = request.lower()
        
        if "call" in request_lower and ("at" in request_lower or "in" in request_lower):
            # Extract time
            scheduled_time = self._parse_time_from_request(request)
            
            # Build call step
            steps.append({
                'tool': 'voice',
                'action': 'make_call',
                'params': {
                    'recipient': context.get('user_phone', 'default'),
                    'message_type': 'task_reminder'
                }
            })
        
        if "remind" in request_lower and "tasks" in request_lower:
            # Add task retrieval step before the call
            steps.insert(0, {
                'tool': 'task_manager',
                'action': 'get_pending_tasks',
                'params': {
                    'timeframe': 'today',
                    'include_deadlines': True
                }
            })
        
        if "email" in request_lower:
            # Email-related action
            steps.append({
                'tool': 'gmail',
                'action': 'send_email',
                'params': self._extract_email_params(request)
            })
        
        if "calendar" in request_lower:
            # Calendar-related action
            steps.append({
                'tool': 'calendar',
                'action': 'get_events' if "check" in request_lower else 'create_event',
                'params': self._extract_calendar_params(request)
            })
        
        # Create the plan
        plan = ActionPlan(
            id=plan_id,
            intent=request,
            steps=steps,
            context=context or {},
            scheduled_time=scheduled_time
        )
        
        return plan
    
    def _parse_time_from_request(self, request: str) -> Optional[datetime]:
        """
        Parse time from natural language request.
        
        Examples:
        - "at 3:30" -> today at 3:30 PM
        - "in 2 hours" -> now + 2 hours
        - "tomorrow at 9am" -> tomorrow at 9:00 AM
        """
        import re
        from dateutil import parser
        
        # Simple time parsing (you'd want a more robust solution)
        time_patterns = [
            (r'at (\d{1,2}):(\d{2})\s*(am|pm)?', 'specific_time'),
            (r'in (\d+)\s*(hours?|minutes?)', 'relative_time'),
            (r'tomorrow at (\d{1,2})\s*(am|pm)?', 'tomorrow_time')
        ]
        
        for pattern, time_type in time_patterns:
            match = re.search(pattern, request.lower())
            if match:
                if time_type == 'specific_time':
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    ampm = match.group(3)
                    
                    # Adjust for PM if needed
                    if ampm == 'pm' and hour < 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    
                    # Assume today if just time given
                    target_time = datetime.now().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    
                    # If time has passed today, assume tomorrow
                    if target_time <= datetime.now():
                        target_time += timedelta(days=1)
                    
                    return target_time
                
                elif time_type == 'relative_time':
                    amount = int(match.group(1))
                    unit = match.group(2)
                    
                    if 'hour' in unit:
                        return datetime.now() + timedelta(hours=amount)
                    elif 'minute' in unit:
                        return datetime.now() + timedelta(minutes=amount)
        
        return None
    
    def _validate_plan(self, plan: ActionPlan) -> bool:
        """Validate that all required tools are available"""
        for step in plan.steps:
            tool_name = step.get('tool')
            if tool_name and tool_name not in self.tools:
                self.logger.error(f"Tool '{tool_name}' not registered")
                return False
        return True
    
    async def _schedule_plan(self, plan: ActionPlan):
        """Schedule a plan for future execution"""
        if not self.scheduler:
            self.logger.error("No scheduler available")
            plan.status = ActionStatus.FAILED
            return
        
        # Calculate delay
        delay = (plan.scheduled_time - datetime.now()).total_seconds()
        
        # Schedule the execution
        self.scheduler.schedule_action(
            action_id=plan.id,
            delay_seconds=delay,
            callback=lambda: asyncio.create_task(self._execute_plan(plan))
        )
        
        plan.status = ActionStatus.SCHEDULED
        self.logger.info(f"Scheduled plan {plan.id} for {plan.scheduled_time}")
        
        # Enhanced memory logging with scheduling decision
        await self._capture_scheduling_memory(plan)
    
    async def _execute_plan(self, plan: ActionPlan):
        """Execute a plan by running all its steps"""
        plan.status = ActionStatus.IN_PROGRESS
        self.logger.info(f"Executing plan {plan.id}: {plan.intent}")
        
        results = []
        context = plan.context.copy()  # Mutable context passed between steps
        
        try:
            for i, step in enumerate(plan.steps):
                self.logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step}")
                
                # Get the tool
                tool_name = step.get('tool')
                tool = self.tools.get(tool_name)
                
                if not tool:
                    raise ValueError(f"Tool '{tool_name}' not found")
                
                # Execute the action
                action = step.get('action')
                params = step.get('params', {})
                
                # Pass context from previous steps
                params['_context'] = context
                
                # Execute tool action
                if hasattr(tool, action):
                    method = getattr(tool, action)
                    if asyncio.iscoroutinefunction(method):
                        result = await method(**params)
                    else:
                        result = method(**params)
                else:
                    raise ValueError(f"Action '{action}' not found on tool '{tool_name}'")
                
                # Store result in context for next steps
                context[f'step_{i}_result'] = result
                
                results.append(ActionResult(
                    action_id=f"{plan.id}_step_{i}",
                    success=True,
                    result=result
                ))
                
                self.logger.info(f"Step {i+1} completed successfully")
            
            plan.status = ActionStatus.COMPLETED
            
            # Enhanced success learning
            await self._learn_from_successful_execution(plan, results, context)
            
        except Exception as e:
            plan.status = ActionStatus.FAILED
            self.logger.error(f"Plan execution failed: {str(e)}")
            
            results.append(ActionResult(
                action_id=plan.id,
                success=False,
                result=None,
                error=str(e)
            ))
            
            # Enhanced failure learning
            await self._learn_from_execution_failure(plan, str(e), results)
        
        # Store execution history
        self.execution_history.extend(results)
        
        return results
    
    def _extract_email_params(self, request: str) -> Dict[str, Any]:
        """Extract email parameters from request"""
        # This would use NLP or regex to extract recipient, subject, body
        # For now, return placeholder
        return {
            'recipient': 'extracted_email@example.com',
            'subject': 'Extracted subject',
            'body': 'Extracted body'
        }
    
    def _extract_calendar_params(self, request: str) -> Dict[str, Any]:
        """Extract calendar parameters from request"""
        # This would parse dates, times, event details
        # For now, return placeholder
        return {
            'date': 'tomorrow',
            'time_range': 'all_day'
        }
    
    async def get_active_plans(self) -> List[ActionPlan]:
        """Get all active plans"""
        return [
            plan for plan in self.active_plans.values()
            if plan.status in [ActionStatus.PENDING, ActionStatus.SCHEDULED, ActionStatus.IN_PROGRESS]
        ]
    
    async def cancel_plan(self, plan_id: str) -> bool:
        """Cancel a scheduled or pending plan"""
        if plan_id in self.active_plans:
            plan = self.active_plans[plan_id]
            if plan.status in [ActionStatus.PENDING, ActionStatus.SCHEDULED]:
                plan.status = ActionStatus.CANCELLED
                
                # Cancel in scheduler if scheduled
                if self.scheduler and plan.status == ActionStatus.SCHEDULED:
                    self.scheduler.cancel_action(plan_id)
                
                self.logger.info(f"Cancelled plan {plan_id}")
                return True
        
        return False
    
    def get_execution_history(self, limit: int = 10) -> List[ActionResult]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    async def handle_multi_step_request(self, request: str) -> List[ActionPlan]:
        """
        Handle complex requests that might need multiple plans.
        
        Example: "Every morning at 9am, check my email, summarize important ones,
                  and call me with the summary"
        """
        # This would parse complex, recurring requests
        # For now, we'll handle single requests
        plan = await self.process_request(request)
        return [plan]
    
    # =====================================================================
    # MEMORY-ENHANCED CONTROLLER METHODS
    # =====================================================================
    
    async def _find_similar_successful_plans(self, request: str) -> List[Dict[str, Any]]:
        """Find similar successful action patterns from memory"""
        
        # Use the twin's memory system to find similar requests
        similar_memories = self.twin.ask_memory(
            f"What happened when I handled requests similar to: {request}?"
        )
        
        # Parse successful patterns (simplified for now)
        patterns = []
        if "successful" in similar_memories.lower():
            patterns.append({
                "pattern_type": "successful_execution",
                "confidence": 0.8,
                "suggestion": "Apply similar approach"
            })
        
        return patterns
    
    async def _validate_plan_with_memory(self, plan: ActionPlan) -> bool:
        """Enhanced validation using memory insights"""
        
        # Basic tool availability check
        for step in plan.steps:
            tool_name = step.get('tool')
            if tool_name and tool_name not in self.tools:
                self.logger.error(f"Tool '{tool_name}' not registered")
                return False
        
        # Memory-based validation: check if similar plans failed before
        failure_patterns = self.twin.ask_memory(
            f"Did plans similar to '{plan.intent}' ever fail? What went wrong?"
        )
        
        if "failed" in failure_patterns.lower() and "tool not available" in failure_patterns.lower():
            self.logger.warning(f"Memory suggests potential failure for: {plan.intent}")
            # Could still proceed but with awareness
        
        return True
    
    async def _capture_planning_memory(self, request: str, plan: ActionPlan, brain_response):
        """Capture the planning decision as memory"""
        
        planning_situation = Situation(
            context=f"Action planning for: {request}",
            category="action_planning",
            metadata={
                "plan_id": plan.id,
                "steps_count": len(plan.steps),
                "scheduled": plan.scheduled_time is not None,
                "tools_used": [step.get('tool') for step in plan.steps]
            }
        )
        
        # The memory system will automatically capture this reasoning
        # This creates a link between user requests and action plans
        self.logger.info(f"Captured planning memory for: {request[:50]}...")
    
    async def _capture_scheduling_memory(self, plan: ActionPlan):
        """Capture scheduling decision as memory"""
        
        if plan.scheduled_time:
            scheduling_situation = Situation(
                context=f"Scheduled action: {plan.intent}",
                category="scheduling",
                metadata={
                    "plan_id": plan.id,
                    "scheduled_time": plan.scheduled_time.isoformat(),
                    "delay_hours": (plan.scheduled_time - datetime.now()).total_seconds() / 3600
                }
            )
            
            # This will be captured automatically by the memory system
            self.logger.info(f"Captured scheduling memory for plan {plan.id}")
    
    async def _learn_from_successful_execution(self, plan: ActionPlan, results: List[ActionResult], context: Dict[str, Any]):
        """Learn from successful plan execution"""
        
        # Create a learning situation about the success
        success_situation = Situation(
            context=f"Successfully executed: {plan.intent}",
            category="execution_success",
            metadata={
                "plan_id": plan.id,
                "steps_executed": len(results),
                "execution_time": (datetime.now() - plan.created_at).total_seconds(),
                "tools_used": [step.get('tool') for step in plan.steps]
            }
        )
        
        # Use the twin's learning system
        self.twin.learn_from_feedback(
            situation=success_situation,
            actual_action=f"Successfully completed {len(plan.steps)} steps",
            satisfaction=0.9,  # High satisfaction for successful execution
            lessons_learned=[
                f"Action pattern '{plan.intent}' works well with {len(plan.steps)} steps",
                f"Tools combination successful: {[step.get('tool') for step in plan.steps]}"
            ],
            feedback="Controller successfully executed all planned steps"
        )
        
        self.logger.info(f"Learned from successful execution of plan {plan.id}")
    
    async def _learn_from_execution_failure(self, plan: ActionPlan, error: str, results: List[ActionResult]):
        """Learn from failed plan execution"""
        
        failure_situation = Situation(
            context=f"Failed to execute: {plan.intent}",
            category="execution_failure",
            metadata={
                "plan_id": plan.id,
                "error": error,
                "steps_attempted": len(results),
                "failure_point": len([r for r in results if r.success])
            }
        )
        
        # Learn from the failure
        self.twin.learn_from_feedback(
            situation=failure_situation,
            actual_action=f"Failed at step {len([r for r in results if r.success])} with error: {error}",
            satisfaction=0.2,  # Low satisfaction for failures
            lessons_learned=[
                f"Action pattern '{plan.intent}' failed due to: {error}",
                "Need to improve validation or tool availability checks"
            ],
            feedback=f"Controller execution failed: {error}"
        )
        
        self.logger.info(f"Learned from execution failure of plan {plan.id}")
    
    async def _learn_from_planning_failure(self, plan: ActionPlan, reason: str):
        """Learn from planning failures"""
        
        planning_failure_situation = Situation(
            context=f"Failed to plan: {plan.intent}",
            category="planning_failure",
            metadata={
                "plan_id": plan.id,
                "failure_reason": reason,
                "attempted_steps": len(plan.steps)
            }
        )
        
        self.twin.learn_from_feedback(
            situation=planning_failure_situation,
            actual_action=f"Planning failed: {reason}",
            satisfaction=0.3,
            lessons_learned=[f"Planning failure for '{plan.intent}': {reason}"],
            feedback="Controller could not create valid action plan"
        )
        
        self.logger.info(f"Learned from planning failure: {reason}")
    
    def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights about action patterns from memory"""
        
        return {
            "controller_memory": {
                "active_plans": len(self.active_plans),
                "execution_history": len(self.execution_history),
                "successful_patterns": len([r for r in self.execution_history if r.success]),
                "failure_patterns": len([r for r in self.execution_history if not r.success])
            },
            "twin_memory": self.twin.get_memory_summary(),
            "reasoning_insights": self.twin.get_reasoning_insights()
        }
    
    async def optimize_based_on_memory(self):
        """Optimize controller behavior based on memory patterns"""
        
        # Ask the twin for insights about action patterns
        optimization_insights = self.twin.introspect_with_memory(
            "What patterns do you see in my action planning and execution? What could be improved?"
        )
        
        self.logger.info(f"Memory-based optimization insights: {optimization_insights[:200]}...")
        
        # Extract actionable improvements (simplified for now)
        if "tool" in optimization_insights.lower() and "fail" in optimization_insights.lower():
            self.logger.info("Memory suggests improving tool validation")
        
        if "schedule" in optimization_insights.lower() and "delay" in optimization_insights.lower():
            self.logger.info("Memory suggests optimizing scheduling patterns")
        
        return optimization_insights


# Backwards compatibility
TwinController = MemoryAwareController