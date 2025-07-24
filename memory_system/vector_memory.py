"""
Enhanced Vector Memory System for Digital Twin

This module provides semantic memory storage using vector embeddings.
Unlike episodic memory (specific events), this stores knowledge, patterns,
and semantic relationships for similarity-based retrieval.

Features:
- Semantic search using embeddings
- Multi-modal memory types (text, decisions, patterns, knowledge)
- Automatic relationship detection
- Memory consolidation and summarization
- Context-aware retrieval with reasoning influence
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import logging
import numpy as np
from pathlib import Path

# Vector database imports
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not available. Install with: pip install chromadb")

# OpenAI for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VectorMemoryType(Enum):
    """Types of vector memories"""
    KNOWLEDGE = "knowledge"           # Facts, learned information
    PATTERN = "pattern"              # Behavioral patterns, habits
    DECISION_CONTEXT = "decision_context"  # Context that influenced decisions  
    PREFERENCE = "preference"        # Likes, dislikes, tendencies
    SKILL = "skill"                 # Learned abilities, approaches
    INSIGHT = "insight"             # Realizations, understanding
    RELATIONSHIP = "relationship"    # How you interact with people
    STRATEGY = "strategy"           # Approaches that work
    BEHAVIORAL_PATTERN = "behavioral_pattern"  # Observed behavior patterns


@dataclass 
class VectorMemory:
    """A semantic memory stored as vector embeddings"""
    
    id: str
    content: str                    # The actual memory content
    memory_type: VectorMemoryType
    embedding: Optional[List[float]] = None  # Vector representation
    
    # Metadata for context
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Relationships
    related_memories: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    # Usage tracking
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    relevance_score: float = 1.0    # Decays over time if not accessed
    
    # Learning context
    source_reasoning_mode: Optional[str] = None  # heuristic, deliberation, arbitration
    decision_outcome: Optional[float] = None     # Satisfaction if from decision (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding embedding for size)"""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'metadata': self.metadata,
            'tags': self.tags,
            'related_memories': self.related_memories,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count,
            'relevance_score': self.relevance_score,
            'source_reasoning_mode': self.source_reasoning_mode,
            'decision_outcome': self.decision_outcome
        }
    
    def access(self, boost_relevance: bool = True):
        """Mark memory as accessed and boost relevance"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        
        if boost_relevance:
            # Boost relevance when accessed, but cap at 1.0
            self.relevance_score = min(1.0, self.relevance_score + 0.1)


class EnhancedVectorMemory:
    """
    Enhanced vector memory system with semantic search and intelligent consolidation.
    
    This system:
    1. Stores memories as vector embeddings for semantic similarity
    2. Automatically detects relationships between memories
    3. Consolidates similar memories to prevent redundancy
    4. Provides context-aware retrieval based on reasoning state
    5. Learns what memories are most useful over time
    """
    
    def __init__(self, 
                 storage_dir: str = "memory_system/vector",
                 collection_name: str = "twin_semantic_memory",
                 openai_api_key: str = None):
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize embedding function
        self.openai_client = None
        if OPENAI_AVAILABLE and openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Initialize ChromaDB
        self.chroma_client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            self._init_chromadb(collection_name)
        
        # In-memory cache for performance
        self.memory_cache: Dict[str, VectorMemory] = {}
        
        # Load existing memories
        self._load_memory_metadata()
    
    def _init_chromadb(self, collection_name: str):
        """Initialize ChromaDB client and collection"""
        try:
            # Use persistent client
            self.chroma_client = chromadb.PersistentClient(path=str(self.storage_dir / "chroma_db"))
            
            # Use OpenAI embeddings if available, otherwise sentence transformers
            if self.openai_client:
                # Custom embedding function for OpenAI
                class OpenAIEmbeddingFunction:
                    def __init__(self, client):
                        self.client = client
                    
                    def __call__(self, texts: List[str]) -> List[List[float]]:
                        response = self.client.embeddings.create(
                            model="text-embedding-ada-002",
                            input=texts
                        )
                        return [data.embedding for data in response.data]
                
                embedding_function = OpenAIEmbeddingFunction(self.openai_client)
            else:
                # Fallback to sentence transformers
                embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"description": "Digital twin semantic memory"}
            )
            
            self.logger.info(f"ChromaDB initialized with collection: {collection_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
    
    def _load_memory_metadata(self):
        """Load memory metadata from storage"""
        metadata_file = self.storage_dir / "memory_metadata.json"
        
        if not metadata_file.exists():
            return
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                
                for memory_data in data.get('memories', []):
                    memory = VectorMemory(
                        id=memory_data['id'],
                        content=memory_data['content'],
                        memory_type=VectorMemoryType(memory_data['memory_type']),
                        metadata=memory_data.get('metadata', {}),
                        tags=memory_data.get('tags', []),
                        related_memories=memory_data.get('related_memories', []),
                        confidence=memory_data.get('confidence', 0.8),
                        created_at=datetime.fromisoformat(memory_data['created_at']),
                        last_accessed=datetime.fromisoformat(memory_data['last_accessed']) if memory_data.get('last_accessed') else None,
                        access_count=memory_data.get('access_count', 0),
                        relevance_score=memory_data.get('relevance_score', 1.0),
                        source_reasoning_mode=memory_data.get('source_reasoning_mode'),
                        decision_outcome=memory_data.get('decision_outcome')
                    )
                    
                    self.memory_cache[memory.id] = memory
                
                self.logger.info(f"Loaded metadata for {len(self.memory_cache)} vector memories")
                
        except Exception as e:
            self.logger.error(f"Error loading memory metadata: {e}")
    
    def _save_memory_metadata(self):
        """Save memory metadata to storage"""
        metadata_file = self.storage_dir / "memory_metadata.json"
        
        try:
            data = {
                'memories': [memory.to_dict() for memory in self.memory_cache.values()],
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.memory_cache)
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving memory metadata: {e}")
    
    def add_memory(self,
                   content: str,
                   memory_type: VectorMemoryType,
                   metadata: Dict[str, Any] = None,
                   tags: List[str] = None,
                   source_reasoning_mode: str = None,
                   decision_outcome: float = None) -> str:
        """
        Add a new semantic memory.
        
        Args:
            content: The memory content to store
            memory_type: Type of memory
            metadata: Additional metadata
            tags: Tags for categorization
            source_reasoning_mode: Which reasoning mode generated this
            decision_outcome: Satisfaction score if from decision
            
        Returns:
            Memory ID
        """
        
        if not self.collection:
            self.logger.error("Vector storage not available")
            return None
        
        memory_id = str(uuid.uuid4())
        
        # Create memory object
        memory = VectorMemory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
            tags=tags or [],
            source_reasoning_mode=source_reasoning_mode,
            decision_outcome=decision_outcome
        )
        
        # Check for similar existing memories to avoid duplication
        similar_memories = self.search_similar(content, threshold=0.9, limit=3)
        
        if similar_memories:
            # If very similar memory exists, update it instead of creating new
            most_similar = similar_memories[0]
            if most_similar['score'] > 0.95:
                self.logger.info(f"Very similar memory exists, updating instead of creating new")
                return self._update_existing_memory(most_similar['id'], content, memory)
        
        try:
            # Add to ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[{
                    'memory_type': memory_type.value,
                    'created_at': memory.created_at.isoformat(),
                    'tags': ','.join(tags or []),
                    'source_reasoning_mode': source_reasoning_mode or '',
                    **(metadata or {})
                }],
                ids=[memory_id]
            )
            
            # Add to cache
            self.memory_cache[memory_id] = memory
            
            # Save metadata
            self._save_memory_metadata()
            
            # Find and link related memories
            self._link_related_memories(memory_id, content)
            
            self.logger.info(f"Added {memory_type.value} memory: {content[:50]}...")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding memory: {e}")
            return None
    
    def _update_existing_memory(self, existing_id: str, new_content: str, new_memory: VectorMemory) -> str:
        """Update existing similar memory instead of creating duplicate"""
        
        if existing_id not in self.memory_cache:
            return None
        
        existing_memory = self.memory_cache[existing_id]
        
        # Combine content
        combined_content = f"{existing_memory.content}\n\nAdditional context: {new_content}"
        
        # Update in ChromaDB
        self.collection.update(
            ids=[existing_id],
            documents=[combined_content]
        )
        
        # Update memory object
        existing_memory.content = combined_content
        existing_memory.access_count += 1
        existing_memory.relevance_score = min(1.0, existing_memory.relevance_score + 0.1)
        
        # Merge tags and metadata
        existing_memory.tags = list(set(existing_memory.tags + new_memory.tags))
        existing_memory.metadata.update(new_memory.metadata)
        
        self._save_memory_metadata()
        
        return existing_id
    
    def _link_related_memories(self, memory_id: str, content: str):
        """Find and link related memories"""
        
        # Find semantically similar memories
        similar_memories = self.search_similar(content, threshold=0.7, limit=5)
        
        memory = self.memory_cache[memory_id]
        
        for similar in similar_memories:
            if similar['id'] != memory_id:
                # Link both ways
                memory.related_memories.append(similar['id'])
                
                if similar['id'] in self.memory_cache:
                    related_memory = self.memory_cache[similar['id']]
                    if memory_id not in related_memory.related_memories:
                        related_memory.related_memories.append(memory_id)
    
    def search_similar(self, 
                      query: str,
                      memory_types: List[VectorMemoryType] = None,
                      threshold: float = 0.5,
                      limit: int = 10,
                      boost_recent: bool = True) -> List[Dict[str, Any]]:
        """
        Search for semantically similar memories.
        
        Args:
            query: Search query
            memory_types: Filter by memory types
            threshold: Minimum similarity threshold
            limit: Maximum results
            boost_recent: Boost recently accessed memories
            
        Returns:
            List of similar memories with scores
        """
        
        if not self.collection:
            return []
        
        try:
            # Build where clause for filtering
            where_clause = None
            if memory_types:
                type_values = [mt.value for mt in memory_types]
                where_clause = {"memory_type": {"$in": type_values}}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=limit * 2,  # Get more results for filtering
                where=where_clause
            )
            
            # Process results
            memories = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    memory_id = results['ids'][0][i]
                    similarity_score = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    if similarity_score < threshold:
                        continue
                    
                    # Get memory from cache for additional info
                    memory_obj = self.memory_cache.get(memory_id)
                    
                    # Calculate final score with boosts
                    final_score = similarity_score
                    
                    if memory_obj and boost_recent:
                        # Boost recently accessed memories
                        if memory_obj.last_accessed:
                            days_since_access = (datetime.now() - memory_obj.last_accessed).days
                            recency_boost = max(0, (30 - days_since_access) / 30 * 0.2)
                            final_score += recency_boost
                        
                        # Boost by relevance score
                        final_score *= memory_obj.relevance_score
                        
                        # Boost by access count (popular memories)
                        access_boost = min(0.1, memory_obj.access_count * 0.01)
                        final_score += access_boost
                    
                    memory_data = {
                        'id': memory_id,
                        'content': results['documents'][0][i],
                        'score': final_score,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    
                    if memory_obj:
                        memory_data.update({
                            'memory_type': memory_obj.memory_type.value,
                            'tags': memory_obj.tags,
                            'access_count': memory_obj.access_count,
                            'created_at': memory_obj.created_at,
                            'related_memories': memory_obj.related_memories
                        })
                        
                        # Mark as accessed
                        memory_obj.access()
                    
                    memories.append(memory_data)
            
            # Sort by final score
            memories.sort(key=lambda x: x['score'], reverse=True)
            
            # Save updated access counts
            self._save_memory_metadata()
            
            return memories[:limit]
            
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return []
    
    def get_contextual_memories(self,
                               query: str,
                               reasoning_mode: str = None,
                               current_state: Dict[str, Any] = None,
                               limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories relevant to current context and reasoning mode.
        
        This provides smarter memory retrieval based on:
        - Current reasoning mode (heuristic prefers patterns, deliberation prefers knowledge)
        - Current state (energy, stress affects what memories are relevant)
        - Recent decision outcomes (prefer memories from successful decisions)
        """
        
        # Determine which memory types to prioritize
        preferred_types = []
        
        if reasoning_mode == "heuristic":
            preferred_types = [VectorMemoryType.PATTERN, VectorMemoryType.STRATEGY]
        elif reasoning_mode == "deliberation":
            preferred_types = [VectorMemoryType.KNOWLEDGE, VectorMemoryType.INSIGHT]
        elif reasoning_mode == "arbitration":
            preferred_types = [VectorMemoryType.PREFERENCE, VectorMemoryType.RELATIONSHIP]
        
        # Get base similar memories
        all_memories = self.search_similar(query, limit=limit*2)
        
        # Score memories based on context
        contextual_memories = []
        
        for memory in all_memories:
            memory_obj = self.memory_cache.get(memory['id'])
            if not memory_obj:
                continue
            
            base_score = memory['score']
            
            # Boost preferred types for current reasoning mode
            if memory_obj.memory_type in preferred_types:
                base_score *= 1.3
            
            # Boost memories from successful decisions
            if memory_obj.decision_outcome and memory_obj.decision_outcome > 0.7:
                base_score *= 1.2
            
            # Boost memories from same reasoning mode
            if memory_obj.source_reasoning_mode == reasoning_mode:
                base_score *= 1.1
            
            # Adjust for current state
            if current_state:
                state_boost = self._calculate_state_relevance_boost(memory_obj, current_state)
                base_score += state_boost
            
            memory['contextual_score'] = base_score
            contextual_memories.append(memory)
        
        # Sort by contextual score
        contextual_memories.sort(key=lambda x: x['contextual_score'], reverse=True)
        
        return contextual_memories[:limit]
    
    def _calculate_state_relevance_boost(self, memory: VectorMemory, current_state: Dict[str, Any]) -> float:
        """Calculate how relevant a memory is to current state"""
        
        boost = 0.0
        
        # If low energy, boost memories about energy management
        if current_state.get('current_energy') == 'low':
            if any(word in memory.content.lower() for word in ['energy', 'tired', 'rest', 'break']):
                boost += 0.1
        
        # If high stress, boost memories about stress management
        if current_state.get('current_stress') == 'high':
            if any(word in memory.content.lower() for word in ['stress', 'overwhelm', 'priority', 'calm']):
                boost += 0.1
        
        # Boost memories with similar metadata
        for key, value in current_state.items():
            if key in memory.metadata and memory.metadata[key] == value:
                boost += 0.05
        
        return boost
    
    def consolidate_memories(self, similarity_threshold: float = 0.8):
        """
        Consolidate very similar memories to reduce redundancy.
        
        This prevents the memory system from becoming cluttered with
        near-duplicate memories.
        """
        
        if not self.collection:
            return
        
        consolidated_count = 0
        memory_ids = list(self.memory_cache.keys())
        
        for i, memory_id in enumerate(memory_ids):
            if memory_id not in self.memory_cache:
                continue  # Already consolidated
            
            memory = self.memory_cache[memory_id]
            
            # Find very similar memories
            similar = self.search_similar(
                memory.content,
                threshold=similarity_threshold,
                limit=5
            )
            
            # Consolidate with most similar
            for similar_memory in similar:
                if (similar_memory['id'] != memory_id and 
                    similar_memory['id'] in self.memory_cache and
                    similar_memory['score'] > similarity_threshold):
                    
                    # Merge memories
                    self._merge_memories(memory_id, similar_memory['id'])
                    consolidated_count += 1
                    break
        
        if consolidated_count > 0:
            self.logger.info(f"Consolidated {consolidated_count} similar memories")
        
        return consolidated_count
    
    def _merge_memories(self, primary_id: str, secondary_id: str):
        """Merge two similar memories"""
        
        primary = self.memory_cache[primary_id]
        secondary = self.memory_cache[secondary_id]
        
        # Combine content
        combined_content = f"{primary.content}\n\nRelated: {secondary.content}"
        
        # Merge metadata
        primary.metadata.update(secondary.metadata)
        primary.tags = list(set(primary.tags + secondary.tags))
        primary.related_memories = list(set(primary.related_memories + secondary.related_memories))
        
        # Keep higher confidence and combine access counts
        primary.confidence = max(primary.confidence, secondary.confidence)
        primary.access_count += secondary.access_count
        primary.relevance_score = max(primary.relevance_score, secondary.relevance_score)
        
        # Update in ChromaDB
        self.collection.update(
            ids=[primary_id],
            documents=[combined_content],
            metadatas=[{
                'memory_type': primary.memory_type.value,
                'created_at': primary.created_at.isoformat(),
                'tags': ','.join(primary.tags),
                'source_reasoning_mode': primary.source_reasoning_mode or '',
                **primary.metadata
            }]
        )
        
        # Remove secondary memory
        self.collection.delete(ids=[secondary_id])
        del self.memory_cache[secondary_id]
        
        self._save_memory_metadata()
    
    def decay_unused_memories(self, days_threshold: int = 90, decay_rate: float = 0.1):
        """
        Decay relevance of unused memories over time.
        
        This helps prioritize frequently accessed memories over old unused ones.
        """
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        decayed_count = 0
        
        for memory in self.memory_cache.values():
            # Skip recently accessed memories
            if memory.last_accessed and memory.last_accessed > cutoff_date:
                continue
            
            # Skip high-importance memories
            if memory.decision_outcome and memory.decision_outcome > 0.8:
                continue
            
            # Decay relevance
            old_score = memory.relevance_score
            memory.relevance_score = max(0.1, memory.relevance_score - decay_rate)
            
            if memory.relevance_score < old_score:
                decayed_count += 1
        
        if decayed_count > 0:
            self._save_memory_metadata()
            self.logger.info(f"Decayed relevance for {decayed_count} unused memories")
        
        return decayed_count
    
    def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights about the memory system"""
        
        if not self.memory_cache:
            return {"message": "No memories stored"}
        
        insights = {
            "total_memories": len(self.memory_cache),
            "by_type": {},
            "by_reasoning_mode": {},
            "access_patterns": {},
            "relationship_network": {},
            "quality_metrics": {}
        }
        
        # Count by type
        for memory in self.memory_cache.values():
            mem_type = memory.memory_type.value
            insights["by_type"][mem_type] = insights["by_type"].get(mem_type, 0) + 1
            
            # Count by reasoning mode
            if memory.source_reasoning_mode:
                mode = memory.source_reasoning_mode
                insights["by_reasoning_mode"][mode] = insights["by_reasoning_mode"].get(mode, 0) + 1
        
        # Access patterns
        accessed_memories = [m for m in self.memory_cache.values() if m.access_count > 0]
        if accessed_memories:
            avg_access = sum(m.access_count for m in accessed_memories) / len(accessed_memories)
            most_accessed = max(accessed_memories, key=lambda x: x.access_count)
            
            insights["access_patterns"] = {
                "memories_accessed": len(accessed_memories),
                "average_access_count": avg_access,
                "most_accessed_content": most_accessed.content[:100],
                "most_accessed_count": most_accessed.access_count
            }
        
        # Relationship network
        total_links = sum(len(m.related_memories) for m in self.memory_cache.values())
        insights["relationship_network"] = {
            "total_links": total_links,
            "average_links_per_memory": total_links / len(self.memory_cache) if self.memory_cache else 0
        }
        
        # Quality metrics
        memories_with_outcomes = [m for m in self.memory_cache.values() if m.decision_outcome is not None]
        if memories_with_outcomes:
            avg_outcome = sum(m.decision_outcome for m in memories_with_outcomes) / len(memories_with_outcomes)
            insights["quality_metrics"] = {
                "memories_with_outcomes": len(memories_with_outcomes),
                "average_decision_satisfaction": avg_outcome
            }
        
        return insights
    
    def cleanup_low_quality_memories(self, min_relevance: float = 0.2, min_confidence: float = 0.3):
        """Remove low-quality memories"""
        
        to_remove = []
        
        for memory_id, memory in self.memory_cache.items():
            if (memory.relevance_score < min_relevance and 
                memory.confidence < min_confidence and
                memory.access_count == 0):
                to_remove.append(memory_id)
        
        # Remove from ChromaDB and cache
        if to_remove:
            self.collection.delete(ids=to_remove)
            
            for memory_id in to_remove:
                del self.memory_cache[memory_id]
            
            self._save_memory_metadata()
            self.logger.info(f"Cleaned up {len(to_remove)} low-quality memories")
        
        return len(to_remove)