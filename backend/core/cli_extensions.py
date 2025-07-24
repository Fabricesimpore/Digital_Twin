"""
CLI Extensions for Human-in-the-Loop Approval Management
"""
import asyncio
import argparse
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
from tabulate import tabulate

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .twin_decision_loop import TwinDecisionLoop
from .hitl_engine import ApprovalStatus


class ApprovalCLI:
    """CLI for managing approval requests"""
    
    def __init__(self):
        self.twin = None
        self.config_path = Path("backend/config/cli_config.json")
        
    async def initialize_twin(self):
        """Initialize the twin decision loop"""
        if not self.twin:
            self.twin = TwinDecisionLoop()
    
    async def list_pending(self, args):
        """List pending approval requests"""
        await self.initialize_twin()
        
        pending = self.twin.get_pending_approvals()
        
        if not pending:
            print("✅ No pending approvals")
            return
        
        # Prepare table data
        headers = ["ID", "Type", "Target", "Criticality", "Age", "Content Preview"]
        rows = []
        
        for req in pending:
            age = datetime.now() - req.created_at
            age_str = self._format_age(age)
            
            content_preview = str(req.action.get('content', ''))[:50]
            if len(str(req.action.get('content', ''))) > 50:
                content_preview += "..."
            
            rows.append([
                req.id[:8],
                req.action.get('type', 'unknown'),
                req.action.get('target', 'unknown')[:20],
                req.criticality.value.upper(),
                age_str,
                content_preview
            ])
        
        print(f"\n📋 Pending Approvals ({len(pending)} total):")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        # Show summary by criticality
        by_criticality = {}
        for req in pending:
            crit = req.criticality.value
            by_criticality[crit] = by_criticality.get(crit, 0) + 1
        
        print(f"\nSummary: {', '.join(f'{count} {crit}' for crit, count in by_criticality.items())}")
    
    async def show_details(self, args):
        """Show detailed information about a specific request"""
        await self.initialize_twin()
        
        request_id = args.id
        pending = self.twin.get_pending_approvals()
        
        # Find the request
        request = None
        for req in pending:
            if req.id.startswith(request_id):
                request = req
                break
        
        if not request:
            print(f"❌ Request {request_id} not found")
            return
        
        # Display detailed information
        print(f"\n📄 Approval Request Details")
        print("=" * 50)
        print(f"ID: {request.id}")
        print(f"Status: {request.status.value.upper()}")
        print(f"Criticality: {request.criticality.value.upper()}")
        print(f"Created: {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        age = datetime.now() - request.created_at
        print(f"Age: {self._format_age(age)}")
        print(f"Timeout: {request.timeout_minutes} minutes")
        
        # Action details
        print(f"\n🎯 Action Details:")
        print(f"Type: {request.action.get('type', 'unknown')}")
        print(f"Target: {request.action.get('target', 'unknown')}")
        
        content = request.action.get('content', '')
        if content:
            print(f"Content: {content}")
        
        context = request.action.get('context', {})
        if context:
            print(f"Context: {json.dumps(context, indent=2)}")
        
        # Classification explanation
        explanation = self.twin.action_classifier.explain_classification(request.action)
        print(f"\n🧠 Classification Reasoning:")
        print(explanation)
    
    async def approve(self, args):
        """Approve a pending request"""
        await self.initialize_twin()
        
        request_id = args.id
        feedback = args.feedback
        
        success = await self.twin.approve_action(request_id, feedback)
        
        if success:
            print(f"✅ Request {request_id[:8]} approved")
            if feedback:
                print(f"Feedback: {feedback}")
        else:
            print(f"❌ Failed to approve request {request_id[:8]} (not found or already resolved)")
    
    async def deny(self, args):
        """Deny a pending request"""
        await self.initialize_twin()
        
        request_id = args.id
        feedback = args.feedback
        
        success = await self.twin.deny_action(request_id, feedback)
        
        if success:
            print(f"❌ Request {request_id[:8]} denied")
            if feedback:
                print(f"Feedback: {feedback}")
        else:
            print(f"❌ Failed to deny request {request_id[:8]} (not found or already resolved)")
    
    async def defer(self, args):
        """Defer a pending request"""
        await self.initialize_twin()
        
        request_id = args.id
        minutes = args.minutes
        
        success = await self.twin.defer_action(request_id, minutes)
        
        if success:
            print(f"⏰ Request {request_id[:8]} deferred for {minutes} minutes")
        else:
            print(f"❌ Failed to defer request {request_id[:8]} (not found or already resolved)")
    
    async def show_history(self, args):
        """Show approval history"""
        await self.initialize_twin()
        
        limit = args.limit or 20
        history = self.twin.hitl_engine.get_approval_history(limit)
        
        if not history:
            print("📜 No approval history found")
            return
        
        # Prepare table data
        headers = ["ID", "Type", "Target", "Decision", "Response Time", "Date"]
        rows = []
        
        for req in history:
            response_time = ""
            if req.response_time:
                response_time = f"{req.response_time:.1f}s"
            
            rows.append([
                req.id[:8],
                req.action.get('type', 'unknown'),
                req.action.get('target', 'unknown')[:20],
                req.status.value.upper(),
                response_time,
                req.created_at.strftime('%m/%d %H:%M')
            ])
        
        print(f"\n📜 Approval History (last {len(history)} entries):")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        # Show summary statistics
        approved = sum(1 for r in history if r.status == ApprovalStatus.APPROVED)
        denied = sum(1 for r in history if r.status == ApprovalStatus.DENIED)
        timeout = sum(1 for r in history if r.status == ApprovalStatus.TIMEOUT)
        auto_approved = sum(1 for r in history if r.status == ApprovalStatus.AUTO_APPROVED)
        
        print(f"\nSummary: {approved} approved, {denied} denied, {timeout} timeout, {auto_approved} auto-approved")
    
    async def show_stats(self, args):
        """Show system statistics"""
        await self.initialize_twin()
        
        stats = self.twin.get_stats()
        
        print("\n📊 Digital Twin Statistics")
        print("=" * 40)
        
        # Main stats
        print(f"Actions processed: {stats.get('actions_processed', 0)}")
        print(f"Auto-executed: {stats.get('auto_executed', 0)}")
        print(f"Human approved: {stats.get('human_approved', 0)}")
        print(f"Human denied: {stats.get('human_denied', 0)}")
        print(f"Errors: {stats.get('errors', 0)}")
        
        if stats.get('runtime_seconds'):
            runtime_hours = stats['runtime_seconds'] / 3600
            print(f"Runtime: {runtime_hours:.2f} hours")
        
        # HITL stats
        hitl_stats = stats.get('hitl_stats', {})
        if hitl_stats:
            print(f"\n🤝 Human-in-the-Loop:")
            print(f"Total requests: {hitl_stats.get('total_requests', 0)}")
            print(f"Approval rate: {hitl_stats.get('approval_rate', 0):.1%}")
            if hitl_stats.get('avg_response_time_seconds'):
                print(f"Avg response time: {hitl_stats['avg_response_time_seconds']:.1f}s")
            print(f"Pending: {hitl_stats.get('pending_count', 0)}")
        
        # Memory stats
        memory_stats = stats.get('memory_stats', {})
        if memory_stats:
            print(f"\n🧠 Memory System:")
            print(f"Updates processed: {memory_stats.get('processed_count', 0)}")
            print(f"Queue size: {memory_stats.get('queue_size', 0)}")
            if memory_stats.get('error_count', 0) > 0:
                print(f"Errors: {memory_stats['error_count']}")
        
        # Learning insights
        learning = stats.get('learning_insights', {})
        if learning:
            print(f"\n🎓 Learning Insights:")
            print(f"Feedback entries: {learning.get('total_feedback_entries', 0)}")
            print(f"Overall approval rate: {learning.get('approval_rate', 0):.1%}")
            
            if learning.get('common_approved_patterns'):
                print(f"Top approved pattern: {learning['common_approved_patterns'][0]['pattern']}")
    
    async def interactive_mode(self, args):
        """Enter interactive approval mode"""
        await self.initialize_twin()
        
        print("🤖 Interactive Approval Mode")
        print("Commands: list, show <id>, approve <id>, deny <id>, defer <id> [minutes], stats, quit")
        print("=" * 60)
        
        while True:
            try:
                command = input("\n> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'list':
                    await self.list_pending(argparse.Namespace())
                elif cmd == 'stats':
                    await self.show_stats(argparse.Namespace())
                elif cmd == 'show' and len(command) > 1:
                    await self.show_details(argparse.Namespace(id=command[1]))
                elif cmd == 'approve' and len(command) > 1:
                    feedback = ' '.join(command[2:]) if len(command) > 2 else None
                    await self.approve(argparse.Namespace(id=command[1], feedback=feedback))
                elif cmd == 'deny' and len(command) > 1:
                    feedback = ' '.join(command[2:]) if len(command) > 2 else None
                    await self.deny(argparse.Namespace(id=command[1], feedback=feedback))
                elif cmd == 'defer' and len(command) > 1:
                    minutes = int(command[2]) if len(command) > 2 else 10
                    await self.defer(argparse.Namespace(id=command[1], minutes=minutes))
                else:
                    print("Unknown command. Try: list, show <id>, approve <id>, deny <id>, defer <id>, stats, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("👋 Goodbye!")
    
    def _format_age(self, age_delta: timedelta) -> str:
        """Format age timedelta as human readable string"""
        total_seconds = int(age_delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Digital Twin Approval CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List pending approvals
    list_parser = subparsers.add_parser('list', help='List pending approval requests')
    
    # Show detailed request
    show_parser = subparsers.add_parser('show', help='Show detailed request information')
    show_parser.add_argument('id', help='Request ID (can be partial)')
    
    # Approve request
    approve_parser = subparsers.add_parser('approve', help='Approve a request')
    approve_parser.add_argument('id', help='Request ID (can be partial)')
    approve_parser.add_argument('--feedback', help='Optional feedback message')
    
    # Deny request
    deny_parser = subparsers.add_parser('deny', help='Deny a request')
    deny_parser.add_argument('id', help='Request ID (can be partial)')
    deny_parser.add_argument('--feedback', help='Optional feedback message')
    
    # Defer request
    defer_parser = subparsers.add_parser('defer', help='Defer a request')
    defer_parser.add_argument('id', help='Request ID (can be partial)')
    defer_parser.add_argument('--minutes', type=int, default=10, help='Minutes to defer (default: 10)')
    
    # Show history
    history_parser = subparsers.add_parser('history', help='Show approval history')
    history_parser.add_argument('--limit', type=int, help='Number of entries to show')
    
    # Show statistics
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Enter interactive mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance and run command
    cli = ApprovalCLI()
    
    try:
        if args.command == 'list':
            asyncio.run(cli.list_pending(args))
        elif args.command == 'show':
            asyncio.run(cli.show_details(args))
        elif args.command == 'approve':
            asyncio.run(cli.approve(args))
        elif args.command == 'deny':
            asyncio.run(cli.deny(args))
        elif args.command == 'defer':
            asyncio.run(cli.defer(args))
        elif args.command == 'history':
            asyncio.run(cli.show_history(args))
        elif args.command == 'stats':
            asyncio.run(cli.show_stats(args))
        elif args.command == 'interactive':
            asyncio.run(cli.interactive_mode(args))
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()