"""
Browser Activity Tracker

Tracks web browsing activity including visited URLs, tab switches, and time spent on websites.
Supports Chrome DevTools Protocol for detailed browser monitoring.

Features:
- URL tracking with privacy filtering
- Tab switch detection
- Time spent per website
- Website categorization
- Privacy-aware URL sanitization
- Support for multiple browsers
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import re

from .observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel, ObserverConfig

# Optional Chrome DevTools Protocol support
try:
    import websocket
    import requests
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False


@dataclass
class BrowserTab:
    """Information about a browser tab"""
    tab_id: str
    url: str
    title: str
    browser: str
    is_active: bool = False
    created_time: datetime = None
    last_active_time: datetime = None
    total_time_seconds: int = 0
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now()
        if self.last_active_time is None:
            self.last_active_time = datetime.now()


@dataclass
class WebsiteSession:
    """Session information for a specific website"""
    domain: str
    url: str
    title: str
    start_time: datetime
    end_time: datetime
    total_duration: int = 0
    page_views: int = 1
    category: ActivityCategory = ActivityCategory.UNKNOWN
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time


class BrowserTracker:
    """
    Browser activity tracker for monitoring web browsing behavior.
    
    Tracks:
    - URL visits and time spent
    - Tab switches and browsing patterns
    - Website categories and productivity metrics
    - Search queries and content interaction
    """
    
    def __init__(self, config: ObserverConfig = None):
        self.config = config or ObserverConfig()
        self.logger = logging.getLogger(__name__)
        
        # Tracker state
        self.is_running = False
        self.active_tabs: Dict[str, BrowserTab] = {}
        self.current_tab: Optional[BrowserTab] = None
        self.website_sessions: List[WebsiteSession] = []
        
        # Tracking data
        self.domain_time: Dict[str, int] = {}  # domain -> total seconds
        self.url_visits: Dict[str, int] = {}   # url -> visit count
        self.search_queries: List[Dict[str, Any]] = []
        
        # Callbacks
        self.observation_callbacks: List[Callable[[ObservationEvent], None]] = []
        
        # Configuration
        self.track_urls = self.config.get('observers.browser_tracker.track_urls', True)
        self.track_tab_switches = self.config.get('observers.browser_tracker.track_tab_switches', True)
        
        # Chrome DevTools connection
        self.chrome_ws = None
        self.chrome_debugging_port = 9222
        
        # Website categorization patterns
        self._init_website_categories()
    
    def _init_website_categories(self):
        """Initialize website categorization patterns"""
        
        self.category_patterns = {
            ActivityCategory.PRODUCTIVITY: [
                r'.*google\.(com|co\..*)/.*workspace.*',
                r'.*office\.com.*',
                r'.*notion\.so.*',
                r'.*trello\.com.*',
                r'.*asana\.com.*',
                r'.*slack\.com.*',
                r'.*teams\.microsoft\.com.*',
                r'.*figma\.com.*',
                r'.*canva\.com.*'
            ],
            ActivityCategory.DEVELOPMENT: [
                r'.*github\.com.*',
                r'.*stackoverflow\.com.*',
                r'.*gitlab\.com.*',
                r'.*bitbucket\.org.*',
                r'.*codepen\.io.*',
                r'.*repl\.it.*',
                r'.*codesandbox\.io.*',
                r'.*developer\.mozilla\.org.*',
                r'.*docs\.python\.org.*'
            ],
            ActivityCategory.RESEARCH: [
                r'.*google\.(com|co\..*)/search.*',
                r'.*bing\.com/search.*',
                r'.*wikipedia\.org.*',
                r'.*scholar\.google\.com.*',
                r'.*arxiv\.org.*',
                r'.*researchgate\.net.*',
                r'.*jstor\.org.*'
            ],
            ActivityCategory.SOCIAL_MEDIA: [
                r'.*facebook\.com.*',
                r'.*twitter\.com.*',
                r'.*x\.com.*',
                r'.*instagram\.com.*',
                r'.*linkedin\.com.*',
                r'.*reddit\.com.*',
                r'.*tiktok\.com.*',
                r'.*snapchat\.com.*'
            ],
            ActivityCategory.ENTERTAINMENT: [
                r'.*youtube\.com.*',
                r'.*netflix\.com.*',
                r'.*twitch\.tv.*',
                r'.*spotify\.com.*',
                r'.*hulu\.com.*',
                r'.*disney.*\.com.*',
                r'.*primevideo\.com.*'
            ],
            ActivityCategory.SHOPPING: [
                r'.*amazon\.(com|co\..*)/.*',
                r'.*ebay\.(com|co\..*)/.*',
                r'.*etsy\.com.*',
                r'.*alibaba\.com.*',
                r'.*shopify\.com.*',
                r'.*walmart\.com.*',
                r'.*target\.com.*'
            ],
            ActivityCategory.FINANCE: [
                r'.*bank.*\.com.*',
                r'.*chase\.com.*',
                r'.*wellsfargo\.com.*',
                r'.*paypal\.com.*',
                r'.*stripe\.com.*',
                r'.*mint\.com.*',
                r'.*robinhood\.com.*',
                r'.*coinbase\.com.*'
            ],
            ActivityCategory.EDUCATION: [
                r'.*coursera\.org.*',
                r'.*edx\.org.*',
                r'.*udemy\.com.*',
                r'.*khanacademy\.org.*',
                r'.*codecademy\.com.*',
                r'.*pluralsight\.com.*',
                r'.*lynda\.com.*'
            ]
        }
    
    def add_observation_callback(self, callback: Callable[[ObservationEvent], None]):
        """Add callback for new browser observations"""
        self.observation_callbacks.append(callback)
    
    def _categorize_url(self, url: str) -> ActivityCategory:
        """Categorize a URL based on patterns"""
        
        url_lower = url.lower()
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.match(pattern, url_lower):
                    return category
        
        return ActivityCategory.UNKNOWN
    
    def _extract_search_query(self, url: str) -> Optional[str]:
        """Extract search query from search engine URLs"""
        
        search_patterns = [
            (r'google\.(com|co\..*)/search.*[?&]q=([^&]*)', 2),
            (r'bing\.com/search.*[?&]q=([^&]*)', 1),
            (r'duckduckgo\.com/.*[?&]q=([^&]*)', 1),
            (r'yahoo\.com/search.*[?&]p=([^&]*)', 1)
        ]
        
        for pattern, group_index in search_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                query = match.group(group_index)
                # URL decode basic characters
                query = query.replace('%20', ' ').replace('+', ' ')
                return query
        
        return None
    
    def _sanitize_url_for_privacy(self, url: str) -> str:
        """Sanitize URL based on privacy settings"""
        
        privacy_settings = self.config.get_privacy_settings()
        
        # Check if URL should be blocked entirely
        blocked_patterns = privacy_settings.get('blocked_url_patterns', [])
        for pattern in blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return "[BLOCKED_URL]"
        
        # Determine privacy level based on URL
        url_lower = url.lower()
        
        # Financial sites - never log
        if any(term in url_lower for term in ['bank', 'banking', 'payment', 'crypto', 'wallet']):
            return "[FINANCIAL_URL]"
        
        # Private browsing indicators
        if 'private' in url_lower or 'incognito' in url_lower:
            return "[PRIVATE_URL]"
        
        # For sensitive URLs, sanitize query parameters
        if any(term in url_lower for term in ['login', 'auth', 'password', 'token']):
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}[SENSITIVE_PARAMS]"
        
        # Remove potentially sensitive query parameters
        parsed = urlparse(url)
        if parsed.query:
            # Keep only safe parameters
            safe_params = []
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() not in ['token', 'password', 'key', 'auth', 'secret', 'session']:
                        if len(value) > 50:  # Long values might be sensitive
                            safe_params.append(f"{key}=[LONG_VALUE]")
                        else:
                            safe_params.append(f"{key}={value}")
            
            if safe_params:
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{'&'.join(safe_params)}"
            else:
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        return url
    
    def _should_track_url(self, url: str) -> bool:
        """Determine if URL should be tracked"""
        
        if not self.track_urls:
            return False
        
        # Skip special URLs
        if url.startswith('chrome://') or url.startswith('about:') or url.startswith('moz-extension://'):
            return False
        
        # Check privacy settings
        privacy_settings = self.config.get_privacy_settings()
        blocked_patterns = privacy_settings.get('blocked_url_patterns', [])
        
        for pattern in blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    async def _setup_chrome_debugging(self) -> bool:
        """Set up Chrome DevTools Protocol connection"""
        
        if not CDP_AVAILABLE:
            self.logger.warning("Chrome DevTools Protocol not available (missing websocket/requests)")
            return False
        
        try:
            # Check if Chrome is running with debugging enabled
            response = requests.get(f'http://localhost:{self.chrome_debugging_port}/json/version', timeout=2)
            
            if response.status_code == 200:
                # Get list of tabs
                tabs_response = requests.get(f'http://localhost:{self.chrome_debugging_port}/json')
                tabs = tabs_response.json()
                
                if tabs:
                    # Connect to the first tab for now
                    tab = tabs[0]
                    websocket_url = tab['webSocketDebuggerUrl']
                    
                    self.chrome_ws = websocket.WebSocket()
                    self.chrome_ws.connect(websocket_url)
                    
                    # Enable runtime and page domains
                    self.chrome_ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
                    self.chrome_ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
                    
                    self.logger.info("Chrome DevTools Protocol connection established")
                    return True
            
        except Exception as e:
            self.logger.debug(f"Chrome debugging not available: {e}")
        
        return False
    
    async def _monitor_chrome_tabs(self):
        """Monitor Chrome tabs using DevTools Protocol"""
        
        while self.is_running and self.chrome_ws:
            try:
                # Get current tabs
                response = requests.get(f'http://localhost:{self.chrome_debugging_port}/json')
                tabs = response.json()
                
                for tab_data in tabs:
                    tab_id = tab_data['id']
                    url = tab_data.get('url', '')
                    title = tab_data.get('title', '')
                    
                    if not self._should_track_url(url):
                        continue
                    
                    # Update or create tab
                    if tab_id not in self.active_tabs:
                        self.active_tabs[tab_id] = BrowserTab(
                            tab_id=tab_id,
                            url=url,
                            title=title,
                            browser='Chrome'
                        )
                    else:
                        # Check for URL changes
                        tab = self.active_tabs[tab_id]
                        if tab.url != url:
                            # URL changed - record previous session
                            await self._record_tab_session(tab)
                            
                            # Update tab info
                            tab.url = url
                            tab.title = title
                            tab.last_active_time = datetime.now()
                
                # Remove closed tabs
                current_tab_ids = {tab['id'] for tab in tabs}
                closed_tabs = set(self.active_tabs.keys()) - current_tab_ids
                
                for closed_tab_id in closed_tabs:
                    await self._record_tab_session(self.active_tabs[closed_tab_id])
                    del self.active_tabs[closed_tab_id]
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring Chrome tabs: {e}")
                await asyncio.sleep(5)
    
    async def _record_tab_session(self, tab: BrowserTab):
        """Record a completed tab session"""
        
        if not tab.url or not self._should_track_url(tab.url):
            return
        
        # Calculate session duration
        duration = int((datetime.now() - tab.last_active_time).total_seconds())
        
        if duration < 5:  # Ignore very short sessions
            return
        
        # Update domain time tracking
        try:
            domain = urlparse(tab.url).netloc
            if domain:
                self.domain_time[domain] = self.domain_time.get(domain, 0) + duration
                self.url_visits[tab.url] = self.url_visits.get(tab.url, 0) + 1
        except:
            pass
        
        # Check for search queries
        search_query = self._extract_search_query(tab.url)
        if search_query:
            self.search_queries.append({
                'query': search_query,
                'timestamp': tab.last_active_time.isoformat(),
                'url': self._sanitize_url_for_privacy(tab.url)
            })
        
        # Create observation event
        sanitized_url = self._sanitize_url_for_privacy(tab.url)
        category = self._categorize_url(tab.url)
        
        event = ObservationEvent(
            timestamp=datetime.now(),
            source="browser_tracker",
            event_type="page_session",
            app_name=tab.browser,
            window_title=tab.title,
            url=sanitized_url,
            duration_seconds=duration,
            category=category,
            metadata={
                'tab_id': tab.tab_id,
                'domain': urlparse(tab.url).netloc if tab.url else '',
                'search_query': search_query,
                'visit_count': self.url_visits.get(tab.url, 1)
            }
        )
        
        # Store session
        website_session = WebsiteSession(
            domain=urlparse(tab.url).netloc if tab.url else '',
            url=sanitized_url,
            title=tab.title,
            start_time=tab.last_active_time,
            end_time=datetime.now(),
            total_duration=duration,
            category=category
        )
        
        self.website_sessions.append(website_session)
        
        # Notify callbacks
        for callback in self.observation_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in browser observation callback: {e}")
    
    async def _monitor_browser_fallback(self):
        """Fallback browser monitoring without DevTools Protocol"""
        
        # This is a simplified approach that monitors browser activity
        # by checking running processes and window titles
        
        self.logger.info("Using fallback browser monitoring")
        
        last_browser_check = None
        
        while self.is_running:
            try:
                # This would integrate with screen_observer to detect browser windows
                # For now, we'll implement a basic version
                
                # Check for browser processes (simplified)
                import psutil
                
                browser_processes = []
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        name = proc.info['name'].lower()
                        if any(browser in name for browser in ['chrome', 'firefox', 'safari', 'edge']):
                            browser_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if browser_processes and len(browser_processes) != last_browser_check:
                    # Browser activity detected
                    event = ObservationEvent(
                        timestamp=datetime.now(),
                        source="browser_tracker",
                        event_type="browser_activity",
                        app_name="Browser",
                        metadata={
                            'active_browsers': len(browser_processes),
                            'fallback_mode': True
                        }
                    )
                    
                    for callback in self.observation_callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            self.logger.error(f"Error in browser observation callback: {e}")
                
                last_browser_check = len(browser_processes)
                await asyncio.sleep(10)  # Check every 10 seconds in fallback mode
                
            except Exception as e:
                self.logger.error(f"Error in fallback browser monitoring: {e}")
                await asyncio.sleep(10)
    
    async def start_tracking(self):
        """Start browser activity tracking"""
        
        if not self.config.is_observer_enabled('browser_tracker'):
            self.logger.info("Browser tracker is disabled in configuration")
            return
        
        self.is_running = True
        self.logger.info("Starting browser activity tracking")
        
        # Try to set up Chrome DevTools Protocol
        chrome_connected = await self._setup_chrome_debugging()
        
        if chrome_connected:
            await self._monitor_chrome_tabs()
        else:
            await self._monitor_browser_fallback()
    
    def stop_tracking(self):
        """Stop browser activity tracking"""
        self.is_running = False
        
        if self.chrome_ws:
            try:
                self.chrome_ws.close()
            except:
                pass
            self.chrome_ws = None
        
        self.logger.info("Browser activity tracking stopped")
    
    def get_browsing_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of browsing activity"""
        
        # Filter recent sessions
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_sessions = [
            session for session in self.website_sessions
            if session.start_time >= cutoff_time
        ]
        
        if not recent_sessions:
            return {
                'summary': f'No browsing activity recorded in the last {hours} hours',
                'total_sessions': 0,
                'unique_domains': 0,
                'total_time_minutes': 0
            }
        
        # Calculate statistics
        total_time = sum(session.total_duration for session in recent_sessions)
        unique_domains = len(set(session.domain for session in recent_sessions))
        
        # Top domains by time
        domain_times = {}
        for session in recent_sessions:
            domain_times[session.domain] = domain_times.get(session.domain, 0) + session.total_duration
        
        top_domains = sorted(domain_times.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Category breakdown
        category_times = {}
        for session in recent_sessions:
            cat = session.category.value
            category_times[cat] = category_times.get(cat, 0) + session.total_duration
        
        return {
            'summary': f'{len(recent_sessions)} browsing sessions across {unique_domains} domains',
            'total_sessions': len(recent_sessions),
            'unique_domains': unique_domains,
            'total_time_minutes': total_time // 60,
            'top_domains': [
                {
                    'domain': domain,
                    'time_minutes': time_seconds // 60,
                    'percentage': (time_seconds / total_time * 100) if total_time > 0 else 0
                }
                for domain, time_seconds in top_domains
            ],
            'category_breakdown': {
                category: {
                    'time_minutes': time_seconds // 60,
                    'percentage': (time_seconds / total_time * 100) if total_time > 0 else 0
                }
                for category, time_seconds in category_times.items()
            },
            'recent_searches': self.search_queries[-10:] if self.search_queries else []
        }
    
    def get_productivity_analysis(self) -> Dict[str, Any]:
        """Analyze browsing productivity patterns"""
        
        if not self.website_sessions:
            return {'analysis': 'No browsing data available for analysis'}
        
        total_time = sum(session.total_duration for session in self.website_sessions)
        
        if total_time == 0:
            return {'analysis': 'No significant browsing time recorded'}
        
        # Categorize time
        category_times = {}
        for session in self.website_sessions:
            cat = session.category.value
            category_times[cat] = category_times.get(cat, 0) + session.total_duration
        
        # Calculate productivity metrics
        productive_categories = ['productivity', 'development', 'research', 'education']
        productive_time = sum(category_times.get(cat, 0) for cat in productive_categories)
        
        distracting_categories = ['entertainment', 'social_media']
        distracting_time = sum(category_times.get(cat, 0) for cat in distracting_categories)
        
        productivity_ratio = (productive_time / total_time) * 100 if total_time > 0 else 0
        distraction_ratio = (distracting_time / total_time) * 100 if total_time > 0 else 0
        
        # Session analysis
        avg_session_duration = total_time / len(self.website_sessions)
        long_sessions = len([s for s in self.website_sessions if s.total_duration > 600])  # > 10 minutes
        
        # Generate insights
        insights = []
        
        if productivity_ratio > 60:
            insights.append("High productivity browsing pattern detected")
        elif productivity_ratio < 30:
            insights.append("Low productivity browsing - consider focus techniques")
        
        if distraction_ratio > 30:
            insights.append("High distraction time - consider blocking distracting sites")
        
        if avg_session_duration < 120:  # < 2 minutes
            insights.append("Short browsing sessions suggest high task switching")
        elif avg_session_duration > 1200:  # > 20 minutes
            insights.append("Long browsing sessions suggest deep focus periods")
        
        return {
            'productivity_percentage': productivity_ratio,
            'distraction_percentage': distraction_ratio,
            'average_session_minutes': avg_session_duration / 60,
            'long_focus_sessions': long_sessions,
            'total_search_queries': len(self.search_queries),
            'insights': insights,
            'recommendations': self._generate_browsing_recommendations(category_times, total_time)
        }
    
    def _generate_browsing_recommendations(self, category_times: Dict[str, int], total_time: int) -> List[str]:
        """Generate browsing behavior recommendations"""
        
        recommendations = []
        
        entertainment_time = category_times.get('entertainment', 0)
        social_time = category_times.get('social_media', 0)
        
        if (entertainment_time + social_time) / total_time > 0.4:
            recommendations.append("Consider using website blockers during work hours")
        
        if len(self.search_queries) > 50:
            recommendations.append("You do a lot of research - consider bookmarking useful resources")
        
        if category_times.get('development', 0) > 0:
            recommendations.append("Track coding-related browsing to optimize development workflow")
        
        return recommendations