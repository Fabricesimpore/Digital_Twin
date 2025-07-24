# Digital Twin Brain Module 🧠

A modular, learning system that creates a digital twin of your thinking patterns, decision-making process, and behavioral habits.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Customize Your Persona

Edit `persona.yaml` to match your actual traits, values, and preferences. This is crucial for accurate twin behavior.

### 4. Run the Test Suite

```bash
python test_brain.py
```

This will simulate various scenarios and show how your twin would respond.

## Architecture

### Core Components

1. **Identity Layer** (`persona.yaml`)
   - Personality traits
   - Values and principles
   - Communication style
   - Work preferences
   - Decision patterns

2. **Reasoning Layer** (`digital_twin.py`)
   - Combines context + memory + identity
   - Uses GPT-4o for nuanced reasoning
   - Returns actions with confidence scores

3. **Memory Layer** (`memory_interface.py`)
   - Vector database (Chroma) for semantic search
   - Stores decisions, patterns, and learnings
   - Retrieves relevant context for decisions

## Usage Example

```python
from digital_twin import DigitalTwin, Situation

# Initialize your twin
twin = DigitalTwin(persona_path="persona.yaml", api_key="your-key")

# Create a situation
situation = Situation(
    context="Important client emailed about urgent bug",
    category="email",
    metadata={"sender": "client@company.com", "urgency": "high"}
)

# Get your twin's response
response = twin.reason(situation)
print(f"Your twin would: {response.action}")
print(f"Because: {response.reasoning}")
```

## Adding Memory

```python
from memory_interface import ChromaMemory, MemoryManager

# Initialize memory
memory = ChromaMemory()
manager = MemoryManager(memory)

# Remember a decision
manager.remember_decision(
    context="Client asked for rush delivery",
    decision="Agreed but negotiated 20% rush fee",
    reasoning="Maintains boundaries while accommodating client needs"
)

# Remember a preference
manager.remember_preference(
    category="work_hours",
    preference="No meetings before 9am",
    strength="strong"
)
```

## Next Steps

### Week 1: Behavioral Data Collection
- [ ] Connect Gmail API to observe email patterns
- [ ] Log your actual decisions vs twin predictions
- [ ] Fine-tune persona.yaml based on observations

### Week 2: Integration
- [ ] Add calendar integration
- [ ] Implement WhatsApp/Slack monitoring
- [ ] Build learning feedback loop

### Week 3: Automation
- [ ] Add tool use (browser, desktop control)
- [ ] Implement voice interface (Twilio + Whisper)
- [ ] Create autonomous task execution

## Key Design Decisions

1. **Modular Architecture**: Each layer (identity, reasoning, memory) is independent and replaceable

2. **LLM-Powered Reasoning**: Uses GPT-4o for complex reasoning while maintaining your specific identity

3. **Local-First Memory**: Chroma DB runs locally, keeping your data private

4. **Learning Loop**: Twin observes, predicts, and learns from corrections

5. **Extensible**: Ready for Gmail, Calendar, WhatsApp, and tool integrations

## Customization Tips

- **Persona Tuning**: The more accurate your persona.yaml, the better your twin performs
- **Memory Seeding**: Pre-load important decisions and patterns
- **Confidence Threshold**: Adjust when the twin should ask vs act autonomously

## Privacy & Security

- All data stored locally by default
- API keys never logged or stored in memory
- Decisions logged for learning can be encrypted

## Future Enhancements

- Real-time behavior shadowing
- Multi-modal inputs (voice, images)
- Emotional state modeling
- Creative output generation
- Team/relationship dynamics

---

Ready to build your digital self? Start by running the tests and customizing your persona!