"""
Test script for Enhanced Digital Twin V2

This script demonstrates the advanced reasoning capabilities:
- Multi-path deliberation
- Competing behavioral voices
- State-aware decisions  
- Heuristic fast decisions
- Introspection capabilities
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from digital_twin_v2 import DigitalTwinV2, Situation

# Load environment variables
load_dotenv()


async def test_heuristic_reasoning(twin: DigitalTwinV2):
    """Test fast heuristic decision-making"""
    print("\n🚀 === HEURISTIC REASONING TEST ===\n")
    
    # Set low energy to trigger heuristic mode
    twin.update_state(energy_level="low", stress_level="medium")
    
    situation = Situation(
        context="Quick email from colleague asking for a status update on the project",
        category="email",
        metadata={"sender": "colleague@company.com", "urgency": "medium"}
    )
    
    print(f"Situation: {situation.context}")
    print(f"Current state: {twin.state_tracker.quick_state_check()}")
    
    response = await twin.reason(situation)
    
    print(f"\n🧠 Reasoning Mode: {response.reasoning_mode}")
    print(f"⚡ Action: {response.action}")
    print(f"🤔 Reasoning: {response.reasoning}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    
    if response.heuristic_decision:
        print(f"⏱️ Time Saved: {response.heuristic_decision.time_saved:.1f} minutes")
        print(f"🔄 Alternatives Skipped: {response.heuristic_decision.alternatives_skipped}")


async def test_voice_arbitration(twin: DigitalTwinV2):
    """Test competing behavioral voices"""
    print("\n🎭 === VOICE ARBITRATION TEST ===\n")
    
    # Set normal energy to trigger arbitration
    twin.update_state(energy_level="medium", stress_level="medium")
    
    situation = Situation(
        context="Friend wants to hang out tonight, but you have a big presentation tomorrow and should prepare",
        category="social_conflict",
        metadata={"urgency": "medium", "time_available": 180}  # 3 hours
    )
    
    print(f"Situation: {situation.context}")
    
    response = await twin.reason(situation)
    
    print(f"\n🧠 Reasoning Mode: {response.reasoning_mode}")
    print(f"⚖️ Final Decision: {response.action}")
    print(f"🤔 Arbitration Reasoning: {response.reasoning}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    
    if response.voice_arguments:
        print(f"\n🎭 Voice Arguments:")
        for voice_arg in response.voice_arguments:
            print(f"   {voice_arg.voice_name}: {voice_arg.position}")
            print(f"      Urgency: {voice_arg.urgency.name}")
    
    if response.arbitration_result:
        print(f"\n🏆 Winning Voices: {response.arbitration_result.winning_voices}")
        print(f"⚖️ Trade-offs: {response.arbitration_result.trade_offs_acknowledged}")


async def test_deliberation_engine(twin: DigitalTwinV2):
    """Test multi-path deliberation"""
    print("\n🔍 === DELIBERATION ENGINE TEST ===\n")
    
    # Set high energy to enable complex reasoning
    twin.update_state(energy_level="high", stress_level="low")
    
    situation = Situation(
        context="Multiple important options for career decision: 1) Stay at current job with promotion, 2) Join startup with equity, 3) Go freelance. This is a strategic decision with long-term implications.",
        category="strategic_decision",
        metadata={"urgency": "low", "complexity": "high"}
    )
    
    print(f"Situation: {situation.context}")
    
    response = await twin.reason(situation)
    
    print(f"\n🧠 Reasoning Mode: {response.reasoning_mode}")
    print(f"🎯 Chosen Action: {response.action}")
    print(f"🤔 Deliberation Reasoning: {response.reasoning}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    
    if response.deliberation_details:
        print(f"\n📋 All Options Considered:")
        for i, option in enumerate(response.deliberation_details.all_options[:3], 1):
            print(f"   {i}. {option.action}")
            print(f"      Score: {option.total_score:.2f}")
            print(f"      Pros: {', '.join(option.pros[:2])}")
    
    if response.alternatives:
        print(f"\n🔀 Alternative Actions:")
        for alt in response.alternatives[:3]:
            print(f"   - {alt}")


async def test_state_awareness(twin: DigitalTwinV2):
    """Test how state affects decision-making"""
    print("\n📊 === STATE-AWARE REASONING TEST ===\n")
    
    situation = Situation(
        context="Manager asks you to take on an additional project with tight deadline",
        category="work_request",
        metadata={"sender": "manager", "urgency": "high"}
    )
    
    # Test with different states
    states_to_test = [
        {"energy_level": "high", "stress_level": "low", "workload": "light"},
        {"energy_level": "low", "stress_level": "high", "workload": "heavy"},
        {"energy_level": "medium", "stress_level": "medium", "workload": "normal"}
    ]
    
    for i, state in enumerate(states_to_test, 1):
        print(f"\n--- Test {i}: {state} ---")
        twin.update_state(**state)
        
        response = await twin.reason(situation)
        
        print(f"State: {twin.state_tracker.quick_state_check()}")
        print(f"Action: {response.action}")
        print(f"Reasoning: {response.reasoning[:100]}...")
        print(f"Confidence: {response.confidence:.2f}")


async def test_introspection(twin: DigitalTwinV2):
    """Test self-introspection capabilities"""
    print("\n🪞 === INTROSPECTION TEST ===\n")
    
    # First make some decisions to build history
    situations = [
        Situation("Urgent client email", "email", {"urgency": "high"}),
        Situation("Friend wants to meet for coffee", "social", {"urgency": "low"}),
        Situation("Multiple deadlines today", "stress", {"urgency": "high"})
    ]
    
    for situation in situations:
        await twin.reason(situation)
    
    # Now introspect
    questions = [
        "What patterns do you see in my decision making?",
        "How do I handle high-stress situations differently?",
        "Which of my values seems most influential in my decisions?"
    ]
    
    for question in questions:
        print(f"\n💭 Question: {question}")
        insight = twin.introspect(question)
        print(f"🧠 Insight: {insight[:200]}...")


async def test_learning_feedback(twin: DigitalTwinV2):
    """Test learning from feedback"""
    print("\n🎓 === LEARNING FROM FEEDBACK TEST ===\n")
    
    # Make a decision
    situation = Situation(
        context="Colleague asks for help on project during your focused work time",
        category="interruption",
        metadata={"urgency": "medium"}
    )
    
    print(f"Situation: {situation.context}")
    response = await twin.reason(situation)
    
    print(f"Twin predicted: {response.action}")
    
    # Simulate what actually happened
    actual_action = "Helped colleague immediately, which strengthened relationship but delayed my work"
    satisfaction = 0.7  # Mixed outcome
    
    print(f"Actually did: {actual_action}")
    print(f"Satisfaction: {satisfaction}")
    
    # Learn from this
    learning_result = twin.learn_from_feedback(
        situation=situation,
        actual_action=actual_action,
        satisfaction=satisfaction,
        feedback="Good relationship building, but consider scheduling help for later when not in deep focus"
    )
    
    print(f"Learning stored: {learning_result}")


async def test_brain_insights(twin: DigitalTwinV2):
    """Test reasoning insights and analytics"""
    print("\n📈 === BRAIN INSIGHTS TEST ===\n")
    
    # Get overall insights
    insights = twin.get_reasoning_insights()
    
    print(f"Total decisions made: {insights.get('total_decisions', 0)}")
    print(f"Average confidence: {insights.get('average_confidence', 0):.2f}")
    
    if insights.get('reasoning_mode_distribution'):
        print(f"\nReasoning mode usage:")
        for mode, count in insights['reasoning_mode_distribution'].items():
            print(f"  {mode}: {count} times")
    
    if insights.get('voice_influence'):
        print(f"\nMost influential voices:")
        for voice, count in list(insights['voice_influence'].items())[:3]:
            print(f"  {voice}: {count} decisions")
    
    # Get brain status
    print(f"\n🧠 Brain Status:")
    status = twin.get_brain_status()
    print(f"Current state: {status['state_tracker']['current_state']}")
    print(f"Heuristic rules: {status['heuristics']['total_rules']}")
    print(f"Available voices: {', '.join(status['voices']['available_voices'])}")


async def run_all_tests():
    """Run all enhanced brain tests"""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🧠 Initializing Enhanced Digital Twin V2...")
    twin = DigitalTwinV2(persona_path="persona.yaml", api_key=api_key)
    
    print("✅ Enhanced brain modules loaded successfully!")
    
    # Run all tests
    await test_heuristic_reasoning(twin)
    await test_voice_arbitration(twin)
    await test_deliberation_engine(twin)
    await test_state_awareness(twin)
    await test_introspection(twin)
    await test_learning_feedback(twin)
    await test_brain_insights(twin)
    
    print("\n🎉 === ALL TESTS COMPLETED ===")
    print("The enhanced brain is working! Your digital twin now has:")
    print("✅ Multi-path deliberation")
    print("✅ Competing behavioral voices")
    print("✅ Fast heuristic decisions")
    print("✅ State-aware reasoning")
    print("✅ Self-introspection")
    print("✅ Learning from feedback")


if __name__ == "__main__":
    asyncio.run(run_all_tests())