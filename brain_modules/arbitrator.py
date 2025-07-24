"""
Arbitrator Module for Digital Twin

This module resolves conflicts between different behavioral voices and makes
final decisions. It acts as the "executive function" of the brain, weighing
different perspectives and choosing the best course of action.

The arbitrator considers:
1. Voice urgency levels
2. Current context and state
3. Personal values and priorities
4. Past decision outcomes
5. Practical constraints
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from .behavioral_voices import VoiceArgument, VoiceStrength
from .deliberation_engine import DeliberationOption, DeliberationResult


@dataclass
class ArbitrationContext:
    """Context information for making arbitration decisions"""
    current_energy: str = "medium"  # low, medium, high
    current_stress: str = "medium"  # low, medium, high
    available_time: Optional[int] = None  # minutes
    current_priorities: List[str] = field(default_factory=list)
    recent_decisions: List[Dict[str, Any]] = field(default_factory=list)
    external_pressures: List[str] = field(default_factory=list)


@dataclass
class ArbitrationResult:
    """Result of the arbitration process"""
    final_decision: str
    winning_voices: List[str]  # Which voices influenced the decision most
    voice_weights: Dict[str, float]  # How much each voice influenced (0-1)
    reasoning: str  # Why this decision was made
    confidence: float  # Overall confidence (0-1)
    considered_alternatives: List[str]
    trade_offs_acknowledged: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'final_decision': self.final_decision,
            'winning_voices': self.winning_voices,
            'voice_weights': self.voice_weights,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'considered_alternatives': self.considered_alternatives,
            'trade_offs_acknowledged': self.trade_offs_acknowledged
        }


class DecisionArbitrator:
    """
    The arbitrator that resolves conflicts between behavioral voices
    and makes final decisions for the digital twin.
    
    This is the "executive function" that weighs competing priorities
    and chooses the best course of action.
    """
    
    def __init__(self, llm_client, persona: Dict[str, Any]):
        self.llm_client = llm_client
        self.persona = persona
        self.logger = logging.getLogger(__name__)
        
        # Extract core decision-making principles from persona
        self.decision_principles = self._extract_decision_principles()
        
        # Track decision history for learning
        self.decision_history: List[ArbitrationResult] = []
    
    def _extract_decision_principles(self) -> Dict[str, float]:
        """Extract decision-making principles from persona"""
        principles = {
            "efficiency_weight": 0.7,
            "relationship_weight": 0.8,
            "wellbeing_weight": 0.6,
            "growth_weight": 0.5,
            "values_multiplier": 1.2,  # How much to weight value alignment
            "urgency_sensitivity": 0.8,  # How much urgency affects decisions
            "stress_threshold": 0.7  # Above this stress, prioritize wellbeing
        }
        
        # Adjust based on persona
        values = self.persona.get('values', [])
        traits = self.persona.get('traits', [])
        
        # Adjust weights based on values
        if 'productivity' in values:
            principles["efficiency_weight"] += 0.2
        if 'connection' in values:
            principles["relationship_weight"] += 0.2
        if 'growth' in values:
            principles["growth_weight"] += 0.3
        
        # Adjust based on traits
        if 'analytical' in traits:
            principles["efficiency_weight"] += 0.1
        if 'empathetic' in traits:
            principles["relationship_weight"] += 0.1
        
        return principles
    
    async def arbitrate(self, 
                       voice_arguments: List[VoiceArgument],
                       situation: str,
                       context: ArbitrationContext = None) -> ArbitrationResult:
        """
        Main arbitration process - resolves conflicts between voices.
        
        Args:
            voice_arguments: Arguments from all behavioral voices
            situation: The situation being decided
            context: Current context and constraints
            
        Returns:
            ArbitrationResult with final decision and reasoning
        """
        
        if not voice_arguments:
            raise ValueError("No voice arguments provided for arbitration")
        
        # Step 1: Analyze voice conflicts and agreements
        conflict_analysis = self._analyze_voice_conflicts(voice_arguments)
        
        # Step 2: Apply context-based weights
        weighted_voices = self._apply_contextual_weights(voice_arguments, context)
        
        # Step 3: Check for clear consensus or dominant voice
        if self._has_clear_consensus(weighted_voices):
            return await self._build_consensus_decision(weighted_voices, situation, context)
        
        # Step 4: Resolve conflicts using arbitration logic
        resolution = await self._resolve_conflicts(weighted_voices, situation, context, conflict_analysis)
        
        # Step 5: Store decision for learning
        self.decision_history.append(resolution)
        
        return resolution
    
    def _analyze_voice_conflicts(self, voice_arguments: List[VoiceArgument]) -> Dict[str, Any]:
        """Analyze conflicts and agreements between voices"""
        
        analysis = {
            "conflicts": [],
            "agreements": [],
            "dominant_themes": [],
            "urgency_levels": {}
        }
        
        # Group by urgency
        for arg in voice_arguments:
            urgency_level = arg.urgency.name
            if urgency_level not in analysis["urgency_levels"]:
                analysis["urgency_levels"][urgency_level] = []
            analysis["urgency_levels"][urgency_level].append(arg.voice_name)
        
        # Look for conflicting positions
        positions = [(arg.voice_name, arg.position) for arg in voice_arguments]
        
        # Simple conflict detection - voices suggesting opposite actions
        efficiency_args = [arg for arg in voice_arguments if arg.voice_name == "Efficiency"]
        wellbeing_args = [arg for arg in voice_arguments if arg.voice_name == "Wellbeing"]
        
        if efficiency_args and wellbeing_args:
            eff_pos = efficiency_args[0].position.lower()
            well_pos = wellbeing_args[0].position.lower()
            
            # Check for time/stress conflicts
            if ("immediate" in eff_pos or "quick" in eff_pos) and ("break" in well_pos or "rest" in well_pos):
                analysis["conflicts"].append({
                    "type": "time_pressure_vs_wellbeing",
                    "voices": ["Efficiency", "Wellbeing"],
                    "description": "Efficiency wants quick action, Wellbeing wants rest"
                })
        
        # Look for agreements
        common_keywords = {}
        for arg in voice_arguments:
            words = arg.position.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_keywords[word] = common_keywords.get(word, 0) + 1
        
        # Find words mentioned by multiple voices
        agreement_words = [word for word, count in common_keywords.items() if count > 1]
        if agreement_words:
            analysis["agreements"] = agreement_words[:3]  # Top 3
        
        return analysis
    
    def _apply_contextual_weights(self, 
                                 voice_arguments: List[VoiceArgument],
                                 context: ArbitrationContext = None) -> List[Tuple[VoiceArgument, float]]:
        """Apply contextual weights to voice arguments"""
        
        weighted_voices = []
        
        for arg in voice_arguments:
            # Base weight from decision principles
            base_weight = self.decision_principles.get(f"{arg.voice_name.lower()}_weight", 0.5)
            
            # Urgency multiplier
            urgency_multiplier = arg.urgency.value * self.decision_principles["urgency_sensitivity"]
            
            # Context adjustments
            context_multiplier = 1.0
            if context:
                context_multiplier = self._calculate_context_multiplier(arg, context)
            
            # Final weight
            final_weight = base_weight * (1 + urgency_multiplier) * context_multiplier
            
            weighted_voices.append((arg, final_weight))
            
            self.logger.debug(f"Voice '{arg.voice_name}': base={base_weight:.2f}, "
                            f"urgency={urgency_multiplier:.2f}, context={context_multiplier:.2f}, "
                            f"final={final_weight:.2f}")
        
        return weighted_voices
    
    def _calculate_context_multiplier(self, 
                                    voice_arg: VoiceArgument,
                                    context: ArbitrationContext) -> float:
        """Calculate how context affects this voice's weight"""
        
        multiplier = 1.0
        voice_name = voice_arg.voice_name.lower()
        
        # Energy level adjustments
        if context.current_energy == "low":
            if voice_name == "wellbeing":
                multiplier *= 1.5  # Wellbeing more important when tired
            elif voice_name == "efficiency":
                multiplier *= 0.7  # Efficiency less achievable when tired
        
        # Stress level adjustments
        if context.current_stress == "high":
            if voice_name == "wellbeing":
                multiplier *= 1.4  # Wellbeing crucial when stressed
            elif voice_name == "efficiency":
                multiplier *= 0.8  # Efficiency may suffer under stress
        
        # Time pressure adjustments
        if context.available_time and context.available_time < 30:  # Less than 30 minutes
            if voice_name == "efficiency":
                multiplier *= 1.3  # Efficiency more important with limited time
            elif voice_name == "growth":
                multiplier *= 0.6  # Learning takes time
        
        # Priority alignments
        if context.current_priorities:
            for priority in context.current_priorities:
                if priority.lower() in voice_arg.position.lower():
                    multiplier *= 1.2  # Boost voices aligned with current priorities
        
        return multiplier
    
    def _has_clear_consensus(self, weighted_voices: List[Tuple[VoiceArgument, float]]) -> bool:
        """Check if there's a clear consensus among voices"""
        
        if not weighted_voices:
            return False
        
        # Sort by weight
        sorted_voices = sorted(weighted_voices, key=lambda x: x[1], reverse=True)
        
        # Check if top voice is significantly stronger
        top_weight = sorted_voices[0][1]
        if len(sorted_voices) > 1:
            second_weight = sorted_voices[1][1]
            
            # Clear consensus if top voice has >50% more weight
            if top_weight > second_weight * 1.5:
                return True
        
        # Check if multiple voices agree on similar action
        positions = [arg.position.lower() for arg, weight in weighted_voices[:3]]  # Top 3
        
        # Simple agreement check - if positions share key words
        common_words = set()
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                words1 = set(pos1.split())
                words2 = set(pos2.split())
                common = words1.intersection(words2)
                common_words.update(common)
        
        # Consensus if significant overlap
        return len(common_words) > 2
    
    async def _build_consensus_decision(self, 
                                       weighted_voices: List[Tuple[VoiceArgument, float]],
                                       situation: str,
                                       context: ArbitrationContext = None) -> ArbitrationResult:
        """Build decision when there's clear consensus"""
        
        # Sort by weight
        sorted_voices = sorted(weighted_voices, key=lambda x: x[1], reverse=True)
        top_voice_arg, top_weight = sorted_voices[0]
        
        # Calculate normalized weights
        total_weight = sum(weight for _, weight in weighted_voices)
        normalized_weights = {
            arg.voice_name: weight / total_weight 
            for arg, weight in weighted_voices
        }
        
        reasoning = f"Clear consensus reached. {top_voice_arg.voice_name} voice provides the strongest guidance: {top_voice_arg.reasoning}"
        
        return ArbitrationResult(
            final_decision=top_voice_arg.position,
            winning_voices=[top_voice_arg.voice_name],
            voice_weights=normalized_weights,
            reasoning=reasoning,
            confidence=0.85,  # High confidence for consensus
            considered_alternatives=[arg.position for arg, _ in sorted_voices[1:3]],
            trade_offs_acknowledged=top_voice_arg.concerns
        )
    
    async def _resolve_conflicts(self, 
                                weighted_voices: List[Tuple[VoiceArgument, float]],
                                situation: str,
                                context: ArbitrationContext = None,
                                conflict_analysis: Dict[str, Any] = None) -> ArbitrationResult:
        """Resolve conflicts between voices using LLM arbitration"""
        
        # Build arbitration prompt
        arbitration_prompt = self._build_arbitration_prompt(
            weighted_voices, situation, context, conflict_analysis
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are the executive decision-maker resolving conflicts between different aspects of personality. Be thoughtful and consider trade-offs."},
                    {"role": "user", "content": arbitration_prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            
            # Extract decision components
            final_decision = data.get("final_decision", "Unable to reach decision")
            reasoning = data.get("reasoning", "")
            confidence = float(data.get("confidence", 0.5))
            winning_voices = data.get("winning_voices", [])
            trade_offs = data.get("trade_offs", [])
            
            # Calculate voice weights
            total_weight = sum(weight for _, weight in weighted_voices)
            voice_weights = {
                arg.voice_name: weight / total_weight 
                for arg, weight in weighted_voices
            }
            
            # Get alternatives
            alternatives = [arg.position for arg, _ in weighted_voices if arg.position != final_decision]
            
            return ArbitrationResult(
                final_decision=final_decision,
                winning_voices=winning_voices,
                voice_weights=voice_weights,
                reasoning=reasoning,
                confidence=confidence,
                considered_alternatives=alternatives[:3],  # Top 3 alternatives
                trade_offs_acknowledged=trade_offs
            )
            
        except Exception as e:
            self.logger.error(f"Failed to resolve conflicts: {e}")
            
            # Fallback to highest weighted voice
            sorted_voices = sorted(weighted_voices, key=lambda x: x[1], reverse=True)
            top_voice_arg, _ = sorted_voices[0]
            
            return ArbitrationResult(
                final_decision=top_voice_arg.position,
                winning_voices=[top_voice_arg.voice_name],
                voice_weights={arg.voice_name: 1.0 if arg.voice_name == top_voice_arg.voice_name else 0.0 
                             for arg, _ in weighted_voices},
                reasoning=f"Fallback decision: {top_voice_arg.reasoning}",
                confidence=0.3,  # Low confidence for fallback
                considered_alternatives=[],
                trade_offs_acknowledged=[]
            )
    
    def _build_arbitration_prompt(self, 
                                 weighted_voices: List[Tuple[VoiceArgument, float]],
                                 situation: str,
                                 context: ArbitrationContext = None,
                                 conflict_analysis: Dict[str, Any] = None) -> str:
        """Build prompt for LLM arbitration"""
        
        # Persona summary
        persona_summary = f"""
        Decision Maker Profile:
        - Name: {self.persona.get('name', 'User')}
        - Core Values: {', '.join(self.persona.get('values', []))}
        - Key Traits: {', '.join(self.persona.get('traits', []))}
        - Decision Style: {self.persona.get('decision_patterns', {}).get('style', 'analytical')}
        """
        
        # Context information
        context_info = ""
        if context:
            context_info = f"""
        Current Context:
        - Energy Level: {context.current_energy}
        - Stress Level: {context.current_stress}
        - Available Time: {context.available_time} minutes
        - Current Priorities: {', '.join(context.current_priorities)}
        """
        
        # Voice arguments with weights
        voice_details = ""
        for arg, weight in weighted_voices:
            voice_details += f"""
        
        {arg.voice_name} Voice (Weight: {weight:.2f}):
        - Position: {arg.position}
        - Reasoning: {arg.reasoning}
        - Urgency: {arg.urgency.name}
        - Key Concerns: {', '.join(arg.concerns[:2])}
        """
        
        # Conflict analysis
        conflict_info = ""
        if conflict_analysis and conflict_analysis.get("conflicts"):
            conflict_info = f"""
        
        Identified Conflicts:
        {json.dumps(conflict_analysis['conflicts'], indent=2)}
        """
        
        return f"""
        {persona_summary}
        
        Situation: {situation}
        {context_info}
        
        Internal Voice Arguments:
        {voice_details}
        {conflict_info}
        
        As the executive decision-maker, resolve these competing voices and make a final decision.
        
        Consider:
        1. Which voices have the strongest arguments for this specific situation?
        2. What are the key trade-offs being made?
        3. How do the current context and constraints affect the decision?
        4. What would this person most likely choose given their values and patterns?
        
        Provide your decision in JSON format:
        {{
            "final_decision": "Clear, specific action to take",
            "reasoning": "Why this decision was chosen, considering all voices and trade-offs",
            "confidence": 0.85,
            "winning_voices": ["Voice1", "Voice2"],
            "trade_offs": ["Trade-off 1", "Trade-off 2"]
        }}
        """
    
    def get_decision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in past decisions"""
        
        if not self.decision_history:
            return {"message": "No decision history available"}
        
        patterns = {
            "total_decisions": len(self.decision_history),
            "average_confidence": sum(d.confidence for d in self.decision_history) / len(self.decision_history),
            "most_influential_voices": {},
            "common_trade_offs": []
        }
        
        # Count voice influence
        voice_counts = {}
        for decision in self.decision_history:
            for voice in decision.winning_voices:
                voice_counts[voice] = voice_counts.get(voice, 0) + 1
        
        patterns["most_influential_voices"] = dict(sorted(voice_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Common trade-offs
        all_trade_offs = []
        for decision in self.decision_history:
            all_trade_offs.extend(decision.trade_offs_acknowledged)
        
        trade_off_counts = {}
        for trade_off in all_trade_offs:
            trade_off_counts[trade_off] = trade_off_counts.get(trade_off, 0) + 1
        
        patterns["common_trade_offs"] = list(dict(sorted(trade_off_counts.items(), key=lambda x: x[1], reverse=True)).keys())[:5]
        
        return patterns