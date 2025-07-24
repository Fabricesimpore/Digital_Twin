"""
Feedback Tracker - Learns from human decisions to improve future classifications
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class FeedbackEntry:
    """Represents a single feedback entry"""
    action_type: str
    action_target: str
    criticality: str
    decision: str  # approved, denied, timeout
    response_time: Optional[float]
    timestamp: datetime
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class PatternMatcher:
    """Matches actions to find similar patterns"""
    
    def __init__(self):
        self.feature_weights = {
            'action_type': 0.4,
            'target_domain': 0.3,
            'time_of_day': 0.1,
            'day_of_week': 0.1,
            'content_keywords': 0.1
        }
    
    def extract_features(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from an action"""
        features = {}
        
        # Action type
        features['action_type'] = action.get('type', 'unknown')
        
        # Target domain (e.g., CEO, Client, Team)
        target = action.get('target', '')
        if '@' in target:
            domain = target.split('@')[1] if '@' in target else 'unknown'
            features['target_domain'] = domain
        else:
            # Extract role/category from target
            target_lower = target.lower()
            if any(vip in target_lower for vip in ['ceo', 'cto', 'investor', 'board']):
                features['target_domain'] = 'vip'
            elif any(client in target_lower for client in ['client', 'customer']):
                features['target_domain'] = 'client'
            else:
                features['target_domain'] = 'other'
        
        # Time features
        now = datetime.now()
        features['time_of_day'] = now.hour // 6  # 0-3 (night, morning, afternoon, evening)
        features['day_of_week'] = now.weekday()  # 0-6
        
        # Content keywords
        content = action.get('content', '').lower()
        keywords = []
        for keyword in ['urgent', 'important', 'meeting', 'deadline', 'review', 'report']:
            if keyword in content:
                keywords.append(keyword)
        features['content_keywords'] = ','.join(sorted(keywords))
        
        return features
    
    def calculate_similarity(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> float:
        """Calculate similarity between two actions (0-1)"""
        features1 = self.extract_features(action1)
        features2 = self.extract_features(action2)
        
        total_similarity = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in ['time_of_day', 'day_of_week']:
                # Numeric features - use distance
                diff = abs(features1[feature] - features2[feature])
                max_diff = 3 if feature == 'time_of_day' else 6
                similarity = 1.0 - (diff / max_diff)
            else:
                # Categorical features - exact match
                similarity = 1.0 if features1[feature] == features2[feature] else 0.0
            
            total_similarity += weight * similarity
        
        return total_similarity
    
    def find_similar_actions(self, action: Dict[str, Any], history: List[FeedbackEntry], 
                           min_similarity: float = 0.7) -> List[Tuple[FeedbackEntry, float]]:
        """Find similar actions in history"""
        similar = []
        
        for entry in history:
            historical_action = {
                'type': entry.action_type,
                'target': entry.action_target,
                'content': entry.context.get('content', '')
            }
            
            similarity = self.calculate_similarity(action, historical_action)
            if similarity >= min_similarity:
                similar.append((entry, similarity))
        
        # Sort by similarity (highest first)
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar


class FeedbackTracker:
    """Tracks and learns from human feedback on actions"""
    
    def __init__(self):
        self.history: List[FeedbackEntry] = []
        self.pattern_matcher = PatternMatcher()
        self.storage_path = Path("backend/data/feedback_history.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Learning parameters
        self.min_history_for_learning = 5
        self.confidence_threshold = 0.8
        
        # Load historical data
        self._load_history()
    
    def track_request(self, request):
        """Track a new approval request"""
        # Just log that we're tracking - actual feedback comes later
        pass
    
    def track_approval(self, request):
        """Track an approved action"""
        entry = FeedbackEntry(
            action_type=request.action.get('type'),
            action_target=request.action.get('target'),
            criticality=request.criticality.value,
            decision='approved',
            response_time=request.response_time,
            timestamp=request.resolved_at,
            context=request.action.get('context', {})
        )
        self.history.append(entry)
        self._save_history()
    
    def track_denial(self, request):
        """Track a denied action"""
        entry = FeedbackEntry(
            action_type=request.action.get('type'),
            action_target=request.action.get('target'),
            criticality=request.criticality.value,
            decision='denied',
            response_time=request.response_time,
            timestamp=request.resolved_at,
            context=request.action.get('context', {})
        )
        self.history.append(entry)
        self._save_history()
    
    def track_timeout(self, request):
        """Track a timed-out action"""
        entry = FeedbackEntry(
            action_type=request.action.get('type'),
            action_target=request.action.get('target'),
            criticality=request.criticality.value,
            decision='timeout',
            response_time=None,
            timestamp=request.resolved_at,
            context=request.action.get('context', {})
        )
        self.history.append(entry)
        self._save_history()
    
    def track_deferral(self, request, minutes: int):
        """Track a deferred action"""
        # Log deferral in context for pattern learning
        context = request.action.get('context', {})
        context['deferred_minutes'] = minutes
        
        entry = FeedbackEntry(
            action_type=request.action.get('type'),
            action_target=request.action.get('target'),
            criticality=request.criticality.value,
            decision='deferred',
            response_time=None,
            timestamp=datetime.now(),
            context=context
        )
        self.history.append(entry)
        self._save_history()
    
    def get_approval_rate(self, action: Dict[str, Any]) -> Optional[float]:
        """Get historical approval rate for similar actions"""
        similar_actions = self.pattern_matcher.find_similar_actions(action, self.history)
        
        if len(similar_actions) < self.min_history_for_learning:
            return None
        
        # Calculate weighted approval rate
        total_weight = 0.0
        weighted_approvals = 0.0
        
        for entry, similarity in similar_actions[:20]:  # Use top 20 most similar
            weight = similarity
            total_weight += weight
            
            if entry.decision == 'approved':
                weighted_approvals += weight
        
        if total_weight > 0:
            return weighted_approvals / total_weight
        return None
    
    def get_similar_action_count(self, action: Dict[str, Any]) -> int:
        """Count similar actions in history"""
        similar_actions = self.pattern_matcher.find_similar_actions(action, self.history)
        return len(similar_actions)
    
    def get_average_response_time(self, action: Dict[str, Any]) -> Optional[float]:
        """Get average response time for similar actions"""
        similar_actions = self.pattern_matcher.find_similar_actions(action, self.history)
        
        response_times = []
        for entry, _ in similar_actions:
            if entry.response_time is not None:
                response_times.append(entry.response_time)
        
        if response_times:
            return np.mean(response_times)
        return None
    
    def get_time_patterns(self) -> Dict[str, Any]:
        """Analyze time-based patterns in approvals"""
        patterns = {
            'by_hour': defaultdict(lambda: {'approved': 0, 'denied': 0}),
            'by_day': defaultdict(lambda: {'approved': 0, 'denied': 0}),
            'response_time_by_criticality': defaultdict(list)
        }
        
        for entry in self.history:
            hour = entry.timestamp.hour
            day = entry.timestamp.weekday()
            
            if entry.decision in ['approved', 'denied']:
                patterns['by_hour'][hour][entry.decision] += 1
                patterns['by_day'][day][entry.decision] += 1
            
            if entry.response_time is not None:
                patterns['response_time_by_criticality'][entry.criticality].append(entry.response_time)
        
        # Calculate averages
        for criticality, times in patterns['response_time_by_criticality'].items():
            if times:
                patterns['response_time_by_criticality'][criticality] = {
                    'mean': np.mean(times),
                    'median': np.median(times),
                    'std': np.std(times)
                }
        
        return dict(patterns)
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learned patterns"""
        insights = {
            'total_feedback_entries': len(self.history),
            'approval_rate': 0,
            'common_approved_patterns': [],
            'common_denied_patterns': [],
            'average_response_times': {},
            'time_patterns': self.get_time_patterns()
        }
        
        # Overall approval rate
        if self.history:
            approved = sum(1 for e in self.history if e.decision == 'approved')
            insights['approval_rate'] = approved / len(self.history)
        
        # Find common patterns
        action_patterns = defaultdict(lambda: {'approved': 0, 'denied': 0})
        
        for entry in self.history:
            pattern_key = f"{entry.action_type}|{entry.action_target}"
            if entry.decision in ['approved', 'denied']:
                action_patterns[pattern_key][entry.decision] += 1
        
        # Sort patterns by frequency
        for pattern, counts in action_patterns.items():
            total = counts['approved'] + counts['denied']
            if total >= 3:  # Minimum occurrences
                approval_rate = counts['approved'] / total
                pattern_info = {
                    'pattern': pattern,
                    'total_count': total,
                    'approval_rate': approval_rate
                }
                
                if approval_rate > 0.7:
                    insights['common_approved_patterns'].append(pattern_info)
                elif approval_rate < 0.3:
                    insights['common_denied_patterns'].append(pattern_info)
        
        # Sort by total count
        insights['common_approved_patterns'].sort(key=lambda x: x['total_count'], reverse=True)
        insights['common_denied_patterns'].sort(key=lambda x: x['total_count'], reverse=True)
        
        return insights
    
    def suggest_criticality_adjustment(self, action: Dict[str, Any]) -> Optional[str]:
        """Suggest criticality level based on historical patterns"""
        similar_actions = self.pattern_matcher.find_similar_actions(action, self.history)
        
        if len(similar_actions) < self.min_history_for_learning:
            return None
        
        # Check if user always approves quickly
        quick_approvals = 0
        slow_approvals = 0
        denials = 0
        
        for entry, similarity in similar_actions[:10]:
            if entry.decision == 'approved' and entry.response_time:
                if entry.response_time < 60:  # Less than 1 minute
                    quick_approvals += 1
                else:
                    slow_approvals += 1
            elif entry.decision == 'denied':
                denials += 1
        
        total = quick_approvals + slow_approvals + denials
        
        if total >= 5:
            if quick_approvals / total > 0.8:
                return "lower"  # User always approves quickly, can lower criticality
            elif denials / total > 0.6:
                return "higher"  # User often denies, should increase criticality
        
        return None
    
    def _save_history(self):
        """Save feedback history to disk"""
        try:
            data = [entry.to_dict() for entry in self.history]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback history: {e}")
    
    def _load_history(self):
        """Load feedback history from disk"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                self.history = [FeedbackEntry.from_dict(entry) for entry in data]
                print(f"Loaded {len(self.history)} feedback entries")
        except Exception as e:
            print(f"Error loading feedback history: {e}")


if __name__ == "__main__":
    # Example usage
    tracker = FeedbackTracker()
    
    # Simulate some feedback
    from action_classifier import CriticalityLevel
    
    class MockRequest:
        def __init__(self, action, criticality, decision, response_time=None):
            self.action = action
            self.criticality = CriticalityLevel(criticality)
            self.resolved_at = datetime.now()
            self.response_time = response_time
    
    # Track some approvals
    test_actions = [
        MockRequest(
            {'type': 'email_send', 'target': 'team@company.com', 'content': 'Weekly update'},
            'low', 'approved', 30
        ),
        MockRequest(
            {'type': 'email_send', 'target': 'CEO@company.com', 'content': 'Quarterly report'},
            'high', 'approved', 120
        ),
        MockRequest(
            {'type': 'calendar_create', 'target': 'Client meeting', 'content': 'Demo call'},
            'medium', 'denied', 45
        )
    ]
    
    for request in test_actions:
        if request.response_time:
            tracker.track_approval(request)
        else:
            tracker.track_denial(request)
    
    # Get insights
    insights = tracker.get_learning_insights()
    print(json.dumps(insights, indent=2, default=str))
    
    # Test pattern matching
    new_action = {
        'type': 'email_send',
        'target': 'team@company.com',
        'content': 'Project update'
    }
    
    approval_rate = tracker.get_approval_rate(new_action)
    print(f"\nApproval rate for similar actions: {approval_rate}")
    
    suggestion = tracker.suggest_criticality_adjustment(new_action)
    print(f"Criticality adjustment suggestion: {suggestion}")