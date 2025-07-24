"""
Episodic Memory System for Digital Twin

This module handles specific event memories - the "what happened when" of your life.
Unlike semantic memory (facts/patterns), episodic memory stores concrete experiences:

- Specific conversations and their outcomes
- Decisions made and their results  
- Events that happened at specific times
- Emotional states during important moments
- Patterns of what worked vs what didn't

This creates a timeline of your digital twin's experiences for learning and reflection.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import logging
from pathlib import Path


class MemoryType(Enum):
    """Types of episodic memories"""
    DECISION = "decision"           # A choice you made
    CONVERSATION = "conversation"   # Interaction with someone
    EVENT = "event"                # Something that happened
    OUTCOME = "outcome"             # Result of an action
    REFLECTION = "reflection"       # Thought or insight
    FEEDBACK = "feedback"           # Learning from results
    STATE_CHANGE = "state_change"   # Mood/energy shifts
    PATTERN = "pattern"             # Noticed behavioral pattern


class MemoryImportance(Enum):
    """How significant this memory is"""
    CRITICAL = "critical"     # Life-changing, major decisions
    HIGH = "high"            # Important events, key relationships
    MEDIUM = "medium"        # Daily significant events
    LOW = "low"             # Routine but worth remembering
    TRIVIAL = "trivial"     # Minor events, might be cleaned up


@dataclass
class EpisodicMemory:
    """A specific memory of something that happened"""
    
    # Core identification
    id: str
    memory_type: MemoryType
    timestamp: datetime
    
    # Content
    title: str                          # Brief description
    description: str                    # Detailed account
    context: Dict[str, Any]            # Situation context
    
    # Participants and relationships
    people_involved: List[str] = field(default_factory=list)
    location: Optional[str] = None
    
    # Emotional and state context
    emotional_state: Optional[str] = None    # happy, stressed, excited, etc.
    energy_level: Optional[str] = None       # high, medium, low
    
    # Decision and outcome tracking
    decision_made: Optional[str] = None      # What you decided
    reasoning: Optional[str] = None          # Why you decided
    outcome: Optional[str] = None            # What happened as a result
    satisfaction: Optional[float] = None     # How happy with outcome (0-1)
    
    # Learning and patterns
    lessons_learned: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)  # IDs of related memories
    
    # Metadata
    importance: MemoryImportance = MemoryImportance.MEDIUM
    confidence: float = 0.8              # How sure we are about details
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    def __post_init__(self):
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
        if isinstance(self.importance, str):
            self.importance = MemoryImportance(self.importance)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'memory_type': self.memory_type.value,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'description': self.description,
            'context': self.context,
            'people_involved': self.people_involved,
            'location': self.location,
            'emotional_state': self.emotional_state,
            'energy_level': self.energy_level,
            'decision_made': self.decision_made,
            'reasoning': self.reasoning,
            'outcome': self.outcome,
            'satisfaction': self.satisfaction,
            'lessons_learned': self.lessons_learned,
            'tags': self.tags,
            'related_memories': self.related_memories,
            'importance': self.importance.value,
            'confidence': self.confidence,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpisodicMemory':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            title=data['title'],
            description=data['description'],
            context=data.get('context', {}),
            people_involved=data.get('people_involved', []),
            location=data.get('location'),
            emotional_state=data.get('emotional_state'),
            energy_level=data.get('energy_level'),
            decision_made=data.get('decision_made'),
            reasoning=data.get('reasoning'),
            outcome=data.get('outcome'),
            satisfaction=data.get('satisfaction'),
            lessons_learned=data.get('lessons_learned', []),
            tags=data.get('tags', []),
            related_memories=data.get('related_memories', []),
            importance=MemoryImportance(data.get('importance', 'medium')),
            confidence=data.get('confidence', 0.8),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None,
            access_count=data.get('access_count', 0)
        )
    
    def access(self):
        """Mark this memory as accessed"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def add_outcome(self, outcome: str, satisfaction: float, lessons: List[str] = None):
        """Add outcome information to a decision memory"""
        self.outcome = outcome
        self.satisfaction = satisfaction
        if lessons:
            self.lessons_learned.extend(lessons)
    
    def link_to_memory(self, other_memory_id: str):
        """Link to another related memory"""
        if other_memory_id not in self.related_memories:
            self.related_memories.append(other_memory_id)


class EpisodicMemorySystem:
    """
    Manages episodic memories - the specific events and experiences of your life.
    
    Features:
    - Stores concrete events with rich context
    - Tracks decision outcomes and satisfaction
    - Links related memories together
    - Provides temporal and contextual search
    - Learns patterns from past experiences
    """
    
    def __init__(self, storage_dir: str = "memory_system/episodic"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage for current session
        self.memories: Dict[str, EpisodicMemory] = {}
        
        # Load existing memories
        self._load_memories()
    
    def _load_memories(self):
        """Load memories from storage"""
        storage_file = self.storage_dir / "episodic_memories.json"
        
        if not storage_file.exists():
            self.logger.info("No existing episodic memories found")
            return
        
        try:
            with open(storage_file, 'r') as f:
                data = json.load(f)
                
                for memory_data in data.get('memories', []):
                    memory = EpisodicMemory.from_dict(memory_data)
                    self.memories[memory.id] = memory
                
                self.logger.info(f"Loaded {len(self.memories)} episodic memories")
                
        except Exception as e:
            self.logger.error(f"Error loading episodic memories: {e}")
    
    def _save_memories(self):
        """Save memories to storage"""
        storage_file = self.storage_dir / "episodic_memories.json"
        
        try:
            data = {
                'memories': [memory.to_dict() for memory in self.memories.values()],
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.memories)
            }
            
            with open(storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving episodic memories: {e}")
    
    def store_memory(self, 
                    title: str,
                    description: str,
                    memory_type: MemoryType,
                    context: Dict[str, Any] = None,
                    **kwargs) -> EpisodicMemory:
        """
        Store a new episodic memory.
        
        Args:
            title: Brief description of what happened
            description: Detailed account
            memory_type: Type of memory (decision, conversation, etc.)
            context: Situational context
            **kwargs: Additional memory fields
        
        Returns:
            Created EpisodicMemory
        """
        
        memory_id = str(uuid.uuid4())
        
        memory = EpisodicMemory(
            id=memory_id,
            memory_type=memory_type,
            timestamp=datetime.now(),
            title=title,
            description=description,
            context=context or {},
            **kwargs
        )
        
        self.memories[memory_id] = memory
        self._save_memories()
        
        self.logger.info(f"Stored {memory_type.value} memory: {title}")
        return memory
    
    def store_decision_memory(self,
                             decision: str,
                             situation: str,
                             reasoning: str,
                             context: Dict[str, Any] = None,
                             importance: MemoryImportance = MemoryImportance.MEDIUM) -> EpisodicMemory:
        """
        Store a decision memory with rich context.
        
        Args:
            decision: What was decided
            situation: The situation that required a decision
            reasoning: Why this decision was made
            context: Additional context
            importance: How important this decision was
        
        Returns:
            Created decision memory
        """
        
        return self.store_memory(
            title=f"Decision: {decision[:50]}...",
            description=f"Situation: {situation}\nDecision: {decision}\nReasoning: {reasoning}",
            memory_type=MemoryType.DECISION,
            context=context,
            decision_made=decision,
            reasoning=reasoning,
            importance=importance
        )
    
    def store_conversation_memory(self,
                                 person: str,
                                 topic: str,
                                 key_points: List[str],
                                 outcome: str = None,
                                 context: Dict[str, Any] = None) -> EpisodicMemory:
        """Store a conversation memory"""
        
        description = f"Conversation with {person} about {topic}\n"
        description += f"Key points: {'; '.join(key_points)}"
        if outcome:
            description += f"\nOutcome: {outcome}"
        
        return self.store_memory(
            title=f"Conversation with {person}: {topic}",
            description=description,
            memory_type=MemoryType.CONVERSATION,
            context=context,
            people_involved=[person],
            outcome=outcome,
            tags=[topic, person, "conversation"]
        )
    
    def add_outcome_to_decision(self,
                               decision_memory_id: str,
                               outcome: str,
                               satisfaction: float,
                               lessons_learned: List[str] = None) -> bool:
        """
        Add outcome information to an existing decision memory.
        
        This is crucial for learning - connecting decisions to their results.
        """
        
        if decision_memory_id not in self.memories:
            self.logger.warning(f"Decision memory {decision_memory_id} not found")
            return False
        
        memory = self.memories[decision_memory_id]
        memory.add_outcome(outcome, satisfaction, lessons_learned)
        
        self._save_memories()
        
        self.logger.info(f"Added outcome to decision: {outcome} (satisfaction: {satisfaction:.2f})")
        return True
    
    def search_memories(self,
                       query: str = None,
                       memory_type: MemoryType = None,
                       person: str = None,
                       time_range: Tuple[datetime, datetime] = None,
                       tags: List[str] = None,
                       min_importance: MemoryImportance = None,
                       limit: int = 10) -> List[EpisodicMemory]:
        """
        Search memories with various filters.
        
        Args:
            query: Text to search in title/description
            memory_type: Filter by memory type
            person: Filter by person involved
            time_range: (start_date, end_date) tuple
            tags: List of tags to match
            min_importance: Minimum importance level
            limit: Maximum results to return
        
        Returns:
            List of matching memories, sorted by relevance/recency
        """
        
        matching_memories = []
        
        for memory in self.memories.values():
            # Apply filters
            if memory_type and memory.memory_type != memory_type:
                continue
            
            if person and person not in memory.people_involved:
                continue
            
            if time_range:
                start_date, end_date = time_range
                if not (start_date <= memory.timestamp <= end_date):
                    continue
            
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            if min_importance:
                importance_order = [MemoryImportance.TRIVIAL, MemoryImportance.LOW, 
                                  MemoryImportance.MEDIUM, MemoryImportance.HIGH, 
                                  MemoryImportance.CRITICAL]
                if importance_order.index(memory.importance) < importance_order.index(min_importance):
                    continue
            
            # Text search
            if query:
                query_lower = query.lower()
                if not (query_lower in memory.title.lower() or 
                       query_lower in memory.description.lower()):
                    continue
            
            matching_memories.append(memory)
        
        # Sort by recency and importance
        def sort_key(mem):
            importance_weight = {
                MemoryImportance.CRITICAL: 5,
                MemoryImportance.HIGH: 4,
                MemoryImportance.MEDIUM: 3,
                MemoryImportance.LOW: 2,
                MemoryImportance.TRIVIAL: 1
            }
            
            # Combine recency (higher is more recent) with importance
            recency_score = (datetime.now() - mem.timestamp).days
            recency_score = max(0, 30 - recency_score) / 30  # 0-1 scale, recent = higher
            
            return importance_weight[mem.importance] + recency_score
        
        matching_memories.sort(key=sort_key, reverse=True)
        
        # Mark accessed
        for memory in matching_memories[:limit]:
            memory.access()
        
        self._save_memories()
        
        return matching_memories[:limit]
    
    def get_recent_memories(self, days: int = 7, limit: int = 20) -> List[EpisodicMemory]:
        """Get recent memories within the specified days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        time_range = (cutoff_date, datetime.now())
        
        return self.search_memories(time_range=time_range, limit=limit)
    
    def get_memories_by_person(self, person: str, limit: int = 10) -> List[EpisodicMemory]:
        """Get all memories involving a specific person"""
        
        return self.search_memories(person=person, limit=limit)
    
    def get_decision_outcomes(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get decision memories with outcomes for learning analysis.
        
        Returns decisions and their satisfaction scores to identify patterns.
        """
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        decision_memories = self.search_memories(
            memory_type=MemoryType.DECISION,
            time_range=(cutoff_date, datetime.now()),
            limit=50
        )
        
        outcomes = []
        for memory in decision_memories:
            if memory.outcome and memory.satisfaction is not None:
                outcomes.append({
                    'id': memory.id,
                    'decision': memory.decision_made,
                    'reasoning': memory.reasoning,
                    'outcome': memory.outcome,
                    'satisfaction': memory.satisfaction,
                    'lessons': memory.lessons_learned,
                    'context': memory.context,
                    'timestamp': memory.timestamp
                })
        
        return outcomes
    
    def find_similar_situations(self, 
                               current_situation: str,
                               context: Dict[str, Any] = None,
                               limit: int = 5) -> List[EpisodicMemory]:
        """
        Find memories of similar situations for pattern matching.
        
        This helps answer: "What did I do last time this happened?"
        """
        
        # Extract key words from current situation
        situation_words = set(current_situation.lower().split())
        
        # Score memories by similarity
        scored_memories = []
        
        for memory in self.memories.values():
            # Calculate similarity score
            memory_text = f"{memory.title} {memory.description}".lower()
            memory_words = set(memory_text.split())
            
            # Word overlap similarity
            common_words = situation_words.intersection(memory_words)
            word_similarity = len(common_words) / len(situation_words.union(memory_words))
            
            # Context similarity
            context_similarity = 0
            if context and memory.context:
                context_keys = set(context.keys())
                memory_keys = set(memory.context.keys())
                if context_keys and memory_keys:
                    context_similarity = len(context_keys.intersection(memory_keys)) / len(context_keys.union(memory_keys))
            
            # Combine similarities
            total_similarity = word_similarity + (context_similarity * 0.3)
            
            if total_similarity > 0.1:  # Minimum threshold
                scored_memories.append((memory, total_similarity))
        
        # Sort by similarity
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches
        similar_memories = [memory for memory, score in scored_memories[:limit]]
        
        # Mark as accessed
        for memory in similar_memories:
            memory.access()
        
        self._save_memories()
        
        return similar_memories
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        
        if not self.memories:
            return {"message": "No memories stored"}
        
        stats = {
            "total_memories": len(self.memories),
            "by_type": {},
            "by_importance": {},
            "by_month": {},
            "most_accessed": [],
            "recent_activity": 0,
            "people_involved": {},
            "satisfaction_patterns": {}
        }
        
        # Count by type and importance
        for memory in self.memories.values():
            mem_type = memory.memory_type.value
            importance = memory.importance.value
            
            stats["by_type"][mem_type] = stats["by_type"].get(mem_type, 0) + 1
            stats["by_importance"][importance] = stats["by_importance"].get(importance, 0) + 1
            
            # Count by month
            month_key = memory.timestamp.strftime("%Y-%m")
            stats["by_month"][month_key] = stats["by_month"].get(month_key, 0) + 1
            
            # Count people
            for person in memory.people_involved:
                stats["people_involved"][person] = stats["people_involved"].get(person, 0) + 1
        
        # Most accessed memories
        accessed_memories = [(mem.title, mem.access_count) for mem in self.memories.values() if mem.access_count > 0]
        stats["most_accessed"] = sorted(accessed_memories, key=lambda x: x[1], reverse=True)[:5]
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        stats["recent_activity"] = sum(1 for mem in self.memories.values() if mem.timestamp >= week_ago)
        
        # Satisfaction patterns for decisions
        decision_memories = [mem for mem in self.memories.values() 
                           if mem.memory_type == MemoryType.DECISION and mem.satisfaction is not None]
        
        if decision_memories:
            avg_satisfaction = sum(mem.satisfaction for mem in decision_memories) / len(decision_memories)
            high_satisfaction = sum(1 for mem in decision_memories if mem.satisfaction >= 0.8)
            low_satisfaction = sum(1 for mem in decision_memories if mem.satisfaction <= 0.4)
            
            stats["satisfaction_patterns"] = {
                "average_satisfaction": avg_satisfaction,
                "high_satisfaction_count": high_satisfaction,
                "low_satisfaction_count": low_satisfaction,
                "total_decisions_tracked": len(decision_memories)
            }
        
        return stats
    
    def cleanup_old_memories(self, days: int = 365, keep_important: bool = True):
        """Clean up old, low-importance memories to prevent storage bloat"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for memory_id, memory in self.memories.items():
            if memory.timestamp < cutoff_date:
                # Keep important memories regardless of age
                if keep_important and memory.importance in [MemoryImportance.HIGH, MemoryImportance.CRITICAL]:
                    continue
                
                # Keep frequently accessed memories
                if memory.access_count > 5:
                    continue
                
                # Keep memories with outcomes (learning data)
                if memory.outcome and memory.satisfaction is not None:
                    continue
                
                to_remove.append(memory_id)
        
        # Remove old memories
        for memory_id in to_remove:
            del self.memories[memory_id]
        
        if to_remove:
            self._save_memories()
            self.logger.info(f"Cleaned up {len(to_remove)} old memories")
        
        return len(to_remove)