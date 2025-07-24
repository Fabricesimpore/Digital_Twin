"""
Human-in-the-Loop (HITL) Engine - Routes critical actions for human approval
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json
from pathlib import Path
from collections import deque
import threading
import time

from .action_classifier import CriticalityLevel, ActionClassifier


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


class ApprovalRequest:
    """Represents a request for human approval"""
    
    def __init__(self, action: Dict[str, Any], criticality: CriticalityLevel):
        self.id = str(uuid.uuid4())
        self.action = action
        self.criticality = criticality
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.resolved_at: Optional[datetime] = None
        self.response_time: Optional[float] = None
        self.human_feedback: Optional[str] = None
        self.timeout_minutes = self._get_timeout_minutes(criticality)
        
    def _get_timeout_minutes(self, criticality: CriticalityLevel) -> int:
        """Get timeout based on criticality"""
        timeouts = {
            CriticalityLevel.HIGH: 5,    # 5 minutes for critical
            CriticalityLevel.MEDIUM: 15,  # 15 minutes for medium
            CriticalityLevel.LOW: 60     # 1 hour for low (if needed)
        }
        return timeouts.get(criticality, 15)
    
    def is_expired(self) -> bool:
        """Check if request has timed out"""
        if self.status != ApprovalStatus.PENDING:
            return False
        expiry = self.created_at + timedelta(minutes=self.timeout_minutes)
        return datetime.now() > expiry
    
    def approve(self, feedback: Optional[str] = None):
        """Approve the request"""
        self.status = ApprovalStatus.APPROVED
        self.resolved_at = datetime.now()
        self.response_time = (self.resolved_at - self.created_at).total_seconds()
        self.human_feedback = feedback
    
    def deny(self, feedback: Optional[str] = None):
        """Deny the request"""
        self.status = ApprovalStatus.DENIED
        self.resolved_at = datetime.now()
        self.response_time = (self.resolved_at - self.created_at).total_seconds()
        self.human_feedback = feedback
    
    def defer(self, minutes: int = 10):
        """Defer the request"""
        self.status = ApprovalStatus.DEFERRED
        self.created_at = datetime.now() + timedelta(minutes=minutes)
        self.status = ApprovalStatus.PENDING  # Reset to pending after deferral
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'action': self.action,
            'criticality': self.criticality.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'response_time': self.response_time,
            'human_feedback': self.human_feedback,
            'timeout_minutes': self.timeout_minutes
        }


class HITLEngine:
    """Human-in-the-Loop engine for critical action approval"""
    
    def __init__(self, alert_dispatcher=None, feedback_tracker=None):
        self.classifier = ActionClassifier()
        self.alert_dispatcher = alert_dispatcher
        self.feedback_tracker = feedback_tracker
        
        # Approval queue and history
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: deque = deque(maxlen=1000)
        
        # Callbacks for different approval channels
        self.approval_handlers: Dict[str, Callable] = {}
        
        # Background task for timeout handling
        self.timeout_checker_task = None
        self.running = False
        
        # Persistence
        self.storage_path = Path("backend/data/hitl_history.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load history
        self._load_history()
    
    def start(self):
        """Start the HITL engine"""
        self.running = True
        # Start timeout checker in background thread
        threading.Thread(target=self._timeout_checker_loop, daemon=True).start()
    
    def stop(self):
        """Stop the HITL engine"""
        self.running = False
        self._save_history()
    
    async def request_approval(self, action: Dict[str, Any]) -> ApprovalRequest:
        """
        Request approval for an action
        
        Args:
            action: Action requiring approval
            
        Returns:
            ApprovalRequest object
        """
        # Classify the action
        criticality = self.classifier.classify_action(action)
        
        # Create approval request
        request = ApprovalRequest(action, criticality)
        
        # Check if action can be auto-approved based on patterns
        if self._can_auto_approve(action, criticality):
            request.status = ApprovalStatus.AUTO_APPROVED
            request.resolved_at = datetime.now()
            self.approval_history.append(request)
            return request
        
        # Add to pending queue
        self.pending_approvals[request.id] = request
        
        # Send alerts based on criticality
        if criticality == CriticalityLevel.HIGH:
            await self._send_high_priority_alert(request)
        elif criticality == CriticalityLevel.MEDIUM:
            await self._send_medium_priority_alert(request)
        
        # Track the request
        if self.feedback_tracker:
            self.feedback_tracker.track_request(request)
        
        return request
    
    def approve(self, request_id: str, feedback: Optional[str] = None) -> bool:
        """Approve a pending request"""
        if request_id not in self.pending_approvals:
            return False
        
        request = self.pending_approvals[request_id]
        request.approve(feedback)
        
        # Move to history
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        
        # Track feedback
        if self.feedback_tracker:
            self.feedback_tracker.track_approval(request)
        
        self._save_history()
        return True
    
    def deny(self, request_id: str, feedback: Optional[str] = None) -> bool:
        """Deny a pending request"""
        if request_id not in self.pending_approvals:
            return False
        
        request = self.pending_approvals[request_id]
        request.deny(feedback)
        
        # Move to history
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        
        # Track feedback
        if self.feedback_tracker:
            self.feedback_tracker.track_denial(request)
        
        self._save_history()
        return True
    
    def defer(self, request_id: str, minutes: int = 10) -> bool:
        """Defer a pending request"""
        if request_id not in self.pending_approvals:
            return False
        
        request = self.pending_approvals[request_id]
        request.defer(minutes)
        
        # Track deferral
        if self.feedback_tracker:
            self.feedback_tracker.track_deferral(request, minutes)
        
        return True
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.pending_approvals.values())
    
    def get_approval_history(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get approval history"""
        return list(self.approval_history)[-limit:]
    
    async def _send_high_priority_alert(self, request: ApprovalRequest):
        """Send high priority alert with proper error handling"""
        if not self.alert_dispatcher:
            return
        
        message = self._format_alert_message(request)
        
        # Send alerts with individual error handling and timeouts
        tasks = [
            self._safe_alert_call(self.alert_dispatcher.send_call, message, request.id, "call"),
            self._safe_alert_call(self.alert_dispatcher.send_sms, message, request.id, "sms"),
            self._safe_alert_call(self.alert_dispatcher.send_notification, message, request.id, "notification"),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        success_count = sum(1 for r in results if r is True)
        print(f"High priority alert sent via {success_count}/3 channels for request {request.id}")
    
    async def _safe_alert_call(self, alert_func, message: str, request_id: str, channel: str) -> bool:
        """Safely call alert function with timeout and error handling"""
        try:
            result = await asyncio.wait_for(alert_func(message, request_id), timeout=30.0)
            return bool(result)
        except asyncio.TimeoutError:
            print(f"Alert timeout via {channel} for request {request_id}")
            return False
        except Exception as e:
            print(f"Alert error via {channel}: {e}")
            return False
    
    async def _send_medium_priority_alert(self, request: ApprovalRequest):
        """Send medium priority alert (SMS + notification)"""
        if not self.alert_dispatcher:
            return
        
        message = self._format_alert_message(request)
        
        await asyncio.gather(
            self.alert_dispatcher.send_sms(message, request.id),
            self.alert_dispatcher.send_notification(message, request.id),
            return_exceptions=True
        )
    
    def _format_alert_message(self, request: ApprovalRequest) -> str:
        """Format alert message for human"""
        action = request.action
        action_type = action.get('type', 'Unknown')
        target = action.get('target', 'Unknown')
        content = action.get('content', '')[:100]  # Truncate long content
        
        return (
            f"🤖 Digital Twin needs approval:\n"
            f"Action: {action_type}\n"
            f"Target: {target}\n"
            f"Content: {content}...\n"
            f"Reply YES to approve, NO to deny, or DEFER to postpone"
        )
    
    def _can_auto_approve(self, action: Dict[str, Any], criticality: CriticalityLevel) -> bool:
        """Check if action can be auto-approved based on learned patterns"""
        if criticality == CriticalityLevel.HIGH:
            return False  # Never auto-approve high criticality
        
        if not self.feedback_tracker:
            return False
        
        # Check if we have enough positive history for this action type
        approval_rate = self.feedback_tracker.get_approval_rate(action)
        if approval_rate is not None and approval_rate > 0.95:
            # 95%+ approval rate means we can auto-approve
            similar_count = self.feedback_tracker.get_similar_action_count(action)
            if similar_count > 10:  # Need at least 10 similar actions
                return True
        
        return False
    
    def _timeout_checker_loop(self):
        """Background loop to check for timeouts"""
        while self.running:
            try:
                # Check for expired requests
                expired_ids = []
                for request_id, request in self.pending_approvals.items():
                    if request.is_expired():
                        expired_ids.append(request_id)
                
                # Handle expired requests
                for request_id in expired_ids:
                    request = self.pending_approvals[request_id]
                    request.status = ApprovalStatus.TIMEOUT
                    request.resolved_at = datetime.now()
                    
                    # Move to history
                    self.approval_history.append(request)
                    del self.pending_approvals[request_id]
                    
                    # Track timeout
                    if self.feedback_tracker:
                        self.feedback_tracker.track_timeout(request)
                
                # Save if we had timeouts
                if expired_ids:
                    self._save_history()
                
            except Exception as e:
                print(f"Error in timeout checker: {e}")
            
            # Check every 30 seconds
            time.sleep(30)
    
    def _save_history(self):
        """Save approval history to disk"""
        try:
            history_data = [req.to_dict() for req in self.approval_history]
            with open(self.storage_path, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            print(f"Error saving HITL history: {e}")
    
    def _load_history(self):
        """Load approval history from disk"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    history_data = json.load(f)
                
                # Reconstruct ApprovalRequest objects
                for data in history_data:
                    # Create request with saved data
                    action = data['action']
                    criticality = CriticalityLevel(data['criticality'])
                    request = ApprovalRequest(action, criticality)
                    
                    # Restore state
                    request.id = data['id']
                    request.status = ApprovalStatus(data['status'])
                    request.created_at = datetime.fromisoformat(data['created_at'])
                    if data['resolved_at']:
                        request.resolved_at = datetime.fromisoformat(data['resolved_at'])
                    request.response_time = data.get('response_time')
                    request.human_feedback = data.get('human_feedback')
                    
                    self.approval_history.append(request)
        except Exception as e:
            print(f"Error loading HITL history: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HITL statistics"""
        total_requests = len(self.approval_history)
        approved = sum(1 for r in self.approval_history if r.status == ApprovalStatus.APPROVED)
        denied = sum(1 for r in self.approval_history if r.status == ApprovalStatus.DENIED)
        timeout = sum(1 for r in self.approval_history if r.status == ApprovalStatus.TIMEOUT)
        auto_approved = sum(1 for r in self.approval_history if r.status == ApprovalStatus.AUTO_APPROVED)
        
        avg_response_time = None
        response_times = [r.response_time for r in self.approval_history if r.response_time]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'total_requests': total_requests,
            'approved': approved,
            'denied': denied,
            'timeout': timeout,
            'auto_approved': auto_approved,
            'approval_rate': approved / total_requests if total_requests > 0 else 0,
            'avg_response_time_seconds': avg_response_time,
            'pending_count': len(self.pending_approvals)
        }


if __name__ == "__main__":
    # Example usage
    async def test_hitl():
        engine = HITLEngine()
        engine.start()
        
        # Test approval request
        test_action = {
            'type': 'email_send',
            'target': 'CEO@company.com',
            'content': 'Quarterly report attached',
            'context': {}
        }
        
        request = await engine.request_approval(test_action)
        print(f"Created approval request: {request.id}")
        print(f"Criticality: {request.criticality.value}")
        print(f"Status: {request.status.value}")
        
        # Simulate approval
        engine.approve(request.id, "Looks good, send it")
        
        # Check stats
        stats = engine.get_stats()
        print(f"\nHITL Stats: {json.dumps(stats, indent=2)}")
        
        engine.stop()
    
    # Run test
    asyncio.run(test_hitl())