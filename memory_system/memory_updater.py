"""
Memory Updater for Digital Twin

This module automatically captures and stores memories from the twin's reasoning
and decision-making processes. It acts as the "memory formation" system that
converts experiences into both episodic and semantic memories.

Key functions:
- Automatically store reasoning outcomes
- Extract patterns from decisions
- Create memories from feedback
- Link related experiences
- Update memory relevance based on outcomes
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from .episodic_memory import EpisodicMemorySystem, EpisodicMemory, MemoryType, MemoryImportance
from .vector_memory import EnhancedVectorMemory, VectorMemoryType
from ..digital_twin_v2 import TwinResponse, Situation

# Import observer components
try:
    from ..observer.observer_utils import ObservationEvent, ActivityCategory
    OBSERVER_AVAILABLE = True
except ImportError:
    OBSERVER_AVAILABLE = False

# Import goal system components
try:
    from ..goal_system.goal_manager import Goal, Milestone, GoalStatus
    from ..goal_system.goal_reasoner import GoalContext, GoalRelevance
    GOAL_SYSTEM_AVAILABLE = True
except ImportError:
    GOAL_SYSTEM_AVAILABLE = False


class MemoryUpdater:
    """
    Automatically captures and stores memories from the twin's experiences.
    
    This system:
    1. Listens to all twin decisions and outcomes
    2. Extracts memorable patterns and insights
    3. Stores both specific events (episodic) and learned patterns (semantic)
    4. Updates memory relevance based on success/failure
    5. Creates memory links between related experiences
    """
    
    def __init__(self, 
                 episodic_memory: EpisodicMemorySystem,
                 vector_memory: EnhancedVectorMemory):
        
        self.episodic_memory = episodic_memory
        self.vector_memory = vector_memory
        self.logger = logging.getLogger(__name__)
        
        # Track what we've already stored to avoid duplicates
        self.stored_decisions = set()
        self.pattern_extraction_cache = {}
    
    def capture_decision_memory(self, 
                               situation: Situation,
                               response: TwinResponse,
                               context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Capture a decision as both episodic and semantic memory.
        
        Args:
            situation: The situation that required a decision
            response: The twin's response
            context: Additional context (state, people, etc.)
            
        Returns:
            Dict with episodic_id and semantic_id of stored memories
        """
        
        # Create unique identifier for this decision
        decision_key = f"{situation.timestamp.isoformat()}_{hash(situation.context)}"
        
        if decision_key in self.stored_decisions:
            self.logger.debug("Decision already stored, skipping duplicate")
            return {}
        
        # Store episodic memory (specific event)
        episodic_id = self._store_episodic_decision(situation, response, context)
        
        # Store semantic memory (patterns and knowledge)
        semantic_id = self._store_semantic_decision(situation, response, context)
        
        # Mark as stored
        self.stored_decisions.add(decision_key)
        
        self.logger.info(f"Captured decision memory: {response.action[:50]}...")
        
        return {
            "episodic_id": episodic_id,
            "semantic_id": semantic_id
        }
    
    def _store_episodic_decision(self, 
                                situation: Situation,
                                response: TwinResponse,
                                context: Dict[str, Any] = None) -> str:
        """Store the specific decision event"""
        
        # Determine importance based on confidence and reasoning mode
        importance = MemoryImportance.MEDIUM
        
        if response.confidence > 0.9:
            importance = MemoryImportance.HIGH
        elif response.confidence < 0.5:
            importance = MemoryImportance.LOW
        
        # Enhance for complex reasoning
        if response.reasoning_mode == "deliberation":
            importance = MemoryImportance.HIGH
        
        # Extract people involved
        people_involved = []
        if situation.metadata.get('sender'):
            people_involved.append(situation.metadata['sender'])
        
        # Store the decision
        memory = self.episodic_memory.store_decision_memory(
            decision=response.action,
            situation=situation.context,
            reasoning=response.reasoning,
            context={
                "reasoning_mode": response.reasoning_mode,
                "confidence": response.confidence,
                "category": situation.category,
                "metadata": situation.metadata,
                "state_context": context or {}
            },
            importance=importance
        )
        
        # Add additional episodic details
        if context:
            memory.emotional_state = context.get('current_mood')
            memory.energy_level = context.get('current_energy')
            memory.location = context.get('location')
        
        memory.people_involved = people_involved
        memory.tags = [
            situation.category,
            response.reasoning_mode,
            f"confidence_{int(response.confidence * 10)}"
        ]
        
        # Add voice information if available
        if response.voice_arguments:
            winning_voices = [arg.voice_name for arg in response.voice_arguments 
                            if arg.urgency.value > 0.7]
            memory.tags.extend([f"voice_{voice.lower()}" for voice in winning_voices])
        
        return memory.id
    
    def _store_semantic_decision(self,
                                situation: Situation,
                                response: TwinResponse,
                                context: Dict[str, Any] = None) -> str:
        """Store the decision pattern/knowledge"""
        
        # Create semantic content based on reasoning mode
        if response.reasoning_mode == "heuristic":
            content = self._create_heuristic_semantic_content(situation, response)
            memory_type = VectorMemoryType.PATTERN
            
        elif response.reasoning_mode == "deliberation":
            content = self._create_deliberation_semantic_content(situation, response)
            memory_type = VectorMemoryType.STRATEGY
            
        elif response.reasoning_mode == "arbitration":
            content = self._create_arbitration_semantic_content(situation, response)
            memory_type = VectorMemoryType.PREFERENCE
            
        else:
            content = f"Decision approach: {response.action} for situations like '{situation.context}'"
            memory_type = VectorMemoryType.PATTERN
        
        # Store in vector memory
        semantic_id = self.vector_memory.add_memory(
            content=content,
            memory_type=memory_type,
            metadata={
                "situation_category": situation.category,
                "reasoning_mode": response.reasoning_mode,
                "confidence": response.confidence,
                "timestamp": situation.timestamp.isoformat()
            },
            tags=[situation.category, response.reasoning_mode],
            source_reasoning_mode=response.reasoning_mode
        )
        
        return semantic_id
    
    def capture_observation_memory(self, observation: 'ObservationEvent') -> Optional[str]:
        """Capture memory from observer system observations"""
        
        if not OBSERVER_AVAILABLE or not observation:
            return None
        
        try:
            # Store observation as episodic memory
            memory_id = self.episodic_memory.store_decision_memory(
                decision=f"Observed {observation.event_type}",
                situation=f"User activity: {observation.app_name}",
                reasoning=f"Detected {observation.category.value} activity",
                metadata={
                    'source': 'observer_system',
                    'observation_type': observation.event_type,
                    'app_name': observation.app_name,
                    'window_title': observation.window_title,
                    'url': observation.url,
                    'category': observation.category.value,
                    'duration_seconds': observation.duration_seconds,
                    'timestamp': observation.timestamp.isoformat(),
                    'privacy_level': observation.privacy_level.value,
                    'confidence': observation.confidence
                }
            )
            
            # Store behavioral patterns in semantic memory
            if observation.duration_seconds > 60:  # Only significant activities
                pattern_content = self._create_behavioral_pattern_content(observation)
                
                self.vector_memory.add_memory(
                    content=pattern_content,
                    memory_type=VectorMemoryType.BEHAVIORAL_PATTERN,
                    metadata={
                        'activity_category': observation.category.value,
                        'app_name': observation.app_name,
                        'duration_minutes': observation.duration_seconds // 60,
                        'timestamp': observation.timestamp.isoformat(),
                        'source': 'observer_system'
                    },
                    tags=['behavior', observation.category.value, 'observed_activity']
                )
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error capturing observation memory: {e}")
            return None
    
    def _create_behavioral_pattern_content(self, observation: 'ObservationEvent') -> str:
        """Create semantic content for behavioral patterns"""
        
        if observation.category == ActivityCategory.PRODUCTIVITY:
            content = f"User engages in productive work using {observation.app_name}"
        elif observation.category == ActivityCategory.DEVELOPMENT:
            content = f"User does development work with {observation.app_name}"
        elif observation.category == ActivityCategory.COMMUNICATION:
            content = f"User communicates using {observation.app_name}"
        elif observation.category == ActivityCategory.RESEARCH:
            content = f"User researches information using {observation.app_name}"
        elif observation.category == ActivityCategory.ENTERTAINMENT:
            content = f"User takes entertainment breaks with {observation.app_name}"
        else:
            content = f"User spends time on {observation.category.value} activities with {observation.app_name}"
        
        # Add duration context
        duration_minutes = observation.duration_seconds // 60
        if duration_minutes > 60:
            content += f" for extended periods (usually {duration_minutes} minutes or more)"
        elif duration_minutes > 15:
            content += f" for moderate periods (typically {duration_minutes} minutes)"
        else:
            content += f" for brief periods (around {duration_minutes} minutes)"
        
        # Add timing context if available
        hour = observation.timestamp.hour
        if 9 <= hour <= 11:
            content += " during morning hours"
        elif 13 <= hour <= 17:
            content += " during afternoon hours"
        elif 18 <= hour <= 21:
            content += " during evening hours"
        
        return content
    
    def capture_activity_session_memory(self, 
                                      session_summary: Dict[str, Any],
                                      insights: List[str] = None) -> Optional[str]:
        """Capture memory from activity session analysis"""
        
        try:
            # Store session as episodic memory
            session_description = f"Work session: {session_summary.get('duration_minutes', 0)} minutes"
            session_context = f"Productivity score: {session_summary.get('productivity_score', 0):.2f}"
            
            memory_id = self.episodic_memory.store_decision_memory(
                decision="Complete work session",
                situation=session_description,
                reasoning=session_context,
                metadata={
                    'source': 'observer_system',
                    'session_type': 'work_session',
                    'productivity_score': session_summary.get('productivity_score', 0),
                    'duration_minutes': session_summary.get('duration_minutes', 0),
                    'focus_sessions': session_summary.get('focus_sessions', 0),
                    'break_sessions': session_summary.get('break_sessions', 0),
                    'top_apps': session_summary.get('top_applications', [])[:3],  # Top 3 apps
                    'activity_categories': session_summary.get('categories', {}),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Store productivity insights
            if insights:
                for insight in insights:
                    self.vector_memory.add_memory(
                        content=f"Productivity insight: {insight}",
                        memory_type=VectorMemoryType.INSIGHT,
                        metadata={
                            'source': 'observer_system',
                            'insight_type': 'productivity',
                            'session_id': memory_id,
                            'timestamp': datetime.now().isoformat()
                        },
                        tags=['productivity', 'behavioral_insight', 'observer_derived']
                    )
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error capturing activity session memory: {e}")
            return None
    
    def _create_heuristic_semantic_content(self, situation: Situation, response: TwinResponse) -> str:
        """Create semantic content for heuristic decisions"""
        
        content = f"Pattern: When {situation.context.lower()}, "
        content += f"the effective approach is to {response.action}. "
        
        if response.heuristic_decision:
            content += f"This pattern saved approximately {response.heuristic_decision.time_saved} minutes "
            content += f"and was chosen with {response.confidence:.2f} confidence."
        
        if response.alternatives:
            content += f" Alternatives considered but rejected: {', '.join(response.alternatives[:2])}."
        
        return content
    
    def _create_deliberation_semantic_content(self, situation: Situation, response: TwinResponse) -> str:
        """Create semantic content for deliberation decisions"""
        
        content = f"Strategic approach for {situation.category} situations: {response.action}. "
        content += f"Reasoning: {response.reasoning} "
        
        if response.deliberation_details:
            content += f"This was chosen from {len(response.deliberation_details.all_options)} options "
            content += f"based on systematic evaluation. "
            
            # Include top alternative for comparison
            if len(response.deliberation_details.all_options) > 1:
                alt_option = response.deliberation_details.all_options[1]
                content += f"Top alternative was '{alt_option.action}' with score {alt_option.total_score:.2f}."
        
        return content
    
    def _create_arbitration_semantic_content(self, situation: Situation, response: TwinResponse) -> str:
        """Create semantic content for voice arbitration decisions"""
        
        content = f"Value-based decision for {situation.category}: {response.action}. "
        
        if response.arbitration_result:
            winning_voices = response.arbitration_result.winning_voices
            content += f"This decision prioritized {', '.join(winning_voices)} perspectives. "
            
            if response.trade_offs:
                content += f"Trade-offs accepted: {'; '.join(response.trade_offs[:2])}. "
        
        if response.voice_arguments:
            # Summarize the voice positions
            voice_positions = {arg.voice_name: arg.position for arg in response.voice_arguments}
            content += f"Voice positions considered: {voice_positions}."
        
        return content
    
    def capture_outcome_memory(self,
                              original_decision_id: str,
                              actual_outcome: str,
                              satisfaction: float,
                              lessons_learned: List[str] = None,
                              feedback: str = None) -> bool:
        """
        Capture the outcome of a previous decision.
        
        This is crucial for learning - connecting decisions to their results.
        
        Args:
            original_decision_id: ID of the original episodic decision memory
            actual_outcome: What actually happened
            satisfaction: How satisfied with the outcome (0-1)
            lessons_learned: List of insights gained
            feedback: Additional feedback text
            
        Returns:
            Success status
        """
        
        # Update episodic memory with outcome
        success = self.episodic_memory.add_outcome_to_decision(
            decision_memory_id=original_decision_id,
            outcome=actual_outcome,
            satisfaction=satisfaction,
            lessons_learned=lessons_learned
        )
        
        if not success:
            self.logger.warning(f"Could not find decision memory {original_decision_id}")
            return False
        
        # Create new semantic memory about what works/doesn't work
        outcome_content = self._create_outcome_semantic_content(
            original_decision_id, actual_outcome, satisfaction, lessons_learned, feedback
        )
        
        if outcome_content:
            self.vector_memory.add_memory(
                content=outcome_content,
                memory_type=VectorMemoryType.INSIGHT,
                metadata={
                    "original_decision_id": original_decision_id,
                    "satisfaction": satisfaction,
                    "outcome_type": "positive" if satisfaction >= 0.7 else "negative"
                },
                tags=["outcome", "learning"],
                decision_outcome=satisfaction
            )
        
        self.logger.info(f"Captured outcome memory: satisfaction={satisfaction:.2f}")
        return True
    
    def _create_outcome_semantic_content(self,
                                       decision_id: str,
                                       outcome: str,
                                       satisfaction: float,
                                       lessons: List[str] = None,
                                       feedback: str = None) -> str:
        """Create semantic content about decision outcomes"""
        
        # Get original decision details
        original_memory = self.episodic_memory.memories.get(decision_id)
        if not original_memory:
            return None
        
        satisfaction_desc = "successful" if satisfaction >= 0.7 else "unsatisfactory" if satisfaction <= 0.4 else "mixed"
        
        content = f"Outcome learning: The decision '{original_memory.decision_made}' resulted in {satisfaction_desc} outcomes. "
        content += f"Actual result: {outcome}. "
        
        if satisfaction >= 0.7:
            content += f"This approach worked well and should be repeated in similar situations. "
        elif satisfaction <= 0.4:
            content += f"This approach did not work well and should be reconsidered. "
        
        if lessons:
            content += f"Key insights: {'; '.join(lessons)}. "
        
        if feedback:
            content += f"Additional feedback: {feedback}"
        
        return content
    
    def capture_conversation_memory(self,
                                   person: str,
                                   topic: str,
                                   key_points: List[str],
                                   outcome: str = None,
                                   context: Dict[str, Any] = None) -> str:
        """Capture a conversation as memory"""
        
        # Store episodic conversation
        conv_memory = self.episodic_memory.store_conversation_memory(
            person=person,
            topic=topic,
            key_points=key_points,
            outcome=outcome,
            context=context
        )
        
        # Store semantic relationship pattern
        relationship_content = f"Communication pattern with {person}: "
        relationship_content += f"Discussed {topic}. Key outcomes: {'; '.join(key_points)}. "
        
        if outcome:
            relationship_content += f"Result: {outcome}."
        
        semantic_id = self.vector_memory.add_memory(
            content=relationship_content,
            memory_type=VectorMemoryType.RELATIONSHIP,
            metadata={
                "person": person,
                "topic": topic,
                "conversation_outcome": outcome
            },
            tags=[person, topic, "conversation"]
        )
        
        return conv_memory.id
    
    def capture_pattern_memory(self,
                              pattern_description: str,
                              examples: List[str],
                              confidence: float = 0.8,
                              context: Dict[str, Any] = None) -> str:
        """
        Capture a behavioral pattern that's been observed.
        
        Args:
            pattern_description: Description of the pattern
            examples: Specific examples of this pattern
            confidence: How confident we are about this pattern
            context: Additional context
            
        Returns:
            Memory ID
        """
        
        content = f"Behavioral pattern: {pattern_description} "
        content += f"Examples: {'; '.join(examples)}. "
        
        if confidence >= 0.8:
            content += "This is a consistent pattern with high confidence."
        elif confidence >= 0.6:
            content += "This pattern appears reliable but needs more observation."
        else:
            content += "This is a tentative pattern that may not be reliable."
        
        return self.vector_memory.add_memory(
            content=content,
            memory_type=VectorMemoryType.PATTERN,
            metadata={
                "pattern_confidence": confidence,
                "example_count": len(examples),
                **(context or {})
            },
            tags=["pattern", "behavior"]
        )
    
    def update_memory_relevance(self,
                               memory_id: str,
                               memory_type: str,  # "episodic" or "semantic"
                               relevance_change: float,
                               reason: str = None):
        """
        Update the relevance of a memory based on new information.
        
        Args:
            memory_id: ID of the memory to update
            memory_type: Whether it's episodic or semantic memory
            relevance_change: How much to change relevance (-1.0 to 1.0)
            reason: Why the relevance is being updated
        """
        
        if memory_type == "semantic":
            if memory_id in self.vector_memory.memory_cache:
                memory = self.vector_memory.memory_cache[memory_id]
                old_relevance = memory.relevance_score
                memory.relevance_score = max(0.1, min(1.0, memory.relevance_score + relevance_change))
                
                if reason:
                    self.logger.info(f"Updated semantic memory relevance: {old_relevance:.2f} -> {memory.relevance_score:.2f} ({reason})")
                
                self.vector_memory._save_memory_metadata()
        
        elif memory_type == "episodic":
            if memory_id in self.episodic_memory.memories:
                memory = self.episodic_memory.memories[memory_id]
                # Episodic memories don't have relevance scores, but we can adjust confidence
                old_confidence = memory.confidence
                memory.confidence = max(0.1, min(1.0, memory.confidence + relevance_change))
                
                if reason:
                    self.logger.info(f"Updated episodic memory confidence: {old_confidence:.2f} -> {memory.confidence:.2f} ({reason})")
                
                self.episodic_memory._save_memories()
    
    def extract_insights_from_patterns(self, 
                                     days: int = 30,
                                     min_pattern_count: int = 3) -> List[str]:
        """
        Analyze recent decisions to extract behavioral insights.
        
        This looks for patterns in decision-making and automatically
        creates insight memories.
        
        Args:
            days: How many days back to analyze
            min_pattern_count: Minimum occurrences to consider a pattern
            
        Returns:
            List of insight memory IDs created
        """
        
        # Get recent decision outcomes
        recent_outcomes = self.episodic_memory.get_decision_outcomes(days=days)
        
        if len(recent_outcomes) < min_pattern_count:
            return []
        
        insights_created = []
        
        # Analyze patterns by category
        category_outcomes = {}
        for outcome in recent_outcomes:
            category = outcome['context'].get('category', 'unknown')
            if category not in category_outcomes:
                category_outcomes[category] = []
            category_outcomes[category].append(outcome)
        
        # Look for patterns in each category
        for category, outcomes in category_outcomes.items():
            if len(outcomes) >= min_pattern_count:
                insight = self._analyze_category_patterns(category, outcomes)
                if insight:
                    insight_id = self.vector_memory.add_memory(
                        content=insight,
                        memory_type=VectorMemoryType.INSIGHT,
                        metadata={
                            "category": category,
                            "pattern_source": "automatic_analysis",
                            "outcome_count": len(outcomes)
                        },
                        tags=["insight", "pattern", category]
                    )
                    insights_created.append(insight_id)
        
        # Analyze reasoning mode effectiveness
        mode_effectiveness = self._analyze_reasoning_mode_effectiveness(recent_outcomes)
        if mode_effectiveness:
            insight_id = self.vector_memory.add_memory(
                content=mode_effectiveness,
                memory_type=VectorMemoryType.INSIGHT,
                metadata={
                    "pattern_source": "reasoning_analysis",
                    "outcome_count": len(recent_outcomes)
                },
                tags=["insight", "reasoning_modes"]
            )
            insights_created.append(insight_id)
        
        if insights_created:
            self.logger.info(f"Extracted {len(insights_created)} behavioral insights")
        
        return insights_created
    
    def _analyze_category_patterns(self, category: str, outcomes: List[Dict[str, Any]]) -> Optional[str]:
        """Analyze patterns within a specific category"""
        
        if len(outcomes) < 3:
            return None
        
        # Calculate average satisfaction
        avg_satisfaction = sum(o['satisfaction'] for o in outcomes) / len(outcomes)
        
        # Find most common decision patterns
        decision_types = {}
        for outcome in outcomes:
            decision = outcome['decision'][:50]  # First 50 chars for grouping
            if decision not in decision_types:
                decision_types[decision] = {'count': 0, 'satisfaction': []}
            decision_types[decision]['count'] += 1
            decision_types[decision]['satisfaction'].append(outcome['satisfaction'])
        
        # Find best performing approach
        best_approach = None
        best_satisfaction = 0
        
        for decision, data in decision_types.items():
            if data['count'] >= 2:  # At least 2 examples
                avg_sat = sum(data['satisfaction']) / len(data['satisfaction'])
                if avg_sat > best_satisfaction:
                    best_satisfaction = avg_sat
                    best_approach = decision
        
        if best_approach and best_satisfaction > 0.7:
            insight = f"Pattern insight for {category}: The approach '{best_approach}' "
            insight += f"consistently performs well (satisfaction: {best_satisfaction:.2f}). "
            insight += f"This pattern appeared {decision_types[best_approach]['count']} times "
            insight += f"out of {len(outcomes)} recent decisions in this category."
            return insight
        
        return None
    
    def _analyze_reasoning_mode_effectiveness(self, outcomes: List[Dict[str, Any]]) -> Optional[str]:
        """Analyze which reasoning modes work best"""
        
        mode_performance = {}
        
        for outcome in outcomes:
            mode = outcome['context'].get('reasoning_mode', 'unknown')
            if mode not in mode_performance:
                mode_performance[mode] = {'count': 0, 'satisfaction': []}
            mode_performance[mode]['count'] += 1
            mode_performance[mode]['satisfaction'].append(outcome['satisfaction'])
        
        # Calculate average satisfaction per mode
        mode_averages = {}
        for mode, data in mode_performance.items():
            if data['count'] >= 2:
                mode_averages[mode] = sum(data['satisfaction']) / len(data['satisfaction'])
        
        if not mode_averages:
            return None
        
        # Find best and worst performing modes
        best_mode = max(mode_averages.items(), key=lambda x: x[1])
        worst_mode = min(mode_averages.items(), key=lambda x: x[1])
        
        if best_mode[1] - worst_mode[1] > 0.2:  # Significant difference
            insight = f"Reasoning mode effectiveness: {best_mode[0]} reasoning performs best "
            insight += f"(satisfaction: {best_mode[1]:.2f}) while {worst_mode[0]} performs worst "
            insight += f"(satisfaction: {worst_mode[1]:.2f}). "
            insight += f"Consider using {best_mode[0]} more frequently for similar situations."
            return insight
        
        return None
    
    def capture_goal_memory(self, 
                           goal: 'Goal',
                           action_type: str,  # created, updated, completed, milestone_achieved
                           details: Dict[str, Any] = None) -> Optional[str]:
        """Capture goal-related events as memory"""
        
        if not GOAL_SYSTEM_AVAILABLE or not goal:
            return None
        
        try:
            # Store episodic memory for goal event
            memory_id = self.episodic_memory.store_decision_memory(
                decision=f"Goal {action_type}: {goal.title}",
                situation=f"Working on {goal.goal_type.value} goal",
                reasoning=f"Goal {action_type} - {goal.description}",
                metadata={
                    'source': 'goal_system',
                    'goal_id': goal.id,
                    'goal_type': goal.goal_type.value,
                    'action_type': action_type,
                    'goal_priority': goal.priority,
                    'progress_percentage': goal.progress_percentage,
                    'target_date': goal.target_date.isoformat(),
                    'related_apps': goal.related_apps,
                    'impact_areas': goal.impact_areas,
                    'timestamp': datetime.now().isoformat(),
                    **(details or {})
                }
            )
            
            # Store semantic memory for goal patterns
            if action_type in ['created', 'completed']:
                pattern_content = self._create_goal_pattern_content(goal, action_type, details)
                
                self.vector_memory.add_memory(
                    content=pattern_content,
                    memory_type=VectorMemoryType.PATTERN,
                    metadata={
                        'goal_id': goal.id,
                        'goal_type': goal.goal_type.value,
                        'action_type': action_type,
                        'priority': goal.priority,
                        'source': 'goal_system'
                    },
                    tags=['goal', goal.goal_type.value, action_type, f'priority_{goal.priority}']
                )
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error capturing goal memory: {e}")
            return None
    
    def capture_milestone_memory(self,
                                milestone: 'Milestone',
                                action_type: str,  # created, started, progress_updated, completed
                                progress_details: Dict[str, Any] = None) -> Optional[str]:
        """Capture milestone-related events as memory"""
        
        if not GOAL_SYSTEM_AVAILABLE or not milestone:
            return None
        
        try:
            # Store episodic memory for milestone event
            memory_id = self.episodic_memory.store_decision_memory(
                decision=f"Milestone {action_type}: {milestone.title}",
                situation=f"Working on milestone for goal {milestone.goal_id}",
                reasoning=f"Milestone {action_type} - {milestone.description}",
                metadata={
                    'source': 'goal_system',
                    'milestone_id': milestone.id,
                    'goal_id': milestone.goal_id,
                    'action_type': action_type,
                    'milestone_priority': milestone.priority,
                    'progress_percentage': milestone.progress_percentage,
                    'target_date': milestone.target_date.isoformat(),
                    'estimated_effort_hours': milestone.estimated_effort_hours,
                    'actual_effort_hours': milestone.actual_effort_hours,
                    'success_criteria': milestone.success_criteria,
                    'timestamp': datetime.now().isoformat(),
                    **(progress_details or {})
                }
            )
            
            # Store progress patterns for milestones
            if action_type == 'progress_updated' and progress_details:
                pattern_content = self._create_milestone_progress_pattern_content(milestone, progress_details)
                
                self.vector_memory.add_memory(
                    content=pattern_content,
                    memory_type=VectorMemoryType.PATTERN,
                    metadata={
                        'milestone_id': milestone.id,
                        'goal_id': milestone.goal_id,
                        'action_type': action_type,
                        'progress_amount': progress_details.get('progress_increase', 0),
                        'source': 'goal_system'
                    },
                    tags=['milestone', 'progress', 'goal_work']
                )
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error capturing milestone memory: {e}")
            return None
    
    def capture_goal_context_memory(self,
                                   goal_context: 'GoalContext',
                                   decision_context: str,
                                   relevance: 'GoalRelevance') -> Optional[str]:
        """Capture how goals influenced a decision"""
        
        if not GOAL_SYSTEM_AVAILABLE or not goal_context:
            return None
        
        try:
            # Create semantic memory about goal-informed decision making
            content = f"Goal-informed decision: {decision_context}. "
            
            if goal_context.active_goals:
                active_goal_titles = [g.title for g in goal_context.active_goals[:3]]
                content += f"Active goals considered: {', '.join(active_goal_titles)}. "
            
            if goal_context.urgent_milestones:
                urgent_titles = [m.title for m in goal_context.urgent_milestones[:2]]
                content += f"Urgent milestones: {', '.join(urgent_titles)}. "
            
            if goal_context.current_priorities:
                content += f"Current priorities: {', '.join(goal_context.current_priorities[:3])}. "
            
            content += f"Goal relevance level: {relevance.value}."
            
            if goal_context.strategic_recommendations:
                content += f" Strategic guidance: {goal_context.strategic_recommendations[0]}"
            
            semantic_id = self.vector_memory.add_memory(
                content=content,
                memory_type=VectorMemoryType.STRATEGY,
                metadata={
                    'source': 'goal_system',
                    'decision_context': decision_context,
                    'goal_relevance': relevance.value,
                    'active_goal_count': len(goal_context.active_goals),
                    'urgent_milestone_count': len(goal_context.urgent_milestones),
                    'relevant_goal_ids': goal_context.relevant_goal_ids,
                    'timestamp': datetime.now().isoformat()
                },
                tags=['goal_context', 'strategic_decision', relevance.value]
            )
            
            return semantic_id
            
        except Exception as e:
            self.logger.error(f"Error capturing goal context memory: {e}")
            return None
    
    def _create_goal_pattern_content(self, goal: 'Goal', action_type: str, details: Dict[str, Any] = None) -> str:
        """Create semantic content for goal patterns"""
        
        if action_type == 'created':
            content = f"Goal creation pattern: User creates {goal.goal_type.value} goals "
            content += f"with {goal.estimated_duration_weeks} week timelines "
            content += f"and priority level {goal.priority}. "
            
            if goal.impact_areas:
                content += f"Focuses on {', '.join(goal.impact_areas)} impact areas. "
            
            if goal.related_apps:
                content += f"Typically uses {', '.join(goal.related_apps[:3])} apps for this type of work."
        
        elif action_type == 'completed':
            completion_time = details.get('actual_duration_weeks', goal.estimated_duration_weeks)
            content = f"Goal completion pattern: {goal.goal_type.value} goals "
            content += f"like '{goal.title}' typically take {completion_time:.1f} weeks to complete. "
            
            if details and details.get('success_factors'):
                content += f"Success factors: {', '.join(details['success_factors'])}. "
            
            final_progress = goal.progress_percentage
            content += f"Final progress achieved: {final_progress:.1f}%."
        
        else:
            content = f"Goal {action_type} pattern for {goal.goal_type.value} goals"
        
        return content
    
    def _create_milestone_progress_pattern_content(self, milestone: 'Milestone', progress_details: Dict[str, Any]) -> str:
        """Create semantic content for milestone progress patterns"""
        
        progress_increase = progress_details.get('progress_increase', 0)
        time_spent = progress_details.get('time_spent_hours', 0)
        work_context = progress_details.get('work_context', 'general work')
        
        content = f"Milestone progress pattern: Working on '{milestone.title}' "
        content += f"in {work_context} context results in {progress_increase:.1f}% progress "
        
        if time_spent > 0:
            efficiency = progress_increase / time_spent if time_spent > 0 else 0
            content += f"with {time_spent:.1f} hours invested (efficiency: {efficiency:.1f}% per hour). "
        
        if milestone.obstacles_encountered:
            recent_obstacles = milestone.obstacles_encountered[-2:]  # Last 2 obstacles
            content += f"Recent challenges: {'; '.join(recent_obstacles)}. "
        
        content += f"Current progress: {milestone.progress_percentage:.1f}% complete."
        
        return content
    
    def link_observation_to_goals(self,
                                 observation: 'ObservationEvent',
                                 goal_ids: List[str],
                                 relevance_scores: List[float]) -> bool:
        """Link observed activities to relevant goals"""
        
        if not OBSERVER_AVAILABLE or not GOAL_SYSTEM_AVAILABLE:
            return False
        
        try:
            for goal_id, relevance in zip(goal_ids, relevance_scores):
                if relevance > 0.5:  # Only link if reasonably relevant
                    # Create semantic memory linking observation to goal
                    content = f"Activity-goal connection: Using {observation.app_name} "
                    content += f"for {observation.category.value} activities "
                    content += f"contributes to goal {goal_id} "
                    content += f"(relevance: {relevance:.2f}). "
                    
                    duration_minutes = observation.duration_seconds // 60
                    content += f"Session duration: {duration_minutes} minutes."
                    
                    self.vector_memory.add_memory(
                        content=content,
                        memory_type=VectorMemoryType.BEHAVIORAL_PATTERN,
                        metadata={
                            'source': 'goal_observer_link',
                            'goal_id': goal_id,
                            'app_name': observation.app_name,
                            'activity_category': observation.category.value,
                            'relevance_score': relevance,
                            'duration_minutes': duration_minutes,
                            'timestamp': observation.timestamp.isoformat()
                        },
                        tags=['goal_activity', 'observed_behavior', observation.category.value]
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking observation to goals: {e}")
            return False
    
    def capture_strategic_insight_memory(self,
                                       insight: str,
                                       goal_ids: List[str],
                                       insight_type: str,  # timeline, capacity, risk, opportunity
                                       confidence: float = 0.8,
                                       supporting_data: Dict[str, Any] = None) -> Optional[str]:
        """Capture strategic insights about goals and planning"""
        
        if not GOAL_SYSTEM_AVAILABLE:
            return None
        
        try:
            content = f"Strategic insight ({insight_type}): {insight}. "
            
            if goal_ids:
                content += f"Applies to goals: {', '.join(goal_ids[:3])}. "
            
            if supporting_data:
                if 'timeline_impact' in supporting_data:
                    content += f"Timeline impact: {supporting_data['timeline_impact']}. "
                if 'risk_level' in supporting_data:
                    content += f"Risk level: {supporting_data['risk_level']}. "
            
            content += f"Confidence: {confidence:.2f}."
            
            semantic_id = self.vector_memory.add_memory(
                content=content,
                memory_type=VectorMemoryType.INSIGHT,
                metadata={
                    'source': 'strategic_planning',
                    'insight_type': insight_type,
                    'goal_ids': goal_ids,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat(),
                    **(supporting_data or {})
                },
                tags=['strategic_insight', insight_type, 'planning']
            )
            
            return semantic_id
            
        except Exception as e:
            self.logger.error(f"Error capturing strategic insight memory: {e}")
            return None
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory updates"""
        
        stats = {
            "decisions_captured": len(self.stored_decisions),
            "episodic_memories": len(self.episodic_memory.memories),
            "semantic_memories": len(self.vector_memory.memory_cache),
            "pattern_cache_size": len(self.pattern_extraction_cache)
        }
        
        # Add goal-specific statistics if available
        if GOAL_SYSTEM_AVAILABLE:
            goal_memories = [m for m in self.episodic_memory.memories.values() 
                           if m.metadata.get('source') == 'goal_system']
            stats['goal_memories'] = len(goal_memories)
            
            strategic_memories = [m for m_id, m in self.vector_memory.memory_cache.items()
                                if 'strategic' in m.tags or 'goal' in m.tags]
            stats['strategic_memories'] = len(strategic_memories)
        
        return stats