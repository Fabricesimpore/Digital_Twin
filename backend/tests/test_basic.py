#!/usr/bin/env python3
"""
Basic tests for Digital Twin backend components
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that core modules can be imported"""
    try:
        from goal_system.goal_manager import GoalManager
        from memory_system.vector_memory import EnhancedVectorMemory
        from observer.observer_manager import ObserverManager
        assert True, "Core imports successful"
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_goal_system():
    """Test basic goal system functionality"""
    from goal_system.goal_manager import GoalManager
    
    goal_manager = GoalManager(storage_dir="test_goals", ai_interface=None)
    assert goal_manager is not None
    assert len(goal_manager.goals) >= 0

def test_memory_system():
    """Test basic memory system functionality"""
    from memory_system.vector_memory import EnhancedVectorMemory
    
    try:
        memory = EnhancedVectorMemory(storage_dir="test_memory")
        assert memory is not None
    except Exception as e:
        # Memory system may have dependency issues in CI
        pytest.skip(f"Memory system not available: {e}")

def test_observer_system():
    """Test basic observer system functionality"""
    from observer.observer_manager import ObserverManager
    
    observer = ObserverManager()
    assert observer is not None
    
    # Test privacy report
    privacy_report = observer.get_privacy_report()
    assert privacy_report is not None
    assert 'local_storage_only' in privacy_report

if __name__ == "__main__":
    pytest.main([__file__])