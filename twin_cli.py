"""
Digital Twin Interactive CLI

A user-friendly command-line interface for interacting with your digital twin.
This provides an easy way to:
- Chat with your twin and get responses
- Ask memory questions and get insights
- Execute actions through the controller
- Monitor system status and performance
- Export and manage twin data

Usage:
    python twin_cli.py

Commands:
    chat <message>     - Have a conversation with your twin
    ask <question>     - Ask your twin's memory system
    action <request>   - Execute an action request
    schedule <request> - Schedule a future action
    introspect <query> - Deep introspection and self-analysis
    status             - Show system status
    memory             - Show memory statistics
    export             - Export twin data
    optimize           - Run system optimization
    help               - Show this help
    quit/exit          - Exit the CLI
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any

# Rich for beautiful CLI formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich not installed. Install with: pip install rich")

from dotenv import load_dotenv
from twin_decision_loop import UnifiedTwinDecisionLoop

# Load environment variables
load_dotenv()


class TwinCLI:
    """Interactive CLI for the Digital Twin"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.twin = None
        self.session_history = []
        self.running = False
        
        # Configure logging to be less verbose in CLI mode
        logging.basicConfig(level=logging.WARNING)
    
    def print(self, message: str, style: str = None):
        """Print with rich formatting if available"""
        if RICH_AVAILABLE and self.console:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)
    
    def print_panel(self, content: str, title: str = None, style: str = "blue"):
        """Print content in a panel"""
        if RICH_AVAILABLE and self.console:
            self.console.print(Panel(content, title=title, style=style))
        else:
            if title:
                print(f"\n=== {title} ===")
            print(content)
            print("=" * (len(title) + 8) if title else "")
    
    def print_error(self, message: str):
        """Print error message"""
        self.print(f"❌ {message}", style="red")
    
    def print_success(self, message: str):
        """Print success message"""
        self.print(f"✅ {message}", style="green")
    
    def print_info(self, message: str):
        """Print info message"""
        self.print(f"ℹ️  {message}", style="blue")
    
    async def initialize_twin(self) -> bool:
        """Initialize the digital twin system"""
        
        self.print_panel("🧠 Digital Twin Interactive CLI", "Welcome", "bright_blue")
        self.print("Initializing your digital twin system...", style="yellow")
        
        # Check for API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.print_error("OPENAI_API_KEY not found in environment variables")
            self.print("Please set your OpenAI API key in a .env file:")
            self.print("OPENAI_API_KEY=your_key_here")
            return False
        
        try:
            # Tools configuration (optional - will work without real API credentials)
            tools_config = {}
            
            # Check for optional tool credentials
            if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
                tools_config["voice"] = {
                    "class": "tools.voice_tool.VoiceTool",
                    "params": {
                        "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                        "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
                        "from_number": os.getenv("TWILIO_FROM_NUMBER")
                    }
                }
                self.print_info("Twilio voice integration enabled")
            
            if os.path.exists("gmail_credentials.json"):
                tools_config["gmail"] = {
                    "class": "tools.gmail_tool.GmailTool",
                    "params": {
                        "credentials_file": "gmail_credentials.json"
                    }
                }
                self.print_info("Gmail integration enabled")
            
            if os.path.exists("calendar_credentials.json"):
                tools_config["calendar"] = {
                    "class": "tools.calendar_tool.CalendarTool",
                    "params": {
                        "credentials_file": "calendar_credentials.json"
                    }
                }
                self.print_info("Calendar integration enabled")
            
            # Always include task manager
            tools_config["task_manager"] = {
                "class": "tools.task_manager_tool.TaskManagerTool",
                "params": {}
            }
            
            # Initialize the twin
            self.twin = UnifiedTwinDecisionLoop(
                persona_path="persona.yaml",
                api_key=api_key,
                memory_dir="cli_twin_memory",
                tools_config=tools_config if tools_config else None
            )
            
            self.print_success("Digital twin initialized successfully!")
            
            # Show system status
            status = self.twin.get_system_status()
            self.print_info(f"Memory system active with {status['brain']['episodic_memory']['total_memories']} episodic memories")
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to initialize twin: {e}")
            return False
    
    async def handle_chat(self, message: str):
        """Handle chat command"""
        
        if not message.strip():
            self.print_error("Please provide a message to chat about")
            return
        
        self.print_panel(f"💭 You: {message}", style="green")
        
        try:
            # Process through the twin
            result = await self.twin.process(
                content=message,
                request_type="query",
                priority="medium"
            )
            
            # Display response
            self.print_panel(f"🧠 Twin: {result.response_text}", "Response", "blue")
            
            # Show additional info if available
            if result.memory_updates > 0:
                self.print_info(f"Memory updated with {result.memory_updates} new formations")
            
            if result.lessons_learned:
                self.print_info(f"Applied {len(result.lessons_learned)} lessons from past experience")
            
            # Add to session history
            self.session_history.append({
                'type': 'chat',
                'input': message,
                'output': result.response_text,
                'timestamp': datetime.now().isoformat(),
                'processing_time': result.processing_time
            })
            
        except Exception as e:
            self.print_error(f"Chat failed: {e}")
    
    async def handle_ask(self, question: str):
        """Handle ask memory command"""
        
        if not question.strip():
            self.print_error("Please provide a question to ask your memory")
            return
        
        self.print_panel(f"🤔 Question: {question}", style="yellow")
        
        try:
            # Query memory directly
            memory_response = await self.twin.ask_memory(question)
            
            self.print_panel(f"🧠 Memory: {memory_response}", "Memory Response", "cyan")
            
            # Add to session history
            self.session_history.append({
                'type': 'memory_query',
                'input': question,
                'output': memory_response,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.print_error(f"Memory query failed: {e}")
    
    async def handle_action(self, request: str):
        """Handle action command"""
        
        if not request.strip():
            self.print_error("Please provide an action request")
            return
        
        self.print_panel(f"⚡ Action Request: {request}", style="bright_yellow")
        
        try:
            # Process as action through the twin
            result = await self.twin.process(
                content=request,
                request_type="action",
                priority="high"
            )
            
            # Display response
            self.print_panel(f"🎯 Result: {result.response_text}", "Action Result", "green")
            
            # Show action plan details if available
            if result.action_plan:
                plan = result.action_plan
                plan_info = f"Plan ID: {plan.plan_id}\n"
                plan_info += f"Status: {plan.status}\n"
                
                if hasattr(plan, 'steps'):
                    plan_info += f"Steps: {len(plan.steps)}"
                
                if plan.scheduled_time:
                    plan_info += f"\nScheduled: {plan.scheduled_time}"
                
                self.print_panel(plan_info, "Action Plan", "bright_green")
            
            # Add to session history
            self.session_history.append({
                'type': 'action',
                'input': request,
                'output': result.response_text,
                'timestamp': datetime.now().isoformat(),
                'success': result.success,
                'processing_time': result.processing_time
            })
            
        except Exception as e:
            self.print_error(f"Action failed: {e}")
    
    async def handle_schedule(self, request: str):
        """Handle schedule command"""
        
        if not request.strip():
            self.print_error("Please provide a scheduling request")
            return
        
        self.print_panel(f"📅 Schedule Request: {request}", style="bright_cyan")
        
        try:
            # Process as schedule through the twin
            result = await self.twin.process(
                content=request,
                request_type="schedule",
                priority="medium"
            )
            
            # Display response
            self.print_panel(f"⏰ Scheduled: {result.response_text}", "Schedule Result", "cyan")
            
            # Add to session history
            self.session_history.append({
                'type': 'schedule',
                'input': request,
                'output': result.response_text,
                'timestamp': datetime.now().isoformat(),
                'success': result.success
            })
            
        except Exception as e:
            self.print_error(f"Scheduling failed: {e}")
    
    async def handle_introspect(self, query: str):
        """Handle introspection command"""
        
        if not query.strip():
            self.print_error("Please provide an introspection question")
            return
        
        self.print_panel(f"🪞 Introspection: {query}", style="magenta")
        
        try:
            # Process as introspection
            result = await self.twin.process(
                content=query,
                request_type="introspect"
            )
            
            # Display insights
            self.print_panel(f"🔍 Insights: {result.response_text}", "Deep Analysis", "bright_magenta")
            
            # Add to session history
            self.session_history.append({
                'type': 'introspection',
                'input': query,
                'output': result.response_text,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.print_error(f"Introspection failed: {e}")
    
    def handle_status(self):
        """Handle status command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            status = self.twin.get_system_status()
            
            # Create status display
            status_text = f"""Decision Loop:
• Total requests processed: {status['decision_loop']['total_processed']}
• Success rate: {status['decision_loop']['success_rate']:.1%}
• Memory formations: {status['decision_loop']['memory_formations']}
• Patterns learned: {status['decision_loop']['patterns_learned']}

Brain Memory:
• Episodic memories: {status['brain']['episodic_memory']['total_memories']}
• Semantic memories: {status['brain']['semantic_memory']['total_memories']}

Session History:
• Commands executed: {len(self.session_history)}
• Chat messages: {len([h for h in self.session_history if h['type'] == 'chat'])}
• Actions performed: {len([h for h in self.session_history if h['type'] == 'action'])}"""
            
            self.print_panel(status_text, "System Status", "bright_blue")
            
        except Exception as e:
            self.print_error(f"Failed to get status: {e}")
    
    def handle_memory(self):
        """Handle memory command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            memory_summary = self.twin.brain.get_memory_summary()
            
            # Create memory display
            episodic_stats = memory_summary['episodic_memory']
            semantic_stats = memory_summary['semantic_memory']
            
            memory_text = f"""Episodic Memory (Specific Events):
• Total memories: {episodic_stats['total_memories']}
• Recent activity: {episodic_stats.get('recent_activity', 'N/A')}

Semantic Memory (Patterns & Knowledge):
• Total memories: {semantic_stats['total_memories']}
• Memory types: {len(semantic_stats.get('memory_types', {}))}

Current Session:
• Decisions made: {memory_summary['current_session']['decisions_made']}
• Reasoning modes used: {', '.join(set(memory_summary['current_session']['reasoning_modes_used']))}"""
            
            self.print_panel(memory_text, "Memory System", "bright_cyan")
            
        except Exception as e:
            self.print_error(f"Failed to get memory info: {e}")
    
    async def handle_export(self):
        """Handle export command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            self.print("Exporting twin system data...", style="yellow")
            
            # Export complete system
            export_path = await self.twin.export_complete_system()
            
            # Also export session history
            session_path = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_path, 'w') as f:
                json.dump(self.session_history, f, indent=2)
            
            self.print_success(f"System exported to: {export_path}")
            self.print_success(f"Session history exported to: {session_path}")
            
        except Exception as e:
            self.print_error(f"Export failed: {e}")
    
    async def handle_optimize(self):
        """Handle optimize command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            self.print("Running system optimization...", style="yellow")
            
            optimization_results = await self.twin.optimize_system()
            
            # Display results
            opt_text = f"""Memory Maintenance:
• Consolidated memories: {optimization_results['memory_maintenance'].get('consolidated_memories', 0)}
• Decayed memories: {optimization_results['memory_maintenance'].get('decayed_memories', 0)}
• New insights: {optimization_results['memory_maintenance'].get('new_insights', 0)}

System Insights:
{optimization_results['system_insights'][:300]}..."""
            
            self.print_panel(opt_text, "Optimization Results", "bright_green")
            
        except Exception as e:
            self.print_error(f"Optimization failed: {e}")
    
    def handle_observer_status(self):
        """Handle observer command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            # Get current context from observer
            current_context = self.twin.get_current_context()
            
            if current_context:
                context_text = f"""Current Activity:
• App: {current_context.current_app}
• Window: {current_context.current_window_title[:50]}...
• Category: {current_context.activity_category.value}
• State: {current_context.productivity_state}
• Session Duration: {current_context.current_session_duration_minutes} minutes
• Idle: {'Yes' if current_context.is_idle else 'No'} ({current_context.idle_duration_seconds}s)

Recent Activity:
{current_context.recent_activity_summary}"""
                
                self.print_panel(context_text, "Observer Status", "bright_blue")
            else:
                observer_available = hasattr(self.twin, 'observer_manager') and self.twin.observer_manager is not None
                
                if observer_available:
                    self.print_panel("Observer system is available but not currently active.\nUse 'start-observer' to begin passive behavior learning.", "Observer Status", "yellow")
                else:
                    self.print_panel("Observer system is not available.\nThis may be due to missing dependencies or disabled configuration.", "Observer Status", "red")
        
        except Exception as e:
            self.print_error(f"Failed to get observer status: {e}")
    
    def handle_behavioral_insights(self):
        """Handle insights command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            insights = self.twin.get_behavioral_insights()
            
            if 'status' in insights and insights['status'] == 'Observer system not available':
                self.print_panel("Observer system not available for behavioral insights.", "Insights", "red")
                return
            
            # Format insights display
            insights_text = "Behavioral Analysis:\n\n"
            
            # Activity patterns
            if 'activity_patterns' in insights:
                patterns = insights['activity_patterns']
                if 'most_active_hour' in patterns:
                    insights_text += f"• Most active hour: {patterns['most_active_hour']}:00\n"
                if 'most_productive_day' in patterns:
                    insights_text += f"• Most productive day: {patterns['most_productive_day']}\n"
            
            # Productivity insights
            if 'productivity_insights' in insights:
                prod_insights = insights['productivity_insights']
                if 'productivity_score' in prod_insights:
                    score = prod_insights['productivity_score'] * 100
                    insights_text += f"• Productivity score: {score:.1f}%\n"
                if 'productivity_trend' in prod_insights:
                    insights_text += f"• Productivity trend: {prod_insights['productivity_trend']}\n"
            
            # Focus patterns
            if 'focus_patterns' in insights:
                focus = insights['focus_patterns']
                if 'focus_sessions_count' in focus:
                    insights_text += f"• Focus sessions: {focus['focus_sessions_count']}\n"
                if 'average_focus_duration_minutes' in focus:
                    insights_text += f"• Avg focus duration: {focus['average_focus_duration_minutes']:.1f} min\n"
            
            # Anomalies
            if 'anomalies' in insights and insights['anomalies']:
                insights_text += f"\nAnomalies Detected:\n"
                for anomaly in insights['anomalies'][:3]:  # Show first 3
                    insights_text += f"• {anomaly.get('type', 'Unknown')}: {anomaly.get('app', 'N/A')}\n"
            
            if len(insights_text) > 30:  # Has content
                self.print_panel(insights_text, "Behavioral Insights", "bright_cyan")
            else:
                self.print_panel("No behavioral insights available yet.\nStart the observer system and use your computer normally to build insights.", "Insights", "yellow")
        
        except Exception as e:
            self.print_error(f"Failed to get behavioral insights: {e}")
    
    def handle_privacy_report(self):
        """Handle privacy command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            if hasattr(self.twin, 'observer_manager') and self.twin.observer_manager:
                privacy_report = self.twin.observer_manager.get_privacy_report()
                
                privacy_text = f"""Privacy Settings:
• Total observations: {privacy_report['total_observations']}
• Local storage only: {privacy_report['local_storage_only']}
• Encryption enabled: {privacy_report['encryption_enabled']}
• Data retention: {privacy_report['data_retention_days']} days

Data Sources:
"""
                
                for source, count in privacy_report.get('data_sources', {}).items():
                    privacy_text += f"• {source}: {count} observations\n"
                
                privacy_text += "\nActivity Categories:\n"
                for category, count in privacy_report.get('activity_categories', {}).items():
                    privacy_text += f"• {category}: {count} observations\n"
                
                privacy_text += f"\nPrivacy Filters Active:\n"
                privacy_settings = privacy_report.get('privacy_settings', {})
                blocked_categories = privacy_settings.get('blocked_categories', [])
                blocked_apps = privacy_settings.get('blocked_apps', [])
                
                if blocked_categories:
                    privacy_text += f"• Blocked categories: {', '.join(blocked_categories)}\n"
                if blocked_apps:
                    privacy_text += f"• Blocked apps: {', '.join(blocked_apps)}\n"
                
                self.print_panel(privacy_text, "Privacy Report", "bright_magenta")
            else:
                self.print_panel("Observer system not available for privacy report.", "Privacy Report", "red")
        
        except Exception as e:
            self.print_error(f"Failed to get privacy report: {e}")
    
    async def handle_start_observer(self):
        """Handle start-observer command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            self.print("Starting observer system for passive behavior learning...", style="yellow")
            
            success = await self.twin.start_observer_system()
            
            if success:
                self.print_success("Observer system started successfully!")
                self.print("Your twin will now learn from your activities passively.")
                self.print("Use 'observer' to see current activity, 'insights' for patterns.")
            else:
                self.print_error("Failed to start observer system")
                self.print("Check that you have the required permissions and dependencies.")
        
        except Exception as e:
            self.print_error(f"Failed to start observer: {e}")
    
    def handle_stop_observer(self):
        """Handle stop-observer command"""
        
        if not self.twin:
            self.print_error("Twin not initialized")
            return
        
        try:
            self.twin.stop_observer_system()
            self.print_success("Observer system stopped")
            self.print("Passive behavior learning has been disabled.")
        
        except Exception as e:
            self.print_error(f"Failed to stop observer: {e}")
    
    def show_help(self):
        """Show help information"""
        
        help_text = """Available Commands:

💬 chat <message>     - Have a conversation with your twin
🤔 ask <question>     - Ask your twin's memory system
⚡ action <request>   - Execute an action request
📅 schedule <request> - Schedule a future action  
🪞 introspect <query> - Deep introspection and self-analysis
📊 status             - Show system status
🧠 memory             - Show memory statistics
🔍 observer           - Show observer system status
📈 insights           - Show behavioral insights from observations
🔒 privacy            - Show privacy report
▶️  start-observer    - Start passive behavior learning
⏹️  stop-observer     - Stop behavior observation
💾 export             - Export twin data
🔧 optimize           - Run system optimization
❓ help               - Show this help
🚪 quit/exit          - Exit the CLI

Examples:
• chat What should I focus on today?
• ask What patterns do you see in my work habits?
• action Send email to john@example.com about the project
• schedule Call me at 3pm with daily summary
• introspect How can I be more productive?
• observer             - Check what you're currently doing
• insights             - See your productivity patterns"""
        
        self.print_panel(help_text, "Digital Twin CLI Help", "bright_yellow")
    
    async def run_command(self, command_line: str):
        """Parse and run a command"""
        
        if not command_line.strip():
            return
        
        parts = command_line.strip().split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ['quit', 'exit']:
            self.running = False
            self.print_success("Goodbye! Your twin's memories have been saved.")
            return
        
        elif command == 'help':
            self.show_help()
        
        elif command == 'chat':
            await self.handle_chat(args)
        
        elif command == 'ask':
            await self.handle_ask(args)
        
        elif command == 'action':
            await self.handle_action(args)
        
        elif command == 'schedule':
            await self.handle_schedule(args)
        
        elif command == 'introspect':
            await self.handle_introspect(args)
        
        elif command == 'status':
            self.handle_status()
        
        elif command == 'memory':
            self.handle_memory()
        
        elif command == 'export':
            await self.handle_export()
        
        elif command == 'optimize':
            await self.handle_optimize()
        
        elif command == 'observer':
            self.handle_observer_status()
        
        elif command == 'insights':
            self.handle_behavioral_insights()
        
        elif command == 'privacy':
            self.handle_privacy_report()
        
        elif command == 'start-observer':
            await self.handle_start_observer()
        
        elif command == 'stop-observer':
            self.handle_stop_observer()
        
        else:
            self.print_error(f"Unknown command: {command}")
            self.print("Type 'help' to see available commands")
    
    async def run(self):
        """Main CLI loop"""
        
        # Initialize the twin
        if not await self.initialize_twin():
            return
        
        self.running = True
        
        # Show initial help
        self.print("\nYour digital twin is ready! Type 'help' for available commands.")
        self.print("Try starting with: chat Hello, what can you tell me about yourself?")
        
        # Main interaction loop
        while self.running:
            try:
                if RICH_AVAILABLE:
                    command_line = Prompt.ask("\n[bright_green]twin>[/bright_green]", default="")
                else:
                    command_line = input("\ntwin> ")
                
                if command_line.strip():
                    await self.run_command(command_line)
            
            except KeyboardInterrupt:
                self.print("\n\nReceived interrupt signal.")
                if RICH_AVAILABLE:
                    if Confirm.ask("Do you want to exit?"):
                        break
                else:
                    confirm = input("Do you want to exit? (y/N): ")
                    if confirm.lower() == 'y':
                        break
            
            except Exception as e:
                self.print_error(f"Unexpected error: {e}")
        
        # Final export on exit
        if self.twin:
            try:
                await self.handle_export()
            except:
                pass  # Don't fail on exit export


async def main():
    """Main entry point"""
    
    # Check if running in proper environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_key_here")
        return
    
    # Create and run CLI
    cli = TwinCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())