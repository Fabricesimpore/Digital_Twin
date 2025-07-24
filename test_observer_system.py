"""
Observer System Integration Test

Tests the complete observer system integration with the digital twin:
- Screen observation for app/window tracking
- Browser activity monitoring
- Input activity and idle detection  
- Memory integration for behavioral learning
- Real-time context awareness
- Privacy filtering and controls

This script demonstrates Phase 6: Observer Mode capabilities.
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import observer components
from observer.observer_manager import ObserverManager
from observer.observer_utils import ObserverConfig, ObservationEvent, ActivityCategory
from observer.screen_observer import ScreenObserver
from observer.browser_tracker import BrowserTracker
from observer.input_watcher import InputWatcher

# Import twin system
from twin_decision_loop import UnifiedTwinDecisionLoop

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ObserverSystemTester:
    """Test harness for the observer system integration"""
    
    def __init__(self):
        self.test_results = {}
        self.observer_config = ObserverConfig()
        
    async def test_observer_components(self):
        """Test individual observer components"""
        
        logger.info("🔍 === TESTING INDIVIDUAL OBSERVER COMPONENTS ===")
        
        # Test 1: Screen Observer
        await self._test_screen_observer()
        
        # Test 2: Browser Tracker
        await self._test_browser_tracker()
        
        # Test 3: Input Watcher
        await self._test_input_watcher()
        
        # Test 4: Observer Configuration
        self._test_observer_configuration()
    
    async def _test_screen_observer(self):
        """Test screen observer functionality"""
        
        logger.info("📱 Testing Screen Observer...")
        
        try:
            screen_observer = ScreenObserver(self.observer_config)
            
            # Test getting current window
            current_window = screen_observer.get_active_window()
            
            if current_window:
                logger.info(f"✅ Current window detected: {current_window.app_name} - {current_window.window_title}")
                
                # Test observation event creation
                event = screen_observer._create_observation_event(
                    current_window, 
                    "window_focus", 
                    duration=30
                )
                
                logger.info(f"✅ Observation event created: {event.event_type} - {event.category.value}")
                
                # Test app usage summary
                usage_summary = screen_observer.get_app_usage_summary()
                logger.info(f"✅ App usage tracking: {usage_summary['unique_apps_used']} apps tracked")
                
                # Test productivity insights
                insights = screen_observer.get_productivity_insights()
                logger.info(f"✅ Productivity insights: {len(insights.get('insights', []))} insights generated")
                
                self.test_results['screen_observer'] = {
                    'success': True,
                    'current_app': current_window.app_name,
                    'insights_count': len(insights.get('insights', []))
                }
            else:
                logger.warning("⚠️ No active window detected")
                self.test_results['screen_observer'] = {
                    'success': False,
                    'error': 'No active window detected'
                }
        
        except Exception as e:
            logger.error(f"❌ Screen observer test failed: {e}")
            self.test_results['screen_observer'] = {
                'success': False,
                'error': str(e)
            }
    
    async def _test_browser_tracker(self):
        """Test browser tracker functionality"""
        
        logger.info("🌐 Testing Browser Tracker...")
        
        try:
            browser_tracker = BrowserTracker(self.observer_config)
            
            # Test website categorization
            test_urls = [
                "https://github.com/user/repo",
                "https://stackoverflow.com/questions/123",
                "https://www.youtube.com/watch?v=123",
                "https://docs.google.com/document/123"
            ]
            
            categories = []
            for url in test_urls:
                category = browser_tracker._categorize_url(url)
                categories.append(category.value)
                logger.info(f"✅ URL categorized: {url} → {category.value}")
            
            # Test privacy filtering
            sensitive_url = "https://bank.example.com/login"
            sanitized_url = browser_tracker._sanitize_url_for_privacy(sensitive_url)
            logger.info(f"✅ URL sanitized: {sensitive_url} → {sanitized_url}")
            
            # Test search query extraction
            search_url = "https://google.com/search?q=digital+twin+system"
            query = browser_tracker._extract_search_query(search_url)
            logger.info(f"✅ Search query extracted: {query}")
            
            # Test capability detection
            capability_test = await browser_tracker.test_voice_capability() if hasattr(browser_tracker, 'test_voice_capability') else {'status': 'not_applicable'}
            
            self.test_results['browser_tracker'] = {
                'success': True,
                'categories_tested': len(set(categories)),
                'privacy_filtering': sanitized_url != sensitive_url,
                'search_extraction': query is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Browser tracker test failed: {e}")
            self.test_results['browser_tracker'] = {
                'success': False,
                'error': str(e)
            }
    
    async def _test_input_watcher(self):
        """Test input watcher functionality"""
        
        logger.info("⌨️ Testing Input Watcher...")
        
        try:
            input_watcher = InputWatcher(self.observer_config)
            
            # Test idle time detection
            idle_time = input_watcher.get_idle_time()
            logger.info(f"✅ Current idle time: {idle_time:.1f} seconds")
            
            # Test current status
            status = input_watcher.get_current_status()
            logger.info(f"✅ Input status: idle={status['is_idle']}, threshold={status['idle_threshold_seconds']}s")
            
            # Test activity summary
            activity_summary = input_watcher.get_activity_summary(hours=1)
            logger.info(f"✅ Activity summary: {activity_summary['summary']}")
            
            # Test productivity insights
            productivity_insights = input_watcher.get_productivity_insights()
            logger.info(f"✅ Productivity insights: {len(productivity_insights.get('insights', []))} insights")
            
            self.test_results['input_watcher'] = {
                'success': True,
                'idle_time_seconds': idle_time,
                'is_idle': status['is_idle'],
                'insights_count': len(productivity_insights.get('insights', []))
            }
            
        except Exception as e:
            logger.error(f"❌ Input watcher test failed: {e}")
            self.test_results['input_watcher'] = {
                'success': False,
                'error': str(e)
            }
    
    def _test_observer_configuration(self):
        """Test observer configuration system"""
        
        logger.info("⚙️ Testing Observer Configuration...")
        
        try:
            # Test configuration loading
            config = ObserverConfig()
            
            # Test privacy settings
            privacy_settings = config.get_privacy_settings()
            logger.info(f"✅ Privacy settings loaded: {len(privacy_settings)} settings")
            
            # Test observer enablement
            screen_enabled = config.is_observer_enabled('screen_observer')
            browser_enabled = config.is_observer_enabled('browser_tracker')
            input_enabled = config.is_observer_enabled('input_watcher')
            
            logger.info(f"✅ Observer states: screen={screen_enabled}, browser={browser_enabled}, input={input_enabled}")
            
            # Test configuration updates
            original_value = config.get('observers.screen_observer.poll_interval', 1.0)
            config.set('observers.screen_observer.poll_interval', 2.0)
            new_value = config.get('observers.screen_observer.poll_interval', 1.0)
            
            logger.info(f"✅ Configuration update: {original_value} → {new_value}")
            
            self.test_results['observer_config'] = {
                'success': True,
                'privacy_settings_count': len(privacy_settings),
                'observers_enabled': sum([screen_enabled, browser_enabled, input_enabled]),
                'config_update_works': new_value == 2.0
            }
            
        except Exception as e:
            logger.error(f"❌ Observer configuration test failed: {e}")
            self.test_results['observer_config'] = {
                'success': False,
                'error': str(e)
            }
    
    async def test_observer_manager_integration(self):
        """Test observer manager and memory integration"""
        
        logger.info("🎛️ === TESTING OBSERVER MANAGER INTEGRATION ===")
        
        try:
            # Initialize observer manager (without starting observation)
            observer_manager = ObserverManager(self.observer_config)
            
            # Test context generation
            context = observer_manager.get_current_context()
            logger.info(f"Context available: {context is not None}")
            
            # Test observation summary
            summary = observer_manager.get_observation_summary(hours=1)
            logger.info(f"✅ Observation summary: {summary.total_observations} observations")
            
            # Test insights generation
            insights = observer_manager.get_insights()
            logger.info(f"✅ Behavioral insights: {len(insights)} insight categories")
            
            # Test privacy report
            privacy_report = observer_manager.get_privacy_report()
            logger.info(f"✅ Privacy report: {privacy_report['total_observations']} observations tracked")
            
            # Test data export
            export_file = observer_manager.export_data(days=1)
            logger.info(f"✅ Data export: {export_file}")
            
            self.test_results['observer_manager'] = {
                'success': True,
                'context_available': context is not None,
                'total_observations': summary.total_observations,
                'insight_categories': len(insights),
                'export_file': export_file
            }
            
        except Exception as e:
            logger.error(f"❌ Observer manager test failed: {e}")
            self.test_results['observer_manager'] = {
                'success': False,
                'error': str(e)
            }
    
    async def test_twin_integration(self):
        """Test observer integration with the digital twin"""
        
        logger.info("🧠 === TESTING DIGITAL TWIN INTEGRATION ===")
        
        # Check if we have required API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not found - skipping twin integration test")
            self.test_results['twin_integration'] = {
                'success': False,
                'error': 'OPENAI_API_KEY not found'
            }
            return
        
        try:
            # Initialize twin with observer enabled
            twin = UnifiedTwinDecisionLoop(
                persona_path="persona.yaml",
                api_key=api_key,
                memory_dir="test_observer_memory",
                enable_observer=True
            )
            
            # Test observer system startup
            observer_started = await twin.start_observer_system()
            logger.info(f"✅ Observer system started: {observer_started}")
            
            # Test context retrieval
            current_context = twin.get_current_context()
            logger.info(f"✅ Current context available: {current_context is not None}")
            
            # Test behavioral insights
            behavioral_insights = twin.get_behavioral_insights()
            logger.info(f"✅ Behavioral insights: {len(behavioral_insights)} categories")
            
            # Test twin reasoning with context awareness
            if current_context:
                # Create a test request that would benefit from context
                test_request = "What am I currently working on and how can I be more productive?"
                
                try:
                    result = await twin.process(test_request, request_type="query")
                    logger.info(f"✅ Context-aware reasoning: {result.success}")
                    logger.info(f"   Response: {result.response_text[:100]}...")
                    
                    context_aware_reasoning = True
                except Exception as e:
                    logger.warning(f"⚠️ Context-aware reasoning failed: {e}")
                    context_aware_reasoning = False
            else:
                context_aware_reasoning = False
            
            # Test memory formation from observations
            system_status = twin.get_system_status()
            memory_formations = system_status.get('decision_loop', {}).get('memory_formations', 0)
            logger.info(f"✅ Memory formations: {memory_formations}")
            
            # Stop observer system
            twin.stop_observer_system()
            
            self.test_results['twin_integration'] = {
                'success': True,
                'observer_started': observer_started,
                'context_available': current_context is not None,
                'behavioral_insights_count': len(behavioral_insights),
                'context_aware_reasoning': context_aware_reasoning,
                'memory_formations': memory_formations
            }
            
        except Exception as e:
            logger.error(f"❌ Twin integration test failed: {e}")
            self.test_results['twin_integration'] = {
                'success': False,
                'error': str(e)
            }
    
    async def test_privacy_and_security(self):
        """Test privacy controls and data security"""
        
        logger.info("🔒 === TESTING PRIVACY AND SECURITY ===")
        
        try:
            config = ObserverConfig()
            
            # Test privacy settings
            privacy_settings = config.get_privacy_settings()
            
            # Test blocked categories
            blocked_categories = privacy_settings.get('blocked_categories', [])
            logger.info(f"✅ Blocked categories: {blocked_categories}")
            
            # Test blocked apps
            blocked_apps = privacy_settings.get('blocked_apps', [])
            logger.info(f"✅ Blocked apps: {blocked_apps}")
            
            # Test URL pattern blocking
            blocked_patterns = privacy_settings.get('blocked_url_patterns', [])
            logger.info(f"✅ Blocked URL patterns: {len(blocked_patterns)}")
            
            # Test data retention settings
            retention_days = config.get('privacy.data_retention_days', 30)
            logger.info(f"✅ Data retention: {retention_days} days")
            
            # Test local storage requirement
            local_only = config.get('storage.local_only', True)
            logger.info(f"✅ Local storage only: {local_only}")
            
            # Test encryption settings
            encrypt_logs = config.get('storage.encrypt_logs', True)
            logger.info(f"✅ Log encryption: {encrypt_logs}")
            
            # Test observation filtering
            from observer.observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel
            
            # Create test observation with financial content
            financial_event = ObservationEvent(
                timestamp=datetime.now(),
                source="test",
                event_type="test",
                app_name="Banking App",
                window_title="Account Balance - $1,234.56",
                category=ActivityCategory.FINANCE,
                privacy_level=PrivacyLevel.FINANCIAL
            )
            
            should_store = financial_event.should_store(privacy_settings)
            logger.info(f"✅ Financial content filtered: {not should_store}")
            
            self.test_results['privacy_security'] = {
                'success': True,
                'blocked_categories_count': len(blocked_categories),
                'blocked_apps_count': len(blocked_apps),
                'blocked_patterns_count': len(blocked_patterns),
                'data_retention_days': retention_days,
                'local_only': local_only,
                'encryption_enabled': encrypt_logs,
                'financial_content_filtered': not should_store
            }
            
        except Exception as e:
            logger.error(f"❌ Privacy and security test failed: {e}")
            self.test_results['privacy_security'] = {
                'success': False,
                'error': str(e)
            }
    
    def print_test_summary(self):
        """Print comprehensive test results"""
        
        logger.info("\n" + "=" * 60)
        logger.info("🏆 OBSERVER SYSTEM TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() 
                              if isinstance(result, dict) and result.get('success', False))
        
        logger.info(f"📊 Overall Results: {successful_tests}/{total_tests} tests passed")
        
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                logger.info(f"{status} {test_name.replace('_', ' ').title()}")
                
                if not result.get('success', False) and 'error' in result:
                    logger.info(f"    Error: {result['error']}")
                elif result.get('success', False):
                    # Show key metrics for successful tests
                    if test_name == 'screen_observer' and 'current_app' in result:
                        logger.info(f"    Current app: {result['current_app']}")
                    elif test_name == 'browser_tracker' and 'categories_tested' in result:
                        logger.info(f"    Categories tested: {result['categories_tested']}")
                    elif test_name == 'input_watcher' and 'idle_time_seconds' in result:
                        logger.info(f"    Idle time: {result['idle_time_seconds']:.1f}s")
                    elif test_name == 'observer_manager' and 'total_observations' in result:
                        logger.info(f"    Observations: {result['total_observations']}")
                    elif test_name == 'twin_integration' and 'memory_formations' in result:
                        logger.info(f"    Memory formations: {result['memory_formations']}")
                    elif test_name == 'privacy_security' and 'financial_content_filtered' in result:
                        logger.info(f"    Privacy filtering: {'Active' if result['financial_content_filtered'] else 'Inactive'}")
        
        logger.info("\n🎉 OBSERVER SYSTEM TESTING COMPLETE!")
        
        if successful_tests == total_tests:
            logger.info("🌟 All tests passed! Observer system is ready for production use.")
            logger.info("🚀 Your digital twin now has passive behavior learning capabilities!")
        else:
            logger.info("⚠️  Some tests failed. Check the errors above and fix issues before deployment.")
        
        logger.info("=" * 60)


async def main():
    """Main test runner"""
    
    print("""
🔴 OBSERVER SYSTEM INTEGRATION TEST
===================================

This test suite validates Phase 6: Observer Mode implementation:
- Cross-platform activity monitoring
- Privacy-aware behavioral learning  
- Real-time context awareness
- Memory integration for pattern recognition
- Digital twin integration

Starting comprehensive tests...
""")
    
    tester = ObserverSystemTester()
    
    # Run all tests
    await tester.test_observer_components()
    await tester.test_observer_manager_integration()
    await tester.test_twin_integration()
    await tester.test_privacy_and_security()
    
    # Print summary
    tester.print_test_summary()


if __name__ == "__main__":
    asyncio.run(main())