"""
Memory Interface for Digital Twin

This module provides an abstract interface for memory storage and retrieval,
allowing the digital twin to work with different vector databases (Chroma, Pinecone, etc.)
without changing the core logic.

The memory system stores:
- Past decisions and outcomes
- Communication patterns
- Personal preferences and habits
- Learned behaviors
- External knowledge
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import chromadb
from chromadb.utils import embedding_functions
import uuid


class MemoryInterface(ABC):
    """Abstract base class for memory storage systems"""
    
    @abstractmethod
    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a memory to the storage"""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for relevant memories"""
        pass
    
    @abstractmethod
    def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Update an existing memory"""
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a memory"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, category: str = None) -> List[Dict[str, Any]]:
        """Retrieve all memories, optionally filtered by category"""
        pass


class ChromaMemory(MemoryInterface):
    """
    Chroma-based memory implementation.
    
    Chroma is an open-source embedding database that runs locally,
    making it perfect for personal digital twin applications.
    """
    
    def __init__(self, 
                 collection_name: str = "digital_twin_memory",
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize Chroma memory system.
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Where to store the database
            embedding_model: Which embedding model to use
        """
        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence transformers for embeddings (free and local)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Digital twin memory storage"}
        )
    
    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a memory to the database.
        
        Args:
            content: The memory content (will be embedded)
            metadata: Additional metadata (category, timestamp, etc.)
        
        Returns:
            memory_id: Unique identifier for the memory
        """
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        
        # Add memory type classification
        if 'type' not in metadata:
            metadata['type'] = self._classify_memory_type(content)
        
        # Store in Chroma
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def search(self, query: str, k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant memories using semantic similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Metadata filters (e.g., category, date range)
        
        Returns:
            List of relevant memories with scores
        """
        # Build where clause from filters
        where_clause = None
        if filters:
            where_clause = filters
        
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where_clause
        )
        
        # Format results
        memories = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                memory = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'score': 1 - results['distances'][0][i] if results['distances'] else 0  # Convert distance to similarity
                }
                memories.append(memory)
        
        return memories
    
    def update(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Update an existing memory"""
        try:
            # Get existing memory
            existing = self.collection.get(ids=[memory_id])
            
            if not existing['documents']:
                return False
            
            # Prepare updates
            new_content = content if content is not None else existing['documents'][0]
            new_metadata = existing['metadatas'][0] if existing['metadatas'] else {}
            
            if metadata:
                new_metadata.update(metadata)
            
            # Update timestamp
            new_metadata['last_updated'] = datetime.now().isoformat()
            
            # Update in Chroma
            self.collection.update(
                ids=[memory_id],
                documents=[new_content],
                metadatas=[new_metadata]
            )
            
            return True
        except Exception as e:
            print(f"Error updating memory: {e}")
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory"""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    def get_all(self, limit: int = 100, category: str = None) -> List[Dict[str, Any]]:
        """Get all memories, optionally filtered by category"""
        where_clause = {"category": category} if category else None
        
        # Get all memories (up to limit)
        results = self.collection.get(
            limit=limit,
            where=where_clause
        )
        
        # Format results
        memories = []
        if results['documents']:
            for i in range(len(results['documents'])):
                memory = {
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i] if results['metadatas'] else {}
                }
                memories.append(memory)
        
        return memories
    
    def _classify_memory_type(self, content: str) -> str:
        """Simple classification of memory type based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['decided', 'chose', 'selected']):
            return 'decision'
        elif any(word in content_lower for word in ['email', 'message', 'replied']):
            return 'communication'
        elif any(word in content_lower for word in ['learned', 'discovered', 'realized']):
            return 'learning'
        elif any(word in content_lower for word in ['prefer', 'like', 'enjoy']):
            return 'preference'
        elif any(word in content_lower for word in ['routine', 'usually', 'always']):
            return 'habit'
        else:
            return 'general'
    
    def add_behavioral_pattern(self, 
                             situation: str, 
                             action: str, 
                             outcome: str = None,
                             confidence: float = 0.5) -> str:
        """
        Specialized method for adding behavioral patterns.
        
        This is useful for the twin to learn from observed behaviors.
        """
        content = f"In situation: '{situation}', action taken: '{action}'"
        if outcome:
            content += f", outcome: '{outcome}'"
        
        metadata = {
            'type': 'behavioral_pattern',
            'situation': situation,
            'action': action,
            'outcome': outcome,
            'confidence': confidence
        }
        
        return self.add(content, metadata)
    
    def add_communication_sample(self,
                               message: str,
                               response: str,
                               platform: str,
                               recipient_type: str) -> str:
        """
        Store communication patterns for learning writing style.
        """
        content = f"Message: {message}\nResponse: {response}"
        
        metadata = {
            'type': 'communication_sample',
            'platform': platform,  # email, whatsapp, slack, etc.
            'recipient_type': recipient_type,  # boss, colleague, friend, client
            'message_length': len(message),
            'response_length': len(response)
        }
        
        return self.add(content, metadata)
    
    def get_similar_situations(self, situation: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Find similar past situations to inform current decision.
        """
        return self.search(
            query=situation,
            k=k,
            filters={'type': 'behavioral_pattern'}
        )


class MemoryManager:
    """
    High-level memory management for the digital twin.
    
    This class provides convenient methods for common memory operations
    and can switch between different memory backends.
    """
    
    def __init__(self, memory_backend: MemoryInterface = None):
        """Initialize with a specific memory backend or default to Chroma"""
        self.memory = memory_backend or ChromaMemory()
        
    def remember_decision(self, context: str, decision: str, reasoning: str, outcome: str = None):
        """Remember a decision for future reference"""
        content = f"Context: {context}\nDecision: {decision}\nReasoning: {reasoning}"
        if outcome:
            content += f"\nOutcome: {outcome}"
        
        return self.memory.add(
            content=content,
            metadata={
                'type': 'decision',
                'context_summary': context[:100],
                'decision_summary': decision[:100]
            }
        )
    
    def remember_preference(self, category: str, preference: str, strength: str = "medium"):
        """Remember a personal preference"""
        content = f"Preference in {category}: {preference}"
        
        return self.memory.add(
            content=content,
            metadata={
                'type': 'preference',
                'category': category,
                'strength': strength  # strong, medium, weak
            }
        )
    
    def find_relevant_memories(self, situation: str, memory_types: List[str] = None) -> List[Dict[str, Any]]:
        """Find memories relevant to current situation"""
        filters = {}
        if memory_types:
            filters['type'] = {"$in": memory_types}
        
        return self.memory.search(query=situation, k=5, filters=filters)
    
    def export_memories(self, filepath: str = "memories_export.json"):
        """Export all memories to a JSON file for backup"""
        all_memories = self.memory.get_all(limit=10000)
        
        with open(filepath, 'w') as f:
            json.dump(all_memories, f, indent=2)
        
        return f"Exported {len(all_memories)} memories to {filepath}"
    
    def import_memories(self, filepath: str):
        """Import memories from a JSON file"""
        with open(filepath, 'r') as f:
            memories = json.load(f)
        
        imported = 0
        for memory in memories:
            self.memory.add(
                content=memory['content'],
                metadata=memory.get('metadata', {})
            )
            imported += 1
        
        return f"Imported {imported} memories"