# 🤖 Digital Twin - Intelligent Personal Assistant

**Your AI-powered autonomous agent with human oversight for critical decisions**

[![Status](https://img.shields.io/badge/Status-Phase%208%20Complete-success)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 🌟 Overview

Digital Twin is an advanced personal AI assistant that combines autonomous action execution with intelligent human-in-the-loop (HITL) oversight. It can handle routine tasks automatically while requesting your approval for critical decisions via SMS, calls, or notifications.

### ✨ Key Features

- 🤖 **Autonomous Task Execution** - Handles routine work automatically
- 🔔 **Smart Alert System** - SMS/call notifications for critical decisions  
- 🧠 **Continuous Learning** - Improves from your feedback patterns
- 💾 **Real-time Memory** - Streams updates to episodic, semantic, and procedural memory
- 📱 **Multi-channel Alerts** - Desktop → SMS → Phone calls based on urgency
- ⚙️ **Configurable Rules** - Customize what requires approval
- 📊 **Rich Analytics** - Track approval rates and response patterns

## 📁 Project Structure

```
Digital_Twin/
├── README.md                    # This file
├── .env.template               # Environment variables template
├── requirements.txt            # Project dependencies
│
├── backend/                    # 🎯 Phase 8: HITL Intelligence System
│   ├── __init__.py            # Package initialization
│   ├── requirements.txt       # Backend-specific dependencies
│   │
│   ├── core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── action_classifier.py      # Determines action criticality
│   │   ├── hitl_engine.py            # Human-in-the-loop workflow
│   │   ├── alert_dispatcher.py       # SMS/call/notification system
│   │   ├── feedback_tracker.py       # Learning from decisions
│   │   ├── realtime_memory_streamer.py # Memory system updates
│   │   ├── twin_decision_loop.py     # Main orchestrator
│   │   ├── cli_extensions.py         # Command-line interface
│   │   │
│   │   # Validation & utilities
│   │   ├── env_validator.py          # Environment validation
│   │   ├── config_validator.py       # Configuration validation
│   │   ├── safe_imports.py           # Safe dependency imports
│   │   └── run_validations.py        # Complete system validation
│   │
│   ├── config/                # Configuration files
│   │   ├── criticality_rules.yaml    # Action classification rules
│   │   └── twin_config.json          # System configuration
│   │
│   ├── data/                  # Runtime data storage
│   │   ├── hitl_history.json         # Approval history
│   │   ├── feedback_history.json     # Learning data
│   │   └── memory_buffer.json        # Memory updates buffer
│   │
│   ├── logs/                  # Application logs
│   │   └── twin_decisions.log        # Decision audit trail
│   │
│   └── tests/                 # Test files
│
├── brain_modules/             # 🧠 Core AI reasoning system
│   ├── arbitrator.py          # Decision arbitration
│   ├── behavioral_voices.py   # Behavioral pattern voices
│   ├── deliberation_engine.py # Multi-perspective reasoning
│   ├── heuristic_brain.py     # Quick decision heuristics
│   └── state_tracker.py       # Internal state management
│
├── memory_system/            # 🧠 Long-term memory components
│   ├── episodic_memory.py     # Event-based memories
│   ├── vector_memory.py       # Semantic embeddings
│   ├── memory_retrieval.py    # Context-aware retrieval
│   └── memory_updater.py      # Memory maintenance
│
├── goal_system/              # 🎯 Goal-oriented planning
│   ├── goal_manager.py        # Goal lifecycle management
│   ├── goal_reasoner.py       # Goal analysis and reasoning
│   └── strategic_planner.py   # Long-term planning
│
├── observer/                 # 👁️ Real-world monitoring
│   ├── observer_manager.py    # Observer orchestration
│   ├── screen_observer.py     # Screen activity monitoring
│   ├── browser_tracker.py     # Web activity tracking
│   └── input_watcher.py       # Input device monitoring
│
├── tools/                    # 🔧 External integrations
│   ├── gmail_tool.py          # Email management
│   ├── calendar_tool.py       # Calendar integration
│   ├── task_manager_tool.py   # Task management
│   └── voice_tool.py          # Speech capabilities
│
├── frontend/                 # 🖥️ User interfaces (future)
│   ├── web/                   # Web dashboard
│   └── mobile/                # Mobile app
│
└── docs/                     # 📚 Documentation
    └── README.md              # Additional documentation
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd Digital_Twin

# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Run system validation
python backend/core/run_validations.py
```

### 2. Configuration

```bash
# Create environment file from template
python backend/core/env_validator.py --create-template

# Edit .env.template with your credentials:
# - OpenAI API key for brain modules
# - Twilio credentials for SMS/calls
# - Other service credentials

# Rename to .env when done
mv .env.template .env
```

### 3. Start the System

```bash
# Option 1: Phase 8 HITL System (Latest)
cd backend/core
python twin_decision_loop.py

# Option 2: Interactive CLI
python cli_extensions.py interactive

# Option 3: Full integrated system (All phases)
python digital_twin_v3.py
```

## 🎯 Phase 8: Human-in-the-Loop Intelligence

The latest and most advanced system that balances autonomy with human control:

### Core Features

- **Smart Classification**: Automatically determines if actions need approval
- **Multi-channel Alerts**: SMS → Call → Desktop notifications based on urgency
- **Continuous Learning**: Improves decision-making from your feedback
- **Real-time Memory**: Streams all activities to persistent memory
- **CLI Management**: Full command-line interface for approval queue

### Usage Examples

```bash
# List pending approvals
python backend/core/cli_extensions.py list

# Show detailed request
python backend/core/cli_extensions.py show abc123

# Approve/deny actions
python backend/core/cli_extensions.py approve abc123 --feedback "Looks good"
python backend/core/cli_extensions.py deny abc123 --feedback "Too risky"

# View system statistics
python backend/core/cli_extensions.py stats

# Interactive mode
python backend/core/cli_extensions.py interactive
```

### SMS/Call Responses
When you receive an alert:
- Reply **"YES"** or **"1"** to approve
- Reply **"NO"** or **"2"** to deny
- Reply **"DEFER"** or **"3"** to postpone

## 🧠 Brain Modules (Phases 1-5)

Advanced multi-perspective reasoning system:

```python
from brain_modules import HeuristicBrain

brain = HeuristicBrain()
decision = brain.make_decision("Should I take this job offer?", {
    'salary': 120000,
    'location': 'remote',
    'company_size': 'startup'
})
```

## 🎯 Goal System (Phase 6-7)

Strategic planning and goal management:

```python
from goal_system import GoalManager

goals = GoalManager()
goals.add_goal("Launch product", priority="high", deadline="2024-06-01")
next_actions = goals.get_next_actions()
```

## 👁️ Observer System

Real-world monitoring and context awareness:

```python
from observer import ObserverManager

observer = ObserverManager()
observer.start_monitoring(['screen', 'browser', 'calendar'])
context = observer.get_current_context()
```

## ⚙️ Configuration

### Environment Variables

```bash
# Core AI
OPENAI_API_KEY=your_openai_key

# Phase 8 HITL System
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+0987654321
TWILIO_WEBHOOK_URL=https://your-webhook-url.com

# Optional integrations
GMAIL_CREDENTIALS_PATH=path/to/gmail/credentials.json
CALENDAR_CREDENTIALS_PATH=path/to/calendar/credentials.json
```

### Persona Customization

Edit `persona.yaml` to customize your twin's personality:

```yaml
core_values:
  - "Be honest and direct"
  - "Prioritize long-term thinking"
  - "Value work-life balance"

decision_style: "analytical"
risk_tolerance: "moderate"
communication_style: "professional but friendly"
```

### Action Classification Rules

Edit `backend/config/criticality_rules.yaml`:

```yaml
vip_contacts:
  - "CEO"
  - "Investor"
  - "Board Member"

action_defaults:
  email_send: "medium"
  call_make: "high"
  reminder_set: "low"

keyword_patterns:
  high: ["urgent", "critical", "emergency"]
  medium: ["important", "review"]
  low: ["fyi", "archive"]
```

## 📊 System Monitoring

### Real-time Statistics
```python
from backend import TwinDecisionLoop

twin = TwinDecisionLoop()
stats = twin.get_stats()

print(f"Actions processed: {stats['actions_processed']}")
print(f"Auto-executed: {stats['auto_executed']}")
print(f"Human approved: {stats['human_approved']}")
print(f"Approval rate: {stats['hitl_stats']['approval_rate']:.1%}")
```

### Learning Analytics
```python
insights = twin.feedback_tracker.get_learning_insights()
print(f"Total feedback: {insights['total_feedback_entries']}")
print(f"Common approved patterns: {insights['common_approved_patterns']}")
```

## 🔧 Development

### Running All Validations
```bash
# Check all systems
python backend/core/run_validations.py

# Auto-fix missing files
python backend/core/run_validations.py --fix

# Create setup script
python backend/core/run_validations.py --create-setup
```

### Testing Different Phases
```bash
# Test brain modules
python test_brain_v2.py

# Test goal system
python test_goal_integration.py

# Test observer system
python test_observer_system.py

# Test memory system
python test_memory_system.py

# Test Phase 8 HITL system
python backend/core/twin_decision_loop.py
```

### Adding Custom Components

```python
# Custom action handler
async def handle_custom_action(action):
    print(f"Handling: {action}")
    return True

twin.register_action_handler('custom_action', handle_custom_action)

# Custom behavioral voice
from brain_modules.behavioral_voices import BehavioralVoice

class MyCustomVoice(BehavioralVoice):
    def get_perspective(self, situation):
        return "My custom perspective on this situation..."
```

## 🛡️ Security Features

- **Environment Variables**: Secure credential storage
- **VIP Protection**: Automatic high-priority classification
- **Audit Trail**: Complete decision and action logging
- **Timeout Protection**: Automatic request expiration
- **Multi-factor Alerts**: SMS → Call escalation for critical items
- **Encrypted Storage**: Sensitive data protection

## 🔍 Troubleshooting

### System Not Starting
```bash
# Run complete validation
python backend/core/run_validations.py

# Check individual components
python test_brain_v2.py
python test_memory_system.py
```

### SMS/Calls Not Working
```bash
# Validate Twilio setup
python backend/core/env_validator.py

# Test Twilio connection
python -c "
from twilio.rest import Client
import os
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
print('Twilio connected:', client.api.account.fetch().friendly_name)
"
```

### Memory Issues
```bash
# Check memory system
python test_memory_system.py

# View memory statistics
python -c "
from memory_system import EpisodicMemory
memory = EpisodicMemory()
print('Memory entries:', len(memory.memories))
"
```

### Performance Issues
```bash
# Check system stats
python backend/core/cli_extensions.py stats

# Monitor resource usage
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

## 🗺️ Development Roadmap

### Completed Phases
- ✅ **Phase 1-3**: Basic brain with multi-perspective reasoning
- ✅ **Phase 4-5**: Heuristic decision making and behavioral voices  
- ✅ **Phase 6**: Observer mode with real-world monitoring
- ✅ **Phase 7**: Goal-aware strategic planning
- ✅ **Phase 8**: Human-in-the-loop intelligence with real-time alerts

### Upcoming Phases
- **Phase 9**: Mobile app, voice responses, calendar integration
- **Phase 10**: Multi-user workflows, advanced analytics dashboard
- **Phase 11**: Predictive AI, enterprise security, cloud deployment

### Future Enhancements
- 🌐 **Web Dashboard**: Rich visual interface for all components
- 📱 **Mobile App**: iOS/Android apps for approval management
- 🎤 **Voice Interface**: Natural language interactions
- 🔄 **Workflow Automation**: Complex multi-step processes
- 🌍 **Multi-language**: International language support
- 🏢 **Enterprise**: Multi-user, role-based access control

## 📚 Documentation

- **[Phase 8 HITL README](backend/README.md)** - Detailed backend documentation
- **[Build Plan](DIGITAL_TWIN_BUILD_PLAN.md)** - Complete development roadmap
- **[System Overview](DIGITAL_TWIN_SYSTEM_OVERVIEW.md)** - Architecture details
- **[Setup Guide](SETUP_GUIDE.md)** - Detailed installation guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Run tests
python -m pytest backend/tests/

# Run validations
python backend/core/run_validations.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models powering the brain modules
- **Twilio** for reliable SMS/call infrastructure  
- **Python Community** for excellent async and AI libraries
- **Open Source Contributors** for inspiration and foundational tools

## 📞 Support

- 📖 **Documentation**: Check the component README files
- 🐛 **Issues**: Open a GitHub issue with details
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: contact@your-domain.com

---

**🎉 Phase 8 Complete!** Your Digital Twin now operates as a complete intelligent system with:
- **Autonomous execution** for routine tasks
- **Human oversight** for critical decisions  
- **Multi-perspective reasoning** for complex problems
- **Strategic goal planning** for long-term success
- **Real-world awareness** through continuous observation
- **Continuous learning** from every interaction

*Built with ❤️ for productivity, intelligence, and peace of mind.*