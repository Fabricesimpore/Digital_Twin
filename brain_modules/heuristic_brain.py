"""
Heuristic Brain for Digital Twin

This module provides fast, pattern-based decision making for situations
where full deliberation isn't needed. It uses learned behavioral patterns
and simple heuristics to make quick decisions.

Use cases:
- Time-sensitive situations
- Routine decisions
- High-confidence patterns from past feedback
- Low-stakes choices
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
import re
from enum import Enum


class HeuristicType(Enum):
    """Types of heuristics"""
    TIME_BASED = "time_based"           # Based on time of day/week
    PATTERN_MATCH = "pattern_match"     # Based on situation similarity
    PRIORITY_RULE = "priority_rule"     # Based on priority/urgency rules
    ENERGY_BASED = "energy_based"       # Based on current energy state
    RELATIONSHIP_RULE = "relationship_rule"  # Based on person/relationship
    HABIT = "habit"                     # Learned habitual responses


@dataclass
class Heuristic:
    """A fast decision rule"""
    id: str
    rule_type: HeuristicType
    condition: str  # When this rule applies
    action: str     # What to do
    confidence: float = 0.8
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rule_type': self.rule_type.value,
            'condition': self.condition,
            'action': self.action,
            'confidence': self.confidence,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Heuristic':
        return cls(
            id=data['id'],
            rule_type=HeuristicType(data['rule_type']),
            condition=data['condition'],
            action=data['action'],
            confidence=data.get('confidence', 0.8),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        )


@dataclass
class HeuristicDecision:
    """Result of a heuristic decision"""
    action: str
    heuristic_used: Heuristic
    confidence: float
    reasoning: str
    alternatives_skipped: int  # How many alternatives we didn't consider
    time_saved: float  # Estimated time saved by using heuristic
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'heuristic_id': self.heuristic_used.id,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'alternatives_skipped': self.alternatives_skipped,
            'time_saved': self.time_saved
        }


class HeuristicBrain:
    """
    Fast decision-making system using learned patterns and heuristics.
    
    This provides quick decisions for routine situations without requiring
    full deliberation, making the twin more responsive.
    """
    
    def __init__(self, persona: Dict[str, Any], storage_file: str = "heuristics.json"):
        self.persona = persona
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        
        # Heuristic rules
        self.heuristics: Dict[str, Heuristic] = {}
        
        # Decision history for learning
        self.decision_history: List[HeuristicDecision] = []
        
        # Load existing heuristics
        self._load_heuristics()
        
        # Initialize default heuristics if none exist
        if not self.heuristics:
            self._initialize_default_heuristics()
    
    def _load_heuristics(self):
        """Load heuristics from storage"""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                
                for heuristic_data in data.get('heuristics', []):
                    heuristic = Heuristic.from_dict(heuristic_data)
                    self.heuristics[heuristic.id] = heuristic
                
                self.logger.info(f"Loaded {len(self.heuristics)} heuristics")
                
        except FileNotFoundError:
            self.logger.info("No existing heuristics found")
        except Exception as e:
            self.logger.error(f"Error loading heuristics: {e}")
    
    def _save_heuristics(self):
        """Save heuristics to storage"""
        try:
            data = {
                'heuristics': [h.to_dict() for h in self.heuristics.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving heuristics: {e}")
    
    def _initialize_default_heuristics(self):
        """Initialize default heuristics based on persona"""
        
        default_heuristics = []
        
        # Time-based heuristics
        default_heuristics.extend([
            Heuristic(
                id="morning_urgent_email",
                rule_type=HeuristicType.TIME_BASED,
                condition="urgent email AND time < 10:00",
                action="Respond immediately with brief acknowledgment and action plan",
                confidence=0.9
            ),
            Heuristic(
                id="evening_non_urgent",
                rule_type=HeuristicType.TIME_BASED,
                condition="non-urgent request AND time > 18:00",
                action="Acknowledge receipt and defer to tomorrow",
                confidence=0.8
            ),
            Heuristic(
                id="lunch_meeting_request",
                rule_type=HeuristicType.TIME_BASED,
                condition="meeting request AND time 12:00-13:00",
                action="Suggest alternative time to protect lunch break",
                confidence=0.85
            )
        ])
        
        # Priority-based heuristics
        default_heuristics.extend([
            Heuristic(
                id="client_urgent_escalate",
                rule_type=HeuristicType.PRIORITY_RULE,
                condition="client request AND marked urgent",
                action="Drop current task and address immediately",
                confidence=0.95
            ),
            Heuristic(
                id="low_priority_batch",
                rule_type=HeuristicType.PRIORITY_RULE,
                condition="low priority task AND multiple similar tasks",
                action="Batch with similar tasks for later processing",
                confidence=0.7
            )
        ])
        
        # Relationship-based heuristics
        if 'connection' in self.persona.get('values', []):
            default_heuristics.extend([
                Heuristic(
                    id="friend_social_request",
                    rule_type=HeuristicType.RELATIONSHIP_RULE,
                    condition="friend request AND social activity",
                    action="Accept if no major conflicts, suggest alternative if busy",
                    confidence=0.8
                ),
                Heuristic(
                    id="boss_request_prioritize",
                    rule_type=HeuristicType.RELATIONSHIP_RULE,
                    condition="boss request AND not conflicting with other boss priorities",
                    action="Prioritize and provide timeline",
                    confidence=0.9
                )
            ])
        
        # Energy-based heuristics
        default_heuristics.extend([
            Heuristic(
                id="low_energy_defer_complex",
                rule_type=HeuristicType.ENERGY_BASED,
                condition="low energy AND complex task",
                action="Defer complex work to high energy time, do simple tasks",
                confidence=0.85
            ),
            Heuristic(
                id="high_energy_tackle_hard",
                rule_type=HeuristicType.ENERGY_BASED,
                condition="high energy AND challenging task available",
                action="Prioritize the challenging task while energy is high",
                confidence=0.9
            )
        ])
        
        # Efficiency-based (if efficiency is a trait)
        if 'efficient' in self.persona.get('traits', []):
            default_heuristics.extend([
                Heuristic(
                    id="quick_decision_threshold",
                    rule_type=HeuristicType.PATTERN_MATCH,
                    condition="decision time > 5 minutes AND low stakes",
                    action="Choose good enough option rather than optimize",
                    confidence=0.75
                ),
                Heuristic(
                    id="email_batch_process",
                    rule_type=HeuristicType.HABIT,
                    condition="multiple emails AND similar response needed",
                    action="Process in batch with template responses",
                    confidence=0.8
                )
            ])
        
        # Add all default heuristics
        for heuristic in default_heuristics:
            self.heuristics[heuristic.id] = heuristic
        
        self._save_heuristics()
        self.logger.info(f"Initialized {len(default_heuristics)} default heuristics")
    
    def can_use_heuristic(self, 
                         situation: str,
                         context: Dict[str, Any] = None,
                         time_pressure: bool = False,
                         energy_level: str = "medium") -> bool:
        """
        Determine if we should use heuristic decision-making.
        
        Args:
            situation: The situation description
            context: Additional context
            time_pressure: Whether there's time pressure
            energy_level: Current energy level
            
        Returns:
            bool: Whether to use heuristic reasoning
        """
        
        # Always use heuristics if time pressure
        if time_pressure:
            return True
        
        # Use heuristics for low-energy situations
        if energy_level == "low":
            return True
        
        # Use heuristics for routine patterns
        routine_keywords = ["email", "meeting", "call", "task", "reminder"]
        if any(keyword in situation.lower() for keyword in routine_keywords):
            return True
        
        # Use heuristics if we have high-confidence patterns
        matching_heuristics = self._find_matching_heuristics(situation, context)
        if any(h.confidence > 0.8 and h.success_rate > 0.7 for h in matching_heuristics):
            return True
        
        # Don't use heuristics for complex or high-stakes situations
        complex_keywords = ["conflict", "important decision", "major", "strategic"]
        if any(keyword in situation.lower() for keyword in complex_keywords):
            return False
        
        return False
    
    def make_heuristic_decision(self, 
                               situation: str,
                               context: Dict[str, Any] = None) -> Optional[HeuristicDecision]:
        """
        Make a quick decision using heuristics.
        
        Args:
            situation: The situation description
            context: Additional context
            
        Returns:
            HeuristicDecision if applicable, None if no heuristic matches
        """
        
        # Find matching heuristics
        matching_heuristics = self._find_matching_heuristics(situation, context)
        
        if not matching_heuristics:
            return None
        
        # Choose best heuristic (highest confidence * success_rate)
        best_heuristic = max(
            matching_heuristics,
            key=lambda h: h.confidence * (h.success_rate if h.success_rate > 0 else 0.5)
        )
        
        # Update usage
        best_heuristic.last_used = datetime.now()
        self._save_heuristics()
        
        # Create decision
        decision = HeuristicDecision(
            action=best_heuristic.action,
            heuristic_used=best_heuristic,
            confidence=best_heuristic.confidence * best_heuristic.success_rate,
            reasoning=f"Applied {best_heuristic.rule_type.value} rule: {best_heuristic.condition}",
            alternatives_skipped=len(matching_heuristics) - 1,
            time_saved=self._estimate_time_saved(best_heuristic.rule_type)
        )
        
        self.decision_history.append(decision)
        
        self.logger.info(f"Heuristic decision: {decision.action} (confidence: {decision.confidence:.2f})")
        
        return decision
    
    def _find_matching_heuristics(self, 
                                 situation: str,
                                 context: Dict[str, Any] = None) -> List[Heuristic]:
        """Find heuristics that match the current situation"""
        
        matching = []
        situation_lower = situation.lower()
        current_time = datetime.now()
        
        for heuristic in self.heuristics.values():
            if self._heuristic_matches(heuristic, situation_lower, context, current_time):
                matching.append(heuristic)
        
        return matching
    
    def _heuristic_matches(self, 
                          heuristic: Heuristic,
                          situation_lower: str,
                          context: Dict[str, Any] = None,
                          current_time: datetime = None) -> bool:
        """Check if a heuristic matches the current situation"""
        
        condition = heuristic.condition.lower()
        context = context or {}
        
        # Parse condition for different rule types
        if heuristic.rule_type == HeuristicType.TIME_BASED:
            return self._match_time_condition(condition, situation_lower, current_time)
        
        elif heuristic.rule_type == HeuristicType.PATTERN_MATCH:
            return self._match_pattern_condition(condition, situation_lower, context)
        
        elif heuristic.rule_type == HeuristicType.PRIORITY_RULE:
            return self._match_priority_condition(condition, situation_lower, context)
        
        elif heuristic.rule_type == HeuristicType.ENERGY_BASED:
            return self._match_energy_condition(condition, situation_lower, context)
        
        elif heuristic.rule_type == HeuristicType.RELATIONSHIP_RULE:
            return self._match_relationship_condition(condition, situation_lower, context)
        
        elif heuristic.rule_type == HeuristicType.HABIT:
            return self._match_habit_condition(condition, situation_lower, context)
        
        return False
    
    def _match_time_condition(self, condition: str, situation: str, current_time: datetime) -> bool:
        """Match time-based conditions"""
        
        # Extract time constraints from condition
        time_match = re.search(r'time\s*([<>]=?)\s*(\d{1,2}):?(\d{2})?', condition)
        if time_match:
            operator = time_match.group(1)
            hour = int(time_match.group(2))
            minute = int(time_match.group(3)) if time_match.group(3) else 0
            
            condition_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if operator == '<' and current_time >= condition_time:
                return False
            elif operator == '>' and current_time <= condition_time:
                return False
        
        # Check if other parts of condition match
        condition_parts = condition.split(' and ')
        for part in condition_parts:
            if 'time' not in part and part.strip() not in situation:
                return False
        
        return True
    
    def _match_pattern_condition(self, condition: str, situation: str, context: Dict[str, Any]) -> bool:
        """Match pattern-based conditions"""
        
        # Simple keyword matching for now
        condition_keywords = condition.replace(' and ', '|').replace(' or ', '|').split('|')
        
        for keyword in condition_keywords:
            keyword = keyword.strip()
            if keyword in situation:
                return True
        
        return False
    
    def _match_priority_condition(self, condition: str, situation: str, context: Dict[str, Any]) -> bool:
        """Match priority-based conditions"""
        
        # Check for priority keywords
        if 'urgent' in condition and 'urgent' not in situation:
            return False
        
        if 'client' in condition and 'client' not in situation:
            return False
        
        if 'low priority' in condition and 'low' not in context.get('priority', ''):
            return False
        
        return True
    
    def _match_energy_condition(self, condition: str, situation: str, context: Dict[str, Any]) -> bool:
        """Match energy-based conditions"""
        
        current_energy = context.get('current_energy', 'medium')
        
        if 'low energy' in condition and current_energy != 'low':
            return False
        
        if 'high energy' in condition and current_energy != 'high':
            return False
        
        # Check for task complexity
        if 'complex task' in condition:
            complex_keywords = ['complex', 'difficult', 'challenging', 'analysis', 'strategic']
            if not any(keyword in situation for keyword in complex_keywords):
                return False
        
        return True
    
    def _match_relationship_condition(self, condition: str, situation: str, context: Dict[str, Any]) -> bool:
        """Match relationship-based conditions"""
        
        # Check for relationship keywords
        relationship_keywords = ['friend', 'boss', 'client', 'colleague', 'team']
        
        for rel_type in relationship_keywords:
            if rel_type in condition and rel_type in situation:
                return True
        
        return False
    
    def _match_habit_condition(self, condition: str, situation: str, context: Dict[str, Any]) -> bool:
        """Match habit-based conditions"""
        
        # Simple pattern matching for habits
        return any(word in situation for word in condition.split() if len(word) > 3)
    
    def _estimate_time_saved(self, rule_type: HeuristicType) -> float:
        """Estimate time saved by using this heuristic"""
        
        time_savings = {
            HeuristicType.TIME_BASED: 2.0,      # 2 minutes
            HeuristicType.PATTERN_MATCH: 5.0,   # 5 minutes
            HeuristicType.PRIORITY_RULE: 1.0,   # 1 minute
            HeuristicType.ENERGY_BASED: 3.0,    # 3 minutes
            HeuristicType.RELATIONSHIP_RULE: 2.0, # 2 minutes
            HeuristicType.HABIT: 1.0             # 1 minute
        }
        
        return time_savings.get(rule_type, 2.0)
    
    def learn_from_feedback(self, 
                           decision: HeuristicDecision,
                           actual_outcome: str,
                           satisfaction: float) -> None:
        """
        Learn from feedback on heuristic decisions.
        
        Args:
            decision: The heuristic decision made
            actual_outcome: What actually happened
            satisfaction: How satisfied (0-1) with the outcome
        """
        
        heuristic = decision.heuristic_used
        
        # Update success/failure counts
        if satisfaction >= 0.7:  # Satisfied with outcome
            heuristic.success_count += 1
        else:
            heuristic.failure_count += 1
        
        # Adjust confidence based on satisfaction
        if satisfaction >= 0.8:
            heuristic.confidence = min(1.0, heuristic.confidence + 0.05)
        elif satisfaction <= 0.3:
            heuristic.confidence = max(0.1, heuristic.confidence - 0.1)
        
        self._save_heuristics()
        self.logger.info(f"Updated heuristic {heuristic.id}: satisfaction={satisfaction:.2f}, "
                        f"success_rate={heuristic.success_rate:.2f}")
    
    def add_custom_heuristic(self, 
                            condition: str,
                            action: str,
                            rule_type: HeuristicType = HeuristicType.PATTERN_MATCH,
                            confidence: float = 0.7) -> Heuristic:
        """Add a custom heuristic rule"""
        
        import uuid
        heuristic = Heuristic(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            rule_type=rule_type,
            condition=condition,
            action=action,
            confidence=confidence
        )
        
        self.heuristics[heuristic.id] = heuristic
        self._save_heuristics()
        
        self.logger.info(f"Added custom heuristic: {condition} -> {action}")
        return heuristic
    
    def get_heuristic_stats(self) -> Dict[str, Any]:
        """Get statistics about heuristic usage"""
        
        if not self.heuristics:
            return {"message": "No heuristics available"}
        
        stats = {
            "total_heuristics": len(self.heuristics),
            "total_decisions": len(self.decision_history),
            "by_type": {},
            "top_performing": [],
            "avg_confidence": 0.0,
            "avg_time_saved": 0.0
        }
        
        # Stats by type
        for heuristic in self.heuristics.values():
            rule_type = heuristic.rule_type.value
            if rule_type not in stats["by_type"]:
                stats["by_type"][rule_type] = {"count": 0, "avg_success_rate": 0.0}
            
            stats["by_type"][rule_type]["count"] += 1
            stats["by_type"][rule_type]["avg_success_rate"] += heuristic.success_rate
        
        # Average success rates
        for rule_type in stats["by_type"]:
            count = stats["by_type"][rule_type]["count"]
            stats["by_type"][rule_type]["avg_success_rate"] /= count
        
        # Top performing heuristics
        top_heuristics = sorted(
            self.heuristics.values(),
            key=lambda h: h.success_rate * h.confidence,
            reverse=True
        )[:5]
        
        stats["top_performing"] = [
            {
                "id": h.id,
                "condition": h.condition,
                "success_rate": h.success_rate,
                "confidence": h.confidence
            }
            for h in top_heuristics
        ]
        
        # Overall averages
        if self.heuristics:
            stats["avg_confidence"] = sum(h.confidence for h in self.heuristics.values()) / len(self.heuristics)
        
        if self.decision_history:
            stats["avg_time_saved"] = sum(d.time_saved for d in self.decision_history) / len(self.decision_history)
        
        return stats