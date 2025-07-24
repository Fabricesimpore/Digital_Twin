"""
Scheduler Module for Digital Twin

Handles time-based triggers and recurring actions for the digital twin.
Supports one-time scheduled actions and recurring patterns.

Uses asyncio for lightweight scheduling without external dependencies.
For production, you might want to use APScheduler or Celery.
"""

import asyncio
import logging
from typing import Dict, Callable, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class ScheduleType(Enum):
    """Types of scheduled actions"""
    ONE_TIME = "one_time"
    RECURRING_DAILY = "recurring_daily"
    RECURRING_WEEKLY = "recurring_weekly"
    RECURRING_CUSTOM = "recurring_custom"


@dataclass
class ScheduledAction:
    """Represents a scheduled action"""
    id: str
    action_type: ScheduleType
    scheduled_time: datetime
    callback: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    recurring_pattern: Optional[str] = None  # cron-like pattern for custom
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence (excluding callback)"""
        return {
            'id': self.id,
            'action_type': self.action_type.value,
            'scheduled_time': self.scheduled_time.isoformat(),
            'params': self.params,
            'recurring_pattern': self.recurring_pattern,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'active': self.active
        }


class TwinScheduler:
    """
    Manages time-based actions for the digital twin.
    
    Features:
    - One-time scheduled actions
    - Recurring actions (daily, weekly, custom)
    - Persistence across restarts
    - Cancellation and modification
    """
    
    def __init__(self, persistence_file: str = "scheduled_actions.json"):
        self.scheduled_actions: Dict[str, ScheduledAction] = {}
        self.persistence_file = persistence_file
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
        self._running = False
        
        # Load persisted actions on startup
        self._load_scheduled_actions()
    
    def _load_scheduled_actions(self):
        """Load scheduled actions from persistence file"""
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded {len(data)} scheduled actions")
                    # Note: Callbacks need to be re-registered after load
            except Exception as e:
                self.logger.error(f"Failed to load scheduled actions: {e}")
    
    def _save_scheduled_actions(self):
        """Save scheduled actions to persistence file"""
        try:
            data = [action.to_dict() for action in self.scheduled_actions.values()]
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save scheduled actions: {e}")
    
    async def start(self):
        """Start the scheduler"""
        self._running = True
        self.logger.info("Scheduler started")
        
        # Start monitoring loop
        asyncio.create_task(self._monitor_scheduled_actions())
        
        # Reschedule any active actions
        for action in self.scheduled_actions.values():
            if action.active and action.next_execution:
                asyncio.create_task(self._schedule_action(action))
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        
        # Cancel all running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        self.logger.info("Scheduler stopped")
    
    def schedule_action(self, 
                       action_id: str,
                       delay_seconds: float = None,
                       scheduled_time: datetime = None,
                       callback: Callable = None,
                       params: Dict[str, Any] = None,
                       action_type: ScheduleType = ScheduleType.ONE_TIME,
                       recurring_pattern: str = None) -> bool:
        """
        Schedule an action for future execution.
        
        Args:
            action_id: Unique identifier for the action
            delay_seconds: Delay in seconds from now (alternative to scheduled_time)
            scheduled_time: Specific time to execute
            callback: Function to call when time arrives
            params: Parameters to pass to callback
            action_type: Type of schedule (one-time or recurring)
            recurring_pattern: Pattern for recurring actions
        
        Returns:
            bool: Success status
        """
        
        # Calculate scheduled time
        if delay_seconds is not None:
            scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)
        elif scheduled_time is None:
            self.logger.error("Must provide either delay_seconds or scheduled_time")
            return False
        
        # Create scheduled action
        action = ScheduledAction(
            id=action_id,
            action_type=action_type,
            scheduled_time=scheduled_time,
            callback=callback,
            params=params or {},
            recurring_pattern=recurring_pattern,
            next_execution=scheduled_time
        )
        
        # Store action
        self.scheduled_actions[action_id] = action
        self._save_scheduled_actions()
        
        # Schedule execution
        if self._running:
            asyncio.create_task(self._schedule_action(action))
        
        self.logger.info(f"Scheduled action {action_id} for {scheduled_time}")
        return True
    
    async def _schedule_action(self, action: ScheduledAction):
        """Internal method to schedule a single action"""
        if not action.active or not action.next_execution:
            return
        
        # Calculate delay
        delay = (action.next_execution - datetime.now()).total_seconds()
        
        if delay > 0:
            # Wait until execution time
            await asyncio.sleep(delay)
        
        # Execute if still active
        if action.active and action.id in self.scheduled_actions:
            await self._execute_action(action)
    
    async def _execute_action(self, action: ScheduledAction):
        """Execute a scheduled action"""
        self.logger.info(f"Executing scheduled action {action.id}")
        
        try:
            # Execute callback
            if action.callback:
                if asyncio.iscoroutinefunction(action.callback):
                    result = await action.callback(**action.params)
                else:
                    result = action.callback(**action.params)
                
                self.logger.info(f"Action {action.id} executed successfully")
            
            # Update execution time
            action.last_executed = datetime.now()
            
            # Handle recurring actions
            if action.action_type != ScheduleType.ONE_TIME:
                action.next_execution = self._calculate_next_execution(action)
                if action.next_execution:
                    # Schedule next execution
                    asyncio.create_task(self._schedule_action(action))
            else:
                # One-time action completed
                action.active = False
            
            self._save_scheduled_actions()
            
        except Exception as e:
            self.logger.error(f"Failed to execute action {action.id}: {e}")
    
    def _calculate_next_execution(self, action: ScheduledAction) -> Optional[datetime]:
        """Calculate next execution time for recurring actions"""
        if not action.last_executed:
            return None
        
        if action.action_type == ScheduleType.RECURRING_DAILY:
            # Same time tomorrow
            return action.last_executed + timedelta(days=1)
        
        elif action.action_type == ScheduleType.RECURRING_WEEKLY:
            # Same time next week
            return action.last_executed + timedelta(weeks=1)
        
        elif action.action_type == ScheduleType.RECURRING_CUSTOM:
            # Parse custom pattern (simplified - you'd want croniter for real cron)
            if action.recurring_pattern == "hourly":
                return action.last_executed + timedelta(hours=1)
            elif action.recurring_pattern == "every_30_min":
                return action.last_executed + timedelta(minutes=30)
            # Add more patterns as needed
        
        return None
    
    def cancel_action(self, action_id: str) -> bool:
        """Cancel a scheduled action"""
        if action_id in self.scheduled_actions:
            action = self.scheduled_actions[action_id]
            action.active = False
            
            # Cancel running task if exists
            if action_id in self.running_tasks:
                self.running_tasks[action_id].cancel()
                del self.running_tasks[action_id]
            
            self._save_scheduled_actions()
            self.logger.info(f"Cancelled action {action_id}")
            return True
        
        return False
    
    def get_scheduled_actions(self, active_only: bool = True) -> List[ScheduledAction]:
        """Get all scheduled actions"""
        actions = list(self.scheduled_actions.values())
        if active_only:
            actions = [a for a in actions if a.active]
        return sorted(actions, key=lambda x: x.next_execution or datetime.max)
    
    async def _monitor_scheduled_actions(self):
        """Monitor and clean up completed actions periodically"""
        while self._running:
            # Clean up inactive one-time actions older than 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            to_remove = []
            
            for action_id, action in self.scheduled_actions.items():
                if (not action.active and 
                    action.action_type == ScheduleType.ONE_TIME and
                    action.last_executed and 
                    action.last_executed < cutoff):
                    to_remove.append(action_id)
            
            for action_id in to_remove:
                del self.scheduled_actions[action_id]
                self.logger.info(f"Cleaned up completed action {action_id}")
            
            if to_remove:
                self._save_scheduled_actions()
            
            # Check every hour
            await asyncio.sleep(3600)
    
    def schedule_recurring_reminder(self, 
                                  action_id: str,
                                  time_of_day: str,  # "09:00", "15:30"
                                  callback: Callable,
                                  params: Dict[str, Any] = None,
                                  days: List[str] = None) -> bool:
        """
        Convenience method to schedule daily reminders.
        
        Args:
            action_id: Unique identifier
            time_of_day: Time in HH:MM format
            callback: Function to call
            params: Parameters for callback
            days: List of days (Mon, Tue, etc.) - None means every day
        
        Returns:
            bool: Success status
        """
        # Parse time
        try:
            hour, minute = map(int, time_of_day.split(':'))
            
            # Calculate first execution
            now = datetime.now()
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time passed today, schedule for tomorrow
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)
            
            # Create recurring action
            return self.schedule_action(
                action_id=action_id,
                scheduled_time=scheduled_time,
                callback=callback,
                params=params,
                action_type=ScheduleType.RECURRING_DAILY
            )
            
        except Exception as e:
            self.logger.error(f"Failed to schedule recurring reminder: {e}")
            return False


# Example usage functions
async def example_reminder_callback(message: str, **kwargs):
    """Example callback for reminders"""
    print(f"⏰ Reminder: {message}")
    # This would trigger the voice call system in real implementation


async def example_task_check_callback(**kwargs):
    """Example callback for checking tasks"""
    print("📋 Checking pending tasks...")
    # This would query the task system and format a summary


if __name__ == "__main__":
    # Example usage
    async def test_scheduler():
        scheduler = TwinScheduler()
        await scheduler.start()
        
        # Schedule a one-time action in 5 seconds
        scheduler.schedule_action(
            action_id="test_1",
            delay_seconds=5,
            callback=example_reminder_callback,
            params={"message": "This is a test reminder!"}
        )
        
        # Schedule a daily reminder
        scheduler.schedule_recurring_reminder(
            action_id="daily_standup",
            time_of_day="09:00",
            callback=example_task_check_callback
        )
        
        # Wait a bit to see it work
        await asyncio.sleep(10)
        
        # Show scheduled actions
        actions = scheduler.get_scheduled_actions()
        for action in actions:
            print(f"Scheduled: {action.id} at {action.next_execution}")
        
        await scheduler.stop()
    
    # Run test
    asyncio.run(test_scheduler())