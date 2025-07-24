"""
Twin Decision Loop - Main orchestrator with real-time intelligence and HITL
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json
from pathlib import Path
import logging

from .action_classifier import ActionClassifier, CriticalityLevel
from .hitl_engine import HITLEngine, ApprovalStatus
from .realtime_memory_streamer import MemoryStreamer, RealTimeObserver
from .alert_dispatcher import AlertDispatcher
from .feedback_tracker import FeedbackTracker


class TwinDecisionLoop:
    """Main decision loop with real-time intelligence and human oversight"""
    
    def __init__(self, memory_systems: Optional[Dict[str, Any]] = None):
        """Initialize the twin decision loop"""
        # Core components
        self.action_classifier = ActionClassifier()
        self.feedback_tracker = FeedbackTracker()
        self.alert_dispatcher = AlertDispatcher()
        self.hitl_engine = HITLEngine(self.alert_dispatcher, self.feedback_tracker)
        self.memory_streamer = MemoryStreamer(memory_systems)
        self.real_time_observer = RealTimeObserver(self.memory_streamer)
        
        # State
        self.running = False
        self.action_queue: asyncio.Queue = asyncio.Queue()
        self.execution_handlers: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            'actions_processed': 0,
            'auto_executed': 0,
            'human_approved': 0,
            'human_denied': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Logging
        self.logger = self._setup_logging()
        
        # Configuration
        self.config_path = Path("backend/config/twin_config.json")
        self.config = self._load_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('TwinDecisionLoop')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_path = Path("backend/logs/twin_decisions.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load twin configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            'auto_execute_threshold': 0.95,  # Confidence threshold for auto-execution
            'max_concurrent_actions': 5,
            'timeout_hours': 24,
            'learning_enabled': True
        }
    
    async def start(self):
        """Start the twin decision loop"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Start components
        self.memory_streamer.start()
        self.hitl_engine.start()
        
        # Start main processing loop
        self.logger.info("Twin decision loop started")
        await self._main_loop()
    
    async def stop(self):
        """Stop the twin decision loop"""
        self.running = False
        
        # Stop components
        self.memory_streamer.stop()
        self.hitl_engine.stop()
        
        self.logger.info(f"Twin decision loop stopped. Stats: {self.stats}")
    
    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a handler for executing specific action types"""
        self.execution_handlers[action_type] = handler
    
    async def queue_action(self, action: Dict[str, Any]):
        """Queue an action for processing"""
        await self.action_queue.put(action)
    
    async def _main_loop(self):
        """Main processing loop"""
        tasks = []
        
        while self.running:
            try:
                # Process queued actions
                while not self.action_queue.empty() and len(tasks) < self.config['max_concurrent_actions']:
                    action = await self.action_queue.get()
                    task = asyncio.create_task(self._process_action(action))
                    tasks.append(task)
                
                # Wait for some tasks to complete
                if tasks:
                    done, tasks = await asyncio.wait(
                        tasks, 
                        timeout=1.0,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for task in done:
                        try:
                            await task
                        except Exception as e:
                            self.logger.error(f"Error in action processing: {e}")
                            self.stats['errors'] += 1
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(1.0)  # Longer delay on error
    
    async def _process_action(self, action: Dict[str, Any]):
        """Process a single action through the decision pipeline"""
        self.stats['actions_processed'] += 1
        action_id = f"action_{self.stats['actions_processed']}"
        
        self.logger.info(f"Processing action {action_id}: {action.get('type')} -> {action.get('target')}")
        
        try:
            # Step 1: Observe the action for memory
            self.real_time_observer.observe_action(action)
            
            # Step 2: Classify criticality
            criticality = self.action_classifier.classify_action(action)
            self.logger.info(f"Action {action_id} classified as {criticality.value}")
            
            # Step 3: Check if we can auto-execute
            if await self._can_auto_execute(action, criticality):
                success = await self._execute_action(action)
                if success:
                    self.stats['auto_executed'] += 1
                    self.logger.info(f"Action {action_id} auto-executed successfully")
                    
                    # Update memory with successful action
                    self.real_time_observer.observe_action({
                        **action,
                        'result': 'auto_executed',
                        'success': True
                    })
                else:
                    self.logger.error(f"Action {action_id} auto-execution failed")
                return
            
            # Step 4: Request human approval
            approval_request = await self.hitl_engine.request_approval(action)
            self.logger.info(f"Action {action_id} requires approval, request ID: {approval_request.id}")
            
            # Step 5: Wait for human decision
            decision = await self._wait_for_decision(approval_request)
            
            # Step 6: Act on decision
            if decision.status == ApprovalStatus.APPROVED:
                self.stats['human_approved'] += 1
                success = await self._execute_action(action)
                
                # Update memory
                self.real_time_observer.observe_action({
                    **action,
                    'result': 'human_approved_and_executed',
                    'success': success
                })
                
                self.logger.info(f"Action {action_id} approved and executed: {success}")
                
            elif decision.status == ApprovalStatus.DENIED:
                self.stats['human_denied'] += 1
                self.logger.info(f"Action {action_id} denied by human")
                
                # Update memory
                self.real_time_observer.observe_action({
                    **action,
                    'result': 'human_denied',
                    'success': False
                })
                
            elif decision.status == ApprovalStatus.TIMEOUT:
                self.logger.warning(f"Action {action_id} timed out waiting for approval")
                
                # Update memory
                self.real_time_observer.observe_action({
                    **action,
                    'result': 'timeout',
                    'success': False
                })
            
        except Exception as e:
            self.logger.error(f"Error processing action {action_id}: {e}")
            self.stats['errors'] += 1
    
    async def _can_auto_execute(self, action: Dict[str, Any], criticality: CriticalityLevel) -> bool:
        """Determine if an action can be auto-executed"""
        # Never auto-execute high criticality actions
        if criticality == CriticalityLevel.HIGH:
            return False
        
        # Check learning-based confidence
        if self.config.get('learning_enabled', True):
            approval_rate = self.feedback_tracker.get_approval_rate(action)
            if approval_rate is not None:
                threshold = self.config.get('auto_execute_threshold', 0.95)
                similar_count = self.feedback_tracker.get_similar_action_count(action)
                
                # Need both high approval rate and sufficient history
                if approval_rate >= threshold and similar_count >= 10:
                    return True
        
        # Auto-execute low criticality routine actions
        if criticality == CriticalityLevel.LOW:
            routine_actions = ['log', 'archive', 'reminder_set', 'focus_session']
            if action.get('type') in routine_actions:
                return True
        
        return False
    
    async def _wait_for_decision(self, request) -> Any:
        """Wait for human decision on approval request"""
        # Poll for decision with timeout
        max_wait_seconds = request.timeout_minutes * 60
        check_interval = 5  # Check every 5 seconds
        elapsed = 0
        
        while elapsed < max_wait_seconds and self.running:
            # Check if decision was made
            if request.status != ApprovalStatus.PENDING:
                return request
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        # Handle timeout
        if request.status == ApprovalStatus.PENDING:
            request.status = ApprovalStatus.TIMEOUT
            request.resolved_at = datetime.now()
        
        return request
    
    async def _execute_action(self, action: Dict[str, Any]) -> bool:
        """Execute an approved action"""
        action_type = action.get('type')
        
        if action_type in self.execution_handlers:
            try:
                handler = self.execution_handlers[action_type]
                result = await handler(action) if asyncio.iscoroutinefunction(handler) else handler(action)
                return result is not False  # Consider None as success
            except Exception as e:
                self.logger.error(f"Error executing action {action_type}: {e}")
                return False
        else:
            self.logger.warning(f"No handler registered for action type: {action_type}")
            # For testing, simulate execution
            await asyncio.sleep(0.1)
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        runtime = None
        if self.stats['start_time']:
            runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'hitl_stats': self.hitl_engine.get_stats(),
            'memory_stats': self.memory_streamer.get_stats(),
            'queue_size': self.action_queue.qsize(),
            'learning_insights': self.feedback_tracker.get_learning_insights()
        }
    
    def get_pending_approvals(self) -> List[Any]:
        """Get pending approval requests"""
        return self.hitl_engine.get_pending_approvals()
    
    async def approve_action(self, request_id: str, feedback: Optional[str] = None) -> bool:
        """Approve a pending action"""
        return self.hitl_engine.approve(request_id, feedback)
    
    async def deny_action(self, request_id: str, feedback: Optional[str] = None) -> bool:
        """Deny a pending action"""
        return self.hitl_engine.deny(request_id, feedback)
    
    async def defer_action(self, request_id: str, minutes: int = 10) -> bool:
        """Defer a pending action"""
        return self.hitl_engine.defer(request_id, minutes)


# Example action handlers
class ExampleActionHandlers:
    """Example implementations of action handlers"""
    
    @staticmethod
    async def handle_email_send(action: Dict[str, Any]) -> bool:
        """Handle email sending"""
        print(f"📧 Sending email to {action.get('target')}: {action.get('content', '')[:50]}...")
        await asyncio.sleep(1)  # Simulate API call
        return True
    
    @staticmethod
    async def handle_calendar_create(action: Dict[str, Any]) -> bool:
        """Handle calendar event creation"""
        print(f"📅 Creating calendar event: {action.get('content', {}).get('title', 'Untitled')}")
        await asyncio.sleep(1)
        return True
    
    @staticmethod
    def handle_task_create(action: Dict[str, Any]) -> bool:
        """Handle task creation"""
        print(f"✅ Creating task: {action.get('content', {}).get('title', 'Untitled')}")
        return True
    
    @staticmethod
    def handle_reminder_set(action: Dict[str, Any]) -> bool:
        """Handle reminder setting"""
        print(f"⏰ Setting reminder: {action.get('content', '')}")
        return True


if __name__ == "__main__":
    # Example usage
    async def demo_twin():
        # Create and configure twin
        twin = TwinDecisionLoop()
        
        # Register action handlers
        handlers = ExampleActionHandlers()
        twin.register_action_handler('email_send', handlers.handle_email_send)
        twin.register_action_handler('calendar_create', handlers.handle_calendar_create)
        twin.register_action_handler('task_create', handlers.handle_task_create)
        twin.register_action_handler('reminder_set', handlers.handle_reminder_set)
        
        # Start twin in background
        twin_task = asyncio.create_task(twin.start())
        
        # Queue some test actions
        test_actions = [
            {
                'type': 'reminder_set',
                'target': 'self',
                'content': 'Review quarterly numbers',
                'context': {}
            },
            {
                'type': 'email_send',
                'target': 'team@company.com',
                'content': 'Weekly update: All projects on track',
                'context': {}
            },
            {
                'type': 'email_send',
                'target': 'CEO@company.com',
                'content': 'Urgent: Q4 numbers ready for review',
                'context': {'urgent': True}
            }
        ]
        
        # Queue actions
        for action in test_actions:
            await twin.queue_action(action)
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        # Check stats
        stats = twin.get_stats()
        print(f"\nTwin Stats:\n{json.dumps(stats, indent=2, default=str)}")
        
        # Check pending approvals
        pending = twin.get_pending_approvals()
        if pending:
            print(f"\nPending approvals: {len(pending)}")
            for req in pending:
                print(f"- {req.id[:8]}: {req.action.get('type')} -> {req.action.get('target')}")
        
        # Stop twin
        await twin.stop()
        twin_task.cancel()
    
    # Run demo
    asyncio.run(demo_twin())