"""
Example Integration: "Call me at 3:30 and remind me of tasks"

This example shows how all the components work together to handle
a complex, time-based, multi-tool request.
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import our modules
from digital_twin import DigitalTwin, Situation
from twin_controller import TwinController
from scheduler import TwinScheduler
from memory_interface import ChromaMemory, MemoryManager
from tools.voice_tool import VoiceTool
from tools.task_manager_tool import TaskManagerTool


async def setup_digital_twin_system():
    """
    Set up the complete digital twin system with all components.
    """
    
    # Load environment variables
    load_dotenv()
    
    print("🧠 Initializing Digital Twin System...")
    
    # 1. Initialize the brain
    twin = DigitalTwin(
        persona_path="persona.yaml",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 2. Initialize memory
    memory = ChromaMemory()
    memory_manager = MemoryManager(memory)
    twin.set_memory_interface(memory)
    
    # 3. Initialize controller
    controller = TwinController(twin, memory_manager)
    
    # 4. Initialize scheduler
    scheduler = TwinScheduler()
    await scheduler.start()
    controller.set_scheduler(scheduler)
    
    # 5. Initialize and register tools
    
    # Voice tool for making calls
    voice_tool = VoiceTool(
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER")
    )
    controller.register_tool("voice", voice_tool)
    
    # Task manager for getting tasks
    task_manager = TaskManagerTool()
    controller.register_tool("task_manager", task_manager)
    
    print("✅ System initialized successfully!")
    
    return controller, scheduler, task_manager


async def demonstrate_reminder_call():
    """
    Demonstrate the complete flow of scheduling a reminder call.
    """
    
    # Set up the system
    controller, scheduler, task_manager = await setup_digital_twin_system()
    
    # Create some sample tasks first
    print("\n📝 Creating sample tasks...")
    task_manager.create_task(
        title="Finish project presentation",
        priority="high",
        deadline=datetime.now() + timedelta(hours=4),
        tags=["work", "urgent"]
    )
    
    task_manager.create_task(
        title="Review code changes",
        priority="normal",
        deadline=datetime.now() + timedelta(days=1),
        tags=["work"]
    )
    
    task_manager.create_task(
        title="Call dentist for appointment",
        priority="normal",
        tags=["personal", "health"]
    )
    
    # User request: "Call me at 3:30 and remind me of tasks"
    user_request = "Call me at 3:30 PM and remind me of what needs to be done today"
    
    print(f"\n🗣️ User: '{user_request}'")
    
    # Process the request
    context = {
        "user_phone": os.getenv("USER_PHONE_NUMBER", "+1234567890"),
        "current_time": datetime.now().strftime("%I:%M %p")
    }
    
    print("\n🤖 Processing request...")
    plan = await controller.process_request(user_request, context)
    
    print(f"\n📋 Created action plan:")
    print(f"   ID: {plan.id}")
    print(f"   Intent: {plan.intent}")
    print(f"   Scheduled for: {plan.scheduled_time}")
    print(f"   Status: {plan.status.value}")
    print(f"\n   Steps:")
    for i, step in enumerate(plan.steps, 1):
        print(f"   {i}. {step['tool']}.{step['action']}")
    
    # Show what would happen at 3:30 PM
    print("\n⏰ At 3:30 PM, the system will:")
    print("   1. Retrieve pending tasks for today")
    print("   2. Format them into a natural speech message")
    print("   3. Call your phone and deliver the reminder")
    
    # Simulate immediate execution for demo
    print("\n🎭 Demo: Simulating immediate execution...")
    
    # Get tasks that would be spoken
    pending_tasks = task_manager.get_pending_tasks(timeframe="today")
    print(f"\n📋 Found {len(pending_tasks)} tasks for today:")
    for task in pending_tasks:
        print(f"   - {task['title']} (Priority: {task['priority']})")
        if 'deadline' in task:
            print(f"     Due: {task['deadline']}")
    
    # Show scheduled actions
    print("\n⏱️ Currently scheduled actions:")
    scheduled = scheduler.get_scheduled_actions()
    for action in scheduled:
        print(f"   - {action.id}: Scheduled for {action.next_execution}")
    
    # Clean up
    await scheduler.stop()
    
    print("\n✅ Demo completed!")


async def demonstrate_morning_routine():
    """
    Demonstrate a more complex morning routine automation.
    """
    
    controller, scheduler, task_manager = await setup_digital_twin_system()
    
    print("\n🌅 Setting up morning routine...")
    
    # Schedule daily morning briefing
    success = scheduler.schedule_recurring_reminder(
        action_id="morning_briefing",
        time_of_day="08:00",  # 8 AM every day
        callback=lambda: asyncio.create_task(
            controller.process_request(
                "Check my calendar and tasks, then call me with a morning briefing",
                {"user_phone": os.getenv("USER_PHONE_NUMBER")}
            )
        )
    )
    
    if success:
        print("✅ Morning briefing scheduled for 8:00 AM daily")
    
    # The routine would:
    # 1. Get today's calendar events (when calendar tool is added)
    # 2. Get high-priority tasks
    # 3. Check weather (when weather tool is added)
    # 4. Make a comprehensive briefing call
    
    await scheduler.stop()


async def demonstrate_learning():
    """
    Demonstrate how the twin learns from feedback.
    """
    
    controller, scheduler, task_manager = await setup_digital_twin_system()
    
    print("\n🧠 Demonstrating learning from feedback...")
    
    # Simulate a decision
    situation = Situation(
        context="Colleague wants to schedule a meeting during your usual lunch break",
        category="scheduling_conflict",
        metadata={"requester": "colleague", "time": "12:30 PM"}
    )
    
    # Get twin's prediction
    response = controller.twin.reason(situation)
    print(f"\n🤖 Twin predicts: {response.action}")
    print(f"   Reasoning: {response.reasoning}")
    
    # User actually did something different
    actual_action = "Agreed to meeting but requested it end by 1:15 PM to preserve some lunch time"
    
    print(f"\n👤 You actually: {actual_action}")
    
    # Twin learns from this
    learning = controller.twin.learn_from_feedback(
        situation=situation,
        actual_action=actual_action,
        feedback="Good compromise - maintained boundary while being flexible"
    )
    
    print("\n✅ Twin has learned from this interaction!")
    print("   Next time, it will consider this compromise approach")
    
    await scheduler.stop()


async def main():
    """
    Main demonstration entry point.
    """
    
    print("🚀 Digital Twin Controller Integration Demo")
    print("=" * 50)
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set them in your .env file")
        return
    
    while True:
        print("\nChoose a demo:")
        print("1. Schedule reminder call at 3:30 PM")
        print("2. Set up morning routine")
        print("3. Demonstrate learning from feedback")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            await demonstrate_reminder_call()
        elif choice == "2":
            await demonstrate_morning_routine()
        elif choice == "3":
            await demonstrate_learning()
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    asyncio.run(main())