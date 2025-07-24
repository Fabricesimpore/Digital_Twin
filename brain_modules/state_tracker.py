"""
State Tracker for Digital Twin

This module tracks the user's current emotional, mental, and physical state
to inform decision-making. It considers factors like energy levels, stress,
mood, and context to make more informed choices.

The state can be updated manually, inferred from behavior patterns, or
eventually detected from voice tone, calendar patterns, etc.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging


class EnergyLevel(Enum):
    """Energy level categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StressLevel(Enum):
    """Stress level categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MoodCategory(Enum):
    """General mood categories"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FocusLevel(Enum):
    """Focus/concentration level"""
    SCATTERED = "scattered"
    NORMAL = "normal"
    DEEP_FOCUS = "deep_focus"


@dataclass
class StateSnapshot:
    """A snapshot of the user's state at a specific time"""
    timestamp: datetime
    energy_level: EnergyLevel = EnergyLevel.MEDIUM
    stress_level: StressLevel = StressLevel.MEDIUM
    mood: MoodCategory = MoodCategory.NEUTRAL
    focus_level: FocusLevel = FocusLevel.NORMAL
    
    # Contextual factors
    sleep_quality: Optional[str] = None  # poor, fair, good, excellent
    recent_meals: bool = True  # Has eaten recently
    physical_activity: Optional[str] = None  # none, light, moderate, intense
    social_interaction: Optional[str] = None  # isolated, normal, high
    
    # Work context
    workload: Optional[str] = None  # light, normal, heavy, overwhelming
    deadline_pressure: bool = False
    meeting_density: Optional[str] = None  # sparse, normal, back_to_back
    
    # Environmental factors
    location: Optional[str] = None  # office, home, travel, etc.
    noise_level: Optional[str] = None  # quiet, normal, noisy
    
    # Confidence in this assessment
    confidence: float = 0.7
    
    # How this state was determined
    source: str = "manual"  # manual, inferred, sensor, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'energy_level': self.energy_level.value,
            'stress_level': self.stress_level.value,
            'mood': self.mood.value,
            'focus_level': self.focus_level.value,
            'sleep_quality': self.sleep_quality,
            'recent_meals': self.recent_meals,
            'physical_activity': self.physical_activity,
            'social_interaction': self.social_interaction,
            'workload': self.workload,
            'deadline_pressure': self.deadline_pressure,
            'meeting_density': self.meeting_density,
            'location': self.location,
            'noise_level': self.noise_level,
            'confidence': self.confidence,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            energy_level=EnergyLevel(data.get('energy_level', 'medium')),
            stress_level=StressLevel(data.get('stress_level', 'medium')),
            mood=MoodCategory(data.get('mood', 'neutral')),
            focus_level=FocusLevel(data.get('focus_level', 'normal')),
            sleep_quality=data.get('sleep_quality'),
            recent_meals=data.get('recent_meals', True),
            physical_activity=data.get('physical_activity'),
            social_interaction=data.get('social_interaction'),
            workload=data.get('workload'),
            deadline_pressure=data.get('deadline_pressure', False),
            meeting_density=data.get('meeting_density'),
            location=data.get('location'),
            noise_level=data.get('noise_level'),
            confidence=data.get('confidence', 0.7),
            source=data.get('source', 'manual')
        )


class StateTracker:
    """
    Tracks and manages the user's current state for informed decision-making.
    
    Features:
    - Manual state updates
    - Inferred state from behavior patterns
    - Historical state tracking
    - State-aware recommendations
    """
    
    def __init__(self, storage_file: str = "state_history.json"):
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_state: StateSnapshot = StateSnapshot(timestamp=datetime.now())
        
        # Historical states
        self.state_history: List[StateSnapshot] = []
        
        # Load previous states
        self._load_state_history()
    
    def _load_state_history(self):
        """Load state history from storage"""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                
                # Load current state if available
                if 'current_state' in data:
                    self.current_state = StateSnapshot.from_dict(data['current_state'])
                
                # Load history
                for state_data in data.get('history', []):
                    state = StateSnapshot.from_dict(state_data)
                    self.state_history.append(state)
                
                self.logger.info(f"Loaded {len(self.state_history)} historical states")
                
        except FileNotFoundError:
            self.logger.info("No previous state history found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading state history: {e}")
    
    def _save_state_history(self):
        """Save state history to storage"""
        try:
            data = {
                'current_state': self.current_state.to_dict(),
                'history': [state.to_dict() for state in self.state_history[-100:]]  # Keep last 100
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving state history: {e}")
    
    def update_state(self, **kwargs) -> StateSnapshot:
        """
        Update the current state with new information.
        
        Args:
            **kwargs: State parameters to update (energy_level, stress_level, etc.)
        
        Returns:
            Updated StateSnapshot
        """
        
        # Archive current state to history
        if self.current_state.timestamp:
            self.state_history.append(self.current_state)
        
        # Create new state snapshot
        current_time = datetime.now()
        
        # Start with current values, update with provided kwargs
        state_data = {
            'energy_level': kwargs.get('energy_level', self.current_state.energy_level),
            'stress_level': kwargs.get('stress_level', self.current_state.stress_level),
            'mood': kwargs.get('mood', self.current_state.mood),
            'focus_level': kwargs.get('focus_level', self.current_state.focus_level),
            'sleep_quality': kwargs.get('sleep_quality', self.current_state.sleep_quality),
            'recent_meals': kwargs.get('recent_meals', self.current_state.recent_meals),
            'physical_activity': kwargs.get('physical_activity', self.current_state.physical_activity),
            'social_interaction': kwargs.get('social_interaction', self.current_state.social_interaction),
            'workload': kwargs.get('workload', self.current_state.workload),
            'deadline_pressure': kwargs.get('deadline_pressure', self.current_state.deadline_pressure),
            'meeting_density': kwargs.get('meeting_density', self.current_state.meeting_density),
            'location': kwargs.get('location', self.current_state.location),
            'noise_level': kwargs.get('noise_level', self.current_state.noise_level),
            'confidence': kwargs.get('confidence', 0.8),  # Higher confidence for manual updates
            'source': kwargs.get('source', 'manual')
        }
        
        # Convert string enums if needed
        if isinstance(state_data['energy_level'], str):
            state_data['energy_level'] = EnergyLevel(state_data['energy_level'])
        if isinstance(state_data['stress_level'], str):
            state_data['stress_level'] = StressLevel(state_data['stress_level'])
        if isinstance(state_data['mood'], str):
            state_data['mood'] = MoodCategory(state_data['mood'])
        if isinstance(state_data['focus_level'], str):
            state_data['focus_level'] = FocusLevel(state_data['focus_level'])
        
        self.current_state = StateSnapshot(timestamp=current_time, **state_data)
        
        # Save to storage
        self._save_state_history()
        
        self.logger.info(f"State updated: Energy={self.current_state.energy_level.value}, "
                        f"Stress={self.current_state.stress_level.value}")
        
        return self.current_state
    
    def infer_state_from_behavior(self, 
                                 recent_actions: List[Dict[str, Any]],
                                 calendar_events: List[Dict[str, Any]] = None,
                                 response_times: List[float] = None) -> StateSnapshot:
        """
        Infer current state from recent behavior patterns.
        
        Args:
            recent_actions: List of recent actions/decisions
            calendar_events: Recent calendar events
            response_times: Recent email/message response times
        
        Returns:
            Inferred StateSnapshot
        """
        
        # Start with current state as baseline
        inferred_energy = self.current_state.energy_level
        inferred_stress = self.current_state.stress_level
        inferred_mood = self.current_state.mood
        inferred_focus = self.current_state.focus_level
        
        # Analyze recent actions for energy indicators
        if recent_actions:
            quick_decisions = sum(1 for action in recent_actions if action.get('response_time', 30) < 10)
            delayed_decisions = sum(1 for action in recent_actions if action.get('response_time', 30) > 60)
            
            if quick_decisions > delayed_decisions:
                inferred_energy = EnergyLevel.HIGH
            elif delayed_decisions > quick_decisions:
                inferred_energy = EnergyLevel.LOW
        
        # Analyze calendar density for stress
        if calendar_events:
            now = datetime.now()
            today_events = [
                event for event in calendar_events 
                if event.get('date', now.date()) == now.date()
            ]
            
            if len(today_events) > 6:
                inferred_stress = StressLevel.HIGH
                inferred_focus = FocusLevel.SCATTERED
            elif len(today_events) < 2:
                inferred_stress = StressLevel.LOW
        
        # Analyze response times for focus/stress
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            
            if avg_response_time < 5:  # Very quick responses
                inferred_stress = StressLevel.HIGH
            elif avg_response_time > 30:  # Slow responses
                inferred_focus = FocusLevel.SCATTERED
        
        # Time-based inferences
        current_hour = datetime.now().hour
        
        # Energy patterns by time of day
        if 6 <= current_hour <= 10:  # Morning
            inferred_energy = EnergyLevel.HIGH
        elif 14 <= current_hour <= 16:  # Afternoon dip
            inferred_energy = EnergyLevel.MEDIUM
        elif current_hour >= 20:  # Evening
            inferred_energy = EnergyLevel.LOW
        
        # Update state with inferences
        return self.update_state(
            energy_level=inferred_energy,
            stress_level=inferred_stress,
            mood=inferred_mood,
            focus_level=inferred_focus,
            source="inferred",
            confidence=0.6  # Lower confidence for inferred states
        )
    
    def get_state_recommendations(self) -> List[str]:
        """Get recommendations based on current state"""
        
        recommendations = []
        
        # Energy-based recommendations
        if self.current_state.energy_level == EnergyLevel.LOW:
            recommendations.append("Consider taking a short break or having a healthy snack")
            recommendations.append("Focus on easier, less demanding tasks")
            recommendations.append("Avoid scheduling important meetings if possible")
        
        elif self.current_state.energy_level == EnergyLevel.HIGH:
            recommendations.append("Good time for challenging or creative work")
            recommendations.append("Consider tackling high-priority tasks")
        
        # Stress-based recommendations
        if self.current_state.stress_level == StressLevel.HIGH:
            recommendations.append("Prioritize essential tasks only")
            recommendations.append("Consider breathing exercises or a brief walk")
            recommendations.append("Delegate or defer non-urgent tasks")
            
            if self.current_state.focus_level == FocusLevel.SCATTERED:
                recommendations.append("Break large tasks into smaller, manageable pieces")
        
        # Focus-based recommendations
        if self.current_state.focus_level == FocusLevel.DEEP_FOCUS:
            recommendations.append("Minimize interruptions and notifications")
            recommendations.append("Tackle complex, analytical work")
        
        elif self.current_state.focus_level == FocusLevel.SCATTERED:
            recommendations.append("Handle quick, routine tasks first")
            recommendations.append("Use techniques like Pomodoro for focus")
        
        # Context-based recommendations
        if self.current_state.workload == "heavy":
            recommendations.append("Be selective about new commitments")
            recommendations.append("Look for opportunities to streamline or automate")
        
        if self.current_state.deadline_pressure:
            recommendations.append("Focus on deadline-critical tasks first")
            recommendations.append("Communicate early if deadlines are at risk")
        
        return recommendations
    
    def get_decision_context(self) -> Dict[str, Any]:
        """Get current state as context for decision-making"""
        
        return {
            'current_energy': self.current_state.energy_level.value,
            'current_stress': self.current_state.stress_level.value,
            'current_mood': self.current_state.mood.value,
            'current_focus': self.current_state.focus_level.value,
            'workload': self.current_state.workload,
            'deadline_pressure': self.current_state.deadline_pressure,
            'location': self.current_state.location,
            'time_of_day': datetime.now().hour,
            'recommendations': self.get_state_recommendations()
        }
    
    def analyze_state_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Analyze state patterns over recent days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_states = [
            state for state in self.state_history 
            if state.timestamp >= cutoff_date
        ]
        
        if not recent_states:
            return {"message": "Insufficient data for pattern analysis"}
        
        # Energy patterns
        energy_counts = {}
        stress_counts = {}
        mood_counts = {}
        
        for state in recent_states:
            energy_counts[state.energy_level.value] = energy_counts.get(state.energy_level.value, 0) + 1
            stress_counts[state.stress_level.value] = stress_counts.get(state.stress_level.value, 0) + 1
            mood_counts[state.mood.value] = mood_counts.get(state.mood.value, 0) + 1
        
        # Time-based patterns
        hour_energy = {}
        for state in recent_states:
            hour = state.timestamp.hour
            if hour not in hour_energy:
                hour_energy[hour] = []
            hour_energy[hour].append(state.energy_level.value)
        
        # Average energy by hour
        avg_energy_by_hour = {}
        for hour, energies in hour_energy.items():
            energy_scores = {'low': 1, 'medium': 2, 'high': 3}
            avg_score = sum(energy_scores[e] for e in energies) / len(energies)
            avg_energy_by_hour[hour] = avg_score
        
        return {
            'analysis_period_days': days,
            'total_states': len(recent_states),
            'energy_distribution': energy_counts,
            'stress_distribution': stress_counts,
            'mood_distribution': mood_counts,
            'peak_energy_hours': sorted(avg_energy_by_hour.items(), key=lambda x: x[1], reverse=True)[:3],
            'low_energy_hours': sorted(avg_energy_by_hour.items(), key=lambda x: x[1])[:3]
        }
    
    def get_current_state(self) -> StateSnapshot:
        """Get the current state snapshot"""
        return self.current_state
    
    def quick_state_check(self) -> str:
        """Get a quick text summary of current state"""
        return (f"Energy: {self.current_state.energy_level.value}, "
                f"Stress: {self.current_state.stress_level.value}, "
                f"Focus: {self.current_state.focus_level.value}")


# Convenience functions for quick state updates
def quick_energy_update(tracker: StateTracker, level: str):
    """Quick energy level update"""
    tracker.update_state(energy_level=level)

def quick_stress_update(tracker: StateTracker, level: str):
    """Quick stress level update"""
    tracker.update_state(stress_level=level)

def morning_state_update(tracker: StateTracker, 
                        sleep_quality: str = "good",
                        energy: str = "high"):
    """Morning state update with sleep quality"""
    tracker.update_state(
        sleep_quality=sleep_quality,
        energy_level=energy,
        stress_level="low",  # Usually lower in morning
        source="morning_checkin"
    )