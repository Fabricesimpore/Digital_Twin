"""
Cross-Platform Screen Observer

Tracks active windows, applications, and screen activity across different operating systems.
Provides real-time monitoring of what the user is actively working on.

Features:
- Cross-platform window tracking (macOS, Windows, Linux)
- Active application detection
- Window title capture
- Duration tracking
- Privacy-aware filtering
"""

import logging
import asyncio
import platform
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .observer_utils import ObservationEvent, ActivityCategory, PrivacyLevel, ObserverConfig

# Platform-specific imports
system = platform.system()

if system == "Darwin":  # macOS
    try:
        from AppKit import NSWorkspace, NSApplication
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        logging.warning("macOS AppKit/Quartz not available for screen observation")

elif system == "Windows":
    try:
        import win32gui
        import win32process
        import psutil
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logging.warning("Windows win32gui not available for screen observation")

elif system == "Linux":
    try:
        import subprocess
        LINUX_AVAILABLE = True
    except ImportError:
        LINUX_AVAILABLE = False


@dataclass
class WindowInfo:
    """Information about an active window"""
    app_name: str
    window_title: str
    process_id: int
    window_id: Optional[int] = None
    bounds: Optional[Dict[str, int]] = None  # x, y, width, height
    is_active: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ScreenObserver:
    """
    Cross-platform screen observer for tracking active windows and applications.
    
    Monitors:
    - Active application changes
    - Window title changes
    - Window focus events
    - Application usage duration
    """
    
    def __init__(self, config: ObserverConfig = None):
        self.config = config or ObserverConfig()
        self.logger = logging.getLogger(__name__)
        
        # Observer state
        self.is_running = False
        self.current_window: Optional[WindowInfo] = None
        self.last_observation: Optional[ObservationEvent] = None
        self.session_start_time: Optional[datetime] = None
        
        # Tracking
        self.window_history: List[WindowInfo] = []
        self.app_durations: Dict[str, int] = {}  # app_name -> total seconds
        self.observation_callbacks: List[Callable[[ObservationEvent], None]] = []
        
        # Configuration
        self.poll_interval = self.config.get('observers.screen_observer.poll_interval', 1.0)
        self.min_duration = self.config.get('observers.screen_observer.min_duration', 2)
        
        # Platform detection
        self.system = platform.system()
        self._check_platform_support()
    
    def _check_platform_support(self):
        """Check if the current platform is supported"""
        
        if self.system == "Darwin" and not MACOS_AVAILABLE:
            self.logger.error("macOS screen observation requires AppKit and Quartz")
            return False
        elif self.system == "Windows" and not WINDOWS_AVAILABLE:
            self.logger.error("Windows screen observation requires win32gui and psutil")
            return False
        elif self.system == "Linux" and not LINUX_AVAILABLE:
            self.logger.error("Linux screen observation requires subprocess support")
            return False
        
        return True
    
    def add_observation_callback(self, callback: Callable[[ObservationEvent], None]):
        """Add callback to be called when new observations are made"""
        self.observation_callbacks.append(callback)
    
    def _get_active_window_macos(self) -> Optional[WindowInfo]:
        """Get active window information on macOS"""
        
        if not MACOS_AVAILABLE:
            return None
        
        try:
            # Get frontmost application
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            if not active_app:
                return None
            
            app_name = active_app.localizedName()
            process_id = active_app.processIdentifier()
            
            # Get window information
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, 
                kCGNullWindowID
            )
            
            window_title = ""
            window_id = None
            bounds = None
            
            # Find the frontmost window for this app
            for window in window_list:
                if window.get('kCGWindowOwnerPID') == process_id:
                    window_title = window.get('kCGWindowName', '')
                    window_id = window.get('kCGWindowNumber')
                    
                    # Get window bounds
                    bounds_dict = window.get('kCGWindowBounds', {})
                    if bounds_dict:
                        bounds = {
                            'x': int(bounds_dict.get('X', 0)),
                            'y': int(bounds_dict.get('Y', 0)),
                            'width': int(bounds_dict.get('Width', 0)),
                            'height': int(bounds_dict.get('Height', 0))
                        }
                    break
            
            return WindowInfo(
                app_name=app_name,
                window_title=window_title,
                process_id=process_id,
                window_id=window_id,
                bounds=bounds,
                is_active=True
            )
            
        except Exception as e:
            self.logger.error(f"Error getting active window on macOS: {e}")
            return None
    
    def _get_active_window_windows(self) -> Optional[WindowInfo]:
        """Get active window information on Windows"""
        
        if not WINDOWS_AVAILABLE:
            return None
        
        try:
            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process information
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process name
            try:
                process = psutil.Process(process_id)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"
            
            # Get window bounds
            try:
                rect = win32gui.GetWindowRect(hwnd)
                bounds = {
                    'x': rect[0],
                    'y': rect[1], 
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1]
                }
            except:
                bounds = None
            
            return WindowInfo(
                app_name=app_name,
                window_title=window_title,
                process_id=process_id,
                window_id=hwnd,
                bounds=bounds,
                is_active=True
            )
            
        except Exception as e:
            self.logger.error(f"Error getting active window on Windows: {e}")
            return None
    
    def _get_active_window_linux(self) -> Optional[WindowInfo]:
        """Get active window information on Linux"""
        
        try:
            # Use xdotool to get active window
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            window_id = result.stdout.strip()
            
            # Get window title
            title_result = subprocess.run(['xdotool', 'getwindowname', window_id],
                                        capture_output=True, text=True)
            window_title = title_result.stdout.strip() if title_result.returncode == 0 else ""
            
            # Get process ID
            pid_result = subprocess.run(['xdotool', 'getwindowpid', window_id],
                                      capture_output=True, text=True)
            process_id = int(pid_result.stdout.strip()) if pid_result.returncode == 0 else 0
            
            # Get process name
            try:
                if process_id > 0:
                    process = psutil.Process(process_id)
                    app_name = process.name()
                else:
                    app_name = "Unknown"
            except:
                app_name = "Unknown"
            
            return WindowInfo(
                app_name=app_name,
                window_title=window_title,
                process_id=process_id,
                window_id=int(window_id) if window_id.isdigit() else None,
                is_active=True
            )
            
        except Exception as e:
            self.logger.error(f"Error getting active window on Linux: {e}")
            return None
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window across platforms"""
        
        if self.system == "Darwin":
            return self._get_active_window_macos()
        elif self.system == "Windows":
            return self._get_active_window_windows()
        elif self.system == "Linux":
            return self._get_active_window_linux()
        else:
            self.logger.warning(f"Unsupported platform: {self.system}")
            return None
    
    def _create_observation_event(self, 
                                window_info: WindowInfo, 
                                event_type: str,
                                duration: int = 0) -> ObservationEvent:
        """Create an observation event from window information"""
        
        # Determine if this is a browser and extract URL if possible
        url = ""
        if any(browser in window_info.app_name.lower() for browser in ['chrome', 'firefox', 'safari', 'edge']):
            # Try to extract URL from window title (basic approach)
            if ' - ' in window_info.window_title:
                parts = window_info.window_title.split(' - ')
                if len(parts) > 1 and ('http' in parts[-1] or '.' in parts[-1]):
                    url = parts[-1]
        
        return ObservationEvent(
            timestamp=datetime.now(),
            source="screen_observer",
            event_type=event_type,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            url=url,
            duration_seconds=duration,
            metadata={
                'process_id': window_info.process_id,
                'window_id': window_info.window_id,
                'bounds': window_info.bounds,
                'platform': self.system
            }
        )
    
    def _should_record_window(self, window_info: WindowInfo) -> bool:
        """Determine if this window should be recorded based on privacy settings"""
        
        privacy_settings = self.config.get_privacy_settings()
        
        # Check blocked apps
        blocked_apps = privacy_settings.get('blocked_apps', [])
        if window_info.app_name.lower() in [app.lower() for app in blocked_apps]:
            return False
        
        # Check for private browsing indicators
        if any(indicator in window_info.window_title.lower() 
               for indicator in ['private', 'incognito']):
            return False
        
        # Check for financial/sensitive apps
        sensitive_indicators = ['bank', 'password', 'keychain', 'wallet', 'crypto']
        if any(indicator in window_info.app_name.lower() or 
               indicator in window_info.window_title.lower()
               for indicator in sensitive_indicators):
            return False
        
        return True
    
    async def start_observing(self):
        """Start the screen observation loop"""
        
        if not self.config.is_observer_enabled('screen_observer'):
            self.logger.info("Screen observer is disabled in configuration")
            return
        
        if not self._check_platform_support():
            self.logger.error("Platform not supported for screen observation")
            return
        
        self.is_running = True
        self.session_start_time = datetime.now()
        
        self.logger.info(f"Starting screen observer on {self.system}")
        
        last_window_info = None
        window_start_time = None
        
        while self.is_running:
            try:
                current_window_info = self.get_active_window()
                
                if current_window_info and self._should_record_window(current_window_info):
                    # Check if window has changed
                    window_changed = (
                        last_window_info is None or
                        last_window_info.app_name != current_window_info.app_name or
                        last_window_info.window_title != current_window_info.window_title
                    )
                    
                    if window_changed:
                        # Record duration for previous window
                        if last_window_info and window_start_time:
                            duration = int((datetime.now() - window_start_time).total_seconds())
                            
                            if duration >= self.min_duration:
                                # Create observation event for previous window
                                event = self._create_observation_event(
                                    last_window_info,
                                    "window_focus",
                                    duration
                                )
                                
                                # Update app duration tracking
                                if last_window_info.app_name not in self.app_durations:
                                    self.app_durations[last_window_info.app_name] = 0
                                self.app_durations[last_window_info.app_name] += duration
                                
                                # Store observation
                                self.last_observation = event
                                self.window_history.append(last_window_info)
                                
                                # Notify callbacks
                                for callback in self.observation_callbacks:
                                    try:
                                        callback(event)
                                    except Exception as e:
                                        self.logger.error(f"Error in observation callback: {e}")
                        
                        # Start tracking new window
                        last_window_info = current_window_info
                        window_start_time = datetime.now()
                        self.current_window = current_window_info
                        
                        # Create window switch event
                        switch_event = self._create_observation_event(
                            current_window_info,
                            "window_switch"
                        )
                        
                        for callback in self.observation_callbacks:
                            try:
                                callback(switch_event)
                            except Exception as e:
                                self.logger.error(f"Error in observation callback: {e}")
                
                # Sleep for poll interval
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error in screen observation loop: {e}")
                await asyncio.sleep(self.poll_interval)
        
        # Record final window duration when stopping
        if last_window_info and window_start_time:
            duration = int((datetime.now() - window_start_time).total_seconds())
            if duration >= self.min_duration:
                event = self._create_observation_event(
                    last_window_info,
                    "window_focus",
                    duration
                )
                
                for callback in self.observation_callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Error in final observation callback: {e}")
        
        self.logger.info("Screen observer stopped")
    
    def stop_observing(self):
        """Stop the screen observation"""
        self.is_running = False
    
    def get_current_activity(self) -> Optional[Dict[str, Any]]:
        """Get current activity information"""
        
        if not self.current_window:
            return None
        
        return {
            'app_name': self.current_window.app_name,
            'window_title': self.current_window.window_title,
            'duration_seconds': int((datetime.now() - self.current_window.timestamp).total_seconds()),
            'timestamp': self.current_window.timestamp.isoformat()
        }
    
    def get_app_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of application usage"""
        
        # Calculate time since start
        if self.session_start_time:
            session_duration = int((datetime.now() - self.session_start_time).total_seconds())
        else:
            session_duration = 0
        
        # Get top apps by usage
        sorted_apps = sorted(self.app_durations.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'session_duration_seconds': session_duration,
            'total_windows_tracked': len(self.window_history),
            'unique_apps_used': len(self.app_durations),
            'top_apps': [
                {
                    'app_name': app_name,
                    'duration_seconds': duration,
                    'percentage': (duration / session_duration * 100) if session_duration > 0 else 0
                }
                for app_name, duration in sorted_apps[:10]
            ],
            'current_activity': self.get_current_activity()
        }
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """Analyze productivity patterns from observed activity"""
        
        if not self.window_history:
            return {'insights': 'No activity data available yet'}
        
        # Categorize activities
        productive_time = 0
        distraction_time = 0
        communication_time = 0
        
        productive_apps = ['vscode', 'xcode', 'terminal', 'excel', 'word', 'pages', 'numbers']
        distraction_apps = ['youtube', 'netflix', 'facebook', 'twitter', 'instagram', 'reddit']
        communication_apps = ['slack', 'teams', 'mail', 'outlook', 'messages', 'whatsapp']
        
        for app_name, duration in self.app_durations.items():
            app_lower = app_name.lower()
            
            if any(prod_app in app_lower for prod_app in productive_apps):
                productive_time += duration
            elif any(dist_app in app_lower for dist_app in distraction_apps):
                distraction_time += duration
            elif any(comm_app in app_lower for comm_app in communication_apps):
                communication_time += duration
        
        total_time = sum(self.app_durations.values())
        
        if total_time == 0:
            return {'insights': 'No significant activity recorded yet'}
        
        # Calculate window switching frequency
        window_switches = len(self.window_history)
        session_hours = (datetime.now() - self.session_start_time).total_seconds() / 3600 if self.session_start_time else 1
        switches_per_hour = window_switches / session_hours
        
        # Determine focus level
        if switches_per_hour < 10:
            focus_level = "High"
        elif switches_per_hour < 30:
            focus_level = "Medium"
        else:
            focus_level = "Low"
        
        return {
            'productive_time_percentage': (productive_time / total_time) * 100,
            'distraction_time_percentage': (distraction_time / total_time) * 100,
            'communication_time_percentage': (communication_time / total_time) * 100,
            'window_switches_per_hour': switches_per_hour,
            'focus_level': focus_level,
            'insights': [
                f"Spent {(productive_time/60):.1f} minutes on productive activities",
                f"Had {window_switches} window switches in {session_hours:.1f} hours",
                f"Focus level: {focus_level} based on switching patterns"
            ]
        }