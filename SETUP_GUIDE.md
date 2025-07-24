# Digital Twin Setup Guide 🤖

This guide will help you set up your complete digital twin system with orchestration, scheduling, and voice capabilities.

## 🎯 What You're Building

Your digital twin can now:

- **Understand complex requests**: "Call me at 3:30 and remind me of tasks"
- **Schedule time-based actions**: Automated reminders, daily briefings
- **Orchestrate multiple tools**: Tasks → Voice → Memory in one flow
- **Learn from feedback**: Improves predictions based on your actual behavior
- **Handle voice calls**: Uses Twilio to actually call you with reminders

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **OpenAI API key** (required for GPT-4o)
3. **Twilio account** (optional, for voice calls)
4. **ElevenLabs account** (optional, for advanced TTS)

## 🚀 Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Environment Setup

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit `.env` with your actual API keys:
```bash
# Required
OPENAI_API_KEY=sk-your-actual-openai-key

# Optional (for voice calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+1234567890
```

### Step 3: Customize Your Persona

Edit `persona.yaml` to match your actual:
- Personality traits
- Communication preferences
- Work routines
- Decision patterns

This is crucial for accurate twin behavior!

## 🧪 Testing

### Test the Brain Module

```bash
python test_brain.py
```

This simulates various decisions and shows how your twin reasons.

### Test the Complete System

```bash
python example_integration.py
```

Choose from demos:
1. **Schedule reminder call** - "Call me at 3:30 PM"
2. **Morning routine** - Daily 8 AM briefings
3. **Learning feedback** - How the twin improves

## 📞 Setting Up Voice Calls (Optional)

### Get Twilio Credentials

1. Sign up at [twilio.com](https://twilio.com)
2. Get a phone number ($1/month)
3. Find your Account SID and Auth Token
4. Add them to your `.env` file

### Test Voice System

```python
# In Python
from tools.voice_tool import VoiceTool
import asyncio

voice = VoiceTool()
result = await voice.make_call(
    recipient="+1234567890",
    message="This is a test from your digital twin!",
    message_type="general"
)
```

## 🎮 Usage Examples

### Basic Request Processing

```python
from twin_controller import TwinController
from digital_twin import DigitalTwin

# Initialize
twin = DigitalTwin(api_key="your-key")
controller = TwinController(twin)

# Process request
plan = await controller.process_request(
    "Call me in 2 hours and remind me about the meeting"
)
```

### Scheduling Recurring Actions

```python
from scheduler import TwinScheduler

scheduler = TwinScheduler()
await scheduler.start()

# Daily morning briefing
scheduler.schedule_recurring_reminder(
    action_id="morning_briefing",
    time_of_day="08:00",
    callback=your_briefing_function
)
```

### Managing Tasks

```python
from tools.task_manager_tool import TaskManagerTool

tasks = TaskManagerTool()

# Add task
tasks.create_task(
    title="Review project proposal",
    priority="high",
    deadline=datetime.now() + timedelta(hours=4)
)

# Get tasks for reminder
pending = tasks.get_pending_tasks(timeframe="today")
```

## 🛠️ Architecture Overview

```
User Request: "Call me at 3:30 and remind me of tasks"
       ↓
🧠 Digital Twin (brain)
   - Interprets intent
   - Accesses persona and memory
   - Reasons about best action
       ↓
🎮 Twin Controller (orchestrator)
   - Converts reasoning to action plan
   - Routes to appropriate tools
   - Handles multi-step coordination
       ↓
⏰ Scheduler (time manager)
   - Schedules future execution
   - Manages recurring actions
   - Triggers at specified time
       ↓
🔧 Tools (executors)
   - Task Manager: Gets pending tasks
   - Voice Tool: Makes the call
   - Memory: Logs the interaction
```

## 📊 Key Components

| Component | Purpose | File |
|-----------|---------|------|
| **Brain** | Identity + reasoning + memory | `digital_twin.py` |
| **Controller** | Orchestrates multi-tool actions | `twin_controller.py` |
| **Scheduler** | Handles time-based triggers | `scheduler.py` |
| **Voice Tool** | Makes calls, TTS | `tools/voice_tool.py` |
| **Task Manager** | Manages todos and reminders | `tools/task_manager_tool.py` |
| **Memory** | Stores patterns and learnings | `memory_interface.py` |

## 🎯 Common Use Cases

### 1. Daily Reminders
```python
# "Remind me of my tasks every day at 9 AM"
controller.process_request(
    "Call me every morning at 9 AM with my daily task list"
)
```

### 2. Context-Aware Notifications
```python
# "If I have high-priority tasks due today, call me at lunch"
# The twin learns your patterns and makes smart decisions
```

### 3. Meeting Prep
```python
# "30 minutes before my 2 PM meeting, call me with the agenda"
# Integrates calendar + tasks + voice in one request
```

## 🔧 Customization

### Adding New Tools

1. Create tool class in `tools/your_tool.py`
2. Implement required methods
3. Register with controller:

```python
controller.register_tool("your_tool", YourTool())
```

### Extending Persona

Add new sections to `persona.yaml`:
```yaml
custom_preferences:
  notification_style: "brief_and_direct"
  call_timing: "avoid_early_morning"
```

### Memory Enhancement

Store specific patterns:
```python
memory_manager.remember_preference(
    category="call_timing",
    preference="Prefers calls after 9 AM on weekdays"
)
```

## 🐛 Troubleshooting

### Common Issues

1. **"Tool not registered" error**
   - Make sure to call `controller.register_tool()`

2. **Twilio calls fail**
   - Check phone number format: `+1234567890`
   - Verify account has sufficient balance

3. **Scheduling not working**
   - Ensure scheduler is started: `await scheduler.start()`

4. **Memory not persisting**
   - Check file permissions in `chroma_db/` directory

### Debug Mode

Add logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🚀 Next Steps

Once basic system is working:

1. **Week 1**: Add Gmail integration for email context
2. **Week 2**: Add calendar integration for meeting awareness  
3. **Week 3**: Add browser automation for web tasks
4. **Week 4**: Add WhatsApp/Slack for messaging

## 🆘 Getting Help

1. **Check logs** for error details
2. **Test individual components** before integration
3. **Start simple** and add complexity gradually

## 🎉 Success Metrics

You'll know it's working when:

- Twin accurately predicts your responses to test scenarios
- Scheduled calls happen on time with relevant information
- System learns from your corrections and improves
- You can handle complex, multi-step requests naturally

---

**Ready to build your digital self?** Start with the brain tests and work your way up to the full integration!