#!/usr/bin/env python3
"""
Basic Goal System Test

This script tests the core goal system components without requiring
external dependencies like numpy/chromadb.

Tests:
1. Goal system initialization
2. Goal creation and management  
3. Milestone tracking
4. Strategic planning basics
5. Goal-aware reasoning
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_goal_system_basics():
    """Test basic goal system functionality"""
    
    print("🎯 Testing Goal System Basics")
    print("=" * 50)
    
    try:
        # Test 1: Import goal system components
        print("\n📋 Test 1: Goal System Imports")
        
        from goal_system.goal_manager import GoalManager, GoalType, GoalStatus
        from goal_system.strategic_planner import StrategicPlanner
        from goal_system.goal_reasoner import GoalAwareReasoner
        
        print("✅ Goal system imports successful")
        
        # Test 2: Initialize Goal System
        print("\n🏗️ Test 2: Goal System Initialization")
        
        # Create test directory
        test_dir = Path("test_goal_basic")
        test_dir.mkdir(exist_ok=True)
        
        # Initialize goal system (without AI interface for now)
        goal_manager = GoalManager(storage_dir=str(test_dir), ai_interface=None)
        strategic_planner = StrategicPlanner(goal_manager=goal_manager, observer_manager=None)
        goal_reasoner = GoalAwareReasoner(goal_manager=goal_manager, strategic_planner=strategic_planner)
        
        print("✅ Goal system components initialized successfully")
        
        # Test 3: Create a Goal
        print("\n🎯 Test 3: Goal Creation")
        
        target_date = datetime.now() + timedelta(weeks=4)
        goal = goal_manager.create_goal(
            title="Master Goal-Aware Agent Development",
            description="Build and integrate a complete goal-aware agent system",
            target_date=target_date,
            goal_type=GoalType.PROJECT,
            priority=1,
            impact_areas=["work", "learning", "productivity"],
            related_apps=["VS Code", "Terminal", "Chrome"],
            motivation="Transform the twin from reactive to strategic",
            success_vision="A fully functional goal-aware digital assistant"
        )
        
        print(f"✅ Created goal: {goal.title}")
        print(f"   ID: {goal.id}")
        print(f"   Type: {goal.goal_type.value}")
        print(f"   Priority: {goal.priority}")
        print(f"   Target Date: {goal.target_date.strftime('%Y-%m-%d')}")
        print(f"   Days until deadline: {goal.days_until_deadline}")
        
        # Test 4: Goal Status and Properties
        print("\n📊 Test 4: Goal Status and Properties")
        
        print(f"Goal is overdue: {goal.is_overdue}")
        print(f"Weeks remaining: {goal.weeks_remaining:.1f}")
        print(f"Current progress: {goal.progress_percentage}%")
        print(f"Impact areas: {', '.join(goal.impact_areas)}")
        print(f"Related apps: {', '.join(goal.related_apps)}")
        
        # Test 5: Goal Management Operations
        print("\n🔧 Test 5: Goal Management Operations")
        
        # Get active goals
        active_goals = goal_manager.get_active_goals()
        print(f"Active goals: {len(active_goals)}")
        
        # Get goal summary
        summary = goal_manager.get_goal_summary()
        print(f"Goal summary: {summary}")
        
        # Test 6: Manual Milestone Creation
        print("\n📋 Test 6: Manual Milestone Creation")
        
        from goal_system.goal_manager import Milestone
        
        # Create some milestones manually
        milestone1 = Milestone(
            id="",  # Auto-generated
            title="Design goal system architecture",
            description="Create comprehensive design for goal-aware agent",
            goal_id=goal.id,
            target_date=datetime.now() + timedelta(weeks=1),
            estimated_effort_hours=8,
            priority=1,
            success_criteria=["Architecture documented", "Components defined", "Integration planned"]
        )
        
        milestone2 = Milestone(
            id="",  # Auto-generated
            title="Implement core goal management",
            description="Build goal manager and milestone tracking",
            goal_id=goal.id,
            target_date=datetime.now() + timedelta(weeks=2),
            estimated_effort_hours=16,
            priority=1,
            success_criteria=["Goal creation working", "Milestone tracking active", "Progress updates functioning"]
        )
        
        milestone3 = Milestone(
            id="",  # Auto-generated
            title="Integrate with memory system",
            description="Connect goals to memory and behavioral patterns",
            goal_id=goal.id,
            target_date=datetime.now() + timedelta(weeks=3),
            estimated_effort_hours=12,
            priority=2,
            success_criteria=["Memory integration complete", "Behavioral patterns linked", "Context awareness active"]
        )
        
        # Add milestones to goal manager
        goal_manager.milestones[milestone1.id] = milestone1
        goal_manager.milestones[milestone2.id] = milestone2
        goal_manager.milestones[milestone3.id] = milestone3
        
        goal.milestone_ids = [milestone1.id, milestone2.id, milestone3.id]
        
        print(f"✅ Created {len(goal.milestone_ids)} milestones")
        
        # Test milestone properties
        for i, milestone in enumerate([milestone1, milestone2, milestone3], 1):
            print(f"   Milestone {i}: {milestone.title}")
            print(f"     Days until deadline: {milestone.days_until_deadline}")
            print(f"     Estimated effort: {milestone.estimated_effort_hours} hours")
            print(f"     Priority: {milestone.priority}")
        
        # Test 7: Milestone Progress Updates
        print("\n📈 Test 7: Milestone Progress Updates")
        
        # Update progress on first milestone
        milestone1.update_progress(75.0, "Architecture design mostly complete")
        print(f"Updated milestone 1 progress to {milestone1.progress_percentage}%")
        
        # Update progress on second milestone  
        milestone2.update_progress(40.0, "Core implementation in progress")
        print(f"Updated milestone 2 progress to {milestone2.progress_percentage}%")
        
        # Calculate overall goal progress
        goal_progress = goal.calculate_progress_from_milestones([milestone1, milestone2, milestone3])
        print(f"Overall goal progress: {goal_progress:.1f}%")
        
        # Test 8: Goal-Aware Reasoning
        print("\n🧠 Test 8: Goal-Aware Reasoning")
        
        test_queries = [
            "What should I focus on right now?",
            "How is my project development going?",
            "What are my current priorities?",
            "Should I work on goal system architecture?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            # Get goal context
            goal_context = goal_reasoner.get_goal_context(query)
            print(f"   Goal relevance: {goal_context.goal_relevance.value}")
            print(f"   Active goals considered: {len(goal_context.active_goals)}")
            print(f"   Current priorities: {len(goal_context.current_priorities)}")
            
            # Get recommendations
            recommendations = goal_reasoner.get_goal_informed_recommendations(query)
            if recommendations:
                print(f"   Top recommendation: {recommendations[0]}")
        
        # Test 9: Strategic Planning
        print("\n📊 Test 9: Strategic Planning")
        
        # Create project plan
        milestones = [milestone1, milestone2, milestone3]
        project_plan = strategic_planner.create_project_plan(goal, milestones)
        
        print(f"Created strategic plan:")
        print(f"   Timeline status: {project_plan.timeline_status.value}")
        print(f"   Completion probability: {project_plan.completion_probability:.2f}")
        print(f"   Estimated total hours: {project_plan.estimated_total_hours}")
        print(f"   Hours completed: {project_plan.hours_completed}")
        print(f"   Weekly capacity: {project_plan.weekly_capacity_hours}")
        print(f"   Progress percentage: {project_plan.progress_percentage:.1f}%")
        
        # Get strategic recommendations
        recommendations = strategic_planner.get_strategic_recommendations(goal.id)
        print(f"\nStrategic recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec}")
        
        # Test 10: Daily Briefing
        print("\n📅 Test 10: Daily Goal Briefing")
        
        briefing = goal_reasoner.get_daily_goal_briefing()
        print("Daily Goal Briefing:")
        print("-" * 40)
        print(briefing)
        print("-" * 40)
        
        # Test Summary
        print("\n🎉 Goal System Basic Test Summary")
        print("=" * 50)
        print("✅ Goal system imports working")
        print("✅ Goal creation and management") 
        print("✅ Milestone creation and tracking")
        print("✅ Progress calculation and updates")
        print("✅ Goal-aware reasoning")
        print("✅ Strategic planning")
        print("✅ Daily briefing generation")
        print("\n🚀 Core goal system functionality verified!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure goal system modules are available")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Basic goal test error")
        return False

if __name__ == "__main__":
    print("🚀 Starting Basic Goal System Test")
    print("=" * 60)
    
    success = test_goal_system_basics()
    
    if success:
        print("\n🎉 BASIC GOAL SYSTEM TEST PASSED!")
        print("🚀 Goal-aware agent core functionality is working!")
        print("\nNext steps:")
        print("1. Install numpy/chromadb for full memory integration")
        print("2. Test with twin decision loop integration")
        print("3. Add CLI commands for goal management")
    else:
        print("\n❌ Basic goal system test failed")
        print("Please check the error messages above")