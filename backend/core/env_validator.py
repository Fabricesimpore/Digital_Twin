"""
Environment Variables Validator - Ensures proper setup before system start
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging


class EnvValidator:
    """Validates environment variables and system setup"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Validate all environment requirements"""
        self.errors = []
        self.warnings = []
        
        # Core validations
        self._validate_twilio_config()
        self._validate_directories()
        self._validate_dependencies()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_twilio_config(self):
        """Validate Twilio configuration"""
        required_vars = {
            'TWILIO_ACCOUNT_SID': self._validate_account_sid,
            'TWILIO_AUTH_TOKEN': self._validate_auth_token,
            'TWILIO_PHONE_NUMBER': self._validate_phone_number,
            'USER_PHONE_NUMBER': self._validate_phone_number
        }
        
        missing_vars = []
        
        for var_name, validator in required_vars.items():
            value = os.getenv(var_name)
            
            if not value:
                missing_vars.append(var_name)
                continue
            
            # Validate format
            is_valid, error_msg = validator(value)
            if not is_valid:
                self.errors.append(f"{var_name}: {error_msg}")
        
        if missing_vars:
            self.warnings.append(
                f"Twilio variables not set: {', '.join(missing_vars)}. "
                "SMS/call alerts will be disabled."
            )
        
        # Validate webhook URL if provided
        webhook_url = os.getenv('TWILIO_WEBHOOK_URL')
        if webhook_url:
            if not webhook_url.startswith('https://'):
                self.errors.append("TWILIO_WEBHOOK_URL must use HTTPS")
            elif not self._is_valid_url(webhook_url):
                self.errors.append("TWILIO_WEBHOOK_URL is not a valid URL")
        else:
            self.warnings.append("TWILIO_WEBHOOK_URL not set. Phone calls will be disabled.")
    
    def _validate_account_sid(self, value: str) -> Tuple[bool, str]:
        """Validate Twilio Account SID format"""
        if not re.match(r'^AC[a-f0-9]{32}$', value):
            return False, "Must start with 'AC' followed by 32 hex characters"
        return True, ""
    
    def _validate_auth_token(self, value: str) -> Tuple[bool, str]:
        """Validate Twilio Auth Token format"""
        if len(value) != 32:
            return False, "Must be exactly 32 characters long"
        if not re.match(r'^[a-f0-9]{32}$', value):
            return False, "Must contain only hex characters"
        return True, ""
    
    def _validate_phone_number(self, value: str) -> Tuple[bool, str]:
        """Validate phone number format"""
        if not re.match(r'^\+1[0-9]{10}$', value):
            return False, "Must be in format +1XXXXXXXXXX (US numbers only)"
        return True, ""
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _validate_directories(self):
        """Ensure required directories exist"""
        required_dirs = [
            "backend/data",
            "backend/logs", 
            "backend/config"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                self.errors.append(f"Cannot create directory: {dir_path} (permission denied)")
            except Exception as e:
                self.errors.append(f"Cannot create directory: {dir_path} ({e})")
    
    def _validate_dependencies(self):
        """Check if required Python packages are available"""
        optional_deps = {
            'twilio': 'SMS and call alerts',
            'plyer': 'Desktop notifications',
            'numpy': 'Advanced feedback analysis',
            'tabulate': 'CLI table formatting',
            'yaml': 'Configuration file parsing'
        }
        
        missing_deps = []
        
        for package, description in optional_deps.items():
            try:
                if package == 'yaml':
                    import yaml
                else:
                    __import__(package)
            except ImportError:
                if package in ['twilio', 'plyer']:
                    missing_deps.append(f"{package} ({description})")
                else:
                    self.warnings.append(f"Optional dependency missing: {package} - {description}")
        
        if missing_deps:
            self.warnings.append(
                f"Important dependencies missing: {', '.join(missing_deps)}. "
                f"Install with: pip install {' '.join(dep.split()[0] for dep in missing_deps)}"
            )
    
    def create_env_template(self, file_path: str = ".env.template"):
        """Create environment template file"""
        template = """# Digital Twin Phase 8 Environment Configuration

# Twilio Configuration (Required for SMS/Call alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+1987654321

# Webhook URL for phone call responses (Optional)
TWILIO_WEBHOOK_URL=https://your-domain.com/webhook

# System Configuration (Optional)
TWIN_LOG_LEVEL=INFO
TWIN_MAX_MEMORY_UPDATES=1000
TWIN_AUTO_EXECUTE_THRESHOLD=0.95

# Database Configuration (Future use)
# DATABASE_URL=postgresql://user:pass@localhost/twin_db
"""
        
        try:
            with open(file_path, 'w') as f:
                f.write(template)
            self.logger.info(f"Environment template created: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to create env template: {e}")
    
    def print_validation_report(self):
        """Print formatted validation report"""
        print("\n🔍 Environment Validation Report")
        print("=" * 50)
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
            return
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print(f"\n📝 Status: {'❌ FAILED' if self.errors else '⚠️ WARNINGS ONLY'}")
        
        if self.errors:
            print("\n🛠️  Next Steps:")
            print("1. Fix the errors listed above")
            print("2. Set required environment variables")
            print("3. Run validation again")
        
        print(f"\n💡 Tip: Run create_env_template() to generate .env.template")


def validate_environment() -> bool:
    """Quick validation function"""
    validator = EnvValidator()
    is_valid, errors, warnings = validator.validate_all()
    validator.print_validation_report()
    return is_valid


if __name__ == "__main__":
    # Run validation
    validator = EnvValidator()
    is_valid, errors, warnings = validator.validate_all()
    
    validator.print_validation_report()
    
    # Create template if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--create-template':
        validator.create_env_template()
    
    # Exit with error code if validation failed
    sys.exit(0 if is_valid else 1)