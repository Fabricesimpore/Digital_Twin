"""
Digital Twin V2 - Enhanced Brain Module

This is the upgraded version of the digital twin with advanced reasoning capabilities:

- Multi-path deliberation engine
- Competing behavioral voices (Efficiency, Relationship, Wellbeing, Growth)
- Arbitrator for resolving voice conflicts
- State-aware reasoning (energy, stress, mood tracking)
- Heuristic fast decision-making
- Deep introspection and self-justification

This creates a more human-like, adaptive reasoning system.
"""

import yaml
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
import openai
from pathlib import Path
import logging

# Import the brain modules
from brain_modules.deliberation_engine import DeliberationEngine, DeliberationResult
from brain_modules.behavioral_voices import VoiceOrchestrator, VoiceArgument
from brain_modules.arbitrator import DecisionArbitrator, ArbitrationContext, ArbitrationResult
from brain_modules.state_tracker import StateTracker, StateSnapshot
from brain_modules.heuristic_brain import HeuristicBrain, HeuristicDecision


@dataclass
class Situation:
    """Represents a real-world situation requiring decision or action"""
    context: str  # What's happening
    category: str  # email, schedule_conflict, task, social, etc.
    metadata: Dict[str, Any] = None  # Additional context like sender, urgency, etc.
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TwinResponse:
    """Enhanced response from the digital twin's reasoning"""
    action: str  # What the twin would do
    reasoning: str  # Why this action was chosen
    confidence: float  # How confident the twin is (0-1)
    
    # Enhanced reasoning details
    reasoning_mode: str  # "heuristic", "deliberation", "arbitration"
    deliberation_details: Optional[DeliberationResult] = None
    voice_arguments: Optional[List[VoiceArgument]] = None
    arbitration_result: Optional[ArbitrationResult] = None
    heuristic_decision: Optional[HeuristicDecision] = None
    
    # Alternative considerations
    alternatives: List[str] = None
    trade_offs: List[str] = None
    
    # Memory and learning
    memory_references: List[str] = None
    state_considerations: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/analysis"""
        return {
            'action': self.action,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'reasoning_mode': self.reasoning_mode,
            'deliberation_details': self.deliberation_details.to_dict() if self.deliberation_details else None,
            'voice_arguments': [va.to_dict() for va in self.voice_arguments] if self.voice_arguments else None,
            'arbitration_result': self.arbitration_result.to_dict() if self.arbitration_result else None,
            'heuristic_decision': self.heuristic_decision.to_dict() if self.heuristic_decision else None,
            'alternatives': self.alternatives or [],
            'trade_offs': self.trade_offs or [],
            'memory_references': self.memory_references or [],
            'state_considerations': self.state_considerations or {}
        }


class DigitalTwinV2:
    """
    Enhanced Digital Twin with multi-layered reasoning.
    
    Reasoning Modes:
    1. Heuristic: Fast decisions using learned patterns
    2. Deliberation: Multi-path thinking for complex decisions
    3. Arbitration: Voice-based conflict resolution
    """
    
    def __init__(self, persona_path: str = "persona.yaml", api_key: str = None):
        # Load identity layer
        self.persona = self._load_persona(persona_path)
        
        # Initialize LLM client
        self.llm_client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o"
        
        # Initialize brain modules
        self.state_tracker = StateTracker()
        self.voice_orchestrator = VoiceOrchestrator(self.persona)
        self.arbitrator = DecisionArbitrator(self.llm_client, self.persona)
        self.deliberation_engine = DeliberationEngine(self.llm_client, self.persona)
        self.heuristic_brain = HeuristicBrain(self.persona)
        
        # Memory interface (will be injected)
        self.memory = None
        
        # Decision history for learning
        self.decision_history = []
        
        # Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        self.logger.info("Enhanced Digital Twin V2 initialized")
    
    def _load_persona(self, persona_path: str) -> Dict[str, Any]:
        """Load persona configuration from YAML file"""
        try:
            with open(persona_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: {persona_path} not found. Using default persona.")
            return self._default_persona()
    
    def _default_persona(self) -> Dict[str, Any]:
        """Fallback persona if config not found"""
        return {
            "name": "Digital Twin",
            "traits": ["analytical", "efficient", "friendly"],
            "values": ["honesty", "growth", "connection"],
            "communication_style": {
                "tone": "professional yet warm",
                "brevity": "concise but thorough",
                "formality": "adapts to context"
            },
            "preferences": {},
            "routines": {}
        }
    
    def set_memory_interface(self, memory_interface):
        """Inject memory system"""
        self.memory = memory_interface
    
    def update_state(self, **kwargs) -> StateSnapshot:
        """Update current state (energy, stress, etc.)"""
        return self.state_tracker.update_state(**kwargs)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state for decision context"""
        return self.state_tracker.get_decision_context()
    
    async def reason(self, situation: Situation) -> TwinResponse:
        """
        Main reasoning function with adaptive decision-making.
        
        Chooses the appropriate reasoning mode based on:
        - Time pressure
        - Situation complexity
        - Energy level
        - Available patterns
        """
        
        # Get current state
        current_state = self.get_current_state()
        
        # Determine reasoning mode
        reasoning_mode = self._choose_reasoning_mode(situation, current_state)
        
        self.logger.info(f"Using {reasoning_mode} reasoning for: {situation.context[:50]}...")
        
        # Route to appropriate reasoning system
        if reasoning_mode == "heuristic":
            return await self._reason_heuristic(situation, current_state)
        elif reasoning_mode == "deliberation":
            return await self._reason_deliberation(situation, current_state)
        elif reasoning_mode == "arbitration":
            return await self._reason_arbitration(situation, current_state)
        else:
            # Fallback to arbitration
            return await self._reason_arbitration(situation, current_state)
    
    def _choose_reasoning_mode(self, situation: Situation, current_state: Dict[str, Any]) -> str:
        """Choose the most appropriate reasoning mode"""
        
        # Check if heuristic reasoning is applicable
        time_pressure = situation.metadata.get('urgency') == 'high'
        energy_level = current_state.get('current_energy', 'medium')
        
        if self.heuristic_brain.can_use_heuristic(
            situation.context, 
            current_state, 
            time_pressure, 
            energy_level
        ):
            return "heuristic"
        
        # Check for complex situations that need deliberation
        complex_keywords = ["multiple options", "trade-off", "complex", "strategic", "important decision"]
        if any(keyword in situation.context.lower() for keyword in complex_keywords):
            return "deliberation"
        
        # Default to voice arbitration for most situations
        return "arbitration"
    
    async def _reason_heuristic(self, situation: Situation, current_state: Dict[str, Any]) -> TwinResponse:
        """Fast reasoning using learned heuristics"""
        
        heuristic_decision = self.heuristic_brain.make_heuristic_decision(
            situation.context,
            current_state
        )
        
        if not heuristic_decision:
            # Fall back to arbitration if no heuristic matches
            return await self._reason_arbitration(situation, current_state)
        
        # Retrieve relevant memories if available
        memories = self._retrieve_memories(situation) if self.memory else []
        
        response = TwinResponse(
            action=heuristic_decision.action,
            reasoning=heuristic_decision.reasoning,
            confidence=heuristic_decision.confidence,
            reasoning_mode="heuristic",
            heuristic_decision=heuristic_decision,
            alternatives=[f"Could have used deliberation ({heuristic_decision.alternatives_skipped} options skipped)"],
            memory_references=[mem.get('id', '') for mem in memories[:3]],
            state_considerations=current_state
        )
        
        self._log_decision(situation, response)
        return response
    
    async def _reason_deliberation(self, situation: Situation, current_state: Dict[str, Any]) -> TwinResponse:
        """Deep deliberation with multiple options"""
        
        # Convert current state to deliberation context
        context = ArbitrationContext(
            current_energy=current_state.get('current_energy', 'medium'),
            current_stress=current_state.get('current_stress', 'medium'),
            available_time=situation.metadata.get('time_available'),
            deadline_pressure=current_state.get('deadline_pressure', False)
        )
        
        # Run deliberation
        deliberation_result = await self.deliberation_engine.deliberate(
            situation.context,
            situation.metadata,
            current_state
        )
        
        # Retrieve relevant memories
        memories = self._retrieve_memories(situation) if self.memory else []
        
        response = TwinResponse(
            action=deliberation_result.chosen_option.action,
            reasoning=deliberation_result.deliberation_reasoning,
            confidence=deliberation_result.confidence,
            reasoning_mode="deliberation",
            deliberation_details=deliberation_result,
            alternatives=[opt.action for opt in deliberation_result.all_options[1:4]],  # Top alternatives
            memory_references=[mem.get('id', '') for mem in memories[:3]],
            state_considerations=current_state
        )
        
        self._log_decision(situation, response)
        return response
    
    async def _reason_arbitration(self, situation: Situation, current_state: Dict[str, Any]) -> TwinResponse:
        """Voice-based reasoning with conflict resolution"""
        
        # Get arguments from all behavioral voices
        voice_arguments = self.voice_orchestrator.get_all_voice_arguments(
            situation.context,
            situation.metadata
        )
        
        # Set up arbitration context
        arbitration_context = ArbitrationContext(
            current_energy=current_state.get('current_energy', 'medium'),
            current_stress=current_state.get('current_stress', 'medium'),
            available_time=situation.metadata.get('time_available'),
            current_priorities=current_state.get('current_priorities', []),
            deadline_pressure=current_state.get('deadline_pressure', False)
        )
        
        # Arbitrate between voices
        arbitration_result = await self.arbitrator.arbitrate(
            voice_arguments,
            situation.context,
            arbitration_context
        )
        
        # Retrieve relevant memories
        memories = self._retrieve_memories(situation) if self.memory else []
        
        response = TwinResponse(
            action=arbitration_result.final_decision,
            reasoning=arbitration_result.reasoning,
            confidence=arbitration_result.confidence,
            reasoning_mode="arbitration",
            voice_arguments=voice_arguments,
            arbitration_result=arbitration_result,
            alternatives=arbitration_result.considered_alternatives,
            trade_offs=arbitration_result.trade_offs_acknowledged,
            memory_references=[mem.get('id', '') for mem in memories[:3]],
            state_considerations=current_state
        )
        
        self._log_decision(situation, response)
        return response
    
    def _retrieve_memories(self, situation: Situation, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from vector DB"""
        if not self.memory:
            return []
        
        search_query = f"{situation.category}: {situation.context}"
        
        filters = {}
        if situation.metadata.get('sender'):
            filters['person'] = situation.metadata['sender']
        if situation.category:
            filters['category'] = situation.category
        
        memories = self.memory.search(
            query=search_query,
            k=k,
            filters=filters
        )
        
        return memories
    
    def _log_decision(self, situation: Situation, response: TwinResponse):
        """Log decision for learning and analysis"""
        decision_log = {
            "timestamp": situation.timestamp.isoformat(),
            "situation": {
                "context": situation.context,
                "category": situation.category,
                "metadata": situation.metadata
            },
            "response": response.to_dict()
        }
        self.decision_history.append(decision_log)
    
    def learn_from_feedback(self, 
                           situation: Situation, 
                           actual_action: str, 
                           satisfaction: float = 0.8,
                           feedback: str = None):
        """
        Enhanced learning from feedback across all reasoning systems.
        
        Args:
            situation: Original situation
            actual_action: What actually happened
            satisfaction: How satisfied (0-1) with the outcome
            feedback: Optional detailed feedback
        """
        
        # Find the corresponding prediction in history
        recent_decision = None
        for decision in reversed(self.decision_history):
            if (decision['situation']['context'] == situation.context and
                abs((datetime.fromisoformat(decision['timestamp']) - situation.timestamp).total_seconds()) < 300):
                recent_decision = decision
                break
        
        if not recent_decision:
            self.logger.warning("Could not find corresponding decision for feedback")
            return
        
        # Learn based on reasoning mode used
        reasoning_mode = recent_decision['response']['reasoning_mode']
        
        if reasoning_mode == "heuristic" and recent_decision['response']['heuristic_decision']:
            # Update heuristic success/failure
            heuristic_data = recent_decision['response']['heuristic_decision']
            # We'd need to reconstruct the HeuristicDecision object to call learn_from_feedback
            # For now, log the feedback
            self.logger.info(f"Heuristic feedback: satisfaction={satisfaction:.2f}")
        
        elif reasoning_mode == "arbitration":
            # Update voice weights or arbitration logic
            winning_voices = recent_decision['response']['arbitration_result']['winning_voices']
            self.logger.info(f"Arbitration feedback: winning voices {winning_voices}, satisfaction={satisfaction:.2f}")
        
        # Store in memory if available
        if self.memory:
            learning_content = f"Situation: {situation.context}\nPredicted: {recent_decision['response']['action']}\nActual: {actual_action}\nSatisfaction: {satisfaction:.2f}"
            if feedback:
                learning_content += f"\nFeedback: {feedback}"
            
            self.memory.add(
                content=learning_content,
                metadata={
                    "type": "behavior_correction",
                    "category": situation.category,
                    "reasoning_mode": reasoning_mode,
                    "satisfaction": satisfaction,
                    **situation.metadata
                }
            )
        
        self.logger.info(f"Learned from feedback: {actual_action} (satisfaction: {satisfaction:.2f})")
        
        return {
            "learning_stored": True,
            "reasoning_mode": reasoning_mode,
            "satisfaction": satisfaction
        }
    
    def get_reasoning_insights(self) -> Dict[str, Any]:
        """Get insights into the twin's reasoning patterns"""
        
        if not self.decision_history:
            return {"message": "No decision history available"}
        
        insights = {
            "total_decisions": len(self.decision_history),
            "reasoning_mode_distribution": {},
            "average_confidence": 0.0,
            "state_patterns": {},
            "voice_influence": {},
            "heuristic_stats": self.heuristic_brain.get_heuristic_stats(),
            "arbitration_patterns": self.arbitrator.get_decision_patterns()
        }
        
        # Analyze reasoning modes
        mode_counts = {}
        confidence_sum = 0
        
        for decision in self.decision_history:
            mode = decision['response']['reasoning_mode']
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            confidence_sum += decision['response']['confidence']
        
        insights["reasoning_mode_distribution"] = mode_counts
        insights["average_confidence"] = confidence_sum / len(self.decision_history)
        
        # Analyze voice influence in arbitration decisions
        voice_counts = {}
        for decision in self.decision_history:
            if decision['response']['reasoning_mode'] == 'arbitration':
                arb_result = decision['response'].get('arbitration_result', {})
                winning_voices = arb_result.get('winning_voices', [])
                for voice in winning_voices:
                    voice_counts[voice] = voice_counts.get(voice, 0) + 1
        
        insights["voice_influence"] = dict(sorted(voice_counts.items(), key=lambda x: x[1], reverse=True))
        
        return insights
    
    def introspect(self, question: str) -> str:
        """
        Allow the twin to introspect about its own decision-making.
        
        Examples:
        - "Why do I usually prioritize efficiency over wellbeing?"
        - "What patterns do you see in my decision making?"
        - "How do I handle stress differently than normal situations?"
        """
        
        insights = self.get_reasoning_insights()
        current_state = self.get_current_state()
        
        introspection_prompt = f"""
        I am a digital twin analyzing my own decision-making patterns. Here's my data:
        
        PERSONA:
        {json.dumps(self.persona, indent=2)}
        
        RECENT DECISION PATTERNS:
        {json.dumps(insights, indent=2)}
        
        CURRENT STATE:
        {json.dumps(current_state, indent=2)}
        
        QUESTION: {question}
        
        Analyze this question about my decision-making patterns and provide insights as if you are me reflecting on my own behavior. Be thoughtful, specific, and reference the actual data when possible.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are providing self-introspection for a digital twin, analyzing its own decision patterns and behaviors."},
                    {"role": "user", "content": introspection_prompt}
                ],
                temperature=0.6
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Unable to introspect: {str(e)}"
    
    def shadow_mode(self, enabled: bool = True):
        """Enable shadow mode where the twin observes but doesn't act"""
        self.is_shadow_mode = enabled
        return f"Shadow mode {'enabled' if enabled else 'disabled'}"
    
    def get_brain_status(self) -> Dict[str, Any]:
        """Get status of all brain modules"""
        return {
            "state_tracker": {
                "current_state": self.state_tracker.quick_state_check(),
                "recommendations": self.state_tracker.get_state_recommendations()
            },
            "heuristics": {
                "total_rules": len(self.heuristic_brain.heuristics),
                "recent_decisions": len(self.heuristic_brain.decision_history)
            },
            "voices": {
                "available_voices": list(self.voice_orchestrator.voices.keys())
            },
            "arbitrator": {
                "total_arbitrations": len(self.arbitrator.decision_history)
            },
            "overall": {
                "total_decisions": len(self.decision_history),
                "memory_connected": self.memory is not None
            }
        }