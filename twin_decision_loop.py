"""
Central Twin Decision Loop - Unified Brain + Memory + Controller Integration

This is the central nervous system that orchestrates the complete digital twin:
- Brain: Enhanced reasoning with memory
- Memory: Persistent learning and pattern recognition  
- Controller: Memory-aware action execution
- Scheduler: Time-based action management

The decision loop provides:
1. Unified interface for all twin interactions
2. Seamless integration between reasoning and action
3. Continuous learning from all experiences
4. Memory-enhanced decision making at every step
5. Persistent behavioral evolution

This is the main interface that external systems should use.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from digital_twin_v3 import DigitalTwinV3, Situation, TwinResponse
from twin_controller import MemoryAwareController, ActionPlan, ActionResult
from scheduler import TwinScheduler as ActionScheduler

# Import observer system
try:
    from observer.observer_manager import ObserverManager, CurrentContext
    from observer.observer_utils import ObserverConfig
    OBSERVER_AVAILABLE = True
except ImportError:
    OBSERVER_AVAILABLE = False

# Import goal system
try:
    from goal_system.goal_manager import GoalManager
    from goal_system.strategic_planner import StrategicPlanner
    from goal_system.goal_reasoner import GoalAwareReasoner
    GOAL_SYSTEM_AVAILABLE = True
except ImportError:
    GOAL_SYSTEM_AVAILABLE = False


@dataclass
class TwinRequest:
    """Unified request structure for the digital twin"""
    content: str  # What the user wants
    request_type: str  # "query", "action", "schedule", "introspect"
    context: Dict[str, Any] = None
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    requires_action: bool = True  # Whether this should result in actions
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class TwinResult:
    """Unified result structure from the digital twin"""
    request_id: str
    success: bool
    
    # Reasoning components
    reasoning_response: Optional[TwinResponse] = None
    
    # Action components  
    action_plan: Optional[ActionPlan] = None
    action_results: List[ActionResult] = None
    
    # Meta information
    processing_time: float = 0
    memory_updates: int = 0
    lessons_learned: List[str] = None
    
    # Response content
    response_text: str = ""
    response_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.action_results is None:
            self.action_results = []
        if self.lessons_learned is None:
            self.lessons_learned = []
        if self.response_data is None:
            self.response_data = {}


class UnifiedTwinDecisionLoop:
    """
    The complete digital twin system - Brain + Memory + Controller integrated.
    
    This is the main interface that orchestrates:
    1. Memory-enhanced reasoning for all decisions
    2. Action planning and execution with learning
    3. Continuous memory formation and pattern extraction
    4. Scheduling and time-based behaviors
    5. Self-optimization based on experience
    
    Usage Examples:
        # Simple query
        result = await twin.process("What tasks do I have today?")
        
        # Action request  
        result = await twin.process("Call me at 3pm with task reminders")
        
        # Learning from feedback
        twin.provide_feedback(result.request_id, satisfaction=0.9, lessons=["This worked well"])
        
        # Introspection
        insights = await twin.introspect("How do I usually handle urgent emails?")
    """
    
    def __init__(self,
                 persona_path: str = "persona.yaml",
                 api_key: str = None,
                 memory_dir: str = "twin_memory_system",
                 tools_config: Dict[str, Any] = None,
                 enable_observer: bool = True,
                 enable_goals: bool = True):
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize the core brain with memory
        self.brain = DigitalTwinV3(
            persona_path=persona_path,
            api_key=api_key,
            memory_dir=memory_dir
        )
        
        # Initialize scheduler for time-based actions
        self.scheduler = ActionScheduler()
        
        # Initialize observer system if available and enabled
        self.observer_manager = None
        self.current_context = None
        
        if OBSERVER_AVAILABLE and enable_observer:
            try:
                observer_config = ObserverConfig()
                self.observer_manager = ObserverManager(
                    config=observer_config,
                    memory_interface=self.brain.memory_interface
                )
                
                # Set up observer callbacks
                self.observer_manager.add_context_callback(self._handle_context_update)
                self.observer_manager.add_observation_callback(self._handle_new_observation)
                
                self.logger.info("Observer system initialized and connected to memory")
            except Exception as e:
                self.logger.error(f"Failed to initialize observer system: {e}")
                self.observer_manager = None
        
        # Initialize goal system if available and enabled
        self.goal_manager = None
        self.strategic_planner = None
        self.goal_reasoner = None
        
        if GOAL_SYSTEM_AVAILABLE and enable_goals:
            try:
                # Create goal data directory
                goal_data_dir = Path(memory_dir) / "goal_data"
                goal_data_dir.mkdir(exist_ok=True)
                
                self.goal_manager = GoalManager(
                    storage_dir=str(goal_data_dir),
                    ai_interface=self.brain
                )
                
                self.strategic_planner = StrategicPlanner(
                    goal_manager=self.goal_manager,
                    observer_manager=self.observer_manager
                )
                
                self.goal_reasoner = GoalAwareReasoner(
                    goal_manager=self.goal_manager,
                    strategic_planner=self.strategic_planner
                )
                
                self.logger.info("Goal-aware agent system initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize goal system: {e}")
                self.goal_manager = None
        
        # Initialize memory-aware controller
        self.controller = MemoryAwareController(
            twin=self.brain,
            scheduler=self.scheduler
        )
        
        # Register tools if provided
        if tools_config:
            self._register_tools(tools_config)
        
        # Request tracking
        self.active_requests: Dict[str, TwinRequest] = {}
        self.request_history: List[TwinResult] = []
        
        # Performance and learning metrics
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "memory_formations": 0,
            "patterns_learned": 0
        }
        
        # Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        self.logger.info("🧠 Unified Twin Decision Loop initialized successfully")
        self.logger.info(f"   Brain: DigitalTwinV3 with persistent memory")
        self.logger.info(f"   Controller: Memory-aware action orchestration")
        self.logger.info(f"   Scheduler: Time-based action management")
        self.logger.info(f"   Observer: {'Enabled' if self.observer_manager else 'Disabled'}")
        self.logger.info(f"   Memory: {memory_dir}")
    
    def _handle_context_update(self, context: 'CurrentContext'):
        """Handle context updates from observer system"""
        
        self.current_context = context
        self.logger.debug(f"Context updated: {context.current_app} - {context.productivity_state}")
        
        # Store significant context changes in memory if needed
        if context.productivity_state in ['focused', 'distracted'] and self.brain.memory_updater:
            try:
                context_memory = {
                    'context_type': 'activity_context',
                    'current_state': context.productivity_state,
                    'current_app': context.current_app,
                    'activity_category': context.activity_category.value,
                    'session_duration': context.current_session_duration_minutes,
                    'summary': context.recent_activity_summary,
                    'timestamp': context.timestamp.isoformat()
                }
                
                # This would be stored as contextual information for future decisions
                self.brain.memory_updater.vector_memory.add_memory(
                    content=f"Current activity context: {context.recent_activity_summary}",
                    memory_type=self.brain.memory_updater.vector_memory.VectorMemoryType.DECISION_CONTEXT,
                    metadata=context_memory,
                    tags=['context', 'real_time', context.productivity_state]
                )
                
            except Exception as e:
                self.logger.error(f"Error storing context in memory: {e}")
    
    def _handle_new_observation(self, observation):
        """Handle new observations from observer system"""
        
        # Significant observations are automatically stored in memory by the observer manager
        # Here we can add additional logic for real-time behavioral analysis
        
        if observation.category.value in ['productivity', 'development']:
            self.processing_stats['patterns_learned'] += 1
        
        self.logger.debug(f"New observation: {observation.event_type} - {observation.app_name}")
    
    async def start_observer_system(self):
        """Start the observer system for passive behavior learning"""
        
        if not self.observer_manager:
            self.logger.warning("Observer system not available")
            return False
        
        try:
            self.logger.info("Starting observer system...")
            # Start observing in background
            asyncio.create_task(self.observer_manager.start_observing())
            return True
        except Exception as e:
            self.logger.error(f"Failed to start observer system: {e}")
            return False
    
    def stop_observer_system(self):
        """Stop the observer system"""
        
        if self.observer_manager:
            self.observer_manager.stop_observing()
            self.logger.info("Observer system stopped")
    
    def get_current_context(self) -> Optional['CurrentContext']:
        """Get current activity context from observer system"""
        
        if self.observer_manager:
            return self.observer_manager.get_current_context()
        return None
    
    def get_behavioral_insights(self) -> Dict[str, Any]:
        """Get behavioral insights from observer system"""
        
        if self.observer_manager:
            return self.observer_manager.get_insights()
        
        return {'status': 'Observer system not available'}
    
    def _register_tools(self, tools_config: Dict[str, Any]):
        """Register tools based on configuration"""
        
        for tool_name, tool_config in tools_config.items():
            try:
                # Dynamic tool loading based on config
                tool_class = tool_config.get('class')
                tool_params = tool_config.get('params', {})
                
                if tool_class:
                    # Import and instantiate tool
                    module_name, class_name = tool_class.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    tool_instance = getattr(module, class_name)(**tool_params)
                    
                    self.controller.register_tool(tool_name, tool_instance)
                    self.logger.info(f"Registered tool: {tool_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to register tool {tool_name}: {e}")
    
    async def process(self, 
                     content: str,
                     request_type: str = "auto",
                     context: Dict[str, Any] = None,
                     priority: str = "medium") -> TwinResult:
        """
        Main processing function - handles any kind of request.
        
        This is the unified interface that:
        1. Determines the type of request
        2. Routes to appropriate processing (reasoning vs action)
        3. Ensures memory formation for all experiences
        4. Returns unified results
        
        Args:
            content: What the user wants
            request_type: "query", "action", "schedule", "introspect", or "auto"
            context: Additional context
            priority: Request priority
            
        Returns:
            Unified result with reasoning, actions, and learning
        """
        
        import uuid
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Auto-detect request type if needed
        if request_type == "auto":
            request_type = self._detect_request_type(content)
        
        # Create request
        request = TwinRequest(
            content=content,
            request_type=request_type,
            context=context or {},
            priority=priority,
            requires_action=request_type in ["action", "schedule"]
        )
        
        self.active_requests[request_id] = request
        self.processing_stats["total_requests"] += 1
        
        self.logger.info(f"🎯 Processing {request_type} request: {content[:50]}...")
        
        try:
            # Route to appropriate processor
            if request_type == "query":
                result = await self._process_query(request_id, request)
            elif request_type == "action":
                result = await self._process_action(request_id, request)
            elif request_type == "schedule":
                result = await self._process_schedule(request_id, request)
            elif request_type == "introspect":
                result = await self._process_introspection(request_id, request)
            else:
                # Default to reasoning + potential action
                result = await self._process_hybrid(request_id, request)
            
            # Calculate processing time
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update statistics
            if result.success:
                self.processing_stats["successful_requests"] += 1
            else:
                self.processing_stats["failed_requests"] += 1
            
            # Store in history
            self.request_history.append(result)
            
            # Clean up active request
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            self.logger.info(f"✅ Completed {request_type} request in {result.processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Request processing failed: {e}")
            
            # Create failure result
            result = TwinResult(
                request_id=request_id,
                success=False,
                response_text=f"Processing failed: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Learn from the failure
            await self._learn_from_processing_failure(request, str(e))
            
            self.processing_stats["failed_requests"] += 1
            self.request_history.append(result)
            
            return result
    
    def _detect_request_type(self, content: str) -> str:
        """Auto-detect the type of request"""
        
        content_lower = content.lower()
        
        # Action indicators
        action_keywords = ["call me", "send email", "schedule", "remind me", "create", "delete", "execute"]
        if any(keyword in content_lower for keyword in action_keywords):
            return "action"
        
        # Schedule indicators
        schedule_keywords = ["at ", "in ", "tomorrow", "next week", "every", "daily", "weekly"]
        if any(keyword in content_lower for keyword in schedule_keywords):
            return "schedule"
        
        # Introspection indicators
        intro_keywords = ["how do i", "what patterns", "analyze my", "insights about", "why do i"]
        if any(keyword in content_lower for keyword in intro_keywords):
            return "introspect"
        
        # Default to query
        return "query"
    
    async def _process_query(self, request_id: str, request: TwinRequest) -> TwinResult:
        """Process pure reasoning/query requests"""
        
        # Enhance situation with goal context if available
        enhanced_context = request.content
        goal_context = None
        goal_relevance = None
        
        if self.goal_reasoner:
            try:
                goal_context = self.goal_reasoner.get_goal_context(request.content)
                enhanced_prompt = self.goal_reasoner.enhance_reasoning_prompt(
                    request.content, 
                    request.content
                )
                enhanced_context = enhanced_prompt
                goal_relevance = goal_context.goal_relevance
                
                # Capture goal context memory
                if self.brain.memory_updater:
                    self.brain.memory_updater.capture_goal_context_memory(
                        goal_context=goal_context,
                        decision_context=request.content,
                        relevance=goal_relevance
                    )
                
            except Exception as e:
                self.logger.error(f"Error getting goal context: {e}")
        
        situation = Situation(
            context=enhanced_context,
            category="user_query",
            metadata={
                **request.context,
                "request_type": "query",
                "priority": request.priority,
                "goal_context_applied": goal_context is not None,
                "goal_relevance": goal_relevance.value if goal_relevance else None
            }
        )
        
        # Use brain for reasoning
        brain_response = await self.brain.reason(situation)
        
        # Add goal-informed recommendations if relevant
        goal_recommendations = []
        if self.goal_reasoner and goal_relevance:
            goal_recommendations = self.goal_reasoner.get_goal_informed_recommendations(request.content)
        
        # Create result
        result = TwinResult(
            request_id=request_id,
            success=True,
            reasoning_response=brain_response,
            response_text=brain_response.action,  # For queries, action contains the answer
            memory_updates=1,  # Brain automatically captured this as memory
            lessons_learned=brain_response.lessons_applied,
            response_data={
                "goal_aware": goal_context is not None,
                "goal_recommendations": goal_recommendations,
                "goal_relevance": goal_relevance.value if goal_relevance else None
            }
        )
        
        return result
    
    async def _process_action(self, request_id: str, request: TwinRequest) -> TwinResult:
        """Process action requests that require doing something"""
        
        # Use controller for action planning and execution
        action_plan = await self.controller.process_request(
            request=request.content,
            context=request.context
        )
        
        # The controller already used the brain for reasoning and planning
        result = TwinResult(
            request_id=request_id,
            success=action_plan.status.value in ["completed", "scheduled"],
            action_plan=action_plan,
            response_text=f"Action plan created with {len(action_plan.steps)} steps",
            memory_updates=1,  # Controller and brain both captured memories
            response_data={
                "plan_id": action_plan.id,
                "status": action_plan.status.value,
                "steps": len(action_plan.steps),
                "scheduled_time": action_plan.scheduled_time.isoformat() if action_plan.scheduled_time else None
            }
        )
        
        return result
    
    async def _process_schedule(self, request_id: str, request: TwinRequest) -> TwinResult:
        """Process scheduling requests"""
        
        # Schedule requests are a special type of action
        return await self._process_action(request_id, request)
    
    async def _process_introspection(self, request_id: str, request: TwinRequest) -> TwinResult:
        """Process introspection and self-analysis requests"""
        
        # Use brain's introspection capabilities
        insights = self.brain.introspect_with_memory(request.content)
        
        result = TwinResult(
            request_id=request_id,
            success=True,
            response_text=insights,
            memory_updates=0,  # Introspection doesn't create new memories
            response_data={
                "introspection_type": "memory_analysis",
                "insights_length": len(insights)
            }
        )
        
        return result
    
    async def _process_hybrid(self, request_id: str, request: TwinRequest) -> TwinResult:
        """Process requests that might need both reasoning and action"""
        
        # First, let brain reason about it
        situation = Situation(
            context=request.content,
            category="hybrid_request",
            metadata={
                **request.context,
                "request_type": "hybrid",
                "priority": request.priority
            }
        )
        
        brain_response = await self.brain.reason(situation)
        
        # Determine if action is needed based on brain response
        needs_action = self._determine_if_action_needed(brain_response)
        
        if needs_action:
            # Execute through controller
            action_plan = await self.controller.process_request(
                request=request.content,
                context=request.context
            )
            
            result = TwinResult(
                request_id=request_id,
                success=action_plan.status.value in ["completed", "scheduled"],
                reasoning_response=brain_response,
                action_plan=action_plan,
                response_text=f"Reasoning + Action: {brain_response.action}",
                memory_updates=2,  # Both reasoning and action captured
                lessons_learned=brain_response.lessons_applied
            )
        else:
            # Pure reasoning result
            result = TwinResult(
                request_id=request_id,
                success=True,
                reasoning_response=brain_response,
                response_text=brain_response.action,
                memory_updates=1,
                lessons_learned=brain_response.lessons_applied
            )
        
        return result
    
    def _determine_if_action_needed(self, brain_response: TwinResponse) -> bool:
        """Determine if a brain response requires action"""
        
        action_indicators = [
            "should call", "need to send", "schedule", "create", "execute",
            "remind", "contact", "book", "cancel", "update"
        ]
        
        action_text = brain_response.action.lower()
        return any(indicator in action_text for indicator in action_indicators)
    
    async def _learn_from_processing_failure(self, request: TwinRequest, error: str):
        """Learn from processing failures"""
        
        failure_situation = Situation(
            context=f"Failed to process request: {request.content}",
            category="processing_failure",
            metadata={
                "request_type": request.request_type,
                "error": error,
                "priority": request.priority
            }
        )
        
        # Let the brain learn from this failure
        self.brain.learn_from_feedback(
            situation=failure_situation,
            actual_action=f"Processing failed: {error}",
            satisfaction=0.1,  # Very low satisfaction
            lessons_learned=[f"Processing failure for {request.request_type} requests: {error}"],
            feedback="Decision loop failed to process request"
        )
    
    async def provide_feedback(self,
                              request_id: str,
                              satisfaction: float,
                              lessons_learned: List[str] = None,
                              feedback_text: str = None) -> bool:
        """
        Provide feedback on a completed request for learning.
        
        This is crucial for the twin's continuous improvement.
        
        Args:
            request_id: ID of the request to provide feedback on
            satisfaction: How satisfied with the result (0-1)
            lessons_learned: Specific lessons from this experience
            feedback_text: Additional feedback
            
        Returns:
            Whether feedback was successfully applied
        """
        
        # Find the result in history
        result = None
        for hist_result in self.request_history:
            if hist_result.request_id == request_id:
                result = hist_result
                break
        
        if not result:
            self.logger.warning(f"Could not find result for request {request_id}")
            return False
        
        # Find the original request
        request = None
        if result.reasoning_response:
            # Extract situation from reasoning response (simplified)
            request_content = "Previous request"  # Would need to store this better
        
        if result.action_plan:
            request_content = result.action_plan.intent
        
        if not request_content:
            self.logger.warning("Could not determine original request for feedback")
            return False
        
        # Create feedback situation
        feedback_situation = Situation(
            context=request_content,
            category="user_feedback",
            metadata={
                "request_id": request_id,
                "original_success": result.success,
                "processing_time": result.processing_time
            }
        )
        
        # Apply learning
        learning_result = self.brain.learn_from_feedback(
            situation=feedback_situation,
            actual_action=f"User feedback received: {feedback_text or 'No specific feedback'}",
            satisfaction=satisfaction,
            lessons_learned=lessons_learned or [],
            feedback=feedback_text
        )
        
        # Update statistics
        self.processing_stats["memory_formations"] += 1
        if lessons_learned:
            self.processing_stats["patterns_learned"] += len(lessons_learned)
        
        self.logger.info(f"Applied feedback for request {request_id}: satisfaction={satisfaction:.2f}")
        
        return True
    
    async def introspect(self, question: str) -> str:
        """Direct introspection interface"""
        
        result = await self.process(
            content=question,
            request_type="introspect"
        )
        
        return result.response_text
    
    async def ask_memory(self, question: str) -> str:
        """Direct memory query interface"""
        
        return self.brain.ask_memory(question)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        return {
            "decision_loop": {
                "active_requests": len(self.active_requests),
                "total_processed": self.processing_stats["total_requests"],
                "success_rate": (self.processing_stats["successful_requests"] / 
                               max(1, self.processing_stats["total_requests"])),
                "memory_formations": self.processing_stats["memory_formations"],
                "patterns_learned": self.processing_stats["patterns_learned"]
            },
            "brain": self.brain.get_memory_summary(),
            "controller": self.controller.get_memory_insights(),
            "scheduler": {
                "active_schedules": len(self.scheduler.scheduled_actions) if hasattr(self.scheduler, 'scheduled_actions') else 0
            }
        }
    
    async def optimize_system(self):
        """Run system optimization based on memory patterns"""
        
        self.logger.info("🔧 Running system optimization...")
        
        # Optimize brain memory system
        maintenance_stats = self.brain.maintain_memory_system()
        
        # Optimize controller patterns
        controller_insights = await self.controller.optimize_based_on_memory()
        
        # Extract system-wide insights
        system_insights = self.brain.introspect_with_memory(
            "Analyze the overall performance of the digital twin system. "
            "What patterns do you see in request processing, decision making, and action execution? "
            "What improvements would make the system more effective?"
        )
        
        self.logger.info("✅ System optimization completed")
        self.logger.info(f"Memory maintenance: {maintenance_stats}")
        self.logger.info(f"System insights: {system_insights[:200]}...")
        
        return {
            "memory_maintenance": maintenance_stats,
            "controller_optimization": controller_insights,
            "system_insights": system_insights
        }
    
    async def export_complete_system(self, filepath: str = None) -> str:
        """Export the complete twin system state"""
        
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"complete_twin_export_{timestamp}.json"
        
        # Export brain/memory system
        memory_export = self.brain.export_memories(f"memory_{filepath}")
        
        # Export system state
        import json
        system_state = {
            "export_timestamp": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "processing_stats": self.processing_stats,
            "recent_requests": [
                {
                    "request_id": r.request_id,
                    "success": r.success,
                    "processing_time": r.processing_time,
                    "memory_updates": r.memory_updates,
                    "response_summary": r.response_text[:100]
                }
                for r in self.request_history[-10:]  # Last 10 requests
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(system_state, f, indent=2)
        
        self.logger.info(f"Exported complete twin system to {filepath}")
        
        return filepath
    
    # Goal-Aware Agent Methods
    
    def create_goal(self, title: str, description: str, target_date: datetime, **kwargs) -> Optional[str]:
        """Create a new goal"""
        
        if not self.goal_manager:
            self.logger.warning("Goal system not available")
            return None
        
        try:
            goal = self.goal_manager.create_goal(
                title=title,
                description=description,
                target_date=target_date,
                **kwargs
            )
            
            # Capture goal creation in memory
            if self.brain.memory_updater:
                self.brain.memory_updater.capture_goal_memory(
                    goal=goal,
                    action_type="created",
                    details={"creation_method": "twin_interface"}
                )
            
            self.logger.info(f"Created goal: {goal.title} (ID: {goal.id})")
            return goal.id
            
        except Exception as e:
            self.logger.error(f"Error creating goal: {e}")
            return None
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get active goals with summary information"""
        
        if not self.goal_manager:
            return []
        
        try:
            active_goals = self.goal_manager.get_active_goals()
            
            return [
                {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "type": goal.goal_type.value,
                    "progress": goal.progress_percentage,
                    "priority": goal.priority,
                    "target_date": goal.target_date.isoformat(),
                    "days_remaining": goal.days_until_deadline,
                    "status": goal.status.value
                }
                for goal in active_goals
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting active goals: {e}")
            return []
    
    def get_goal_status(self, goal_id: str = None) -> Dict[str, Any]:
        """Get comprehensive goal status information"""
        
        if not self.goal_manager:
            return {"error": "Goal system not available"}
        
        try:
            if goal_id:
                # Get specific goal status
                goal = self.goal_manager.get_goal_by_id(goal_id)
                if not goal:
                    return {"error": f"Goal {goal_id} not found"}
                
                # Get project plan if available
                project_plan = None
                if self.strategic_planner and goal_id in self.strategic_planner.project_plans:
                    plan = self.strategic_planner.project_plans[goal_id]
                    project_plan = {
                        "timeline_status": plan.timeline_status.value,
                        "completion_probability": plan.completion_probability,
                        "weeks_remaining": plan.current_timeline_weeks,
                        "progress_percentage": plan.progress_percentage
                    }
                
                return {
                    "goal": {
                        "id": goal.id,
                        "title": goal.title,
                        "progress": goal.progress_percentage,
                        "status": goal.status.value,
                        "days_remaining": goal.days_until_deadline
                    },
                    "project_plan": project_plan,
                    "next_milestones": [
                        {
                            "title": m.title,
                            "progress": m.progress_percentage,
                            "days_remaining": m.days_until_deadline
                        }
                        for m in goal.get_next_milestones(
                            list(self.goal_manager.milestones.values()), 
                            limit=3
                        )
                    ]
                }
            else:
                # Get overall goal summary
                return self.goal_manager.get_goal_summary()
                
        except Exception as e:
            self.logger.error(f"Error getting goal status: {e}")
            return {"error": str(e)}
    
    def get_daily_goal_briefing(self) -> str:
        """Get a daily briefing focused on goals"""
        
        if not self.goal_reasoner:
            return "Goal system not available"
        
        try:
            return self.goal_reasoner.get_daily_goal_briefing()
        except Exception as e:
            self.logger.error(f"Error getting daily briefing: {e}")
            return f"Error generating briefing: {e}"
    
    def update_goal_progress(self, milestone_id: str, progress: float, notes: str = "") -> bool:
        """Update progress on a specific milestone"""
        
        if not self.goal_manager:
            return False
        
        try:
            milestone = self.goal_manager.get_milestone_by_id(milestone_id)
            if not milestone:
                self.logger.warning(f"Milestone {milestone_id} not found")
                return False
            
            old_progress = milestone.progress_percentage
            milestone.update_progress(progress, notes)
            
            # Capture progress update in memory
            if self.brain.memory_updater:
                self.brain.memory_updater.capture_milestone_memory(
                    milestone=milestone,
                    action_type="progress_updated",
                    progress_details={
                        "old_progress": old_progress,
                        "new_progress": progress,
                        "progress_increase": progress - old_progress,
                        "notes": notes,
                        "update_method": "twin_interface"
                    }
                )
            
            # Update strategic plan
            if self.strategic_planner:
                self.strategic_planner.update_plan_from_progress(milestone.goal_id)
            
            self.logger.info(f"Updated milestone '{milestone.title}' progress: {old_progress:.1f}% -> {progress:.1f}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress: {e}")
            return False
    
    def get_strategic_recommendations(self, goal_id: str = None) -> List[str]:
        """Get strategic recommendations for goals"""
        
        if not self.strategic_planner:
            return ["Strategic planner not available"]
        
        try:
            if goal_id:
                return self.strategic_planner.get_strategic_recommendations(goal_id)
            else:
                # Get recommendations for all active goals
                recommendations = []
                for goal in self.goal_manager.get_active_goals()[:3]:  # Top 3 goals
                    goal_recs = self.strategic_planner.get_strategic_recommendations(goal.id)
                    for rec in goal_recs[:2]:  # Top 2 per goal
                        recommendations.append(f"{goal.title}: {rec}")
                return recommendations
                
        except Exception as e:
            self.logger.error(f"Error getting strategic recommendations: {e}")
            return [f"Error: {e}"]
    
    def should_mention_goals_proactively(self) -> tuple[bool, str]:
        """Check if goals should be proactively mentioned"""
        
        if not self.goal_reasoner:
            return False, ""
        
        try:
            # Get current activity context
            activity_context = {}
            if self.current_context:
                activity_context = {
                    'current_app': self.current_context.current_app,
                    'activity_category': self.current_context.activity_category.value,
                    'productivity_state': self.current_context.productivity_state
                }
            
            should_mention, message = self.goal_reasoner.should_proactively_mention_goals(activity_context)
            return should_mention, message
            
        except Exception as e:
            self.logger.error(f"Error checking goal mentions: {e}")
            return False, ""
    
    def link_current_activity_to_goals(self) -> bool:
        """Link current observed activity to relevant goals"""
        
        if not (self.observer_manager and self.goal_manager and self.brain.memory_updater):
            return False
        
        try:
            # Get current context
            if not self.current_context:
                return False
            
            # Find goals related to current activity
            current_app = self.current_context.current_app
            activity_category = self.current_context.activity_category.value
            
            relevant_goals = []
            relevance_scores = []
            
            for goal in self.goal_manager.get_active_goals():
                relevance = 0.0
                
                # Check if current app is related to goal
                if current_app in goal.related_apps:
                    relevance += 0.8
                
                # Check activity category alignment
                if activity_category in goal.impact_areas:
                    relevance += 0.6
                
                # Check goal type alignment
                if (activity_category == 'development' and 
                    goal.goal_type.value in ['project', 'learning']):
                    relevance += 0.4
                
                if relevance > 0.3:
                    relevant_goals.append(goal.id)
                    relevance_scores.append(relevance)
            
            # Create synthetic observation for linking
            if relevant_goals:
                from observer.observer_utils import ObservationEvent, ActivityCategory
                
                synthetic_observation = ObservationEvent(
                    timestamp=datetime.now(),
                    event_type="activity_session",
                    app_name=current_app,
                    category=ActivityCategory.PRODUCTIVITY,
                    duration_seconds=self.current_context.current_session_duration_minutes * 60
                )
                
                return self.brain.memory_updater.link_observation_to_goals(
                    observation=synthetic_observation,
                    goal_ids=relevant_goals,
                    relevance_scores=relevance_scores
                )
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error linking activity to goals: {e}")
            return False