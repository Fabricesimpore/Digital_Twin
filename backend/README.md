# Phase 8: Real-Time Intelligence with Human-in-the-Loop Control

## 🎯 Overview

Phase 8 implements a hybrid real-time intelligence system that combines autonomous action execution with human oversight for critical decisions. Your digital twin can now:

- ✅ **Auto-execute routine tasks** (archiving, logging, reminders) 
- 🔔 **Request approval for critical actions** (emails to VIPs, calls, calendar changes)
- 📱 **Alert you via SMS/calls** for urgent decisions
- 🧠 **Learn from your decisions** to improve future classifications
- 💾 **Stream real-time updates** to episodic, semantic, and procedural memory

## 🏗️ Architecture

```
[ Real-World Events ] 
        ↓
[ Observer System ] → [ Memory Streamer ]
        ↓
[ Twin Decision Loop ]
   → if LOW criticality     → [ Auto Execute ]
   → if MEDIUM/HIGH         → [ Request Approval ]
                                    ↓
                           [ SMS/Call/Notification ]
                                    ↓
                           [ Human Decision: YES/NO/DEFER ]
                                    ↓
                           [ Execute & Learn from Feedback ]
```

## 📁 Components

| File | Purpose |
|------|---------|
| `action_classifier.py` | Classifies actions as LOW/MEDIUM/HIGH criticality |
| `hitl_engine.py` | Manages human approval requests and timeouts |
| `alert_dispatcher.py` | Sends SMS/calls/notifications via Twilio |
| `realtime_memory_streamer.py` | Streams updates to twin's memory systems |
| `feedback_tracker.py` | Learns from human decisions to improve classifications |
| `twin_decision_loop.py` | Main orchestrator integrating all components |
| `cli_extensions.py` | Command-line interface for approval management |
| `config/criticality_rules.yaml` | Configurable rules for action classification |

## 🚀 Quick Start

### 1. Setup Environment Variables

```bash
# Required for SMS/call alerts
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token" 
export TWILIO_PHONE_NUMBER="+1234567890"
export USER_PHONE_NUMBER="+0987654321"
export TWILIO_WEBHOOK_URL="https://your-webhook-url.com"
```

### 2. Install Dependencies

```bash
pip install twilio plyer pyyaml tabulate numpy
```

### 3. Run the System

```python
from twin_decision_loop import TwinDecisionLoop
from twin_decision_loop import ExampleActionHandlers
import asyncio

async def main():
    # Create twin
    twin = TwinDecisionLoop()
    
    # Register action handlers
    handlers = ExampleActionHandlers()
    twin.register_action_handler('email_send', handlers.handle_email_send)
    twin.register_action_handler('task_create', handlers.handle_task_create)
    
    # Start twin
    await twin.start()

# Run the twin
asyncio.run(main())
```

### 4. Queue Actions

```python
# Queue a routine action (auto-executed)
await twin.queue_action({
    'type': 'reminder_set',
    'target': 'self', 
    'content': 'Review quarterly numbers',
    'context': {}
})

# Queue a critical action (requires approval)
await twin.queue_action({
    'type': 'email_send',
    'target': 'CEO@company.com',
    'content': 'Urgent: Q4 numbers ready',
    'context': {'urgent': True}
})
```

## 📱 Managing Approvals

### CLI Commands

```bash
# List pending approvals
python cli_extensions.py list

# Show detailed request
python cli_extensions.py show abc123

# Approve a request  
python cli_extensions.py approve abc123 --feedback "Looks good"

# Deny a request
python cli_extensions.py deny abc123 --feedback "Too risky"

# Defer for 30 minutes
python cli_extensions.py defer abc123 --minutes 30

# Show approval history
python cli_extensions.py history --limit 50

# Show system statistics
python cli_extensions.py stats

# Interactive mode
python cli_extensions.py interactive
```

### SMS/Call Responses

When you receive an alert, respond:
- **"YES"** or **"1"** to approve
- **"NO"** or **"2"** to deny  
- **"DEFER"** or **"3"** to postpone

## ⚙️ Configuration

### Criticality Rules (`config/criticality_rules.yaml`)

```yaml
# VIP contacts requiring high criticality
vip_contacts:
  - "CEO"
  - "Investor" 
  - "Board Member"

# Action type defaults
action_defaults:
  email_send: "medium"
  call_make: "high"
  reminder_set: "low"

# Keyword patterns
keyword_patterns:
  high: ["urgent", "critical", "emergency"]
  medium: ["important", "review", "meeting"]
  low: ["fyi", "archive", "reminder"]
```

### Alert Configuration

Set up different alert channels:

```json
{
  "channels": {
    "sms": {
      "type": "twilio_sms",
      "enabled": true
    },
    "call": {
      "type": "twilio_call", 
      "enabled": true
    },
    "notification": {
      "type": "desktop",
      "enabled": true
    }
  }
}
```

## 🧠 Learning System

The twin learns from your decisions:

- **High approval rate (>95%)** → Future similar actions auto-execute
- **Frequent denials** → Increase criticality for similar actions  
- **Quick responses** → Reduce timeout windows
- **Time patterns** → Adjust criticality based on business hours

### Learning Insights

```python
insights = twin.feedback_tracker.get_learning_insights()
print(f"Approval rate: {insights['approval_rate']:.1%}")
print(f"Common approved patterns: {insights['common_approved_patterns']}")
```

## 📊 Monitoring

### Real-time Statistics

```python
stats = twin.get_stats()
print(f"Actions processed: {stats['actions_processed']}")
print(f"Auto-executed: {stats['auto_executed']}")  
print(f"Human approved: {stats['human_approved']}")
```

### Memory System Status

```python
memory_stats = twin.memory_streamer.get_stats()
print(f"Updates processed: {memory_stats['processed_count']}")
print(f"Queue size: {memory_stats['queue_size']}")
```

## 🔧 Customization

### Custom Action Handlers

```python
async def handle_calendar_create(action: Dict[str, Any]) -> bool:
    """Custom handler for calendar events"""
    event_data = action.get('content', {})
    
    # Your custom logic here
    success = await my_calendar_api.create_event(event_data)
    
    return success

# Register the handler
twin.register_action_handler('calendar_create', handle_calendar_create)
```

### Custom Alert Channels

```python
class SlackAlertChannel(AlertChannel):
    async def send(self, message: str, request_id: str) -> bool:
        # Implement Slack notification
        return await slack_client.send_message(message)

# Register custom channel
dispatcher.channels['slack'] = SlackAlertChannel()
```

## 🛡️ Security Considerations

- **Environment Variables**: Never commit Twilio credentials to version control
- **VIP Classification**: Ensure all sensitive contacts are in `vip_contacts` list
- **Timeout Settings**: Configure appropriate timeouts for different criticality levels
- **Webhook Security**: Use HTTPS and validate Twilio webhook signatures

## 📈 Scaling

For production deployment:

1. **Database Integration**: Replace JSON storage with PostgreSQL/MongoDB
2. **Message Queue**: Use Redis/RabbitMQ for action queue
3. **Monitoring**: Add Prometheus metrics and Grafana dashboards  
4. **Load Balancing**: Distribute across multiple instances
5. **Webhook Infrastructure**: Deploy webhook handlers on secure endpoints

## 🐛 Troubleshooting

### Common Issues

**SMS not sending:**
```bash
# Check Twilio credentials
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN

# Test connection
python -c "from twilio.rest import Client; print(Client().api.accounts.list())"
```

**High memory usage:**
```python
# Check memory system stats
stats = twin.memory_streamer.get_stats()
if stats['queue_size'] > 1000:
    print("Memory queue backlog detected")
```

**Missing approvals:**
```bash
# Check pending requests
python cli_extensions.py list

# Check approval history for patterns
python cli_extensions.py history --limit 100
```

## 🎯 Next Steps (Phase 9)

- 📱 Mobile app for approval management
- 🎤 Voice-activated responses  
- 📅 Calendar integration for "Do Not Disturb" modes
- 🤖 Advanced AI for context-aware decisions
- 📊 Rich analytics dashboard
- 🔄 Multi-user approval workflows

---

**Phase 8 Complete!** 🎉 Your digital twin now operates as a trustworthy autonomous agent with intelligent human oversight.