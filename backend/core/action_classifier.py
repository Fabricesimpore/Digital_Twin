"""
Action Classifier - Determines criticality level of actions
"""
from enum import Enum
from typing import Dict, Any, Optional
import re
import yaml
from pathlib import Path


class CriticalityLevel(Enum):
    """Action criticality levels"""
    LOW = "low"      # Auto-execute
    MEDIUM = "medium"  # Notify but don't wait
    HIGH = "high"    # Require user confirmation


class ActionType(Enum):
    """Types of actions the twin can take"""
    EMAIL_SEND = "email_send"
    EMAIL_REPLY = "email_reply"
    CALENDAR_CREATE = "calendar_create"
    CALENDAR_MODIFY = "calendar_modify"
    CALL_MAKE = "call_make"
    SMS_SEND = "sms_send"
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    TASK_CREATE = "task_create"
    REMINDER_SET = "reminder_set"
    FOCUS_SESSION = "focus_session"
    ARCHIVE = "archive"
    LOG = "log"
    SEARCH = "search"
    ANALYZE = "analyze"


class ActionClassifier:
    """Classifies actions by criticality level"""
    
    def __init__(self, rules_path: Optional[Path] = None):
        """Initialize with custom rules if provided"""
        self.rules_path = rules_path or Path("backend/config/criticality_rules.yaml")
        self.rules = self._load_rules()
        self.vip_contacts = self._load_vip_contacts()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load criticality rules from config"""
        if self.rules_path.exists():
            with open(self.rules_path, 'r') as f:
                return yaml.safe_load(f)
        return self._get_default_rules()
    
    def _load_vip_contacts(self) -> set:
        """Load VIP contacts that always require approval"""
        if self.rules_path.exists():
            with open(self.rules_path, 'r') as f:
                rules = yaml.safe_load(f)
                return set(rules.get('vip_contacts', []))
        return {"CEO", "CTO", "Investor", "Board Member", "Client"}
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Default criticality rules"""
        return {
            'action_defaults': {
                ActionType.EMAIL_SEND.value: CriticalityLevel.MEDIUM.value,
                ActionType.EMAIL_REPLY.value: CriticalityLevel.MEDIUM.value,
                ActionType.CALENDAR_CREATE.value: CriticalityLevel.MEDIUM.value,
                ActionType.CALENDAR_MODIFY.value: CriticalityLevel.HIGH.value,
                ActionType.CALL_MAKE.value: CriticalityLevel.HIGH.value,
                ActionType.SMS_SEND.value: CriticalityLevel.MEDIUM.value,
                ActionType.FILE_CREATE.value: CriticalityLevel.LOW.value,
                ActionType.FILE_MODIFY.value: CriticalityLevel.MEDIUM.value,
                ActionType.TASK_CREATE.value: CriticalityLevel.LOW.value,
                ActionType.REMINDER_SET.value: CriticalityLevel.LOW.value,
                ActionType.FOCUS_SESSION.value: CriticalityLevel.LOW.value,
                ActionType.ARCHIVE.value: CriticalityLevel.LOW.value,
                ActionType.LOG.value: CriticalityLevel.LOW.value,
                ActionType.SEARCH.value: CriticalityLevel.LOW.value,
                ActionType.ANALYZE.value: CriticalityLevel.LOW.value,
            },
            'keyword_patterns': {
                'high': ['urgent', 'emergency', 'critical', 'asap', 'deadline'],
                'medium': ['important', 'priority', 'review', 'approve'],
                'low': ['fyi', 'archive', 'log', 'reminder']
            },
            'time_sensitive': {
                'business_hours': {'start': 9, 'end': 18},
                'increase_criticality_outside_hours': True
            }
        }
    
    def classify_action(self, action: Dict[str, Any]) -> CriticalityLevel:
        """
        Classify an action's criticality level
        
        Args:
            action: Dict with keys:
                - type: ActionType
                - target: str (recipient/target of action)
                - content: str (action content)
                - context: Dict (additional context)
        
        Returns:
            CriticalityLevel
        """
        action_type = action.get('type', '')
        target = action.get('target', '')
        content = action.get('content', '')
        context = action.get('context', {})
        
        # Check VIP contacts - always HIGH
        if self._is_vip_target(target):
            return CriticalityLevel.HIGH
        
        # Get base criticality from action type
        base_level = self._get_base_criticality(action_type)
        
        # Adjust based on content keywords
        keyword_level = self._analyze_keywords(content)
        
        # Adjust based on context (time, urgency, etc)
        context_level = self._analyze_context(context)
        
        # Return highest criticality level
        levels = [base_level, keyword_level, context_level]
        levels = [l for l in levels if l is not None]
        
        if CriticalityLevel.HIGH in levels:
            return CriticalityLevel.HIGH
        elif CriticalityLevel.MEDIUM in levels:
            return CriticalityLevel.MEDIUM
        else:
            return CriticalityLevel.LOW
    
    def _is_vip_target(self, target: str) -> bool:
        """Check if target is a VIP"""
        target_lower = target.lower()
        for vip in self.vip_contacts:
            if vip.lower() in target_lower:
                return True
        return False
    
    def _get_base_criticality(self, action_type: str) -> CriticalityLevel:
        """Get base criticality from action type"""
        defaults = self.rules.get('action_defaults', {})
        level_str = defaults.get(action_type, 'medium')
        return CriticalityLevel(level_str)
    
    def _analyze_keywords(self, content: str) -> Optional[CriticalityLevel]:
        """Analyze content for criticality keywords"""
        content_lower = content.lower()
        patterns = self.rules.get('keyword_patterns', {})
        
        for level, keywords in patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return CriticalityLevel(level)
        return None
    
    def _analyze_context(self, context: Dict[str, Any]) -> Optional[CriticalityLevel]:
        """Analyze context for criticality factors"""
        # Check if action is time-sensitive
        import datetime
        now = datetime.datetime.now()
        time_rules = self.rules.get('time_sensitive', {})
        
        if time_rules.get('increase_criticality_outside_hours'):
            business_hours = time_rules.get('business_hours', {})
            start_hour = business_hours.get('start', 9)
            end_hour = business_hours.get('end', 18)
            
            if now.hour < start_hour or now.hour >= end_hour:
                # Outside business hours, increase criticality
                return CriticalityLevel.MEDIUM
        
        # Check for explicit urgency in context
        if context.get('urgent', False):
            return CriticalityLevel.HIGH
        
        return None
    
    def explain_classification(self, action: Dict[str, Any]) -> str:
        """Explain why an action was classified at a certain level"""
        level = self.classify_action(action)
        reasons = []
        
        target = action.get('target', '')
        if self._is_vip_target(target):
            reasons.append(f"Target '{target}' is a VIP contact")
        
        action_type = action.get('type', '')
        base_level = self._get_base_criticality(action_type)
        reasons.append(f"Action type '{action_type}' has base level: {base_level.value}")
        
        content = action.get('content', '')
        keyword_level = self._analyze_keywords(content)
        if keyword_level:
            reasons.append(f"Content contains {keyword_level.value} priority keywords")
        
        context = action.get('context', {})
        context_level = self._analyze_context(context)
        if context_level:
            reasons.append("Action is outside business hours or marked urgent")
        
        return f"Classification: {level.value}\nReasons:\n" + "\n".join(f"- {r}" for r in reasons)


if __name__ == "__main__":
    # Example usage
    classifier = ActionClassifier()
    
    # Test various actions
    test_actions = [
        {
            'type': ActionType.EMAIL_SEND.value,
            'target': 'john@example.com',
            'content': 'Meeting notes from today',
            'context': {}
        },
        {
            'type': ActionType.EMAIL_SEND.value,
            'target': 'CEO@company.com',
            'content': 'Quarterly report ready',
            'context': {}
        },
        {
            'type': ActionType.REMINDER_SET.value,
            'target': 'self',
            'content': 'Review PRs',
            'context': {}
        },
        {
            'type': ActionType.CALL_MAKE.value,
            'target': 'Client - Acme Corp',
            'content': 'Follow up on proposal',
            'context': {'urgent': True}
        }
    ]
    
    for action in test_actions:
        print("\n" + "="*50)
        print(f"Action: {action['type']} to {action['target']}")
        print(classifier.explain_classification(action))