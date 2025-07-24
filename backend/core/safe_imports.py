"""
Safe Import Helper - Handles optional dependencies gracefully
"""
import sys
from typing import Dict, Any, Optional, Tuple


class SafeImporter:
    """Handles optional imports with fallbacks"""
    
    def __init__(self):
        self.available_packages: Dict[str, bool] = {}
        self.import_errors: Dict[str, str] = {}
    
    def safe_import(self, package_name: str, fallback_value: Any = None) -> Tuple[Any, bool]:
        """
        Safely import a package with fallback
        
        Returns:
            (imported_module_or_fallback, success_bool)
        """
        if package_name in self.available_packages:
            if self.available_packages[package_name]:
                return __import__(package_name), True
            else:
                return fallback_value, False
        
        try:
            module = __import__(package_name)
            self.available_packages[package_name] = True
            return module, True
            
        except ImportError as e:
            self.available_packages[package_name] = False
            self.import_errors[package_name] = str(e)
            return fallback_value, False
    
    def check_required_packages(self) -> Dict[str, Dict[str, Any]]:
        """Check status of all required packages"""
        packages = {
            'twilio': {'required': False, 'purpose': 'SMS and call alerts'},
            'plyer': {'required': False, 'purpose': 'Desktop notifications'},
            'numpy': {'required': False, 'purpose': 'Numerical analysis'},
            'yaml': {'required': True, 'purpose': 'Configuration parsing'},
            'tabulate': {'required': False, 'purpose': 'CLI table formatting'},
            'asyncio': {'required': True, 'purpose': 'Async operations'},
        }
        
        results = {}
        
        for package, info in packages.items():
            _, available = self.safe_import(package)
            results[package] = {
                'available': available,
                'required': info['required'],
                'purpose': info['purpose'],
                'error': self.import_errors.get(package, None) if not available else None
            }
        
        return results
    
    def get_missing_requirements(self) -> list:
        """Get list of missing required packages"""
        status = self.check_required_packages()
        missing = []
        
        for package, info in status.items():
            if info['required'] and not info['available']:
                missing.append(package)
        
        return missing
    
    def print_package_status(self):
        """Print formatted package status report"""
        status = self.check_required_packages()
        
        print("\n📦 Package Availability Report")
        print("=" * 50)
        
        required_missing = []
        optional_missing = []
        
        for package, info in status.items():
            status_icon = "✅" if info['available'] else "❌"
            req_text = "(Required)" if info['required'] else "(Optional)"
            
            print(f"{status_icon} {package:<12} {req_text:<12} - {info['purpose']}")
            
            if not info['available']:
                if info['required']:
                    required_missing.append(package)
                else:
                    optional_missing.append(package)
                
                if info['error']:
                    print(f"    Error: {info['error']}")
        
        if required_missing:
            print(f"\n❌ Missing Required Packages: {', '.join(required_missing)}")
            print(f"   Install with: pip install {' '.join(required_missing)}")
        
        if optional_missing:
            print(f"\n⚠️  Missing Optional Packages: {', '.join(optional_missing)}")
            print(f"   Install with: pip install {' '.join(optional_missing)}")
        
        if not required_missing and not optional_missing:
            print("\n✅ All packages available!")


# Global importer instance
importer = SafeImporter()

# Safe import functions for common packages
def safe_import_twilio():
    """Safe import of Twilio with fallbacks"""
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioException, TwilioRestException
        return Client, TwilioException, TwilioRestException, True
    except ImportError:
        # Create mock classes
        class MockClient:
            def __init__(self, *args, **kwargs):
                pass
        
        class MockException(Exception):
            pass
        
        return MockClient, MockException, MockException, False

def safe_import_plyer():
    """Safe import of plyer for notifications"""
    try:
        import plyer
        return plyer, True
    except ImportError:
        # Mock plyer
        class MockPlyer:
            class notification:
                @staticmethod
                def notify(*args, **kwargs):
                    print("Desktop notification not available")
        
        return MockPlyer(), False

def safe_import_numpy():
    """Safe import of numpy with basic fallbacks"""
    try:
        import numpy as np
        return np, True
    except ImportError:
        # Basic math fallbacks
        class MockNumpy:
            @staticmethod
            def mean(values):
                return sum(values) / len(values) if values else 0
            
            @staticmethod
            def median(values):
                if not values:
                    return 0
                sorted_vals = sorted(values)
                n = len(sorted_vals) 
                return sorted_vals[n//2] if n % 2 else (sorted_vals[n//2-1] + sorted_vals[n//2])/2
            
            @staticmethod
            def std(values):
                if not values:
                    return 0
                mean_val = sum(values) / len(values)
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                return variance ** 0.5
        
        return MockNumpy(), False

def safe_import_tabulate():
    """Safe import of tabulate with basic fallback"""
    try:
        from tabulate import tabulate
        return tabulate, True
    except ImportError:
        def basic_tabulate(data, headers=None, tablefmt="grid"):
            """Basic table formatting fallback"""
            if not data:
                return ""
            
            # Simple text table
            if headers:
                output = " | ".join(headers) + "\n"
                output += "-" * len(output) + "\n"
            else:
                output = ""
            
            for row in data:
                output += " | ".join(str(cell) for cell in row) + "\n"
            
            return output
        
        return basic_tabulate, False


# Usage example
if __name__ == "__main__":
    # Check all packages
    importer.print_package_status()
    
    # Test safe imports
    print("\n🧪 Testing Safe Imports:")
    
    Client, TwilioException, TwilioRestException, has_twilio = safe_import_twilio()
    print(f"Twilio: {'Available' if has_twilio else 'Mock fallback'}")
    
    plyer, has_plyer = safe_import_plyer()
    print(f"Plyer: {'Available' if has_plyer else 'Mock fallback'}")
    
    np, has_numpy = safe_import_numpy()
    print(f"NumPy: {'Available' if has_numpy else 'Basic math fallback'}")
    
    tabulate, has_tabulate = safe_import_tabulate()
    print(f"Tabulate: {'Available' if has_tabulate else 'Basic formatting fallback'}")
    
    # Test basic functionality
    print(f"\nMean of [1,2,3,4,5]: {np.mean([1,2,3,4,5])}")
    
    test_table = [["A", "B"], ["1", "2"], ["3", "4"]]
    print(f"\nTable test:\n{tabulate(test_table, headers=['Col1', 'Col2'])}")