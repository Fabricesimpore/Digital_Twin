"""
Digital Twin V3 - Complete System with Persistent Memory

This is the complete digital twin with:
- Enhanced reasoning (deliberation, voices, arbitration, heuristics)
- Persistent memory system (episodic + semantic)
- Automatic learning and pattern extraction
- Context-aware memory retrieval
- Continuous improvement from feedback

This creates a truly persistent, learning digital self.
"""

import yaml
import json
import os
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

# Import the memory system
from memory_system.episodic_memory import EpisodicMemorySystem
from memory_system.vector_memory import EnhancedVectorMemory
from memory_system.memory_updater import MemoryUpdater
from memory_system.memory_retrieval import IntelligentMemoryRetrieval, RetrievalContext


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
    
    # Memory context
    memory_references: List[str] = None
    similar_situations: List[str] = None
    lessons_applied: List[str] = None
    
    # State considerations
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
            'similar_situations': self.similar_situations or [],
            'lessons_applied': self.lessons_applied or [],
            'state_considerations': self.state_considerations or {}
        }


class DigitalTwinV3:
    """
    Complete Digital Twin with persistent memory and continuous learning.
    
    This version:
    1. Reasons with multiple modes (heuristic, deliberation, arbitration)
    2. Remembers all decisions and outcomes (episodic + semantic memory)
    3. Learns from feedback and improves over time
    4. Retrieves relevant memories for context-aware decisions
    5. Extracts patterns automatically from experience
    6. Provides introspection and self-analysis
    """
    
    def __init__(self, 
                 persona_path: str = "persona.yaml", 
                 api_key: str = None,
                 memory_dir: str = "memory_system"):
        
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
        
        # Initialize memory system
        self.episodic_memory = EpisodicMemorySystem(storage_dir=f"{memory_dir}/episodic")
        self.vector_memory = EnhancedVectorMemory(
            storage_dir=f"{memory_dir}/vector",
            openai_api_key=api_key
        )
        
        # Initialize memory management
        self.memory_updater = MemoryUpdater(self.episodic_memory, self.vector_memory)
        self.memory_retrieval = IntelligentMemoryRetrieval(self.episodic_memory, self.vector_memory)
        
        # Decision history for this session
        self.session_decisions = []
        
        # Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        self.logger.info("Digital Twin V3 initialized with persistent memory")
        
        # Load and apply any existing patterns
        self._initialize_from_memory()
    
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
    
    def _initialize_from_memory(self):
        """Initialize the twin with patterns and insights from memory"""
        
        # Extract recent insights to inform decision-making
        recent_insights = self.memory_updater.extract_insights_from_patterns(days=60)
        
        if recent_insights:
            self.logger.info(f"Applied {len(recent_insights)} behavioral patterns from memory")
    
    def update_state(self, **kwargs) -> StateSnapshot:
        """Update current state (energy, stress, etc.)"""
        return self.state_tracker.update_state(**kwargs)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state for decision context"""
        return self.state_tracker.get_decision_context()
    
    async def reason(self, situation: Situation) -> TwinResponse:
        """
        Main reasoning function with memory-enhanced decision-making.
        
        This version:
        1. Retrieves relevant memories for context
        2. Uses memory to influence reasoning mode choice
        3. Applies lessons from similar past situations
        4. Automatically stores the decision for future learning
        """
        
        # Get current state
        current_state = self.get_current_state()
        
        # Retrieve relevant memories for context
        memory_context = self._get_memory_context(situation, current_state)
        
        # Determine reasoning mode (enhanced with memory)
        reasoning_mode = self._choose_reasoning_mode_with_memory(situation, current_state, memory_context)
        
        self.logger.info(f"Using {reasoning_mode} reasoning with {len(memory_context)} memory references")
        
        # Route to appropriate reasoning system
        if reasoning_mode == "heuristic":
            response = await self._reason_heuristic_with_memory(situation, current_state, memory_context)
        elif reasoning_mode == "deliberation":
            response = await self._reason_deliberation_with_memory(situation, current_state, memory_context)
        elif reasoning_mode == "arbitration":
            response = await self._reason_arbitration_with_memory(situation, current_state, memory_context)
        else:
            # Fallback to arbitration
            response = await self._reason_arbitration_with_memory(situation, current_state, memory_context)
        
        # Enhance response with memory information
        response.memory_references = [m.memory_id for m in memory_context]
        response.lessons_applied = self._extract_lessons_applied(memory_context)
        response.similar_situations = self._get_similar_situation_summaries(memory_context)
        
        # Store this decision for future learning
        memory_ids = self.memory_updater.capture_decision_memory(
            situation=situation,
            response=response,
            context=current_state
        )
        
        # Add to session history
        self.session_decisions.append({
            'situation': situation,
            'response': response,
            'memory_ids': memory_ids,
            'timestamp': datetime.now()
        })
        
        return response
    
    def _get_memory_context(self, situation: Situation, current_state: Dict[str, Any]) -> List:
        """Retrieve relevant memories for the current situation"""
        
        retrieval_context = RetrievalContext(
            query=situation.context,
            situation_category=situation.category,
            people_involved=situation.metadata.get('people', []),
            urgency=situation.metadata.get('urgency', 'medium'),
            current_state=current_state
        )
        
        return self.memory_retrieval.retrieve_contextual_memories(
            context=retrieval_context,
            max_memories=6
        )
    
    def _choose_reasoning_mode_with_memory(self, 
                                         situation: Situation, 
                                         current_state: Dict[str, Any],
                                         memory_context: List) -> str:
        """Choose reasoning mode enhanced with memory patterns"""
        
        # Start with base logic
        time_pressure = situation.metadata.get('urgency') == 'high'
        energy_level = current_state.get('current_energy', 'medium')
        
        # Check memory for patterns about what reasoning mode works best
        reasoning_mode_memories = [
            m for m in memory_context 
            if 'reasoning' in m.content.lower() and m.success_boost > 0
        ]
        
        if reasoning_mode_memories:
            # If we have successful patterns, use them
            for memory in reasoning_mode_memories:
                if 'heuristic' in memory.content.lower():
                    return "heuristic"
                elif 'deliberation' in memory.content.lower():
                    return "deliberation"
        
        # Check if heuristic reasoning is applicable
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
        
        # Default to voice arbitration
        return "arbitration"
    
    async def _reason_heuristic_with_memory(self, 
                                          situation: Situation, 
                                          current_state: Dict[str, Any],
                                          memory_context: List) -> TwinResponse:
        """Heuristic reasoning enhanced with memory patterns"""
        
        heuristic_decision = self.heuristic_brain.make_heuristic_decision(
            situation.context,
            current_state
        )
        
        if not heuristic_decision:
            # Fall back to arbitration if no heuristic matches
            return await self._reason_arbitration_with_memory(situation, current_state, memory_context)
        
        # Enhance reasoning with memory insights
        memory_insights = self._extract_heuristic_insights(memory_context)
        enhanced_reasoning = heuristic_decision.reasoning
        
        if memory_insights:
            enhanced_reasoning += f" Based on past experience: {memory_insights}"
        
        response = TwinResponse(
            action=heuristic_decision.action,
            reasoning=enhanced_reasoning,
            confidence=heuristic_decision.confidence,
            reasoning_mode="heuristic",
            heuristic_decision=heuristic_decision,
            alternatives=[f"Could use deliberation ({heuristic_decision.alternatives_skipped} options skipped)"],
            state_considerations=current_state
        )
        
        return response
    
    async def _reason_deliberation_with_memory(self, 
                                             situation: Situation, 
                                             current_state: Dict[str, Any],
                                             memory_context: List) -> TwinResponse:
        """Deliberation enhanced with memory insights"""
        
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
        
        # Enhance with memory insights
        memory_lessons = self._extract_deliberation_lessons(memory_context)
        enhanced_reasoning = deliberation_result.deliberation_reasoning
        
        if memory_lessons:
            enhanced_reasoning += f" Memory insights: {memory_lessons}"
        
        response = TwinResponse(
            action=deliberation_result.chosen_option.action,
            reasoning=enhanced_reasoning,
            confidence=deliberation_result.confidence,
            reasoning_mode="deliberation",
            deliberation_details=deliberation_result,
            alternatives=[opt.action for opt in deliberation_result.all_options[1:4]],
            state_considerations=current_state
        )
        
        return response
    
    async def _reason_arbitration_with_memory(self, 
                                            situation: Situation, 
                                            current_state: Dict[str, Any],
                                            memory_context: List) -> TwinResponse:
        """Voice arbitration enhanced with memory patterns"""
        
        # Get arguments from all behavioral voices
        voice_arguments = self.voice_orchestrator.get_all_voice_arguments(
            situation.context,
            situation.metadata
        )
        
        # Enhance voice arguments with memory
        self._enhance_voices_with_memory(voice_arguments, memory_context)
        
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
        
        # Enhance reasoning with memory
        memory_patterns = self._extract_arbitration_patterns(memory_context)
        enhanced_reasoning = arbitration_result.reasoning
        
        if memory_patterns:
            enhanced_reasoning += f" Historical patterns suggest: {memory_patterns}"
        
        response = TwinResponse(
            action=arbitration_result.final_decision,
            reasoning=enhanced_reasoning,
            confidence=arbitration_result.confidence,
            reasoning_mode="arbitration",
            voice_arguments=voice_arguments,
            arbitration_result=arbitration_result,
            alternatives=arbitration_result.considered_alternatives,
            trade_offs=arbitration_result.trade_offs_acknowledged,
            state_considerations=current_state
        )
        
        return response
    
    def _extract_lessons_applied(self, memory_context: List) -> List[str]:
        """Extract key lessons from memory that influenced the decision"""
        
        lessons = []
        for memory in memory_context:
            if memory.memory_type == 'episodic' and memory.success_boost > 0:
                lessons.append(f"Previously successful: {memory.content[:100]}...")
            elif 'insight' in memory.content.lower():
                lessons.append(f"Learned: {memory.content[:100]}...")
        
        return lessons[:3]  # Top 3 lessons
    
    def _get_similar_situation_summaries(self, memory_context: List) -> List[str]:
        """Get summaries of similar situations from memory"""
        
        similar = []
        for memory in memory_context:
            if memory.memory_type == 'episodic' and memory.context_match > 0.1:
                similar.append(f"Similar situation: {memory.content[:80]}...")
        
        return similar[:2]  # Top 2 similar situations
    
    def _extract_heuristic_insights(self, memory_context: List) -> str:
        """Extract insights relevant to heuristic reasoning"""
        
        insights = []
        for memory in memory_context:
            if 'pattern' in memory.content.lower() and memory.success_boost > 0:
                insights.append(f"this pattern worked well before")
        
        return "; ".join(insights[:2]) if insights else ""
    
    def _extract_deliberation_lessons(self, memory_context: List) -> str:
        """Extract lessons relevant to deliberation"""
        
        lessons = []
        for memory in memory_context:
            if 'strategic' in memory.content.lower() or 'deliberation' in memory.content.lower():
                lessons.append(f"strategic approach previously {memory.content[:50]}...")
        
        return "; ".join(lessons[:2]) if lessons else ""
    
    def _extract_arbitration_patterns(self, memory_context: List) -> str:
        """Extract patterns relevant to voice arbitration"""
        
        patterns = []
        for memory in memory_context:
            if 'voice' in memory.content.lower() or 'values' in memory.content.lower():
                patterns.append(f"value pattern: {memory.content[:50]}...")
        
        return "; ".join(patterns[:2]) if patterns else ""
    
    def _enhance_voices_with_memory(self, voice_arguments: List, memory_context: List):
        """Enhance voice arguments with relevant memories"""
        
        for voice_arg in voice_arguments:
            relevant_memories = [
                m for m in memory_context 
                if voice_arg.voice_name.lower() in m.content.lower()
            ]
            
            if relevant_memories:
                memory_support = relevant_memories[0].content[:100]
                voice_arg.supporting_points.append(f"Past experience: {memory_support}...")
    
    def learn_from_feedback(self, 
                           situation: Situation, 
                           actual_action: str, 
                           satisfaction: float = 0.8,
                           lessons_learned: List[str] = None,
                           feedback: str = None):
        """
        Enhanced learning from feedback with memory system integration.
        
        This version:
        1. Updates both episodic and semantic memories
        2. Adjusts heuristic rules based on outcomes
        3. Updates voice weights in arbitrator
        4. Extracts new patterns automatically
        """
        
        # Find the recent decision
        recent_decision = None
        for decision in reversed(self.session_decisions):
            if (decision['situation'].context == situation.context and
                abs((decision['timestamp'] - situation.timestamp).total_seconds()) < 600):
                recent_decision = decision
                break
        
        if not recent_decision:
            self.logger.warning("Could not find corresponding decision for feedback")
            return
        
        # Update episodic memory with outcome
        episodic_id = recent_decision['memory_ids'].get('episodic_id')
        if episodic_id:
            self.memory_updater.capture_outcome_memory(
                original_decision_id=episodic_id,
                actual_outcome=actual_action,
                satisfaction=satisfaction,
                lessons_learned=lessons_learned,
                feedback=feedback
            )
        
        # Learn specific to reasoning mode used
        reasoning_mode = recent_decision['response'].reasoning_mode
        
        if reasoning_mode == "heuristic":
            # Update heuristic rules
            heuristic_decision = recent_decision['response'].heuristic_decision
            if heuristic_decision:
                self.heuristic_brain.learn_from_feedback(
                    heuristic_decision, actual_action, satisfaction
                )
        
        # Extract new patterns from this feedback
        pattern_insights = self.memory_updater.extract_insights_from_patterns(days=7)
        
        self.logger.info(f"Learned from feedback: satisfaction={satisfaction:.2f}, "
                        f"extracted {len(pattern_insights)} new insights")
        
        return {
            "learning_stored": True,
            "reasoning_mode": reasoning_mode,
            "satisfaction": satisfaction,
            "new_patterns": len(pattern_insights)
        }
    
    def ask_memory(self, question: str) -> str:
        """
        Ask the memory system a specific question.
        
        Examples:
        - "What happened last time I met with John?"
        - "What strategies worked well for email overload?"  
        - "How do I usually handle deadline pressure?"
        """
        
        # Get relevant memories
        retrieval_context = RetrievalContext(
            query=question,
            reasoning_mode="deliberation"  # Use deliberation for memory queries
        )
        
        memories = self.memory_retrieval.retrieve_contextual_memories(
            retrieval_context, max_memories=5
        )
        
        if not memories:
            return "I don't have any relevant memories for that question."
        
        # Format memory response
        response = f"Based on my memories:\n\n"
        
        for i, memory in enumerate(memories[:3], 1):
            response += f"{i}. {memory.content[:200]}...\n"
            if memory.success_boost > 0:
                response += "   (This was successful)\n"
            response += "\n"
        
        return response
    
    def introspect_with_memory(self, question: str) -> str:
        """
        Enhanced introspection using memory system.
        
        This provides deeper self-analysis by examining patterns
        across all stored memories and decisions.
        """
        
        # Get comprehensive insights
        memory_insights = self.vector_memory.get_memory_insights()
        reasoning_insights = self.get_reasoning_insights()
        episodic_stats = self.episodic_memory.get_memory_statistics()
        
        # Build comprehensive context for introspection
        introspection_context = {
            "persona": self.persona,
            "memory_insights": memory_insights,
            "reasoning_patterns": reasoning_insights,
            "episodic_patterns": episodic_stats,
            "recent_decisions": len(self.session_decisions)
        }
        
        introspection_prompt = f"""
        I am analyzing my own behavioral patterns using my complete memory system.
        
        QUESTION: {question}
        
        COMPREHENSIVE DATA:
        {json.dumps(introspection_context, indent=2, default=str)}
        
        Analyze this question deeply, referencing specific patterns from my memory system.
        Provide insights that only someone with access to my complete behavioral history could give.
        Be specific and reference actual patterns when possible.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are providing deep self-introspection for a digital twin with access to comprehensive memory and behavioral data."},
                    {"role": "user", "content": introspection_prompt}
                ],
                temperature=0.6
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Unable to perform deep introspection: {str(e)}"
    
    def get_reasoning_insights(self) -> Dict[str, Any]:
        """Enhanced reasoning insights with memory integration"""
        
        base_insights = super().get_reasoning_insights() if hasattr(super(), 'get_reasoning_insights') else {}
        
        # Add memory-specific insights
        memory_insights = {
            "memory_system": {
                "episodic_memories": len(self.episodic_memory.memories),
                "semantic_memories": len(self.vector_memory.memory_cache),
                "recent_learning": len(self.session_decisions)
            },
            "pattern_extraction": self.memory_updater.get_update_statistics(),
            "retrieval_stats": self.memory_retrieval.get_retrieval_statistics()
        }
        
        return {**base_insights, **memory_insights}
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the memory system"""
        
        return {
            "episodic_memory": self.episodic_memory.get_memory_statistics(),
            "semantic_memory": self.vector_memory.get_memory_insights(),
            "memory_updates": self.memory_updater.get_update_statistics(),
            "current_session": {
                "decisions_made": len(self.session_decisions),
                "reasoning_modes_used": [d['response'].reasoning_mode for d in self.session_decisions]
            }
        }
    
    def maintain_memory_system(self):
        """
        Perform maintenance on the memory system.
        
        This includes:
        - Consolidating similar memories
        - Decaying unused memories
        - Extracting new patterns
        - Cleaning up low-quality memories
        """
        
        maintenance_stats = {}
        
        # Consolidate similar semantic memories
        consolidated = self.vector_memory.consolidate_memories()
        maintenance_stats['consolidated_memories'] = consolidated
        
        # Decay unused memories
        decayed = self.vector_memory.decay_unused_memories()
        maintenance_stats['decayed_memories'] = decayed
        
        # Extract new behavioral insights
        insights = self.memory_updater.extract_insights_from_patterns()
        maintenance_stats['new_insights'] = len(insights)
        
        # Clean up episodic memories
        cleaned_episodic = self.episodic_memory.cleanup_old_memories()
        maintenance_stats['cleaned_episodic'] = cleaned_episodic
        
        # Clean up low-quality semantic memories
        cleaned_semantic = self.vector_memory.cleanup_low_quality_memories()
        maintenance_stats['cleaned_semantic'] = cleaned_semantic
        
        self.logger.info(f"Memory maintenance completed: {maintenance_stats}")
        
        return maintenance_stats
    
    def shadow_mode(self, enabled: bool = True):
        """Enable shadow mode where the twin observes but doesn't act"""
        self.is_shadow_mode = enabled
        return f"Shadow mode {'enabled' if enabled else 'disabled'}. Twin will {'observe and learn' if enabled else 'actively respond'}."
    
    def export_memories(self, filepath: str = None) -> str:
        """Export all memories for backup or analysis"""
        
        if not filepath:
            filepath = f"twin_memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "persona": self.persona,
            "episodic_memories": [m.to_dict() for m in self.episodic_memory.memories.values()],
            "semantic_memory_metadata": [m.to_dict() for m in self.vector_memory.memory_cache.values()],
            "reasoning_insights": self.get_reasoning_insights(),
            "memory_summary": self.get_memory_summary()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return f"Exported complete memory system to {filepath}"