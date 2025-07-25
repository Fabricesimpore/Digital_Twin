# 🧪 Digital Twin CLI Test Plan - Pre-UI Validation

**Objective**: Validate the complete Digital Twin system via CLI before building UI/mobile interfaces

## 🎯 Test Strategy Overview

This comprehensive test plan ensures all core systems work perfectly through the command line:
- ✅ Core intelligence and reasoning 
- ✅ Memory system and learning
- ✅ Goal-aware agent functionality
- ✅ Observer mode and behavioral insights
- ✅ API integrations (Gmail, Calendar, Twilio)
- ✅ Human-in-the-loop approval system
- ✅ Real-world automation workflows

---

## 📋 Phase 1: Environment Setup & Validation

### 1.1 Environment Activation
```bash
# Activate virtual environment
source twin_env/bin/activate

# Verify Python environment
python --version
which python

# Export API keys
export OPENAI_API_KEY=your_openai_api_key
```

### 1.2 Dependencies Check
```bash
# Check installed packages
pip list | grep -E "(openai|rich|chromadb|numpy|twilio)"

# Install missing dependencies if needed
pip install -r requirements.txt
```

### 1.3 Environment File Setup
```bash
# Copy and configure environment
cp .env.template .env
# Edit .env with your actual API keys and credentials
```

**✅ Expected Result**: Clean environment activation with all dependencies available

---

## 📋 Phase 2: Core System Boot Test

### 2.1 Twin CLI Initialization
```bash
# Boot the twin CLI
python twin_cli.py
```

**✅ Expected Output**:
```
🧠 Digital Twin Interactive CLI
Initializing your digital twin system...
✅ Digital twin initialized successfully!
ℹ️  Memory system active with X episodic memories
Your digital twin is ready! Type 'help' for available commands.
twin>
```

### 2.2 Basic Commands Test
```bash
# Test basic functionality
twin> help
twin> status
twin> memory
```

**✅ Expected**: All commands execute without errors, showing system status

---

## 📋 Phase 3: Unit Tests Execution

### 3.1 Goal System Test
```bash
# Test goal-aware agent core
python test_goal_basic.py
```

**✅ Expected Output**:
```
🎯 Testing Goal System Basics
✅ Goal system imports successful
✅ Goal system components initialized successfully
✅ Created goal: Master Goal-Aware Agent Development
🎉 BASIC GOAL SYSTEM TEST PASSED!
```

### 3.2 Integrated System Test
```bash
# Test brain + memory + controller integration  
python test_integrated_system.py
```

**✅ Expected**: Memory-enhanced reasoning, action planning, cross-domain orchestration

### 3.3 Memory System Test
```bash
# Test memory system functionality
python test_memory_system.py
```

**✅ Expected**: Memory storage, retrieval, and pattern learning working

---

## 📋 Phase 4: Core Twin Functionality

### 4.1 Basic Reasoning Test
```bash
twin> chat What should I focus on today?
twin> ask What patterns do you see in my work habits?
twin> introspect How can I be more productive?
```

**✅ Expected**: Thoughtful, contextual responses with memory integration

### 4.2 Action Planning Test
```bash
twin> action Send email to john@example.com about project status
twin> action Create task to review quarterly reports by Friday
twin> schedule Call me at 3pm with daily summary
```

**✅ Expected**: Action plans created, appropriate tool usage, scheduling working

### 4.3 Memory Building Test
```bash
# Build memory through conversation
twin> chat I prefer morning meetings for important decisions
twin> chat I work best on creative tasks after 2pm
twin> ask What have you learned about my preferences?
```

**✅ Expected**: Twin remembers and references previous conversations

---

## 📋 Phase 5: Goal-Aware Agent System

### 5.1 Goal Management
```bash
twin> create-goal "Finish YC Deck" due:2025-07-30
twin> status-goals
twin> progress "YC Deck" 30%
twin> goal-briefing "YC Deck"
```

**✅ Expected**: Goals created, tracked, progress logged, insights provided

### 5.2 Goal-Aware Reasoning
```bash
twin> what should I focus on right now?
twin> how did I usually handle client emails?
twin> why did I choose to work on YC deck first?
```

**✅ Expected**: Responses reference active goals and strategic priorities

---

## 📋 Phase 6: Observer Mode Testing

### 6.1 Observer System Activation
```bash
twin> start-observer
twin> observer
```

**✅ Expected Output**:
```
Starting observer system for passive behavior learning...
✅ Observer system started successfully!

Current Activity:
• App: VS Code
• Window: CLI_TEST_PLAN.md
• Category: DEVELOPMENT
• Session Duration: 15 minutes
```

### 6.2 Behavioral Insights
```bash
twin> insights
twin> privacy
```

**✅ Expected**: Productivity patterns, focus analysis, privacy report

---

## 📋 Phase 7: API Integrations Test

### 7.1 Mock API Test (Safe)
```bash
# Run integrated system test with mock APIs
python test_integrated_system.py
```

### 7.2 Real API Test (Optional)
```bash
# Only run if you have real API credentials configured
python test_realworld_apis.py
```

**✅ Expected**: 
- Gmail: Read/analyze emails
- Calendar: Fetch events, find free time
- Twilio: Voice capabilities ready

---

## 📋 Phase 8: Human-in-the-Loop (HITL) System

### 8.1 HITL Configuration Check
```bash
# Verify HITL settings in .env
grep -E "TWILIO|USER_PHONE" .env
```

### 8.2 HITL Approval Test
```bash
twin> action Send important email to CEO about quarterly results
```

**✅ Expected**: SMS/call requesting approval if action classified as critical

### 8.3 HITL Learning Test
```bash
twin> approvals
twin> system-log  
twin> pattern-insights
```

**✅ Expected**: Shows approval history, decision patterns, learning insights

---

## 📋 Phase 9: System Validation & Diagnostics

### 9.1 System Status Check
```bash
twin> status
twin> memory
twin> export
twin> optimize
```

**✅ Expected**: 
- High success rates
- Active memory formations
- System optimization working
- Clean export functionality

### 9.2 Debug and Diagnostics
```bash
# Optional: Create debug script
python -c "
from twin_decision_loop import UnifiedTwinDecisionLoop
import os
twin = UnifiedTwinDecisionLoop('persona.yaml', os.getenv('OPENAI_API_KEY'), 'debug_memory')
status = twin.get_system_status()
print(f'System Health: {status}')
"
```

---

## 🏆 Phase 10: Validation Checklist

### ✅ Core Systems
- [ ] **Reasoning Engine**: Working via CLI
- [ ] **Memory System**: Responds with context
- [ ] **Goal System**: Tracks and adapts
- [ ] **Observer Mode**: Tracks focus and patterns
- [ ] **Action Planning**: Creates and executes plans

### ✅ Integrations  
- [ ] **APIs**: Gmail, Calendar, Twilio (if configured)
- [ ] **HITL**: Text/call approval triggers
- [ ] **Real-Time Loop**: Decisions stream + feedback
- [ ] **Insights**: Patterns surfaced in CLI

### ✅ Quality Metrics
- [ ] **Response Time**: < 3 seconds for simple queries
- [ ] **Memory Integration**: References past context
- [ ] **Success Rate**: > 90% for standard requests
- [ ] **Error Handling**: Graceful failure recovery

---

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

**Issue**: `OPENAI_API_KEY not found`
```bash
# Solution: Set environment variable
export OPENAI_API_KEY=your_key_here
# Or add to .env file
```

**Issue**: `Module not found` errors
```bash
# Solution: Activate environment and install deps
source twin_env/bin/activate
pip install -r requirements.txt
```

**Issue**: Observer not working
```bash
# Solution: Check platform compatibility
python -c "import platform; print(platform.system())"
# Observer may have limited functionality on some systems
```

**Issue**: Memory system errors
```bash
# Solution: Clear and reinitialize memory
rm -rf cli_twin_memory/
python twin_cli.py  # Will recreate clean memory
```

---

## 🎉 Success Criteria

**The CLI test passes when**:

1. **Boot Test**: Twin initializes cleanly without errors
2. **Unit Tests**: All test files pass successfully  
3. **Core Functions**: Chat, ask, action, schedule all work
4. **Memory Integration**: Twin remembers and learns from interactions
5. **Goal Awareness**: Goal system tracks progress and informs decisions
6. **Observer Mode**: Behavioral tracking and insights (if supported)
7. **API Integration**: At least mock APIs work, real APIs if configured
8. **HITL System**: Approval workflow triggers appropriately
9. **System Health**: Status shows high success rates and active learning

**Ready for UI/Mobile when**:
- ✅ All CLI tests pass consistently
- ✅ Memory system shows learning patterns
- ✅ Real-world actions execute successfully
- ✅ System runs stable for extended sessions
- ✅ Export/import functionality working

---

## 📝 Test Execution Log

Use this section to track your test results:

```
[ ] Phase 1: Environment Setup (Date: _____)
[ ] Phase 2: Core Boot Test (Date: _____)
[ ] Phase 3: Unit Tests (Date: _____)
[ ] Phase 4: Core Functionality (Date: _____)
[ ] Phase 5: Goal System (Date: _____)
[ ] Phase 6: Observer Mode (Date: _____)
[ ] Phase 7: API Integration (Date: _____)
[ ] Phase 8: HITL System (Date: _____)
[ ] Phase 9: System Validation (Date: _____)
[ ] Phase 10: Final Checklist (Date: _____)

Overall Result: [ ] PASS [ ] FAIL
Notes: _________________________________
```

---

**🚀 Once all phases pass, your Digital Twin is validated and ready for UI/mobile development!**