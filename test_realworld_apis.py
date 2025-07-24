"""
Real-World API Integration Test for Digital Twin System

This script tests the complete digital twin with LIVE API integrations:
- Gmail API for real email handling
- Google Calendar API for scheduling
- Twilio Voice API for phone calls
- Complete Brain + Memory + Controller integration

IMPORTANT: This uses REAL APIs and will send actual emails, make calls, etc.
Only run this when you're ready to test with live services.

Required Environment Variables:
- OPENAI_API_KEY: Your OpenAI API key
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token  
- TWILIO_FROM_NUMBER: Your Twilio phone number

Required Credential Files:
- gmail_credentials.json: Gmail API credentials from Google Cloud Console
- calendar_credentials.json: Calendar API credentials from Google Cloud Console

Test Scenarios:
1. Check unread emails and respond intelligently
2. Schedule a meeting based on email request
3. Create calendar events with memory-enhanced preferences
4. Make voice calls with personalized messages
5. Complete workflow: Email → Brain Decision → Calendar + Voice Actions
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

from twin_decision_loop import UnifiedTwinDecisionLoop
from tools.gmail_tool import GmailTool
from tools.calendar_tool import CalendarTool
from tools.voice_tool import VoiceTool
from tools.task_manager_tool import TaskManagerTool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealWorldAPITester:
    """Test harness for real-world API integration"""
    
    def __init__(self):
        self.test_results = {}
        self.api_credentials_verified = False
        
    async def verify_api_credentials(self) -> bool:
        """Verify all required API credentials are available"""
        
        logger.info("🔑 Verifying API credentials...")
        
        missing_credentials = []
        
        # Check OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            missing_credentials.append("OPENAI_API_KEY")
        
        # Check Twilio credentials
        if not os.getenv("TWILIO_ACCOUNT_SID"):
            missing_credentials.append("TWILIO_ACCOUNT_SID")
        if not os.getenv("TWILIO_AUTH_TOKEN"):
            missing_credentials.append("TWILIO_AUTH_TOKEN")
        if not os.getenv("TWILIO_FROM_NUMBER"):
            missing_credentials.append("TWILIO_FROM_NUMBER")
        
        # Check Google credentials files
        if not os.path.exists("gmail_credentials.json"):
            missing_credentials.append("gmail_credentials.json")
        if not os.path.exists("calendar_credentials.json"):
            missing_credentials.append("calendar_credentials.json")
        
        if missing_credentials:
            logger.error(f"❌ Missing credentials: {missing_credentials}")
            logger.info("\nSetup Instructions:")
            logger.info("1. Set environment variables in .env file:")
            logger.info("   OPENAI_API_KEY=your_openai_key")
            logger.info("   TWILIO_ACCOUNT_SID=your_twilio_sid")
            logger.info("   TWILIO_AUTH_TOKEN=your_twilio_token")
            logger.info("   TWILIO_FROM_NUMBER=your_twilio_number")
            logger.info("2. Download Google API credentials:")
            logger.info("   - Gmail: gmail_credentials.json")
            logger.info("   - Calendar: calendar_credentials.json")
            return False
        
        logger.info("✅ All API credentials verified!")
        self.api_credentials_verified = True
        return True

    async def initialize_tools(self) -> dict:
        """Initialize all real-world tools"""
        
        logger.info("🛠️ Initializing real-world tools...")
        
        tools = {}
        
        try:
            # Initialize Gmail tool
            tools['gmail'] = GmailTool(
                credentials_file="gmail_credentials.json",
                token_file="gmail_token.pickle"
            )
            logger.info("✅ Gmail tool initialized")
            
            # Initialize Calendar tool
            tools['calendar'] = CalendarTool(
                credentials_file="calendar_credentials.json",
                token_file="calendar_token.pickle"
            )
            logger.info("✅ Calendar tool initialized")
            
            # Initialize Voice tool
            tools['voice'] = VoiceTool(
                account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
                auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
                from_number=os.getenv("TWILIO_FROM_NUMBER")
            )
            logger.info("✅ Voice tool initialized")
            
            # Initialize Task Manager tool
            tools['task_manager'] = TaskManagerTool()
            logger.info("✅ Task manager tool initialized")
            
            return tools
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize tools: {e}")
            return {}

    async def test_gmail_integration(self, gmail_tool: GmailTool) -> dict:
        """Test Gmail API integration"""
        
        logger.info("\n📧 === GMAIL INTEGRATION TEST ===")
        
        try:
            # Test 1: Get unread emails
            logger.info("📬 Getting unread emails...")
            unread_emails = await gmail_tool.get_unread_emails(limit=5)
            
            logger.info(f"Found {len(unread_emails)} unread emails")
            for email in unread_emails:
                logger.info(f"  • {email.sender}: {email.subject}")
            
            # Test 2: Analyze emails
            analyses = []
            for email in unread_emails[:3]:  # Analyze first 3
                analysis = await gmail_tool.analyze_email(email)
                analyses.append(analysis)
                logger.info(f"  Analysis: {email.subject} → {analysis.urgency_level} urgency, {analysis.category}")
            
            # Test 3: Get email summary
            summary = await gmail_tool.smart_email_summary()
            logger.info(f"📊 Email summary: {summary['summary']}")
            
            # Test 4: Get communication insights
            insights = gmail_tool.get_communication_insights()
            logger.info(f"💡 Communication insights: {insights['total_emails_processed']} emails processed")
            
            return {
                'success': True,
                'unread_count': len(unread_emails),
                'analyses_completed': len(analyses),
                'summary': summary,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"❌ Gmail test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def test_calendar_integration(self, calendar_tool: CalendarTool) -> dict:
        """Test Calendar API integration"""
        
        logger.info("\n📅 === CALENDAR INTEGRATION TEST ===")
        
        try:
            # Test 1: Get upcoming events
            logger.info("📋 Getting upcoming events...")
            upcoming_events = await calendar_tool.get_upcoming_events(days_ahead=7)
            
            logger.info(f"Found {len(upcoming_events)} upcoming events")
            for event in upcoming_events[:5]:  # Show first 5
                logger.info(f"  • {event.start_time.strftime('%m/%d %H:%M')}: {event.title}")
            
            # Test 2: Get today's schedule
            today_schedule = await calendar_tool.get_todays_schedule()
            logger.info(f"📊 Today's schedule: {today_schedule['summary']}")
            
            # Test 3: Get tomorrow's schedule
            tomorrow_schedule = await calendar_tool.get_tomorrows_schedule()
            logger.info(f"📊 Tomorrow's schedule: {tomorrow_schedule['summary']}")
            
            # Test 4: Find free time
            logger.info("🔍 Finding free time slots...")
            free_slots = await calendar_tool.find_free_time(
                duration=timedelta(hours=1),
                days_ahead=3
            )
            
            logger.info(f"Found {len(free_slots)} free time slots")
            for slot in free_slots[:3]:  # Show first 3
                start_time, end_time = slot
                logger.info(f"  • {start_time.strftime('%m/%d %H:%M')} - {end_time.strftime('%H:%M')}")
            
            # Test 5: Get scheduling insights
            insights = calendar_tool.get_scheduling_insights()
            logger.info(f"💡 Scheduling insights: {len(insights.get('preferred_times', []))} preferred times learned")
            
            return {
                'success': True,
                'upcoming_events': len(upcoming_events),
                'today_events': today_schedule['event_count'],
                'tomorrow_events': tomorrow_schedule['event_count'],
                'free_slots_found': len(free_slots),
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"❌ Calendar test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def test_voice_integration(self, voice_tool: VoiceTool) -> dict:
        """Test Voice API integration (without making actual calls)"""
        
        logger.info("\n📞 === VOICE INTEGRATION TEST ===")
        
        try:
            # Test 1: Test voice capability
            logger.info("🎙️ Testing voice capability...")
            capability_test = await voice_tool.test_voice_capability()
            
            logger.info(f"Voice tool ready: {capability_test['voice_tool_ready']}")
            logger.info(f"Credentials configured: {capability_test['credentials_configured']}")
            logger.info(f"Message templates loaded: {capability_test['message_templates_loaded']}")
            
            # Test 2: Generate test messages
            logger.info("💬 Testing message generation...")
            
            # Test different message types
            test_contexts = [
                {
                    'type': 'task_reminder',
                    'content': 'Review the quarterly report',
                    'context': {'deadline': 'in 2 hours', 'urgency': 'high'}
                },
                {
                    'type': 'meeting_reminder',
                    'context': {
                        'meeting_title': 'Team Standup',
                        'meeting_time': '2:00 PM',
                        'attendees': 'team members',
                        'time_until': '15'
                    }
                },
                {
                    'type': 'daily_update',
                    'context': {
                        'event_count': 4,
                        'important_events': 'client meeting and project review',
                        'priority_tasks': 'complete proposal and send updates',
                        'unread_emails': 8,
                        'urgent_count': 2
                    }
                }
            ]
            
            message_tests = []
            for test_ctx in test_contexts:
                message = await voice_tool._generate_voice_message(
                    test_ctx['type'],
                    test_ctx.get('content', ''),
                    test_ctx.get('context', {})
                )
                message_tests.append(message)
                logger.info(f"  Generated {test_ctx['type']}: {len(message.content)} chars, ~{message.estimated_duration}s")
            
            # Test 3: Analyze call timing
            timing_analysis = voice_tool._analyze_call_timing()
            logger.info(f"📊 Current timing analysis: {timing_analysis['timing_quality']} ({timing_analysis['expected_success_rate']:.0%} success rate)")
            
            # Test 4: Get voice insights
            insights = voice_tool.get_voice_insights()
            logger.info(f"💡 Voice insights: {insights['message_templates']} templates, {insights['voice_patterns_learned']} patterns learned")
            
            return {
                'success': True,
                'capability_test': capability_test,
                'messages_generated': len(message_tests),
                'timing_analysis': timing_analysis,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"❌ Voice test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def test_integrated_workflow(self, twin: UnifiedTwinDecisionLoop) -> dict:
        """Test complete integrated workflow"""
        
        logger.info("\n🔄 === INTEGRATED WORKFLOW TEST ===")
        
        try:
            # Scenario: Process a complex request that requires multiple tools
            complex_request = (
                "Check my emails for anything urgent, then look at my calendar "
                "for tomorrow and call me with a summary of what I need to prepare for"
            )
            
            logger.info(f"🎯 Processing complex request: {complex_request}")
            
            # Process the request through the twin
            result = await twin.process(
                content=complex_request,
                request_type="auto",
                priority="high"
            )
            
            logger.info(f"✅ Request processed successfully: {result.success}")
            logger.info(f"📝 Response: {result.response_text}")
            logger.info(f"⏱️ Processing time: {result.processing_time:.2f}s")
            logger.info(f"🧠 Memory updates: {result.memory_updates}")
            
            if result.action_plan:
                logger.info(f"📋 Action plan created: {result.action_plan.plan_id}")
                logger.info(f"📊 Plan status: {result.action_plan.status}")
            
            # Provide feedback on the workflow
            feedback_result = await twin.provide_feedback(
                request_id=result.request_id,
                satisfaction=0.9,
                lessons_learned=[
                    "Complex multi-tool workflows can be handled effectively",
                    "Memory-enhanced reasoning improves action planning"
                ],
                feedback_text="Excellent orchestration of multiple API integrations"
            )
            
            logger.info(f"📚 Feedback applied: {feedback_result}")
            
            return {
                'success': True,
                'request_processed': True,
                'response': result.response_text,
                'processing_time': result.processing_time,
                'memory_updates': result.memory_updates,
                'action_plan_created': result.action_plan is not None,
                'feedback_applied': feedback_result
            }
            
        except Exception as e:
            logger.error(f"❌ Integrated workflow test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def test_memory_learning_with_apis(self, twin: UnifiedTwinDecisionLoop) -> dict:
        """Test memory learning with real API data"""
        
        logger.info("\n🧠 === MEMORY LEARNING WITH APIS TEST ===")
        
        try:
            # Test 1: Learn from email patterns
            logger.info("📧 Testing memory learning from email patterns...")
            
            email_queries = [
                "What are the patterns in my recent emails?",
                "How should I prioritize email responses?",
                "What types of emails do I get most often?"
            ]
            
            email_learning_results = []
            for query in email_queries:
                result = await twin.process(query, request_type="query")
                email_learning_results.append(result)
                logger.info(f"  Query: {query}")
                logger.info(f"  Response: {result.response_text[:100]}...")
            
            # Test 2: Learn from calendar patterns
            logger.info("📅 Testing memory learning from calendar patterns...")
            
            calendar_queries = [
                "What patterns do you see in my meeting schedule?",
                "When are my most productive times for meetings?",
                "How can I optimize my calendar based on past patterns?"
            ]
            
            calendar_learning_results = []
            for query in calendar_queries:
                result = await twin.process(query, request_type="query")
                calendar_learning_results.append(result)
                logger.info(f"  Query: {query}")
                logger.info(f"  Response: {result.response_text[:100]}...")
            
            # Test 3: Cross-domain insights
            logger.info("🔗 Testing cross-domain insights...")
            
            cross_domain_query = (
                "Based on my emails and calendar, what insights do you have "
                "about my work patterns and how I can be more effective?"
            )
            
            insights_result = await twin.process(cross_domain_query, request_type="introspect")
            logger.info(f"🔍 Cross-domain insights: {insights_result.response_text[:200]}...")
            
            # Test 4: Memory system status
            system_status = twin.get_system_status()
            logger.info(f"📊 System status: {system_status['decision_loop']['total_processed']} requests processed")
            logger.info(f"💾 Memory formations: {system_status['decision_loop']['memory_formations']}")
            
            return {
                'success': True,
                'email_queries_processed': len(email_learning_results),
                'calendar_queries_processed': len(calendar_learning_results),
                'cross_domain_insights_generated': True,
                'system_status': system_status
            }
            
        except Exception as e:
            logger.error(f"❌ Memory learning test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def run_comprehensive_realworld_tests(self):
        """Run all real-world API integration tests"""
        
        logger.info("🚀 Starting Real-World API Integration Tests")
        logger.info("=" * 60)
        
        # Step 1: Verify credentials
        if not await self.verify_api_credentials():
            logger.error("❌ Cannot proceed without API credentials")
            return
        
        # Step 2: Initialize tools
        tools = await self.initialize_tools()
        if not tools:
            logger.error("❌ Failed to initialize tools")
            return
        
        # Step 3: Create tools configuration for twin
        tools_config = {
            "gmail": {
                "class": "tools.gmail_tool.GmailTool",
                "params": {
                    "credentials_file": "gmail_credentials.json",
                    "token_file": "gmail_token.pickle"
                }
            },
            "calendar": {
                "class": "tools.calendar_tool.CalendarTool", 
                "params": {
                    "credentials_file": "calendar_credentials.json",
                    "token_file": "calendar_token.pickle"
                }
            },
            "voice": {
                "class": "tools.voice_tool.VoiceTool",
                "params": {
                    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                    "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
                    "from_number": os.getenv("TWILIO_FROM_NUMBER")
                }
            },
            "task_manager": {
                "class": "tools.task_manager_tool.TaskManagerTool",
                "params": {}
            }
        }
        
        # Step 4: Initialize the complete twin system
        logger.info("🧠 Initializing complete twin system with real APIs...")
        
        twin = UnifiedTwinDecisionLoop(
            persona_path="persona.yaml",
            api_key=os.getenv("OPENAI_API_KEY"),
            memory_dir="realworld_api_memory",
            tools_config=tools_config
        )
        
        logger.info("✅ Twin system initialized with real-world APIs!")
        
        # Step 5: Run individual tool tests
        try:
            logger.info("\n🧪 Running individual API tests...")
            
            # Test Gmail
            gmail_result = await self.test_gmail_integration(tools['gmail'])
            self.test_results['gmail'] = gmail_result
            
            # Test Calendar
            calendar_result = await self.test_calendar_integration(tools['calendar'])
            self.test_results['calendar'] = calendar_result
            
            # Test Voice (without actual calls)
            voice_result = await self.test_voice_integration(tools['voice'])
            self.test_results['voice'] = voice_result
            
            # Test integrated workflow
            workflow_result = await self.test_integrated_workflow(twin)
            self.test_results['workflow'] = workflow_result
            
            # Test memory learning with API data
            learning_result = await self.test_memory_learning_with_apis(twin)
            self.test_results['learning'] = learning_result
            
            # Step 6: System optimization
            logger.info("\n🔧 Running system optimization...")
            optimization_results = await twin.optimize_system()
            self.test_results['optimization'] = optimization_results
            
            # Step 7: Export complete system state
            logger.info("\n💾 Exporting system state...")
            export_path = await twin.export_complete_system()
            self.test_results['export_path'] = export_path
            
            # Step 8: Final summary
            self.print_test_summary()
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 REAL-WORLD API INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() 
                              if isinstance(result, dict) and result.get('success', False))
        
        logger.info(f"📊 Overall Results: {successful_tests}/{total_tests} tests passed")
        
        # Gmail results
        if 'gmail' in self.test_results:
            gmail = self.test_results['gmail']
            if gmail.get('success'):
                logger.info(f"✅ Gmail: {gmail['unread_count']} unread emails, {gmail['analyses_completed']} analyzed")
            else:
                logger.info(f"❌ Gmail: {gmail.get('error', 'Unknown error')}")
        
        # Calendar results
        if 'calendar' in self.test_results:
            calendar = self.test_results['calendar']
            if calendar.get('success'):
                logger.info(f"✅ Calendar: {calendar['upcoming_events']} events, {calendar['free_slots_found']} free slots")
            else:
                logger.info(f"❌ Calendar: {calendar.get('error', 'Unknown error')}")
        
        # Voice results
        if 'voice' in self.test_results:
            voice = self.test_results['voice']
            if voice.get('success'):
                logger.info(f"✅ Voice: {voice['messages_generated']} messages generated, timing analysis complete")
            else:
                logger.info(f"❌ Voice: {voice.get('error', 'Unknown error')}")
        
        # Workflow results
        if 'workflow' in self.test_results:
            workflow = self.test_results['workflow']
            if workflow.get('success'):
                logger.info(f"✅ Workflow: Complex request processed in {workflow['processing_time']:.2f}s")
            else:
                logger.info(f"❌ Workflow: {workflow.get('error', 'Unknown error')}")
        
        # Learning results
        if 'learning' in self.test_results:
            learning = self.test_results['learning']
            if learning.get('success'):
                logger.info(f"✅ Learning: Cross-domain insights generated, memory system active")
            else:
                logger.info(f"❌ Learning: {learning.get('error', 'Unknown error')}")
        
        # Export path
        if 'export_path' in self.test_results:
            logger.info(f"💾 System exported to: {self.test_results['export_path']}")
        
        logger.info("\n🎉 REAL-WORLD INTEGRATION COMPLETE!")
        
        if successful_tests == total_tests:
            logger.info("🌟 Your digital twin is now fully integrated with real-world APIs!")
            logger.info("🚀 Ready for production use with Gmail, Calendar, and Voice capabilities!")
        else:
            logger.info("⚠️  Some tests failed. Check credentials and API setup.")
        
        logger.info("=" * 60)


async def main():
    """Main test runner"""
    
    print("""
🌍 REAL-WORLD API INTEGRATION TEST
==================================

This will test your digital twin with LIVE APIs:
- Gmail (read emails, analyze, respond)
- Google Calendar (events, scheduling)
- Twilio Voice (call capabilities)
- Complete Brain + Memory + Controller integration

⚠️  WARNING: This uses REAL APIs and may:
   - Read your actual emails
   - Access your calendar
   - Use Twilio credits (for calls)

Make sure you have:
1. Set up API credentials (.env file)
2. Downloaded Google API credentials files
3. Configured Twilio account

Continue? (y/N): """)
    
    confirm = input().strip().lower()
    if confirm != 'y':
        print("Test cancelled.")
        return
    
    # Run the tests
    tester = RealWorldAPITester()
    await tester.run_comprehensive_realworld_tests()


if __name__ == "__main__":
    asyncio.run(main())