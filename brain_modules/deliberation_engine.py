"""
Deliberation Engine for Digital Twin

This module implements multi-path thinking and evaluation for the digital twin.
Instead of just giving one answer, it considers multiple approaches, evaluates
them against your values and context, then justifies the final choice.

This makes the twin's reasoning more transparent and human-like.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from enum import Enum


class DeliberationCriteria(Enum):
    """Criteria for evaluating options"""
    URGENCY = "urgency"
    IMPORTANCE = "importance"
    ENERGY_REQUIRED = "energy_required"
    TIME_AVAILABLE = "time_available"
    RELATIONSHIP_IMPACT = "relationship_impact"
    STRESS_LEVEL = "stress_level"
    ALIGNMENT_WITH_VALUES = "alignment_with_values"
    LONG_TERM_BENEFIT = "long_term_benefit"


@dataclass
class DeliberationOption:
    """Represents one possible course of action"""
    id: str
    action: str
    reasoning: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    
    # Scoring against different criteria (0-10 scale)
    scores: Dict[DeliberationCriteria, float] = field(default_factory=dict)
    
    # Overall weighted score
    total_score: float = 0.0
    
    # Confidence in this option
    confidence: float = 0.5
    
    # Time/energy estimates
    estimated_time: Optional[int] = None  # minutes
    estimated_energy: Optional[str] = None  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM processing"""
        return {
            'id': self.id,
            'action': self.action,
            'reasoning': self.reasoning,
            'pros': self.pros,
            'cons': self.cons,
            'scores': {k.value: v for k, v in self.scores.items()},
            'total_score': self.total_score,
            'confidence': self.confidence,
            'estimated_time': self.estimated_time,
            'estimated_energy': self.estimated_energy
        }


@dataclass
class DeliberationResult:
    """Result of the deliberation process"""
    chosen_option: DeliberationOption
    all_options: List[DeliberationOption]
    deliberation_reasoning: str
    confidence: float
    decision_factors: List[str]  # What drove the final decision
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'chosen_option': self.chosen_option.to_dict(),
            'all_options': [opt.to_dict() for opt in self.all_options],
            'deliberation_reasoning': self.deliberation_reasoning,
            'confidence': self.confidence,
            'decision_factors': self.decision_factors,
            'timestamp': self.timestamp.isoformat()
        }


class DeliberationEngine:
    """
    Multi-path thinking engine for the digital twin.
    
    This engine:
    1. Generates multiple possible actions for a situation
    2. Evaluates each against relevant criteria
    3. Weighs them according to personal values and context
    4. Chooses the best option with clear reasoning
    """
    
    def __init__(self, llm_client, persona: Dict[str, Any]):
        self.llm_client = llm_client
        self.persona = persona
        self.logger = logging.getLogger(__name__)
        
        # Extract key decision weights from persona
        self.decision_weights = self._extract_decision_weights()
    
    def _extract_decision_weights(self) -> Dict[DeliberationCriteria, float]:
        """Extract decision-making weights from persona"""
        # Default weights - could be customized based on persona
        weights = {
            DeliberationCriteria.URGENCY: 0.8,
            DeliberationCriteria.IMPORTANCE: 0.9,
            DeliberationCriteria.ENERGY_REQUIRED: 0.6,
            DeliberationCriteria.TIME_AVAILABLE: 0.7,
            DeliberationCriteria.RELATIONSHIP_IMPACT: 0.8,
            DeliberationCriteria.STRESS_LEVEL: 0.5,
            DeliberationCriteria.ALIGNMENT_WITH_VALUES: 1.0,
            DeliberationCriteria.LONG_TERM_BENEFIT: 0.7
        }
        
        # Adjust based on persona values
        values = self.persona.get('values', [])
        if 'productivity' in values:
            weights[DeliberationCriteria.URGENCY] += 0.1
            weights[DeliberationCriteria.IMPORTANCE] += 0.1
        
        if 'connection' in values:
            weights[DeliberationCriteria.RELATIONSHIP_IMPACT] += 0.2
        
        if 'growth' in values:
            weights[DeliberationCriteria.LONG_TERM_BENEFIT] += 0.2
        
        # Normalize weights
        max_weight = max(weights.values())
        return {k: v/max_weight for k, v in weights.items()}
    
    async def deliberate(self, 
                        situation: str,
                        context: Dict[str, Any] = None,
                        current_state: Dict[str, Any] = None) -> DeliberationResult:
        """
        Main deliberation process.
        
        Args:
            situation: The situation requiring a decision
            context: Additional context (time, people involved, etc.)
            current_state: Current energy, stress, mood, etc.
        
        Returns:
            DeliberationResult with chosen option and reasoning
        """
        
        # Step 1: Generate multiple options
        options = await self._generate_options(situation, context)
        
        # Step 2: Evaluate each option against criteria
        evaluated_options = await self._evaluate_options(options, situation, context, current_state)
        
        # Step 3: Score and rank options
        ranked_options = self._score_and_rank_options(evaluated_options, current_state)
        
        # Step 4: Make final decision with reasoning
        result = await self._make_final_decision(ranked_options, situation, context)
        
        return result
    
    async def _generate_options(self, 
                               situation: str, 
                               context: Dict[str, Any] = None) -> List[DeliberationOption]:
        """Generate multiple possible actions for the situation"""
        
        # Build prompt for option generation
        prompt = self._build_option_generation_prompt(situation, context)
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are generating multiple possible actions for a decision-making process. Be creative but realistic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for creativity
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            
            # Convert to DeliberationOption objects
            options = []
            for i, option_data in enumerate(data.get('options', [])):
                option = DeliberationOption(
                    id=f"option_{i+1}",
                    action=option_data.get('action', ''),
                    reasoning=option_data.get('reasoning', ''),
                    pros=option_data.get('pros', []),
                    cons=option_data.get('cons', []),
                    estimated_time=option_data.get('estimated_time'),
                    estimated_energy=option_data.get('estimated_energy')
                )
                options.append(option)
            
            return options
            
        except Exception as e:
            self.logger.error(f"Failed to generate options: {e}")
            # Return default options as fallback
            return [
                DeliberationOption(
                    id="fallback",
                    action="Handle situation with standard approach",
                    reasoning="Fallback when option generation fails"
                )
            ]
    
    def _build_option_generation_prompt(self, situation: str, context: Dict[str, Any] = None) -> str:
        """Build prompt for generating options"""
        
        persona_summary = f"""
        Person: {self.persona.get('name', 'User')}
        Traits: {', '.join(self.persona.get('traits', []))}
        Values: {', '.join(self.persona.get('values', []))}
        Communication Style: {self.persona.get('communication_style', {}).get('tone', 'professional')}
        """
        
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        return f"""
{persona_summary}

Situation: {situation}
{context_str}

Generate 3-5 different ways this person could handle this situation. For each option, provide:

1. A clear action description
2. Reasoning for why this person might choose this approach
3. 2-3 pros of this approach
4. 2-3 cons of this approach
5. Estimated time required (in minutes)
6. Estimated energy level required (low/medium/high)

Consider the person's traits, values, and communication style. Include both conventional and creative approaches.

Respond in JSON format:
{{
    "options": [
        {{
            "action": "specific action description",
            "reasoning": "why this person might choose this",
            "pros": ["pro 1", "pro 2"],
            "cons": ["con 1", "con 2"],
            "estimated_time": 30,
            "estimated_energy": "medium"
        }}
    ]
}}
"""
    
    async def _evaluate_options(self, 
                                options: List[DeliberationOption],
                                situation: str,
                                context: Dict[str, Any] = None,
                                current_state: Dict[str, Any] = None) -> List[DeliberationOption]:
        """Evaluate each option against deliberation criteria"""
        
        for option in options:
            # Build evaluation prompt for this specific option
            eval_prompt = self._build_evaluation_prompt(option, situation, context, current_state)
            
            try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are evaluating a decision option against multiple criteria. Be objective and consider trade-offs."},
                        {"role": "user", "content": eval_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for consistent evaluation
                    response_format={"type": "json_object"}
                )
                
                data = json.loads(response.choices[0].message.content)
                
                # Extract scores
                scores = data.get('scores', {})
                for criteria_str, score in scores.items():
                    try:
                        criteria = DeliberationCriteria(criteria_str)
                        option.scores[criteria] = float(score)
                    except (ValueError, TypeError):
                        continue
                
                # Update confidence
                option.confidence = float(data.get('confidence', 0.5))
                
            except Exception as e:
                self.logger.error(f"Failed to evaluate option {option.id}: {e}")
                # Set default scores
                for criteria in DeliberationCriteria:
                    option.scores[criteria] = 5.0  # Neutral score
        
        return options
    
    def _build_evaluation_prompt(self, 
                                option: DeliberationOption,
                                situation: str,
                                context: Dict[str, Any] = None,
                                current_state: Dict[str, Any] = None) -> str:
        """Build prompt for evaluating a specific option"""
        
        state_str = ""
        if current_state:
            state_str = f"\nCurrent State: {json.dumps(current_state, indent=2)}"
        
        return f"""
Situation: {situation}
Context: {json.dumps(context or {}, indent=2)}
{state_str}

Option to Evaluate:
Action: {option.action}
Reasoning: {option.reasoning}
Pros: {option.pros}
Cons: {option.cons}

Rate this option on a scale of 0-10 for each criteria:

- urgency: How well does this handle urgent aspects?
- importance: How important/impactful is this action?
- energy_required: How much energy does this require? (0=high energy, 10=low energy)
- time_available: How well does this fit available time? (considering estimated time: {option.estimated_time} min)
- relationship_impact: What's the impact on relationships?
- stress_level: How stressful is this approach? (0=very stressful, 10=not stressful)
- alignment_with_values: How well does this align with core values?
- long_term_benefit: What are the long-term benefits?

Also provide an overall confidence score (0-1) for how good this option is.

Respond in JSON:
{{
    "scores": {{
        "urgency": 8.0,
        "importance": 7.5,
        ...
    }},
    "confidence": 0.85
}}
"""
    
    def _score_and_rank_options(self, 
                               options: List[DeliberationOption],
                               current_state: Dict[str, Any] = None) -> List[DeliberationOption]:
        """Calculate weighted scores and rank options"""
        
        for option in options:
            # Calculate weighted total score
            total_score = 0.0
            weight_sum = 0.0
            
            for criteria, score in option.scores.items():
                weight = self.decision_weights.get(criteria, 0.5)
                total_score += score * weight
                weight_sum += weight
            
            # Normalize by total weights
            option.total_score = total_score / weight_sum if weight_sum > 0 else 0.0
            
            # Adjust for current state
            if current_state:
                option.total_score = self._adjust_for_current_state(option, current_state)
        
        # Sort by total score (highest first)
        return sorted(options, key=lambda x: x.total_score, reverse=True)
    
    def _adjust_for_current_state(self, 
                                 option: DeliberationOption, 
                                 current_state: Dict[str, Any]) -> float:
        """Adjust option score based on current state"""
        score = option.total_score
        
        # If low energy, penalize high-energy options
        if current_state.get('energy_level') == 'low' and option.estimated_energy == 'high':
            score *= 0.8
        
        # If high stress, favor low-stress options
        if current_state.get('stress_level') == 'high':
            stress_score = option.scores.get(DeliberationCriteria.STRESS_LEVEL, 5.0)
            if stress_score > 7.0:  # Low stress option
                score *= 1.1
        
        # If time is limited, favor quick options
        time_available = current_state.get('time_available_minutes', 60)
        if option.estimated_time and option.estimated_time > time_available:
            score *= 0.7
        
        return score
    
    async def _make_final_decision(self, 
                                  ranked_options: List[DeliberationOption],
                                  situation: str,
                                  context: Dict[str, Any] = None) -> DeliberationResult:
        """Make the final decision and generate reasoning"""
        
        if not ranked_options:
            raise ValueError("No options available for decision")
        
        chosen_option = ranked_options[0]  # Highest scored option
        
        # Generate decision reasoning
        reasoning_prompt = self._build_decision_reasoning_prompt(
            chosen_option, ranked_options[1:3], situation, context
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are explaining why a specific decision was made, considering all alternatives."},
                    {"role": "user", "content": reasoning_prompt}
                ],
                temperature=0.4
            )
            
            deliberation_reasoning = response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Failed to generate decision reasoning: {e}")
            deliberation_reasoning = f"Chose {chosen_option.action} based on highest overall score of {chosen_option.total_score:.2f}"
        
        # Identify key decision factors
        decision_factors = self._identify_decision_factors(chosen_option, ranked_options)
        
        return DeliberationResult(
            chosen_option=chosen_option,
            all_options=ranked_options,
            deliberation_reasoning=deliberation_reasoning,
            confidence=chosen_option.confidence,
            decision_factors=decision_factors
        )
    
    def _build_decision_reasoning_prompt(self, 
                                        chosen_option: DeliberationOption,
                                        alternatives: List[DeliberationOption],
                                        situation: str,
                                        context: Dict[str, Any] = None) -> str:
        """Build prompt for explaining the final decision"""
        
        alt_summaries = []
        for alt in alternatives:
            alt_summaries.append(f"- {alt.action} (Score: {alt.total_score:.2f})")
        
        alternatives_str = "\n".join(alt_summaries) if alt_summaries else "No alternatives available"
        
        return f"""
Situation: {situation}
Context: {json.dumps(context or {}, indent=2)}

CHOSEN OPTION:
Action: {chosen_option.action}
Score: {chosen_option.total_score:.2f}
Reasoning: {chosen_option.reasoning}

ALTERNATIVES CONSIDERED:
{alternatives_str}

Explain in 2-3 sentences why the chosen option was selected over the alternatives. Focus on:
1. What key factors made this option best
2. What trade-offs were considered
3. How this aligns with the person's values and situation

Be conversational and insightful, as if you're explaining your thought process to yourself.
"""
    
    def _identify_decision_factors(self, 
                                  chosen_option: DeliberationOption,
                                  all_options: List[DeliberationOption]) -> List[str]:
        """Identify the key factors that drove the decision"""
        
        factors = []
        
        # Check which criteria the chosen option scored highest on
        chosen_scores = chosen_option.scores
        
        for criteria, score in chosen_scores.items():
            # Compare with other options
            is_highest = True
            for other_option in all_options[1:4]:  # Check top alternatives
                other_score = other_option.scores.get(criteria, 0)
                if other_score > score:
                    is_highest = False
                    break
            
            if is_highest and score > 7.0:  # High score and best among options
                factors.append(f"High {criteria.value.replace('_', ' ')}")
        
        # If no clear factors, use top-weighted criteria
        if not factors:
            top_criteria = sorted(chosen_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            factors = [f"{criteria.value.replace('_', ' ')}" for criteria, score in top_criteria]
        
        return factors