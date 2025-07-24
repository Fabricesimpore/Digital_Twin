"""
Digital Twin Core Brain Module

This module implements the core reasoning engine for a digital twin that learns
and mirrors personal behavior, decision-making patterns, and communication style.

Architecture:
- Identity Layer: Loads persona, values, and behavioral traits
- Reasoning Layer: Combines context + memory + identity to make decisions
- Memory Layer: Interfaces with vector DB for long-term memory and learning
"""

import yaml
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import openai
from pathlib import Path


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
    """Response from the digital twin's reasoning"""
    action: str  # What the twin would do
    reasoning: str  # Why this action was chosen
    confidence: float  # How confident the twin is (0-1)
    alternatives: List[str] = None  # Other considered actions
    memory_references: List[str] = None  # Which memories influenced this


class DigitalTwin:
    """
    Core brain module for the digital twin system.
    
    This class orchestrates:
    1. Identity management (who you are)
    2. Memory retrieval (what you remember)
    3. Reasoning (how you think)
    4. Decision making (what you would do)
    """
    
    def __init__(self, persona_path: str = "persona.yaml", api_key: str = None):
        # Load identity layer
        self.persona = self._load_persona(persona_path)
        
        # Initialize LLM client (using OpenAI for now, modular for other providers)
        self.llm_client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Using GPT-4o as specified
        
        # Memory interface (will be implemented separately)
        self.memory = None  # Will be injected or initialized with MemoryInterface
        
        # Decision history for learning
        self.decision_history = []
    
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
        """Inject memory system (Chroma, Pinecone, etc.)"""
        self.memory = memory_interface
    
    def reason(self, situation: Situation) -> TwinResponse:
        """
        Core reasoning function - the brain's main entry point.
        
        Takes a situation and returns what the twin would do based on:
        1. Identity (who am I?)
        2. Memory (what do I remember?)
        3. Context (what's happening?)
        4. Reasoning (what would I do?)
        """
        
        # Step 1: Retrieve relevant memories if available
        memories = self._retrieve_memories(situation) if self.memory else []
        
        # Step 2: Build reasoning prompt combining all layers
        prompt = self._build_reasoning_prompt(situation, memories)
        
        # Step 3: Query LLM for decision
        response = self._query_llm(prompt)
        
        # Step 4: Parse and structure response
        twin_response = self._parse_llm_response(response, memories)
        
        # Step 5: Log decision for future learning
        self._log_decision(situation, twin_response)
        
        return twin_response
    
    def _retrieve_memories(self, situation: Situation, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories from vector DB based on situation context.
        
        Memories can include:
        - Past similar decisions
        - Relevant personal preferences
        - Communication patterns with specific people
        - Learned behaviors
        """
        if not self.memory:
            return []
        
        # Build search query from situation
        search_query = f"{situation.category}: {situation.context}"
        
        # Add metadata filters if available
        filters = {}
        if situation.metadata.get('sender'):
            filters['person'] = situation.metadata['sender']
        if situation.category:
            filters['category'] = situation.category
        
        # Retrieve from vector DB (abstract interface)
        memories = self.memory.search(
            query=search_query,
            k=k,
            filters=filters
        )
        
        return memories
    
    def _build_reasoning_prompt(self, situation: Situation, memories: List[Dict[str, Any]]) -> str:
        """
        Construct the reasoning prompt that combines:
        - Identity/persona
        - Current situation
        - Relevant memories
        - Decision framework
        """
        
        # Extract key persona elements
        traits = ", ".join(self.persona.get("traits", []))
        values = ", ".join(self.persona.get("values", []))
        comm_style = self.persona.get("communication_style", {})
        
        # Format memories if available
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant memories and past behaviors:\n"
            for i, mem in enumerate(memories, 1):
                memory_context += f"{i}. {mem.get('content', '')} [Relevance: {mem.get('score', 0):.2f}]\n"
        
        # Build comprehensive prompt
        prompt = f"""You are modeling the decision-making of a person with the following identity:

IDENTITY:
- Name: {self.persona.get('name', 'User')}
- Core traits: {traits}
- Values: {values}
- Communication style: {json.dumps(comm_style, indent=2)}

CURRENT SITUATION:
Category: {situation.category}
Context: {situation.context}
Metadata: {json.dumps(situation.metadata, indent=2)}
Timestamp: {situation.timestamp}
{memory_context}

TASK:
Based on this person's identity, memories, and the current situation, determine:
1. What action they would most likely take
2. Their reasoning process
3. Confidence level (0-1)
4. Alternative actions they might consider

Respond in JSON format:
{{
    "action": "specific action they would take",
    "reasoning": "why this action aligns with their identity and past behavior",
    "confidence": 0.0-1.0,
    "alternatives": ["other possible action 1", "other possible action 2"]
}}

Think step by step, considering their values, communication style, and any relevant past behaviors."""
        
        return prompt
    
    def _query_llm(self, prompt: str) -> str:
        """Send prompt to LLM and get response"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are simulating the decision-making process of a specific individual based on their identity and history."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Some variability but mostly consistent
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM query error: {e}")
            return json.dumps({
                "action": "unable to decide",
                "reasoning": f"Error querying LLM: {str(e)}",
                "confidence": 0.0,
                "alternatives": []
            })
    
    def _parse_llm_response(self, response: str, memories: List[Dict[str, Any]]) -> TwinResponse:
        """Parse LLM response into structured TwinResponse"""
        try:
            data = json.loads(response)
            
            # Extract memory references if memories were used
            memory_refs = []
            if memories:
                memory_refs = [mem.get('id', f"memory_{i}") for i, mem in enumerate(memories)]
            
            return TwinResponse(
                action=data.get("action", "no action"),
                reasoning=data.get("reasoning", ""),
                confidence=float(data.get("confidence", 0.5)),
                alternatives=data.get("alternatives", []),
                memory_references=memory_refs
            )
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return TwinResponse(
                action="parse error",
                reasoning=f"Failed to parse response: {str(e)}",
                confidence=0.0
            )
    
    def _log_decision(self, situation: Situation, response: TwinResponse):
        """Log decision for future learning and pattern recognition"""
        decision_log = {
            "timestamp": situation.timestamp.isoformat(),
            "situation": {
                "context": situation.context,
                "category": situation.category,
                "metadata": situation.metadata
            },
            "response": {
                "action": response.action,
                "reasoning": response.reasoning,
                "confidence": response.confidence
            }
        }
        self.decision_history.append(decision_log)
        
        # TODO: Persist to disk or database for long-term learning
    
    def learn_from_feedback(self, situation: Situation, actual_action: str, feedback: str = None):
        """
        Learn from what actually happened vs. what was predicted.
        This is crucial for the twin to improve over time.
        """
        # Find the corresponding prediction in history
        # Compare with actual action
        # Store this correction for future memory
        
        learning_entry = {
            "situation": situation,
            "predicted": self.decision_history[-1] if self.decision_history else None,
            "actual": actual_action,
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        # Store in memory if available
        if self.memory:
            self.memory.add(
                content=f"Learned behavior: In situation '{situation.context}', actually did '{actual_action}' instead of predicted action",
                metadata={
                    "type": "behavior_correction",
                    "category": situation.category,
                    **situation.metadata
                }
            )
        
        return learning_entry
    
    def shadow_mode(self, enabled: bool = True):
        """
        Enable shadow mode where the twin observes but doesn't act.
        Useful for initial learning phase.
        """
        self.is_shadow_mode = enabled
        return f"Shadow mode {'enabled' if enabled else 'disabled'}"