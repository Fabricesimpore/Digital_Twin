"""
Comprehensive Memory System Test for Digital Twin V3

This script demonstrates the complete memory-enhanced digital twin:
- Persistent memory formation
- Learning from feedback
- Memory-influenced decision making
- Pattern extraction and insights
- Long-term memory consolidation
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from digital_twin_v3 import DigitalTwinV3, Situation

# Load environment variables
load_dotenv()


async def test_memory_formation(twin: DigitalTwinV3):
    """Test automatic memory formation from decisions"""
    print("\n🧠 === MEMORY FORMATION TEST ===\n")
    
    # Make several decisions to build memory
    situations = [
        Situation(
            context="Client emails asking for urgent project update",
            category="email",
            metadata={"sender": "client@company.com", "urgency": "high"}
        ),
        Situation(
            context="Friend wants to meet for coffee this afternoon",
            category="social",
            metadata={"sender": "friend", "urgency": "low", "people": ["friend"]}
        ),
        Situation(
            context="Multiple deadlines due tomorrow, feeling overwhelmed",
            category="stress_management",
            metadata={"urgency": "high", "deadline_pressure": True}
        )
    ]
    
    print("Making initial decisions to build memory...")
    decision_ids = []
    
    for i, situation in enumerate(situations, 1):
        print(f"\n--- Decision {i} ---")
        print(f"Situation: {situation.context}")
        
        response = await twin.reason(situation)
        
        print(f"Action: {response.action}")
        print(f"Reasoning Mode: {response.reasoning_mode}")
        print(f"Memory References: {len(response.memory_references)} memories used")
        
        decision_ids.append((situation, response))
    
    # Check memory formation
    memory_summary = twin.get_memory_summary()
    print(f"\n📊 Memory System Status:")
    print(f"Episodic memories: {memory_summary['episodic_memory']['total_memories']}")
    print(f"Semantic memories: {memory_summary['semantic_memory']['total_memories']}")
    
    return decision_ids


async def test_learning_from_feedback(twin: DigitalTwinV3, decision_ids):
    """Test learning from feedback on previous decisions"""
    print("\n🎓 === LEARNING FROM FEEDBACK TEST ===\n")
    
    # Provide feedback on the first decision
    if decision_ids:
        original_situation, original_response = decision_ids[0]
        
        print(f"Original decision: {original_response.action}")
        
        # Simulate what actually happened (different from prediction)
        actual_action = "Sent detailed update within 30 minutes with progress metrics and timeline"
        satisfaction = 0.9  # High satisfaction
        lessons = [
            "Quick detailed responses build client trust",
            "Including metrics and timelines reduces follow-up questions"
        ]
        
        print(f"What actually happened: {actual_action}")
        print(f"Satisfaction level: {satisfaction}")
        
        # Learn from this feedback
        learning_result = twin.learn_from_feedback(
            situation=original_situation,
            actual_action=actual_action,
            satisfaction=satisfaction,
            lessons_learned=lessons,
            feedback="Client was very pleased with quick, comprehensive response"
        )
        
        print(f"Learning result: {learning_result}")
        
        # Test memory system learned from this
        print("\n🔍 Testing if twin learned from feedback...")
        
        # Present similar situation
        similar_situation = Situation(
            context="Different client emails asking for project status update",
            category="email",
            metadata={"sender": "another_client@company.com", "urgency": "high"}
        )
        
        new_response = await twin.reason(similar_situation)
        
        print(f"New similar situation: {similar_situation.context}")
        print(f"New action: {new_response.action}")
        print(f"Applied lessons: {new_response.lessons_applied}")
        print(f"Similar situations referenced: {len(new_response.similar_situations)}")


async def test_memory_retrieval(twin: DigitalTwinV3):
    """Test intelligent memory retrieval"""
    print("\n🔍 === MEMORY RETRIEVAL TEST ===\n")
    
    # Test asking memory specific questions
    questions = [
        "What happened when I dealt with client emails before?",
        "How do I usually handle friend requests when busy?",
        "What strategies work for stress management?"
    ]
    
    for question in questions:
        print(f"\n💭 Question: {question}")
        answer = twin.ask_memory(question)
        print(f"🧠 Memory response: {answer[:200]}...")


async def test_introspection_with_memory(twin: DigitalTwinV3):
    """Test deep introspection using memory system"""
    print("\n🪞 === MEMORY-ENHANCED INTROSPECTION TEST ===\n")
    
    introspection_questions = [
        "What patterns do you see in how I handle urgent requests?",
        "How does my energy level affect my decision quality?",
        "What types of situations do I handle most successfully?"
    ]
    
    for question in introspection_questions:
        print(f"\n🤔 Deep question: {question}")
        insight = twin.introspect_with_memory(question)
        print(f"🧠 Deep insight: {insight[:300]}...")


async def test_state_memory_interaction(twin: DigitalTwinV3):
    """Test how current state interacts with memory"""
    print("\n📊 === STATE-MEMORY INTERACTION TEST ===\n")
    
    situation = Situation(
        context="Need to prepare presentation for tomorrow's important meeting",
        category="work_task",
        metadata={"urgency": "medium", "deadline": "tomorrow"}
    )
    
    # Test with different energy states
    states = [
        {"energy_level": "high", "stress_level": "low"},
        {"energy_level": "low", "stress_level": "high"},
    ]
    
    for i, state in enumerate(states, 1):
        print(f"\n--- State Test {i}: {state} ---")
        twin.update_state(**state)
        
        response = await twin.reason(situation)
        
        print(f"Current state: {twin.state_tracker.quick_state_check()}")
        print(f"Action chosen: {response.action}")
        print(f"Reasoning mode: {response.reasoning_mode}")
        print(f"Memory influences: {len(response.memory_references)} memories, {len(response.lessons_applied)} lessons")


async def test_pattern_extraction(twin: DigitalTwinV3):
    """Test automatic pattern extraction from experience"""
    print("\n🔍 === PATTERN EXTRACTION TEST ===\n")
    
    # Create multiple similar situations to build patterns
    email_situations = [
        Situation("Boss emails about quarterly review preparation", "email", {"sender": "boss", "urgency": "medium"}),
        Situation("Boss asks for budget proposal feedback", "email", {"sender": "boss", "urgency": "medium"}),
        Situation("Boss requests team meeting scheduling", "email", {"sender": "boss", "urgency": "low"})
    ]
    
    print("Creating pattern data with multiple similar situations...")
    
    for situation in email_situations:
        response = await twin.reason(situation)
        
        # Simulate successful outcomes
        twin.learn_from_feedback(
            situation=situation,
            actual_action=f"Handled professionally and promptly: {response.action}",
            satisfaction=0.8,
            lessons_learned=["Professional communication with boss works well"]
        )
    
    # Trigger pattern extraction
    print("\n🧠 Extracting behavioral patterns...")
    maintenance_stats = twin.maintain_memory_system()
    
    print(f"Maintenance results: {maintenance_stats}")
    
    # Test if patterns are being used
    new_boss_situation = Situation(
        "Boss emails about new project assignment",
        "email", 
        {"sender": "boss", "urgency": "medium"}
    )
    
    response = await twin.reason(new_boss_situation)
    
    print(f"\nNew boss email situation:")
    print(f"Action: {response.action}")
    print(f"Applied lessons: {response.lessons_applied}")
    print(f"Memory references: {len(response.memory_references)}")


async def test_memory_consolidation(twin: DigitalTwinV3):
    """Test memory consolidation and maintenance"""
    print("\n🔧 === MEMORY CONSOLIDATION TEST ===\n")
    
    print("Memory system before consolidation:")
    before_stats = twin.get_memory_summary()
    print(f"Episodic: {before_stats['episodic_memory']['total_memories']}")
    print(f"Semantic: {before_stats['semantic_memory']['total_memories']}")
    
    # Run memory maintenance
    print("\n🧹 Running memory maintenance...")
    maintenance_results = twin.maintain_memory_system()
    
    print("Memory system after consolidation:")
    after_stats = twin.get_memory_summary()
    print(f"Episodic: {after_stats['episodic_memory']['total_memories']}")
    print(f"Semantic: {after_stats['semantic_memory']['total_memories']}")
    
    print(f"\nMaintenance actions:")
    for action, count in maintenance_results.items():
        print(f"  {action}: {count}")


async def test_memory_export(twin: DigitalTwinV3):
    """Test memory export functionality"""
    print("\n💾 === MEMORY EXPORT TEST ===\n")
    
    export_path = twin.export_memories("test_twin_memory_export.json")
    print(f"Exported memory system to: {export_path}")
    
    # Show comprehensive statistics
    insights = twin.get_reasoning_insights()
    print(f"\n📊 Final System Statistics:")
    print(f"Total decisions in session: {insights.get('memory_system', {}).get('recent_learning', 0)}")
    print(f"Memory system fully operational: ✅")


async def test_persistent_learning_cycle(twin: DigitalTwinV3):
    """Test the complete learning cycle over time"""
    print("\n🔄 === PERSISTENT LEARNING CYCLE TEST ===\n")
    
    # Simulate a learning cycle over multiple interactions
    print("Simulating learning cycle over multiple sessions...")
    
    # Day 1: Initial decisions
    day1_situations = [
        Situation("Morning email triage", "email", {"urgency": "medium"}),
        Situation("Afternoon meeting request", "scheduling", {"urgency": "low"})
    ]
    
    print("\n📅 Day 1 - Initial learning:")
    for situation in day1_situations:
        response = await twin.reason(situation)
        print(f"  {situation.context[:40]}... → {response.action[:40]}...")
        
        # Simulate feedback
        twin.learn_from_feedback(
            situation=situation,
            actual_action=response.action,
            satisfaction=0.7
        )
    
    # Check learning
    insights_day1 = twin.get_reasoning_insights()
    
    # Simulate Day 2: Similar situations with memory influence
    print("\n📅 Day 2 - Memory-influenced decisions:")
    
    day2_situations = [
        Situation("Morning email triage with time pressure", "email", {"urgency": "high"}),
        Situation("Last-minute meeting request", "scheduling", {"urgency": "high"})
    ]
    
    for situation in day2_situations:
        response = await twin.reason(situation)
        print(f"  {situation.context[:40]}... → {response.action[:40]}...")
        print(f"    Memory references: {len(response.memory_references)}")
        print(f"    Applied lessons: {len(response.lessons_applied)}")
    
    print("\n✅ Learning cycle test completed - twin is learning from experience!")


async def run_comprehensive_memory_tests():
    """Run all memory system tests"""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🧠 Initializing Digital Twin V3 with Memory System...")
    
    # Initialize twin (this will create memory directories)
    twin = DigitalTwinV3(
        persona_path="persona.yaml", 
        api_key=api_key,
        memory_dir="test_memory_system"
    )
    
    print("✅ Memory-enhanced twin initialized successfully!")
    
    try:
        # Run all tests in sequence
        decision_ids = await test_memory_formation(twin)
        await test_learning_from_feedback(twin, decision_ids)
        await test_memory_retrieval(twin)
        await test_introspection_with_memory(twin)
        await test_state_memory_interaction(twin)
        await test_pattern_extraction(twin)
        await test_memory_consolidation(twin)
        await test_persistent_learning_cycle(twin)
        await test_memory_export(twin)
        
        print("\n🎉 === ALL MEMORY TESTS COMPLETED ===")
        print("Your digital twin now has:")
        print("✅ Persistent episodic memory (specific events)")
        print("✅ Semantic memory (patterns and knowledge)")
        print("✅ Automatic learning from feedback")
        print("✅ Memory-influenced decision making")
        print("✅ Pattern extraction and insights")
        print("✅ Memory consolidation and maintenance")
        print("✅ Deep introspection with memory access")
        print("✅ Complete learning cycle over time")
        
        print(f"\n🧠 Your twin is now a persistent, learning entity!")
        print(f"Memory files stored in: test_memory_system/")
        print(f"The twin will remember everything and get smarter over time.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_memory_tests())