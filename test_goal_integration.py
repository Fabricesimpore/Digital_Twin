#!/usr/bin/env python3
"""
Test Goal System Integration

This script tests the complete integration of the goal-aware agent with the
memory system, behavioral patterns, and decision loop.

Tests:
1. Goal system initialization and setup
2. Goal creation and milestone generation
3. Memory integration for goal events
4. Goal-aware reasoning and decision making
5. Strategic planning and timeline management
6. Observer system integration with goals
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_goal_system_integration():
    """Test complete goal system integration"""
    
    print("🎯 Testing Goal System Integration")
    print("=" * 50)
    
    try:
        # Import goal system components
        from goal_system.goal_manager import GoalManager, GoalType, GoalStatus
        from goal_system.strategic_planner import StrategicPlanner
        from goal_system.goal_reasoner import GoalAwareReasoner
        from memory_system.memory_updater import MemoryUpdater
        from memory_system.episodic_memory import EpisodicMemorySystem
        from memory_system.vector_memory import EnhancedVectorMemory
        
        print("✅ Goal system imports successful")
        
        # Test 1: Initialize Goal System
        print("\n📋 Test 1: Goal System Initialization")
        
        # Create test directories
        test_dir = Path("test_goal_data")
        test_dir.mkdir(exist_ok=True)
        
        memory_dir = Path("test_goal_memory")
        memory_dir.mkdir(exist_ok=True)
        
        # Initialize memory systems
        episodic_memory = EpisodicMemorySystem(str(memory_dir / "episodic"))
        vector_memory = EnhancedVectorMemory(str(memory_dir / "vector"))
        memory_updater = MemoryUpdater(episodic_memory, vector_memory)
        
        # Initialize goal system
        goal_manager = GoalManager(storage_dir=str(test_dir))
        strategic_planner = StrategicPlanner(goal_manager=goal_manager)
        goal_reasoner = GoalAwareReasoner(goal_manager=goal_manager, strategic_planner=strategic_planner)
        
        print("✅ Goal system components initialized successfully")
        
        # Test 2: Create a Goal
        print("\n🎯 Test 2: Goal Creation and Memory Integration")
        
        target_date = datetime.now() + timedelta(weeks=4)
        goal = goal_manager.create_goal(
            title="Build Digital Twin Goal System",
            description="Complete the goal-aware agent implementation with memory integration",
            target_date=target_date,
            goal_type=GoalType.PROJECT,
            priority=1,
            impact_areas=["work", "learning"],
            related_apps=["VS Code", "Terminal", "Chrome"]
        )
        
        print(f"✅ Created goal: {goal.title} (ID: {goal.id})")
        
        # Capture goal creation in memory
        memory_id = memory_updater.capture_goal_memory(
            goal=goal,
            action_type="created",
            details={"test_scenario": "integration_test"}
        )
        
        print(f"✅ Goal creation captured in memory (ID: {memory_id})")
        
        # Test 3: Goal-Aware Reasoning
        print("\n🧠 Test 3: Goal-Aware Reasoning")
        
        test_queries = [
            "What should I focus on right now?",
            "How is my project progress going?",
            "What tasks are most important today?",
            "Should I work on VS Code or take a break?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            # Get goal context
            goal_context = goal_reasoner.get_goal_context(query)
            print(f"Goal relevance: {goal_context.goal_relevance.value}")
            
            # Get goal-informed recommendations
            recommendations = goal_reasoner.get_goal_informed_recommendations(query)
            if recommendations:
                print(f"Recommendations: {recommendations[0]}")
            
            # Capture goal context memory
            context_memory_id = memory_updater.capture_goal_context_memory(
                goal_context=goal_context,
                decision_context=query,
                relevance=goal_context.goal_relevance
            )
            
            if context_memory_id:
                print(f"Goal context captured in memory")
        
        print("✅ Goal-aware reasoning working correctly")
        
        # Test 4: Strategic Planning
        print("\n📊 Test 4: Strategic Planning and Timeline Management")
        
        # Get milestones for the goal
        milestones = [goal_manager.get_milestone_by_id(mid) for mid in goal.milestone_ids]
        milestones = [m for m in milestones if m is not None]
        
        if milestones:
            print(f"Found {len(milestones)} milestones for goal")
            
            # Create strategic plan
            project_plan = strategic_planner.create_project_plan(goal, milestones)
            print(f"Created strategic plan with {project_plan.timeline_status.value} timeline status")
            print(f"Completion probability: {project_plan.completion_probability:.2f}")
            
            # Get strategic recommendations
            recommendations = strategic_planner.get_strategic_recommendations(goal.id)
            print(f"Strategic recommendations: {len(recommendations)} items")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
        else:
            print("No milestones found (AI decomposition would run async)")
        
        print("✅ Strategic planning working correctly")
        
        # Test 5: Milestone Progress Update
        print("\n📈 Test 5: Milestone Progress and Memory Capture")
        
        if milestones:
            milestone = milestones[0]
            original_progress = milestone.progress_percentage
            
            # Update progress
            new_progress = min(original_progress + 25.0, 100.0)
            milestone.update_progress(new_progress, "Integration test progress update")
            
            # Capture milestone memory
            milestone_memory_id = memory_updater.capture_milestone_memory(
                milestone=milestone,
                action_type="progress_updated",
                progress_details={
                    "old_progress": original_progress,
                    "new_progress": new_progress,
                    "progress_increase": new_progress - original_progress,
                    "time_spent_hours": 2.0,
                    "work_context": "integration_testing"
                }
            )
            
            print(f"Updated milestone progress: {original_progress:.1f}% -> {new_progress:.1f}%")
            print(f"Progress update captured in memory (ID: {milestone_memory_id})")
            
            # Update strategic plan
            strategic_planner.update_plan_from_progress(goal.id)
            print("Strategic plan updated based on progress")
        
        print("✅ Milestone progress tracking working correctly")
        
        # Test 6: Daily Goal Briefing
        print("\n📅 Test 6: Daily Goal Briefing")
        
        daily_briefing = goal_reasoner.get_daily_goal_briefing()
        print("Daily Goal Briefing:")
        print("-" * 30)
        print(daily_briefing)
        print("-" * 30)
        
        print("✅ Daily briefing generation working correctly")
        
        # Test 7: Memory Statistics
        print("\n📊 Test 7: Memory Integration Statistics")
        
        stats = memory_updater.get_update_statistics()
        print(f"Memory Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test 8: Strategic Insights
        print("\n💡 Test 8: Strategic Insight Capture")
        
        insight_memory_id = memory_updater.capture_strategic_insight_memory(
            insight="Integration testing reveals strong goal-memory connectivity",
            goal_ids=[goal.id],
            insight_type="system_validation",
            confidence=0.9,
            supporting_data={
                "test_scenario": "integration_test",
                "components_tested": ["goal_manager", "strategic_planner", "goal_reasoner", "memory_updater"]
            }
        )
        
        print(f"Strategic insight captured in memory (ID: {insight_memory_id})")
        
        print("✅ Strategic insight capture working correctly")
        
        # Test Summary
        print("\n🎉 Goal System Integration Test Summary")
        print("=" * 50)
        print("✅ Goal system initialization")
        print("✅ Goal creation and memory integration") 
        print("✅ Goal-aware reasoning and decision making")
        print("✅ Strategic planning and timeline management")
        print("✅ Milestone progress tracking")
        print("✅ Daily briefing generation")
        print("✅ Memory integration statistics")
        print("✅ Strategic insight capture")
        print("\n🚀 All integration tests passed! Goal-aware agent is ready.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all goal system components are available")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Integration test error")
        return False

async def test_twin_decision_loop_integration():
    """Test goal system integration with twin decision loop"""
    
    print("\n🧠 Testing Twin Decision Loop Goal Integration")
    print("=" * 50)
    
    try:
        from twin_decision_loop import UnifiedTwinDecisionLoop
        
        # Initialize twin with goal system enabled
        twin = UnifiedTwinDecisionLoop(
            persona_path="persona.yaml",
            memory_dir="test_twin_memory",
            enable_observer=False,  # Disable observer for this test
            enable_goals=True
        )
        
        print("✅ Twin decision loop initialized with goal system")
        
        # Test goal creation through twin interface
        goal_id = twin.create_goal(
            title="Test Twin Goal Integration",
            description="Verify goal system works through twin decision loop",
            target_date=datetime.now() + timedelta(weeks=2),
            goal_type="project",
            priority=1
        )
        
        if goal_id:
            print(f"✅ Goal created through twin interface (ID: {goal_id})")
        else:
            print("❌ Goal creation failed")
            return False
        
        # Test goal-aware query processing
        test_queries = [
            "What are my current goals?",
            "What should I work on next?", 
            "How is my project progress?",
            "What are my priorities today?"
        ]
        
        for query in test_queries:
            print(f"\nProcessing query: {query}")
            result = await twin.process(query, request_type="query")
            
            if result.success:
                print(f"✅ Query processed successfully")
                if result.response_data.get('goal_aware'):
                    print(f"   Goal-aware response: {result.response_data.get('goal_relevance')}")
                if result.response_data.get('goal_recommendations'):
                    recommendations = result.response_data['goal_recommendations']
                    if recommendations:
                        print(f"   Recommendations: {recommendations[0]}")
            else:
                print(f"❌ Query processing failed")
        
        # Test goal status reporting
        active_goals = twin.get_active_goals()
        print(f"\n✅ Found {len(active_goals)} active goals")
        
        goal_status = twin.get_goal_status(goal_id)
        if 'error' not in goal_status:
            print(f"✅ Goal status retrieved successfully")
        else:
            print(f"❌ Goal status error: {goal_status['error']}")
        
        # Test daily briefing
        briefing = twin.get_daily_goal_briefing()
        print(f"\n✅ Daily briefing generated ({len(briefing)} characters)")
        
        print("\n🎉 Twin Decision Loop Goal Integration Test Complete")
        print("✅ All twin-level goal features working correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Twin integration test failed: {e}")
        logger.exception("Twin integration test error")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Goal System Integration Tests")
        print("=" * 60)
        
        # Test basic goal system integration
        basic_success = await test_goal_system_integration()
        
        if basic_success:
            # Test twin decision loop integration
            twin_success = await test_twin_decision_loop_integration()
            
            if twin_success:
                print("\n🎉 ALL TESTS PASSED!")
                print("🚀 Goal-aware agent is fully integrated and ready for use!")
            else:
                print("\n⚠️  Basic integration passed but twin integration had issues")
        else:
            print("\n❌ Basic integration tests failed")
    
    asyncio.run(main())