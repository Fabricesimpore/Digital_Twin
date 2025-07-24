"""
Test script for the Digital Twin brain module.

This script simulates various real-world situations to test how the digital twin
reasons and makes decisions based on the configured persona.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from digital_twin import DigitalTwin, Situation

# Load environment variables
load_dotenv()


def test_email_scenarios(twin: DigitalTwin):
    """Test email-related decision making"""
    print("\n=== EMAIL SCENARIOS ===\n")
    
    # Scenario 1: Urgent client email
    situation1 = Situation(
        context="Client emails about a critical bug in production that's affecting their customers. They seem stressed and need immediate help.",
        category="email",
        metadata={
            "sender": "important_client@company.com",
            "subject": "URGENT: Production issue affecting customers",
            "urgency": "high",
            "time_received": "9:00 AM"
        }
    )
    
    print("Scenario 1: Urgent client email")
    print(f"Context: {situation1.context}")
    response1 = twin.reason(situation1)
    print(f"Twin would: {response1.action}")
    print(f"Reasoning: {response1.reasoning}")
    print(f"Confidence: {response1.confidence:.2f}")
    print(f"Alternatives: {response1.alternatives}")
    print("-" * 50)
    
    # Scenario 2: Meeting request conflict
    situation2 = Situation(
        context="Colleague wants to schedule a brainstorming meeting at 3 PM, but you already have a personal commitment (gym/family time) blocked on your calendar.",
        category="email",
        metadata={
            "sender": "colleague@company.com",
            "subject": "Brainstorming session today?",
            "urgency": "medium",
            "conflict_type": "personal_time"
        }
    )
    
    print("\nScenario 2: Meeting conflict with personal time")
    print(f"Context: {situation2.context}")
    response2 = twin.reason(situation2)
    print(f"Twin would: {response2.action}")
    print(f"Reasoning: {response2.reasoning}")
    print(f"Confidence: {response2.confidence:.2f}")
    print("-" * 50)
    
    # Scenario 3: Newsletter/Low priority
    situation3 = Situation(
        context="Daily newsletter from a tech blog you're subscribed to, featuring articles about AI and productivity tools.",
        category="email",
        metadata={
            "sender": "newsletter@techblog.com",
            "subject": "Daily Digest: AI Tools for Productivity",
            "urgency": "low",
            "type": "newsletter"
        }
    )
    
    print("\nScenario 3: Newsletter/Low priority email")
    print(f"Context: {situation3.context}")
    response3 = twin.reason(situation3)
    print(f"Twin would: {response3.action}")
    print(f"Reasoning: {response3.reasoning}")
    print(f"Confidence: {response3.confidence:.2f}")
    print("-" * 50)


def test_task_prioritization(twin: DigitalTwin):
    """Test task prioritization decisions"""
    print("\n=== TASK PRIORITIZATION ===\n")
    
    situation = Situation(
        context="It's Monday morning. You have: 1) Finish code review (2 hrs), 2) Prepare presentation for tomorrow (3 hrs), 3) Respond to 5 emails (30 min), 4) Learn new framework from tutorial (2 hrs). How would you prioritize?",
        category="task_management",
        metadata={
            "time_available": "8 hours",
            "day": "Monday",
            "deadlines": {
                "presentation": "tomorrow",
                "code_review": "end of day",
                "emails": "no deadline",
                "learning": "no deadline"
            }
        }
    )
    
    print(f"Context: {situation.context}")
    response = twin.reason(situation)
    print(f"Twin would: {response.action}")
    print(f"Reasoning: {response.reasoning}")
    print(f"Confidence: {response.confidence:.2f}")
    print("-" * 50)


def test_social_scenarios(twin: DigitalTwin):
    """Test social and communication decisions"""
    print("\n=== SOCIAL SCENARIOS ===\n")
    
    # WhatsApp scenario
    situation1 = Situation(
        context="Friend messages on WhatsApp asking if you want to grab coffee this afternoon. You have work to finish but haven't seen them in 2 weeks.",
        category="social_message",
        metadata={
            "platform": "WhatsApp",
            "sender": "close_friend",
            "last_interaction": "2 weeks ago",
            "current_workload": "high"
        }
    )
    
    print("Scenario: Friend wants to meet")
    print(f"Context: {situation1.context}")
    response1 = twin.reason(situation1)
    print(f"Twin would: {response1.action}")
    print(f"Reasoning: {response1.reasoning}")
    print(f"Confidence: {response1.confidence:.2f}")
    print("-" * 50)
    
    # Professional networking
    situation2 = Situation(
        context="LinkedIn connection requests to connect and 'explore potential synergies'. They work at a company in your field but you don't know them personally.",
        category="social_message",
        metadata={
            "platform": "LinkedIn",
            "sender_type": "unknown_professional",
            "message_type": "generic_networking",
            "industry_relevant": True
        }
    )
    
    print("\nScenario: LinkedIn networking request")
    print(f"Context: {situation2.context}")
    response2 = twin.reason(situation2)
    print(f"Twin would: {response2.action}")
    print(f"Reasoning: {response2.reasoning}")
    print(f"Confidence: {response2.confidence:.2f}")
    print("-" * 50)


def test_learning_decisions(twin: DigitalTwin):
    """Test learning and content consumption decisions"""
    print("\n=== LEARNING & CONTENT DECISIONS ===\n")
    
    situation = Situation(
        context="You have 1 hour free. Options: 1) Watch Ali Abdaal's new productivity video (20 min), 2) Read 2 chapters of business book, 3) Try that new coding framework, 4) Scroll Twitter/Reddit.",
        category="learning_decision",
        metadata={
            "time_available": "1 hour",
            "energy_level": "medium",
            "options": {
                "video": "productivity content from preferred creator",
                "book": "continuing business strategy book",
                "coding": "hands-on learning",
                "social": "passive consumption"
            }
        }
    )
    
    print(f"Context: {situation.context}")
    response = twin.reason(situation)
    print(f"Twin would: {response.action}")
    print(f"Reasoning: {response.reasoning}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Alternatives: {response.alternatives}")
    print("-" * 50)


def test_stress_scenario(twin: DigitalTwin):
    """Test decision making under stress"""
    print("\n=== STRESS SCENARIO ===\n")
    
    situation = Situation(
        context="It's 4 PM, you have 3 deadlines tomorrow, 2 urgent emails to respond to, and your manager just asked for a 'quick call'. You're feeling overwhelmed.",
        category="stress_management",
        metadata={
            "stress_level": "high",
            "pending_tasks": ["3 project deadlines", "2 urgent emails", "manager call"],
            "time_of_day": "4 PM",
            "energy_level": "low"
        }
    )
    
    print(f"Context: {situation.context}")
    response = twin.reason(situation)
    print(f"Twin would: {response.action}")
    print(f"Reasoning: {response.reasoning}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Alternatives: {response.alternatives}")
    print("-" * 50)


def test_learning_from_feedback(twin: DigitalTwin):
    """Test the learning mechanism"""
    print("\n=== LEARNING FROM FEEDBACK ===\n")
    
    # Create a situation
    situation = Situation(
        context="Boss emails asking for project update by end of day",
        category="email",
        metadata={
            "sender": "boss@company.com",
            "urgency": "high"
        }
    )
    
    # Get twin's prediction
    print("Twin predicts...")
    response = twin.reason(situation)
    print(f"Predicted action: {response.action}")
    
    # Simulate what actually happened
    actual_action = "Sent detailed update within 1 hour with progress metrics and next steps"
    
    # Learn from the difference
    print(f"\nActual action taken: {actual_action}")
    learning = twin.learn_from_feedback(
        situation=situation,
        actual_action=actual_action,
        feedback="Boss appreciated the quick, detailed response with metrics"
    )
    
    print("Twin has learned from this interaction.")
    print("-" * 50)


def run_all_tests():
    """Run all test scenarios"""
    # Initialize the digital twin
    # Note: You'll need to set your OpenAI API key as environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    print("Initializing Digital Twin...")
    twin = DigitalTwin(persona_path="persona.yaml", api_key=api_key)
    
    # Enable shadow mode for testing
    print(twin.shadow_mode(enabled=True))
    
    # Run all test scenarios
    test_email_scenarios(twin)
    test_task_prioritization(twin)
    test_social_scenarios(twin)
    test_learning_decisions(twin)
    test_stress_scenario(twin)
    test_learning_from_feedback(twin)
    
    print("\n=== TEST SUMMARY ===")
    print(f"Total decisions made: {len(twin.decision_history)}")
    print("Review the responses to see if they align with your actual behavior.")
    print("Update persona.yaml to better match your patterns.")


if __name__ == "__main__":
    run_all_tests()