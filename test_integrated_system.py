"""
Comprehensive Test for Integrated Brain + Memory + Controller System

This script demonstrates the complete digital twin system with:
- DigitalTwinV3 (Enhanced Brain with Memory)
- MemoryAwareController (Action orchestration with learning)
- UnifiedTwinDecisionLoop (Complete system integration)
- UniversalActionRegistry (Standardized action definitions)

The test demonstrates:
1. Memory-enhanced reasoning and decision making
2. Action planning and execution with learning
3. Cross-domain action orchestration
4. Continuous learning from feedback
5. System optimization based on patterns
6. Complete workflow: Request → Reasoning → Action → Learning
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from twin_decision_loop import UnifiedTwinDecisionLoop, TwinRequest, TwinResult
from action_registry import global_action_registry, ActionCategory, ActionUrgency
from scheduler import ActionScheduler

# Load environment variables
load_dotenv()


class MockVoiceTool:
    """Mock voice tool for testing"""
    
    def __init__(self):
        self.calls_made = []
    
    async def make_call(self, recipient: str, message_type: str = "general", **kwargs):
        """Mock phone call"""
        call_record = {
            "recipient": recipient,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        self.calls_made.append(call_record)
        
        return {
            "success": True,
            "message": f"Called {recipient} with {message_type} message",
            "duration": 120  # 2 minutes
        }


class MockEmailTool:
    """Mock email tool for testing"""
    
    def __init__(self):
        self.emails_sent = []
    
    async def send_email(self, recipient: str, subject: str, body: str, **kwargs):
        """Mock email sending"""
        email_record = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        self.emails_sent.append(email_record)
        
        return {
            "success": True,
            "message": f"Email sent to {recipient}",
            "message_id": f"msg_{len(self.emails_sent)}"
        }


class MockTaskManager:
    """Mock task management tool for testing"""
    
    def __init__(self):
        self.tasks = []
    
    async def create_task(self, title: str, description: str = "", priority: str = "medium", **kwargs):
        """Mock task creation"""
        task = {
            "id": f"task_{len(self.tasks) + 1}",
            "title": title,
            "description": description,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        self.tasks.append(task)
        
        return {
            "success": True,
            "task_id": task["id"],
            "message": f"Created task: {title}"
        }
    
    async def get_pending_tasks(self, timeframe: str = "today", **kwargs):
        """Mock task retrieval"""
        pending_tasks = [t for t in self.tasks if t["status"] == "pending"]
        
        return {
            "success": True,
            "tasks": pending_tasks,
            "count": len(pending_tasks)
        }


async def test_basic_reasoning_with_memory(twin: UnifiedTwinDecisionLoop):
    """Test basic reasoning capabilities with memory integration"""
    print("\n🧠 === BASIC REASONING WITH MEMORY TEST ===\n")
    
    # Test simple queries that build memory
    queries = [
        "What should I do if I receive an urgent email from my boss?",
        "How should I handle conflicting meeting requests?",
        "What's the best way to manage my daily task priorities?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Question: {query}")
        
        result = await twin.process(
            content=query,
            request_type="query",
            priority="medium"
        )
        
        print(f"Success: {result.success}")
        print(f"Response: {result.response_text[:200]}...")
        print(f"Memory updates: {result.memory_updates}")
        print(f"Lessons applied: {len(result.lessons_learned)}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        # Provide feedback to improve learning
        await twin.provide_feedback(
            request_id=result.request_id,
            satisfaction=0.8,
            lessons_learned=[f"Query type '{query[:20]}...' handled well"],
            feedback_text="Good reasoning depth and practical advice"
        )


async def test_action_planning_and_execution(twin: UnifiedTwinDecisionLoop):
    """Test action planning and execution with learning"""
    print("\n⚡ === ACTION PLANNING AND EXECUTION TEST ===\n")
    
    # Test various action requests
    action_requests = [
        {
            "request": "Send an email to john@example.com about the project status update",
            "type": "action",
            "priority": "high"
        },
        {
            "request": "Create a task to review quarterly reports by Friday",
            "type": "action", 
            "priority": "medium"
        },
        {
            "request": "Call me at 3:30 PM to remind me about the team meeting",
            "type": "schedule",
            "priority": "normal"
        }
    ]
    
    for i, req in enumerate(action_requests, 1):
        print(f"\n--- Action Request {i} ---")
        print(f"Request: {req['request']}")
        print(f"Type: {req['type']}, Priority: {req['priority']}")
        
        result = await twin.process(
            content=req["request"],
            request_type=req["type"],
            priority=req["priority"]
        )
        
        print(f"Success: {result.success}")
        print(f"Response: {result.response_text}")
        
        if result.action_plan:
            print(f"Action Plan ID: {result.action_plan.plan_id}")
            print(f"Steps: {len(result.action_plan.steps) if hasattr(result.action_plan, 'steps') else 'N/A'}")
            print(f"Status: {result.action_plan.status}")
            
            if result.action_plan.scheduled_time:
                print(f"Scheduled for: {result.action_plan.scheduled_time}")
        
        print(f"Memory updates: {result.memory_updates}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        # Simulate successful execution feedback
        await twin.provide_feedback(
            request_id=result.request_id,
            satisfaction=0.9,
            lessons_learned=[
                f"Action type '{req['type']}' executed successfully",
                f"Priority '{req['priority']}' handled appropriately"
            ],
            feedback_text="Action completed as expected"
        )


async def test_memory_enhanced_learning(twin: UnifiedTwinDecisionLoop):
    """Test memory-enhanced learning and pattern recognition"""
    print("\n🎓 === MEMORY-ENHANCED LEARNING TEST ===\n")
    
    # Create similar situations to test pattern learning
    similar_requests = [
        "Send urgent email to boss about project delay",
        "Email team about meeting reschedule", 
        "Send follow-up email to client about proposal"
    ]
    
    print("Processing similar email requests to build patterns...")
    
    request_results = []
    for i, request in enumerate(similar_requests, 1):
        print(f"\n--- Email Request {i} ---")
        print(f"Request: {request}")
        
        result = await twin.process(
            content=request,
            request_type="action",
            priority="high"
        )
        
        request_results.append(result)
        print(f"Success: {result.success}")
        print(f"Lessons applied: {len(result.lessons_learned)}")
        
        # Provide varied feedback to see learning
        satisfaction = 0.9 if i == 1 else 0.7 if i == 2 else 0.8
        await twin.provide_feedback(
            request_id=result.request_id,
            satisfaction=satisfaction,
            lessons_learned=[
                f"Email request pattern #{i} satisfaction: {satisfaction}",
                "Email communication is effective for updates"
            ]
        )
    
    # Test if the twin learned from these patterns
    print("\n🔍 Testing pattern application...")
    
    new_similar_request = "Send email to manager about budget approval"
    result = await twin.process(
        content=new_similar_request,
        request_type="action"
    )
    
    print(f"New similar request: {new_similar_request}")
    print(f"Success: {result.success}")
    print(f"Lessons applied: {len(result.lessons_learned)}")
    
    if result.reasoning_response:
        print(f"Applied lessons: {result.reasoning_response.lessons_applied}")
        print(f"Memory references: {len(result.reasoning_response.memory_references)}")


async def test_cross_domain_orchestration(twin: UnifiedTwinDecisionLoop):
    """Test orchestration across multiple domains and tools"""
    print("\n🔀 === CROSS-DOMAIN ORCHESTRATION TEST ===\n")
    
    # Complex request that spans multiple domains
    complex_request = (
        "Prepare for tomorrow's client meeting: "
        "create a task to review the presentation, "
        "send a reminder email to team members, "
        "and call me 30 minutes before the meeting"
    )
    
    print(f"Complex request: {complex_request}")
    
    result = await twin.process(
        content=complex_request,
        request_type="auto",  # Let the system auto-detect
        priority="high"
    )
    
    print(f"\nResult:")
    print(f"Success: {result.success}")
    print(f"Response: {result.response_text}")
    print(f"Processing time: {result.processing_time:.2f}s")
    
    if result.action_plan:
        print(f"Action plan created: {result.action_plan.plan_id}")
        print(f"Plan status: {result.action_plan.status}")
    
    print(f"Memory updates: {result.memory_updates}")
    
    # Provide feedback on complex orchestration
    await twin.provide_feedback(
        request_id=result.request_id,
        satisfaction=0.85,
        lessons_learned=[
            "Complex multi-domain requests can be handled systematically",
            "Breaking down complex requests into actionable steps works well"
        ],
        feedback_text="Good orchestration of multiple action types"
    )


async def test_introspection_and_self_analysis(twin: UnifiedTwinDecisionLoop):
    """Test introspection and self-analysis capabilities"""
    print("\n🪞 === INTROSPECTION AND SELF-ANALYSIS TEST ===\n")
    
    introspection_questions = [
        "What patterns do you see in how I handle email requests?",
        "How effective are my action planning strategies?",
        "What types of requests do I handle most successfully?",
        "What areas of my decision-making could be improved?"
    ]
    
    for i, question in enumerate(introspection_questions, 1):
        print(f"\n--- Introspection {i} ---")
        print(f"Question: {question}")
        
        result = await twin.process(
            content=question,
            request_type="introspect"
        )
        
        print(f"Success: {result.success}")
        print(f"Insight: {result.response_text[:300]}...")
        print(f"Processing time: {result.processing_time:.2f}s")


async def test_system_optimization(twin: UnifiedTwinDecisionLoop):
    """Test system optimization based on learning"""
    print("\n🔧 === SYSTEM OPTIMIZATION TEST ===\n")
    
    print("Running system optimization...")
    
    optimization_results = await twin.optimize_system()
    
    print("\nOptimization Results:")
    print(f"Memory maintenance: {optimization_results['memory_maintenance']}")
    print(f"System insights: {optimization_results['system_insights'][:400]}...")
    
    # Get comprehensive system status
    system_status = twin.get_system_status()
    
    print(f"\nSystem Status:")
    print(f"Decision loop processed: {system_status['decision_loop']['total_processed']} requests")
    print(f"Success rate: {system_status['decision_loop']['success_rate']:.2%}")
    print(f"Memory formations: {system_status['decision_loop']['memory_formations']}")
    print(f"Patterns learned: {system_status['decision_loop']['patterns_learned']}")
    
    brain_memory = system_status['brain']
    print(f"\nBrain Memory:")
    print(f"Episodic memories: {brain_memory['episodic_memory']['total_memories']}")
    print(f"Semantic memories: {brain_memory['semantic_memory']['total_memories']}")


async def test_memory_queries(twin: UnifiedTwinDecisionLoop):
    """Test direct memory querying"""
    print("\n💭 === MEMORY QUERIES TEST ===\n")
    
    memory_questions = [
        "What email requests have I handled recently?",
        "How do I typically handle urgent situations?",
        "What patterns do you see in my task management?",
        "What lessons have I learned about communication?"
    ]
    
    for i, question in enumerate(memory_questions, 1):
        print(f"\n--- Memory Query {i} ---")
        print(f"Question: {question}")
        
        memory_answer = await twin.ask_memory(question)
        
        print(f"Memory response: {memory_answer[:300]}...")


async def test_action_registry_integration(twin: UnifiedTwinDecisionLoop):
    """Test integration with the universal action registry"""
    print("\n📋 === ACTION REGISTRY INTEGRATION TEST ===\n")
    
    # Get registry statistics
    registry_stats = global_action_registry.get_registry_stats()
    
    print("Action Registry Status:")
    print(f"Total actions: {registry_stats['total_actions']}")
    print(f"Categories: {registry_stats['categories']}")
    print(f"Overall success rate: {registry_stats['execution_stats']['overall_success_rate']:.2%}")
    
    # Test action recommendations
    print("\n🎯 Testing action recommendations...")
    
    contexts = [
        "urgent communication",
        "meeting preparation", 
        "task organization",
        "information gathering"
    ]
    
    for context in contexts:
        recommendations = global_action_registry.get_recommended_actions(context)
        print(f"\nContext: '{context}'")
        print(f"Recommended actions: {[a.name for a in recommendations]}")


async def test_error_handling_and_recovery(twin: UnifiedTwinDecisionLoop):
    """Test error handling and recovery mechanisms"""
    print("\n⚠️ === ERROR HANDLING AND RECOVERY TEST ===\n")
    
    # Test with invalid/problematic requests
    error_test_requests = [
        "Call someone but don't tell me who",  # Ambiguous request
        "Send email to invalid-email-format",  # Invalid parameters
        "Schedule meeting for yesterday",       # Impossible timing
        "Use non-existent tool for this task"  # Missing tool
    ]
    
    for i, request in enumerate(error_test_requests, 1):
        print(f"\n--- Error Test {i} ---")
        print(f"Request: {request}")
        
        result = await twin.process(
            content=request,
            request_type="action"
        )
        
        print(f"Success: {result.success}")
        print(f"Response: {result.response_text}")
        
        if not result.success:
            print("✅ Error handled gracefully")
        
        # Even failed requests should generate learning
        await twin.provide_feedback(
            request_id=result.request_id,
            satisfaction=0.3,  # Low satisfaction for errors
            lessons_learned=["Error handling needs improvement for ambiguous requests"],
            feedback_text="Request was unclear or impossible to execute"
        )


async def run_comprehensive_integration_tests():
    """Run all integration tests"""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    print("🚀 Initializing Integrated Digital Twin System...")
    
    # Configure tools for the twin
    tools_config = {
        "voice": {
            "class": "__main__.MockVoiceTool",
            "params": {}
        },
        "gmail": {
            "class": "__main__.MockEmailTool", 
            "params": {}
        },
        "task_manager": {
            "class": "__main__.MockTaskManager",
            "params": {}
        }
    }
    
    # Initialize the complete system
    twin = UnifiedTwinDecisionLoop(
        persona_path="persona.yaml",
        api_key=api_key,
        memory_dir="integration_test_memory",
        tools_config=tools_config
    )
    
    print("✅ Integrated system initialized successfully!")
    print(f"   • Brain: Enhanced reasoning with persistent memory")
    print(f"   • Controller: Memory-aware action orchestration") 
    print(f"   • Registry: Universal action definitions")
    print(f"   • Tools: Voice, Email, Task Management (mocked)")
    
    try:
        # Run all test suites
        await test_basic_reasoning_with_memory(twin)
        await test_action_planning_and_execution(twin)
        await test_memory_enhanced_learning(twin)
        await test_cross_domain_orchestration(twin)
        await test_introspection_and_self_analysis(twin)
        await test_memory_queries(twin)
        await test_action_registry_integration(twin)
        await test_system_optimization(twin)
        await test_error_handling_and_recovery(twin)
        
        print("\n🎉 === ALL INTEGRATION TESTS COMPLETED ===")
        print("\n✅ The integrated Brain + Memory + Controller system demonstrates:")
        print("   • Memory-enhanced reasoning and decision making")
        print("   • Intelligent action planning with learning")
        print("   • Cross-domain action orchestration")
        print("   • Continuous learning from feedback")
        print("   • Pattern recognition and optimization")
        print("   • Comprehensive introspection capabilities")
        print("   • Robust error handling and recovery")
        print("   • Universal action registry integration")
        
        # Final system export
        export_path = await twin.export_complete_system()
        print(f"\n💾 Complete system state exported to: {export_path}")
        
        print(f"\n🧠 Your digital twin is now a fully integrated, learning system!")
        print(f"   Memory files: integration_test_memory/")
        print(f"   The twin remembers everything and continuously improves.")
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_integration_tests())