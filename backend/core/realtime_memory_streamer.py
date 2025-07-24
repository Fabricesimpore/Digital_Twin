"""
Real-time Memory Streaming System - Continuously updates twin's memory
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json
import threading
from queue import Queue, Empty
from pathlib import Path
import time


class MemoryUpdate:
    """Represents a memory update"""
    
    def __init__(self, update_type: str, data: Dict[str, Any], source: str):
        self.update_type = update_type  # episodic, semantic, procedural
        self.data = data
        self.source = source  # email, calendar, action, etc
        self.timestamp = datetime.now()
        self.processed = False
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'update_type': self.update_type,
            'data': self.data,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed
        }


class MemoryStreamer:
    """Streams real-time updates to twin's memory systems"""
    
    def __init__(self, memory_systems: Optional[Dict[str, Any]] = None):
        """
        Initialize with memory systems
        
        Args:
            memory_systems: Dict with keys:
                - episodic: EpisodicMemory instance
                - semantic: SemanticMemory instance
                - procedural: ProceduralMemory instance
        """
        self.memory_systems = memory_systems or {}
        
        # Update queue
        self.update_queue: Queue = Queue()
        
        # Processing stats
        self.processed_count = 0
        self.error_count = 0
        self.last_update_time = None
        
        # Background processor
        self.running = False
        self.processor_thread = None
        
        # Batch settings
        self.batch_size = 10
        self.batch_timeout = 5.0  # seconds
        
        # Persistence
        self.buffer_path = Path("backend/data/memory_buffer.json")
        self.buffer_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Callbacks for different update types
        self.update_handlers: Dict[str, List[Callable]] = {
            'episodic': [],
            'semantic': [],
            'procedural': []
        }
        
        # Load any buffered updates
        self._load_buffer()
    
    def start(self):
        """Start the memory streamer"""
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()
        print("Memory streamer started")
    
    def stop(self):
        """Stop the memory streamer"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5.0)
        self._save_buffer()
        print(f"Memory streamer stopped. Processed {self.processed_count} updates")
    
    def add_update(self, update_type: str, data: Dict[str, Any], source: str):
        """
        Add a memory update to the queue
        
        Args:
            update_type: Type of memory update (episodic, semantic, procedural)
            data: Update data
            source: Source of the update
        """
        update = MemoryUpdate(update_type, data, source)
        self.update_queue.put(update)
    
    def add_episodic_memory(self, event: Dict[str, Any], source: str):
        """Add an episodic memory update"""
        self.add_update('episodic', event, source)
    
    def add_semantic_fact(self, fact: Dict[str, Any], source: str):
        """Add a semantic memory update"""
        self.add_update('semantic', fact, source)
    
    def add_procedural_pattern(self, pattern: Dict[str, Any], source: str):
        """Add a procedural memory update"""
        self.add_update('procedural', pattern, source)
    
    def register_handler(self, update_type: str, handler: Callable):
        """Register a callback for memory updates"""
        if update_type in self.update_handlers:
            self.update_handlers[update_type].append(handler)
    
    def _process_loop(self):
        """Background processing loop"""
        batch = []
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Collect updates for batch processing
                timeout = 0.1  # Small timeout for responsiveness
                
                try:
                    update = self.update_queue.get(timeout=timeout)
                    batch.append(update)
                except Empty:
                    pass
                
                # Process batch if ready
                current_time = time.time()
                should_process = (
                    len(batch) >= self.batch_size or
                    (len(batch) > 0 and current_time - last_batch_time > self.batch_timeout)
                )
                
                if should_process and batch:
                    self._process_batch(batch)
                    batch = []
                    last_batch_time = current_time
                    
            except Exception as e:
                print(f"Error in memory processor: {e}")
                self.error_count += 1
        
        # Process any remaining updates
        if batch:
            self._process_batch(batch)
    
    def _process_batch(self, batch: List[MemoryUpdate]):
        """Process a batch of memory updates"""
        episodic_updates = []
        semantic_updates = []
        procedural_updates = []
        
        # Group updates by type
        for update in batch:
            if update.update_type == 'episodic':
                episodic_updates.append(update)
            elif update.update_type == 'semantic':
                semantic_updates.append(update)
            elif update.update_type == 'procedural':
                procedural_updates.append(update)
        
        # Process each type
        if episodic_updates:
            self._process_episodic_batch(episodic_updates)
        if semantic_updates:
            self._process_semantic_batch(semantic_updates)
        if procedural_updates:
            self._process_procedural_batch(procedural_updates)
        
        # Update stats
        self.processed_count += len(batch)
        self.last_update_time = datetime.now()
        
        # Mark as processed
        for update in batch:
            update.processed = True
    
    def _process_episodic_batch(self, updates: List[MemoryUpdate]):
        """Process episodic memory updates"""
        if 'episodic' in self.memory_systems and self.memory_systems['episodic']:
            memory = self.memory_systems['episodic']
            
            for update in updates:
                try:
                    # Store the episodic memory
                    event_data = update.data
                    memory.store_memory(
                        event_type=event_data.get('type', 'unknown'),
                        content=event_data.get('content', {}),
                        participants=event_data.get('participants', []),
                        outcome=event_data.get('outcome', 'unknown'),
                        metadata={
                            'source': update.source,
                            'timestamp': update.timestamp.isoformat()
                        }
                    )
                except Exception as e:
                    print(f"Error storing episodic memory: {e}")
                    self.error_count += 1
        
        # Call registered handlers
        for handler in self.update_handlers['episodic']:
            try:
                handler(updates)
            except Exception as e:
                print(f"Error in episodic handler: {e}")
    
    def _process_semantic_batch(self, updates: List[MemoryUpdate]):
        """Process semantic memory updates"""
        if 'semantic' in self.memory_systems and self.memory_systems['semantic']:
            memory = self.memory_systems['semantic']
            
            for update in updates:
                try:
                    # Learn the semantic fact
                    fact_data = update.data
                    memory.learn_fact(
                        subject=fact_data.get('subject', 'unknown'),
                        predicate=fact_data.get('predicate', 'is'),
                        object=fact_data.get('object', 'unknown'),
                        confidence=fact_data.get('confidence', 0.8),
                        source=update.source,
                        metadata={
                            'timestamp': update.timestamp.isoformat()
                        }
                    )
                except Exception as e:
                    print(f"Error storing semantic memory: {e}")
                    self.error_count += 1
        
        # Call registered handlers
        for handler in self.update_handlers['semantic']:
            try:
                handler(updates)
            except Exception as e:
                print(f"Error in semantic handler: {e}")
    
    def _process_procedural_batch(self, updates: List[MemoryUpdate]):
        """Process procedural memory updates"""
        if 'procedural' in self.memory_systems and self.memory_systems['procedural']:
            memory = self.memory_systems['procedural']
            
            for update in updates:
                try:
                    # Learn the procedural pattern
                    pattern_data = update.data
                    memory.learn_pattern(
                        trigger=pattern_data.get('trigger', {}),
                        action=pattern_data.get('action', {}),
                        outcome=pattern_data.get('outcome', {}),
                        success=pattern_data.get('success', True)
                    )
                except Exception as e:
                    print(f"Error storing procedural memory: {e}")
                    self.error_count += 1
        
        # Call registered handlers
        for handler in self.update_handlers['procedural']:
            try:
                handler(updates)
            except Exception as e:
                print(f"Error in procedural handler: {e}")
    
    def _save_buffer(self):
        """Save unprocessed updates to disk"""
        try:
            # Get all unprocessed updates
            buffer = []
            while not self.update_queue.empty():
                try:
                    update = self.update_queue.get_nowait()
                    buffer.append(update.to_dict())
                except Empty:
                    break
            
            # Save to file
            if buffer:
                with open(self.buffer_path, 'w') as f:
                    json.dump(buffer, f, indent=2)
                print(f"Saved {len(buffer)} updates to buffer")
        except Exception as e:
            print(f"Error saving memory buffer: {e}")
    
    def _load_buffer(self):
        """Load buffered updates from disk"""
        try:
            if self.buffer_path.exists():
                with open(self.buffer_path, 'r') as f:
                    buffer = json.load(f)
                
                # Re-queue updates
                for data in buffer:
                    update = MemoryUpdate(
                        update_type=data['update_type'],
                        data=data['data'],
                        source=data['source']
                    )
                    update.timestamp = datetime.fromisoformat(data['timestamp'])
                    self.update_queue.put(update)
                
                print(f"Loaded {len(buffer)} updates from buffer")
                
                # Clear buffer file
                self.buffer_path.unlink()
        except Exception as e:
            print(f"Error loading memory buffer: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'queue_size': self.update_queue.qsize(),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'is_running': self.running
        }


class RealTimeObserver:
    """Observes various sources and streams updates to memory"""
    
    def __init__(self, memory_streamer: MemoryStreamer):
        self.memory_streamer = memory_streamer
        self.observers = []
    
    def observe_email(self, email_data: Dict[str, Any]):
        """Observe email events"""
        # Extract episodic memory
        self.memory_streamer.add_episodic_memory({
            'type': 'email_received',
            'content': {
                'from': email_data.get('from'),
                'subject': email_data.get('subject'),
                'body': email_data.get('body', '')[:500],  # Truncate
                'timestamp': email_data.get('timestamp')
            },
            'participants': [email_data.get('from'), 'self'],
            'outcome': 'pending_response'
        }, source='email')
        
        # Extract semantic facts
        if 'important' in email_data.get('subject', '').lower():
            self.memory_streamer.add_semantic_fact({
                'subject': email_data.get('from'),
                'predicate': 'sends_important_emails',
                'object': 'true',
                'confidence': 0.9
            }, source='email')
    
    def observe_calendar(self, event_data: Dict[str, Any]):
        """Observe calendar events"""
        self.memory_streamer.add_episodic_memory({
            'type': 'calendar_event',
            'content': {
                'title': event_data.get('title'),
                'start': event_data.get('start'),
                'end': event_data.get('end'),
                'attendees': event_data.get('attendees', [])
            },
            'participants': event_data.get('attendees', []),
            'outcome': 'scheduled'
        }, source='calendar')
    
    def observe_action(self, action_data: Dict[str, Any]):
        """Observe actions taken"""
        # Track the action as episodic memory
        self.memory_streamer.add_episodic_memory({
            'type': f"action_{action_data.get('type')}",
            'content': action_data,
            'participants': [action_data.get('target', 'unknown')],
            'outcome': action_data.get('result', 'unknown')
        }, source='action')
        
        # Learn patterns from successful actions
        if action_data.get('success', False):
            self.memory_streamer.add_procedural_pattern({
                'trigger': action_data.get('trigger', {}),
                'action': {
                    'type': action_data.get('type'),
                    'parameters': action_data.get('parameters', {})
                },
                'outcome': action_data.get('result'),
                'success': True
            }, source='action')


if __name__ == "__main__":
    # Example usage
    import time
    
    # Create memory streamer
    streamer = MemoryStreamer()
    streamer.start()
    
    # Create observer
    observer = RealTimeObserver(streamer)
    
    # Simulate some events
    observer.observe_email({
        'from': 'boss@company.com',
        'subject': 'Important: Q4 Review',
        'body': 'Please prepare the Q4 review presentation',
        'timestamp': datetime.now().isoformat()
    })
    
    observer.observe_calendar({
        'title': 'Q4 Review Meeting',
        'start': '2024-01-15T14:00:00',
        'end': '2024-01-15T15:00:00',
        'attendees': ['boss@company.com', 'team@company.com']
    })
    
    observer.observe_action({
        'type': 'task_create',
        'target': 'self',
        'parameters': {'title': 'Prepare Q4 review presentation'},
        'trigger': {'source': 'email', 'from': 'boss@company.com'},
        'result': 'task_created',
        'success': True
    })
    
    # Let it process
    time.sleep(2)
    
    # Check stats
    stats = streamer.get_stats()
    print(f"Memory streamer stats: {json.dumps(stats, indent=2)}")
    
    # Stop
    streamer.stop()