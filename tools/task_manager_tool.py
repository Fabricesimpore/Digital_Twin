"""
Task Manager Tool for Digital Twin

Manages tasks and todos, integrating with various task management systems.
Provides a unified interface for task operations regardless of backend.

Supports:
- Local task storage
- Integration with Notion, Todoist, etc.
- Task prioritization and deadlines
- Context-aware task retrieval
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging


class TaskPriority(Enum):
    """Task priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task or todo item"""
    id: str
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            priority=TaskPriority(data.get('priority', 'normal')),
            status=TaskStatus(data.get('status', 'pending')),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            tags=data.get('tags', []),
            context=data.get('context', {})
        )


class TaskManagerTool:
    """
    Unified task management interface for the digital twin.
    
    This tool abstracts different task management backends and provides
    a consistent interface for task operations.
    """
    
    def __init__(self, 
                 storage_file: str = "tasks.json",
                 backend: str = "local"):  # local, notion, todoist, etc.
        """
        Initialize task manager.
        
        Args:
            storage_file: Local storage file for tasks
            backend: Which backend to use
        """
        self.storage_file = storage_file
        self.backend = backend
        self.logger = logging.getLogger(__name__)
        
        # Load tasks from storage
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from local storage"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task.from_dict(task_data)
                        self.tasks[task.id] = task
                self.logger.info(f"Loaded {len(self.tasks)} tasks")
            except Exception as e:
                self.logger.error(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to local storage"""
        try:
            data = [task.to_dict() for task in self.tasks.values()]
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def get_pending_tasks(self, 
                         timeframe: str = "today",
                         include_deadlines: bool = True,
                         **kwargs) -> List[Dict[str, Any]]:
        """
        Get pending tasks based on criteria.
        
        Args:
            timeframe: "today", "this_week", "all"
            include_deadlines: Whether to include deadline info
            
        Returns:
            List of task dictionaries
        """
        # Filter tasks
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        ]
        
        # Apply timeframe filter
        if timeframe == "today":
            today = datetime.now().date()
            pending_tasks = [
                task for task in pending_tasks
                if (task.deadline and task.deadline.date() == today) or
                   (not task.deadline and task.priority == TaskPriority.HIGH)
            ]
        elif timeframe == "this_week":
            week_end = datetime.now() + timedelta(days=7)
            pending_tasks = [
                task for task in pending_tasks
                if task.deadline and task.deadline <= week_end
            ]
        
        # Sort by priority and deadline
        def sort_key(task):
            priority_order = {TaskPriority.HIGH: 0, TaskPriority.NORMAL: 1, TaskPriority.LOW: 2}
            deadline_score = 0 if task.deadline else 999
            if task.deadline:
                deadline_score = (task.deadline - datetime.now()).days
            return (priority_order[task.priority], deadline_score)
        
        pending_tasks.sort(key=sort_key)
        
        # Format for output
        formatted_tasks = []
        for task in pending_tasks:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'priority': task.priority.value,
                'status': task.status.value
            }
            
            if include_deadlines and task.deadline:
                # Format deadline in human-readable way
                deadline_delta = task.deadline - datetime.now()
                if deadline_delta.days == 0:
                    deadline_str = f"today at {task.deadline.strftime('%I:%M %p')}"
                elif deadline_delta.days == 1:
                    deadline_str = f"tomorrow at {task.deadline.strftime('%I:%M %p')}"
                else:
                    deadline_str = task.deadline.strftime('%B %d at %I:%M %p')
                
                task_dict['deadline'] = deadline_str
            
            if task.description:
                task_dict['description'] = task.description
            
            if task.tags:
                task_dict['tags'] = task.tags
            
            formatted_tasks.append(task_dict)
        
        return formatted_tasks
    
    def create_task(self,
                   title: str,
                   description: str = "",
                   priority: str = "normal",
                   deadline: Optional[datetime] = None,
                   tags: List[str] = None) -> Task:
        """Create a new task"""
        import uuid
        
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=TaskPriority(priority),
            deadline=deadline,
            tags=tags or []
        )
        
        self.tasks[task.id] = task
        self._save_tasks()
        
        self.logger.info(f"Created task: {task.title}")
        return task
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus(status)
            self.tasks[task_id].updated_at = datetime.now()
            self._save_tasks()
            return True
        return False
    
    def complete_task(self, task_id: str) -> bool:
        """Mark task as completed"""
        return self.update_task_status(task_id, TaskStatus.COMPLETED.value)
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of all tasks"""
        total = len(self.tasks)
        by_status = {}
        by_priority = {}
        
        for task in self.tasks.values():
            # Count by status
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by priority (only pending tasks)
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                priority = task.priority.value
                by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Tasks due today
        today = datetime.now().date()
        due_today = sum(
            1 for task in self.tasks.values()
            if task.deadline and task.deadline.date() == today
            and task.status != TaskStatus.COMPLETED
        )
        
        # Overdue tasks
        overdue = sum(
            1 for task in self.tasks.values()
            if task.deadline and task.deadline < datetime.now()
            and task.status != TaskStatus.COMPLETED
        )
        
        return {
            'total': total,
            'by_status': by_status,
            'by_priority': by_priority,
            'due_today': due_today,
            'overdue': overdue
        }
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description"""
        query_lower = query.lower()
        return [
            task for task in self.tasks.values()
            if query_lower in task.title.lower() or 
               query_lower in task.description.lower() or
               any(query_lower in tag.lower() for tag in task.tags)
        ]
    
    def get_tasks_for_reminder(self) -> Dict[str, Any]:
        """
        Get tasks formatted for voice reminder.
        
        Returns tasks organized by urgency for natural speech.
        """
        pending = self.get_pending_tasks(timeframe="today", include_deadlines=True)
        
        # Also get overdue tasks
        overdue = [
            task for task in self.tasks.values()
            if task.deadline and task.deadline < datetime.now()
            and task.status != TaskStatus.COMPLETED
        ]
        
        # Format for voice
        reminder_data = {
            'overdue_count': len(overdue),
            'today_count': len(pending),
            'high_priority': [t for t in pending if t['priority'] == 'high'],
            'normal_priority': [t for t in pending if t['priority'] == 'normal']
        }
        
        if overdue:
            reminder_data['overdue_tasks'] = [
                {
                    'title': task.title,
                    'deadline': task.deadline.strftime('%B %d')
                }
                for task in overdue[:3]  # Limit to top 3
            ]
        
        return reminder_data
    
    # Integration methods for external backends
    async def sync_with_notion(self, notion_api_key: str, database_id: str):
        """Sync tasks with Notion database"""
        # This would implement Notion API integration
        pass
    
    async def sync_with_todoist(self, todoist_api_key: str):
        """Sync tasks with Todoist"""
        # This would implement Todoist API integration
        pass


# Example usage
def create_sample_tasks():
    """Create some sample tasks for testing"""
    task_manager = TaskManagerTool()
    
    # Create tasks
    task_manager.create_task(
        title="Review project proposal",
        description="Review and provide feedback on Q1 project proposal",
        priority="high",
        deadline=datetime.now() + timedelta(hours=5),
        tags=["work", "urgent"]
    )
    
    task_manager.create_task(
        title="Send weekly report",
        description="Compile and send weekly progress report to team",
        priority="normal",
        deadline=datetime.now() + timedelta(days=1),
        tags=["work", "recurring"]
    )
    
    task_manager.create_task(
        title="Call John about budget",
        description="Discuss Q2 budget allocation",
        priority="high",
        deadline=datetime.now() + timedelta(hours=3),
        tags=["work", "calls"]
    )
    
    task_manager.create_task(
        title="Buy groceries",
        description="Milk, eggs, bread",
        priority="low",
        tags=["personal"]
    )
    
    # Get pending tasks
    pending = task_manager.get_pending_tasks(timeframe="today")
    print(f"Tasks for today: {len(pending)}")
    for task in pending:
        print(f"- {task['title']} (Priority: {task['priority']})")
        if 'deadline' in task:
            print(f"  Due: {task['deadline']}")


if __name__ == "__main__":
    create_sample_tasks()