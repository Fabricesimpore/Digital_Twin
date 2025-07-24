"""
Behavioral Voices for Digital Twin

This module implements multiple internal "voices" that represent different aspects
of your personality and values. Each voice argues for different approaches based
on its core concern (efficiency, relationships, health, etc.).

The voices simulate your internal dialogue and competing priorities, making
the twin's decision-making more nuanced and human-like.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import logging
from enum import Enum


class VoiceStrength(Enum):
    """How strongly a voice advocates for its position"""
    WHISPER = 0.3   # Gentle suggestion
    SPEAK = 0.6     # Normal advocacy
    SHOUT = 0.9     # Strong insistence


@dataclass
class VoiceArgument:
    """An argument made by a behavioral voice"""
    voice_name: str
    position: str  # What this voice wants to do
    reasoning: str  # Why this voice wants this
    urgency: VoiceStrength  # How strongly it's advocating
    supporting_points: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)  # What this voice is worried about
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'voice_name': self.voice_name,
            'position': self.position,
            'reasoning': self.reasoning,
            'urgency': self.urgency.value,
            'supporting_points': self.supporting_points,
            'concerns': self.concerns
        }


class BehavioralVoice(ABC):
    """Base class for behavioral voices"""
    
    def __init__(self, name: str, core_values: List[str], persona: Dict[str, Any]):
        self.name = name
        self.core_values = core_values
        self.persona = persona
        self.logger = logging.getLogger(f"voice.{name}")
    
    @abstractmethod
    def evaluate_situation(self, situation: str, context: Dict[str, Any] = None) -> VoiceArgument:
        """Evaluate a situation and return this voice's argument"""
        pass
    
    def _get_voice_strength(self, situation: str, context: Dict[str, Any] = None) -> VoiceStrength:
        """Determine how strongly this voice should advocate"""
        # Default implementation - can be overridden
        return VoiceStrength.SPEAK


class EfficiencyVoice(BehavioralVoice):
    """
    The voice of productivity and efficiency.
    Prioritizes getting things done, meeting deadlines, and optimal resource use.
    """
    
    def __init__(self, persona: Dict[str, Any]):
        super().__init__(
            name="Efficiency",
            core_values=["productivity", "optimization", "time_management"],
            persona=persona
        )
    
    def evaluate_situation(self, situation: str, context: Dict[str, Any] = None) -> VoiceArgument:
        # Check for efficiency-related keywords
        efficiency_keywords = ["deadline", "urgent", "quick", "efficient", "productivity", "time"]
        urgency = VoiceStrength.SPEAK
        
        situation_lower = situation.lower()
        if any(keyword in situation_lower for keyword in efficiency_keywords):
            urgency = VoiceStrength.SHOUT
        
        # Analyze the situation for efficiency concerns
        position = self._determine_efficiency_position(situation, context)
        reasoning = self._build_efficiency_reasoning(situation, context)
        
        return VoiceArgument(
            voice_name=self.name,
            position=position,
            reasoning=reasoning,
            urgency=urgency,
            supporting_points=self._get_efficiency_points(situation, context),
            concerns=self._get_efficiency_concerns(situation, context)
        )
    
    def _determine_efficiency_position(self, situation: str, context: Dict[str, Any] = None) -> str:
        """What would the efficiency voice want to do?"""
        
        # Look for time-sensitive or productivity-related situations
        if "deadline" in situation.lower() or "urgent" in situation.lower():
            return "Address this immediately to meet deadlines and maintain productivity"
        
        if "meeting" in situation.lower():
            return "Keep the meeting short, focused, and actionable"
        
        if "email" in situation.lower():
            return "Respond quickly and concisely to clear the inbox"
        
        if "task" in situation.lower() or "project" in situation.lower():
            return "Prioritize based on impact and deadline, then execute systematically"
        
        # Default efficiency stance
        return "Handle this in the most time-effective manner possible"
    
    def _build_efficiency_reasoning(self, situation: str, context: Dict[str, Any] = None) -> str:
        """Why does the efficiency voice want this approach?"""
        traits = self.persona.get('traits', [])
        
        reasoning = "Time is our most valuable resource. "
        
        if 'analytical' in traits:
            reasoning += "We need to approach this systematically to maximize output. "
        
        if context and context.get('time_available'):
            reasoning += f"With limited time available, we must focus on high-impact actions. "
        
        reasoning += "Delaying or over-analyzing will reduce our overall productivity and potentially create stress."
        
        return reasoning
    
    def _get_efficiency_points(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """Supporting points for efficiency approach"""
        points = []
        
        if "deadline" in situation.lower():
            points.append("Meeting deadlines builds trust and reliability")
            points.append("Early completion allows buffer time for unexpected issues")
        
        points.append("Quick decision-making prevents bottlenecks")
        points.append("Efficient handling frees time for higher-value activities")
        
        if context and context.get('workload') == 'high':
            points.append("High workload requires ruthless prioritization")
        
        return points
    
    def _get_efficiency_concerns(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """What is the efficiency voice worried about?"""
        concerns = []
        
        if "meeting" in situation.lower():
            concerns.append("Long meetings without clear agendas waste time")
        
        if "social" in situation.lower():
            concerns.append("Social activities might impact work productivity")
        
        concerns.append("Over-deliberation leads to analysis paralysis")
        concerns.append("Perfectionism can prevent completion")
        
        return concerns


class RelationshipVoice(BehavioralVoice):
    """
    The voice of connection and relationships.
    Prioritizes maintaining relationships, being helpful, and considering others' needs.
    """
    
    def __init__(self, persona: Dict[str, Any]):
        super().__init__(
            name="Relationship",
            core_values=["connection", "empathy", "collaboration"],
            persona=persona
        )
    
    def evaluate_situation(self, situation: str, context: Dict[str, Any] = None) -> VoiceArgument:
        # Check for relationship-related elements
        relationship_keywords = ["friend", "colleague", "client", "team", "meeting", "call", "email"]
        urgency = VoiceStrength.SPEAK
        
        situation_lower = situation.lower()
        if any(keyword in situation_lower for keyword in relationship_keywords):
            urgency = VoiceStrength.SHOUT
        
        # Special cases where relationships are at stake
        if "conflict" in situation_lower or "upset" in situation_lower:
            urgency = VoiceStrength.SHOUT
        
        position = self._determine_relationship_position(situation, context)
        reasoning = self._build_relationship_reasoning(situation, context)
        
        return VoiceArgument(
            voice_name=self.name,
            position=position,
            reasoning=reasoning,
            urgency=urgency,
            supporting_points=self._get_relationship_points(situation, context),
            concerns=self._get_relationship_concerns(situation, context)
        )
    
    def _determine_relationship_position(self, situation: str, context: Dict[str, Any] = None) -> str:
        """What would the relationship voice want to do?"""
        
        if "client" in situation.lower() and "urgent" in situation.lower():
            return "Respond with extra care and attention to maintain client trust"
        
        if "friend" in situation.lower():
            return "Make time for the relationship - friendships need nurturing"
        
        if "colleague" in situation.lower() or "team" in situation.lower():
            return "Be helpful and collaborative to strengthen working relationships"
        
        if "meeting" in situation.lower():
            return "Engage fully and consider everyone's perspectives"
        
        if "email" in situation.lower():
            return "Respond thoughtfully with appropriate warmth and consideration"
        
        return "Consider how this affects others and prioritize maintaining good relationships"
    
    def _build_relationship_reasoning(self, situation: str, context: Dict[str, Any] = None) -> str:
        """Why does the relationship voice want this approach?"""
        values = self.persona.get('values', [])
        
        reasoning = "Relationships are the foundation of everything we do. "
        
        if 'connection' in values:
            reasoning += "Strong connections create opportunities and make work more fulfilling. "
        
        if 'empathy' in self.persona.get('traits', []):
            reasoning += "Understanding others' perspectives leads to better outcomes for everyone. "
        
        reasoning += "Investing in relationships now pays dividends in trust, collaboration, and future opportunities."
        
        return reasoning
    
    def _get_relationship_points(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """Supporting points for relationship approach"""
        points = [
            "Strong relationships enable better collaboration",
            "People remember how you made them feel",
            "Taking time for others builds long-term trust"
        ]
        
        if "client" in situation.lower():
            points.append("Client relationships directly impact business success")
        
        if "team" in situation.lower():
            points.append("Team cohesion improves overall productivity")
        
        return points
    
    def _get_relationship_concerns(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """What is the relationship voice worried about?"""
        concerns = [
            "Being too task-focused might seem cold or uncaring",
            "Rushing responses could damage relationships",
            "Missing social cues or context"
        ]
        
        if "urgent" in situation.lower():
            concerns.append("Urgency might make us seem dismissive of others' needs")
        
        return concerns


class WellbeingVoice(BehavioralVoice):
    """
    The voice of health and wellbeing.
    Prioritizes mental health, physical health, work-life balance, and sustainable practices.
    """
    
    def __init__(self, persona: Dict[str, Any]):
        super().__init__(
            name="Wellbeing",
            core_values=["health", "balance", "sustainability"],
            persona=persona
        )
    
    def evaluate_situation(self, situation: str, context: Dict[str, Any] = None) -> VoiceArgument:
        # Check for wellbeing-related concerns
        stress_keywords = ["overwhelmed", "stressed", "tired", "deadline", "urgent", "pressure"]
        balance_keywords = ["evening", "weekend", "break", "personal", "family", "gym"]
        
        situation_lower = situation.lower()
        urgency = VoiceStrength.SPEAK
        
        if any(keyword in situation_lower for keyword in stress_keywords):
            urgency = VoiceStrength.SHOUT
        elif any(keyword in situation_lower for keyword in balance_keywords):
            urgency = VoiceStrength.SHOUT
        
        position = self._determine_wellbeing_position(situation, context)
        reasoning = self._build_wellbeing_reasoning(situation, context)
        
        return VoiceArgument(
            voice_name=self.name,
            position=position,
            reasoning=reasoning,
            urgency=urgency,
            supporting_points=self._get_wellbeing_points(situation, context),
            concerns=self._get_wellbeing_concerns(situation, context)
        )
    
    def _determine_wellbeing_position(self, situation: str, context: Dict[str, Any] = None) -> str:
        """What would the wellbeing voice want to do?"""
        
        if "overwhelmed" in situation.lower() or "stressed" in situation.lower():
            return "Take a step back, breathe, and break this down into manageable pieces"
        
        if "evening" in situation.lower() or "weekend" in situation.lower():
            return "Protect personal time for rest and recharging"
        
        if "gym" in situation.lower() or "exercise" in situation.lower():
            return "Prioritize physical health - it supports everything else"
        
        if "deadline" in situation.lower() and "multiple" in situation.lower():
            return "Focus on what's truly essential and consider asking for help or extensions"
        
        if context and context.get('energy_level') == 'low':
            return "Conserve energy for the most important tasks and rest when possible"
        
        return "Approach this in a sustainable way that doesn't compromise long-term health"
    
    def _build_wellbeing_reasoning(self, situation: str, context: Dict[str, Any] = None) -> str:
        """Why does the wellbeing voice want this approach?"""
        reasoning = "Sustainable performance requires taking care of ourselves. "
        
        if "stressed" in situation.lower():
            reasoning += "Chronic stress leads to burnout and poor decision-making. "
        
        reasoning += "Short-term sacrifices of wellbeing often lead to longer-term problems. "
        reasoning += "When we're healthy and balanced, we perform better in all areas of life."
        
        return reasoning
    
    def _get_wellbeing_points(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """Supporting points for wellbeing approach"""
        points = [
            "Better health leads to better performance",
            "Work-life balance prevents burnout",
            "Taking breaks actually improves productivity",
            "Physical and mental health are interconnected"
        ]
        
        if "deadline" in situation.lower():
            points.append("Stressed work often needs to be redone")
        
        return points
    
    def _get_wellbeing_concerns(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """What is the wellbeing voice worried about?"""
        concerns = [
            "Overcommitting leads to poor quality work",
            "Skipping breaks creates a cycle of declining performance",
            "Ignoring stress signals can lead to serious health issues"
        ]
        
        if "urgent" in situation.lower():
            concerns.append("Constant urgency creates unsustainable stress levels")
        
        return concerns


class GrowthVoice(BehavioralVoice):
    """
    The voice of learning and growth.
    Prioritizes skill development, learning opportunities, and long-term improvement.
    """
    
    def __init__(self, persona: Dict[str, Any]):
        super().__init__(
            name="Growth",
            core_values=["learning", "development", "improvement"],
            persona=persona
        )
    
    def evaluate_situation(self, situation: str, context: Dict[str, Any] = None) -> VoiceArgument:
        # Check for growth opportunities
        growth_keywords = ["learn", "new", "skill", "course", "challenge", "feedback", "improve"]
        urgency = VoiceStrength.SPEAK
        
        situation_lower = situation.lower()
        if any(keyword in situation_lower for keyword in growth_keywords):
            urgency = VoiceStrength.SHOUT
        
        position = self._determine_growth_position(situation, context)
        reasoning = self._build_growth_reasoning(situation, context)
        
        return VoiceArgument(
            voice_name=self.name,
            position=position,
            reasoning=reasoning,
            urgency=urgency,
            supporting_points=self._get_growth_points(situation, context),
            concerns=self._get_growth_concerns(situation, context)
        )
    
    def _determine_growth_position(self, situation: str, context: Dict[str, Any] = None) -> str:
        """What would the growth voice want to do?"""
        
        if "new" in situation.lower() and ("framework" in situation.lower() or "skill" in situation.lower()):
            return "Invest time in learning this - it could be valuable long-term"
        
        if "feedback" in situation.lower():
            return "Actively seek and thoughtfully consider the feedback for improvement"
        
        if "challenge" in situation.lower():
            return "Embrace the challenge as an opportunity to grow and develop new capabilities"
        
        if "course" in situation.lower() or "tutorial" in situation.lower():
            return "Make time for structured learning to build systematic knowledge"
        
        return "Look for the learning opportunity in this situation"
    
    def _build_growth_reasoning(self, situation: str, context: Dict[str, Any] = None) -> str:
        """Why does the growth voice want this approach?"""
        values = self.persona.get('values', [])
        
        reasoning = "Every situation is a chance to learn and improve. "
        
        if 'growth' in values:
            reasoning += "Continuous learning is what keeps us competitive and engaged. "
        
        if 'innovation' in values:
            reasoning += "New knowledge enables innovation and creative problem-solving. "
        
        reasoning += "Investing in growth now pays dividends throughout our career and life."
        
        return reasoning
    
    def _get_growth_points(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """Supporting points for growth approach"""
        points = [
            "Learning compounds over time",
            "New skills open new opportunities",
            "Growth mindset leads to better problem-solving",
            "Continuous improvement is essential in a changing world"
        ]
        
        if "new" in situation.lower():
            points.append("Early adoption gives competitive advantages")
        
        return points
    
    def _get_growth_concerns(self, situation: str, context: Dict[str, Any] = None) -> List[str]:
        """What is the growth voice worried about?"""
        concerns = [
            "Falling behind due to lack of skill development",
            "Missing learning opportunities due to short-term focus",
            "Becoming obsolete by not adapting to change"
        ]
        
        if "urgent" in situation.lower():
            concerns.append("Urgent tasks often crowd out important learning time")
        
        return concerns


class VoiceOrchestrator:
    """
    Manages all behavioral voices and coordinates their input.
    """
    
    def __init__(self, persona: Dict[str, Any]):
        self.persona = persona
        self.voices = self._initialize_voices(persona)
        self.logger = logging.getLogger("voice_orchestrator")
    
    def _initialize_voices(self, persona: Dict[str, Any]) -> Dict[str, BehavioralVoice]:
        """Initialize all behavioral voices"""
        return {
            "efficiency": EfficiencyVoice(persona),
            "relationship": RelationshipVoice(persona),
            "wellbeing": WellbeingVoice(persona),
            "growth": GrowthVoice(persona)
        }
    
    def get_all_voice_arguments(self, 
                               situation: str, 
                               context: Dict[str, Any] = None) -> List[VoiceArgument]:
        """Get arguments from all voices"""
        arguments = []
        
        for voice_name, voice in self.voices.items():
            try:
                argument = voice.evaluate_situation(situation, context)
                arguments.append(argument)
                self.logger.info(f"Voice '{voice_name}' argues: {argument.position}")
            except Exception as e:
                self.logger.error(f"Error getting argument from voice '{voice_name}': {e}")
        
        return arguments
    
    def get_voice_summary(self, arguments: List[VoiceArgument]) -> Dict[str, Any]:
        """Summarize all voice arguments for decision-making"""
        summary = {
            "total_voices": len(arguments),
            "strongest_voice": None,
            "consensus_areas": [],
            "conflicts": [],
            "voice_positions": {}
        }
        
        # Find strongest voice
        strongest_urgency = 0
        for arg in arguments:
            if arg.urgency.value > strongest_urgency:
                strongest_urgency = arg.urgency.value
                summary["strongest_voice"] = arg.voice_name
        
        # Identify positions
        for arg in arguments:
            summary["voice_positions"][arg.voice_name] = {
                "position": arg.position,
                "urgency": arg.urgency.value,
                "key_concerns": arg.concerns[:2]  # Top 2 concerns
            }
        
        return summary