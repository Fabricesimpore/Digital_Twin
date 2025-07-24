"""
Intelligent Memory Retrieval for Digital Twin

This module provides context-aware memory retrieval that adapts to:
- Current reasoning mode (heuristic, deliberation, arbitration)
- Current state (energy, stress, mood)
- Situational context (category, people, urgency)
- Recent outcomes and learning

It intelligently combines episodic and semantic memories to provide
the most relevant context for decision-making.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .episodic_memory import EpisodicMemorySystem, MemoryType, MemoryImportance
from .vector_memory import EnhancedVectorMemory, VectorMemoryType


@dataclass
class RetrievalContext:
    """Context for memory retrieval"""
    query: str                                  # What we're looking for
    reasoning_mode: str = "arbitration"         # Current reasoning mode
    current_state: Dict[str, Any] = None        # Energy, stress, mood, etc.
    situation_category: str = None              # email, meeting, task, etc.
    people_involved: List[str] = None           # People in the situation
    urgency: str = "medium"                     # low, medium, high
    time_available: int = None                  # Minutes available
    similar_situations: List[str] = None        # Previous similar contexts
    
    def __post_init__(self):
        if self.current_state is None:
            self.current_state = {}
        if self.people_involved is None:
            self.people_involved = []
        if self.similar_situations is None:
            self.similar_situations = []


@dataclass
class MemoryContext:
    """A memory with context and relevance scores"""
    memory_id: str
    content: str
    memory_type: str  # "episodic" or "semantic"
    relevance_score: float
    recency_boost: float
    success_boost: float
    context_match: float
    final_score: float
    
    # Additional metadata
    source: str = None  # Which system provided this memory
    reasoning_influence: str = None  # How this memory should influence reasoning
    confidence: float = 0.8


class IntelligentMemoryRetrieval:
    """
    Context-aware memory retrieval system that provides the most relevant
    memories for current decision-making needs.
    
    Features:
    - Adapts to reasoning mode (heuristics vs deep thinking)
    - Considers current state (tired → simpler memories)
    - Prioritizes successful past decisions
    - Balances recency with relevance
    - Combines episodic and semantic memories intelligently
    """
    
    def __init__(self, 
                 episodic_memory: EpisodicMemorySystem,
                 vector_memory: EnhancedVectorMemory):
        
        self.episodic_memory = episodic_memory
        self.vector_memory = vector_memory
        self.logger = logging.getLogger(__name__)
        
        # Cache for performance
        self.retrieval_cache = {}
        self.cache_expiry = {}
    
    def retrieve_contextual_memories(self, 
                                   context: RetrievalContext,
                                   max_memories: int = 8) -> List[MemoryContext]:
        """
        Main retrieval function that provides the most relevant memories
        for the current context and reasoning mode.
        
        Args:
            context: Retrieval context with query and situation details
            max_memories: Maximum number of memories to return
            
        Returns:
            List of most relevant memories with scores
        """
        
        # Check cache first
        cache_key = self._generate_cache_key(context)
        if self._is_cache_valid(cache_key):
            return self.retrieval_cache[cache_key]
        
        # Get memories from both systems
        episodic_memories = self._retrieve_episodic_memories(context)
        semantic_memories = self._retrieve_semantic_memories(context)
        
        # Score and rank all memories
        all_memories = self._score_memories(
            episodic_memories, semantic_memories, context
        )
        
        # Filter and balance memory types
        final_memories = self._balance_memory_selection(all_memories, context, max_memories)
        
        # Cache the results
        self.retrieval_cache[cache_key] = final_memories
        self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)
        
        self.logger.info(f"Retrieved {len(final_memories)} contextual memories for: {context.query[:50]}...")
        
        return final_memories
    
    def _retrieve_episodic_memories(self, context: RetrievalContext) -> List[Dict[str, Any]]:
        """Retrieve relevant episodic memories"""
        
        # Search parameters based on context
        time_range = None
        if context.urgency == "high":
            # For urgent situations, focus on recent experiences
            time_range = (datetime.now() - timedelta(days=7), datetime.now())
        elif context.reasoning_mode == "heuristic":
            # For heuristic mode, get recent similar patterns
            time_range = (datetime.now() - timedelta(days=30), datetime.now())
        
        # Search episodic memories
        memories = self.episodic_memory.search_memories(
            query=context.query,
            memory_type=MemoryType.DECISION if "decision" in context.query.lower() else None,
            person=context.people_involved[0] if context.people_involved else None,
            time_range=time_range,
            tags=[context.situation_category] if context.situation_category else None,
            limit=15
        )
        
        # Convert to standard format
        episodic_results = []
        for memory in memories:
            episodic_results.append({
                'id': memory.id,
                'content': f"{memory.title}: {memory.description}",
                'type': 'episodic',
                'memory_obj': memory,
                'created_at': memory.timestamp,
                'confidence': memory.confidence,
                'satisfaction': memory.satisfaction if hasattr(memory, 'satisfaction') else None,
                'importance': memory.importance.value,
                'access_count': memory.access_count
            })
        
        return episodic_results
    
    def _retrieve_semantic_memories(self, context: RetrievalContext) -> List[Dict[str, Any]]:
        """Retrieve relevant semantic memories"""
        
        # Determine which types of semantic memories to prioritize
        preferred_types = self._get_preferred_semantic_types(context.reasoning_mode)
        
        # Get contextual memories (this handles reasoning mode preferences)
        memories = self.vector_memory.get_contextual_memories(
            query=context.query,
            reasoning_mode=context.reasoning_mode,
            current_state=context.current_state,
            limit=15
        )
        
        # Convert to standard format
        semantic_results = []
        for memory in memories:
            semantic_results.append({
                'id': memory['id'],
                'content': memory['content'],
                'type': 'semantic',
                'memory_obj': memory,
                'score': memory.get('contextual_score', memory.get('score', 0)),
                'memory_type': memory.get('memory_type'),
                'access_count': memory.get('access_count', 0),
                'tags': memory.get('tags', [])
            })
        
        return semantic_results
    
    def _get_preferred_semantic_types(self, reasoning_mode: str) -> List[VectorMemoryType]:
        """Get preferred semantic memory types for reasoning mode"""
        
        preferences = {
            "heuristic": [VectorMemoryType.PATTERN, VectorMemoryType.STRATEGY],
            "deliberation": [VectorMemoryType.KNOWLEDGE, VectorMemoryType.INSIGHT, VectorMemoryType.STRATEGY],
            "arbitration": [VectorMemoryType.PREFERENCE, VectorMemoryType.RELATIONSHIP, VectorMemoryType.INSIGHT]
        }
        
        return preferences.get(reasoning_mode, [VectorMemoryType.PATTERN, VectorMemoryType.KNOWLEDGE])
    
    def _score_memories(self,
                       episodic_memories: List[Dict[str, Any]],
                       semantic_memories: List[Dict[str, Any]],
                       context: RetrievalContext) -> List[MemoryContext]:
        """Score and rank all memories based on relevance to context"""
        
        scored_memories = []
        
        # Score episodic memories
        for memory in episodic_memories:
            scores = self._calculate_episodic_scores(memory, context)
            
            memory_context = MemoryContext(
                memory_id=memory['id'],
                content=memory['content'],
                memory_type='episodic',
                relevance_score=scores['relevance'],
                recency_boost=scores['recency'],
                success_boost=scores['success'],
                context_match=scores['context'],
                final_score=scores['final'],
                source='episodic_memory',
                confidence=memory['confidence']
            )
            
            scored_memories.append(memory_context)
        
        # Score semantic memories
        for memory in semantic_memories:
            scores = self._calculate_semantic_scores(memory, context)
            
            memory_context = MemoryContext(
                memory_id=memory['id'],
                content=memory['content'],
                memory_type='semantic',
                relevance_score=scores['relevance'],
                recency_boost=scores['recency'],
                success_boost=scores['success'],
                context_match=scores['context'],
                final_score=scores['final'],
                source='vector_memory',
                confidence=memory.get('confidence', 0.8)
            )
            
            scored_memories.append(memory_context)
        
        # Sort by final score
        scored_memories.sort(key=lambda x: x.final_score, reverse=True)
        
        return scored_memories
    
    def _calculate_episodic_scores(self, memory: Dict[str, Any], context: RetrievalContext) -> Dict[str, float]:
        """Calculate relevance scores for episodic memory"""
        
        # Base relevance from search
        relevance_score = 0.8  # Base score for episodic memories
        
        # Recency boost
        if 'created_at' in memory:
            days_old = (datetime.now() - memory['created_at']).days
            recency_boost = max(0, (30 - days_old) / 30 * 0.3)  # 0-0.3 boost
        else:
            recency_boost = 0
        
        # Success boost based on satisfaction
        success_boost = 0
        if memory.get('satisfaction') is not None:
            if memory['satisfaction'] >= 0.8:
                success_boost = 0.2  # High success
            elif memory['satisfaction'] <= 0.4:
                success_boost = -0.1  # Learn from failures too, but lower priority
        
        # Context match boost
        context_match = 0
        memory_obj = memory.get('memory_obj')
        if memory_obj:
            # Category match
            if (hasattr(memory_obj, 'context') and 
                context.situation_category and
                context.situation_category in str(memory_obj.context)):
                context_match += 0.1
            
            # People match
            if (hasattr(memory_obj, 'people_involved') and
                context.people_involved and
                any(person in memory_obj.people_involved for person in context.people_involved)):
                context_match += 0.1
            
            # Importance boost
            if hasattr(memory_obj, 'importance'):
                if memory_obj.importance.value == 'high':
                    context_match += 0.1
                elif memory_obj.importance.value == 'critical':
                    context_match += 0.2
        
        # Access count boost (frequently referenced memories are valuable)
        access_boost = min(0.1, memory.get('access_count', 0) * 0.02)
        
        final_score = relevance_score + recency_boost + success_boost + context_match + access_boost
        
        return {
            'relevance': relevance_score,
            'recency': recency_boost,
            'success': success_boost,
            'context': context_match,
            'final': final_score
        }
    
    def _calculate_semantic_scores(self, memory: Dict[str, Any], context: RetrievalContext) -> Dict[str, float]:
        """Calculate relevance scores for semantic memory"""
        
        # Base relevance from vector search
        relevance_score = memory.get('score', 0.5)
        
        # Recency boost (less important for semantic memories)
        recency_boost = 0  # Semantic memories are timeless
        
        # Success boost based on decision outcomes
        success_boost = 0
        memory_obj = memory.get('memory_obj')
        if isinstance(memory_obj, dict):
            # Look for decision outcome info
            decision_outcome = memory_obj.get('decision_outcome')
            if decision_outcome is not None:
                if decision_outcome >= 0.8:
                    success_boost = 0.15
                elif decision_outcome <= 0.4:
                    success_boost = -0.05
        
        # Context match based on tags and memory type
        context_match = 0
        
        # Reasoning mode alignment
        memory_type = memory.get('memory_type', '')
        preferred_types = [t.value for t in self._get_preferred_semantic_types(context.reasoning_mode)]
        if memory_type in preferred_types:
            context_match += 0.15
        
        # Tag matching
        memory_tags = memory.get('tags', [])
        if context.situation_category and context.situation_category in memory_tags:
            context_match += 0.1
        
        # People matching (for relationship memories)
        if (context.people_involved and 
            any(person in memory_tags for person in context.people_involved)):
            context_match += 0.1
        
        # State-based relevance
        state_boost = self._calculate_state_relevance(memory, context.current_state)
        
        final_score = relevance_score + recency_boost + success_boost + context_match + state_boost
        
        return {
            'relevance': relevance_score,
            'recency': recency_boost,
            'success': success_boost,
            'context': context_match,
            'final': final_score
        }
    
    def _calculate_state_relevance(self, memory: Dict[str, Any], current_state: Dict[str, Any]) -> float:
        """Calculate how relevant a memory is to current state"""
        
        if not current_state:
            return 0
        
        boost = 0
        content = memory.get('content', '').lower()
        
        # Energy-based relevance
        energy_level = current_state.get('current_energy', 'medium')
        if energy_level == 'low':
            if any(word in content for word in ['simple', 'quick', 'easy', 'routine']):
                boost += 0.1
            elif any(word in content for word in ['complex', 'difficult', 'challenging']):
                boost -= 0.05
        elif energy_level == 'high':
            if any(word in content for word in ['complex', 'challenging', 'creative']):
                boost += 0.1
        
        # Stress-based relevance
        stress_level = current_state.get('current_stress', 'medium')
        if stress_level == 'high':
            if any(word in content for word in ['priority', 'urgent', 'essential', 'simple']):
                boost += 0.1
            elif any(word in content for word in ['optional', 'nice-to-have']):
                boost -= 0.05
        
        # Mood-based relevance
        mood = current_state.get('current_mood', 'neutral')
        if mood == 'positive':
            if any(word in content for word in ['creative', 'innovative', 'explore']):
                boost += 0.05
        elif mood == 'negative':
            if any(word in content for word in ['supportive', 'gentle', 'careful']):
                boost += 0.05
        
        return boost
    
    def _balance_memory_selection(self,
                                 scored_memories: List[MemoryContext],
                                 context: RetrievalContext,
                                 max_memories: int) -> List[MemoryContext]:
        """Balance selection between episodic and semantic memories"""
        
        if len(scored_memories) <= max_memories:
            return scored_memories
        
        # Separate by type
        episodic = [m for m in scored_memories if m.memory_type == 'episodic']
        semantic = [m for m in scored_memories if m.memory_type == 'semantic']
        
        # Determine optimal balance based on reasoning mode
        if context.reasoning_mode == "heuristic":
            # Prefer patterns and specific examples
            episodic_ratio = 0.6
        elif context.reasoning_mode == "deliberation":
            # Prefer knowledge and insights
            episodic_ratio = 0.3
        else:  # arbitration
            # Balanced approach
            episodic_ratio = 0.5
        
        # Calculate counts
        episodic_count = int(max_memories * episodic_ratio)
        semantic_count = max_memories - episodic_count
        
        # Select top memories of each type
        selected_episodic = episodic[:episodic_count]
        selected_semantic = semantic[:semantic_count]
        
        # If one type doesn't have enough, use the other
        if len(selected_episodic) < episodic_count:
            additional_semantic = semantic_count + (episodic_count - len(selected_episodic))
            selected_semantic = semantic[:additional_semantic]
        elif len(selected_semantic) < semantic_count:
            additional_episodic = episodic_count + (semantic_count - len(selected_semantic))
            selected_episodic = episodic[:additional_episodic]
        
        # Combine and sort by score
        final_selection = selected_episodic + selected_semantic
        final_selection.sort(key=lambda x: x.final_score, reverse=True)
        
        return final_selection[:max_memories]
    
    def _generate_cache_key(self, context: RetrievalContext) -> str:
        """Generate cache key for retrieval context"""
        
        key_parts = [
            context.query[:50],
            context.reasoning_mode,
            context.situation_category or '',
            '|'.join(context.people_involved),
            context.urgency
        ]
        
        return '|'.join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        
        if cache_key not in self.retrieval_cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def get_similar_situations(self,
                             current_situation: str,
                             context: Dict[str, Any] = None,
                             limit: int = 5) -> List[MemoryContext]:
        """
        Find memories of similar situations for pattern matching.
        
        This is specifically for the "What did I do last time?" use case.
        """
        
        # Use episodic memory's similarity search
        similar_episodic = self.episodic_memory.find_similar_situations(
            current_situation, context, limit
        )
        
        # Convert to MemoryContext format
        similar_memories = []
        for memory in similar_episodic:
            similarity_score = 0.8  # Base score for similar situations
            
            memory_context = MemoryContext(
                memory_id=memory.id,
                content=f"{memory.title}: {memory.description}",
                memory_type='episodic',
                relevance_score=similarity_score,
                recency_boost=0.1 if memory.last_accessed else 0,
                success_boost=0.2 if memory.satisfaction and memory.satisfaction >= 0.7 else 0,
                context_match=0.1,
                final_score=similarity_score + 0.1 + (0.2 if memory.satisfaction and memory.satisfaction >= 0.7 else 0),
                source='episodic_similarity',
                reasoning_influence='similar_situation_pattern'
            )
            
            similar_memories.append(memory_context)
        
        return similar_memories
    
    def clear_cache(self):
        """Clear the retrieval cache"""
        self.retrieval_cache.clear()
        self.cache_expiry.clear()
        self.logger.info("Memory retrieval cache cleared")
    
    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory retrieval"""
        
        return {
            "cache_entries": len(self.retrieval_cache),
            "episodic_memory_count": len(self.episodic_memory.memories),
            "semantic_memory_count": len(self.vector_memory.memory_cache),
            "cache_hit_ratio": 0  # Would need to track hits/misses to calculate
        }