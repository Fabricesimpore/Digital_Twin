"""
Configuration Validator - Validates YAML and JSON config files
"""
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging


class ConfigValidator:
    """Validates configuration files and structures"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_criticality_rules(self, config_path: Path) -> bool:
        """Validate criticality rules YAML file"""
        self.errors = []
        self.warnings = []
        
        if not config_path.exists():
            self.errors.append(f"Config file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Cannot read config file: {e}")
            return False
        
        # Validate structure
        self._validate_criticality_structure(config)
        
        return len(self.errors) == 0
    
    def _validate_criticality_structure(self, config: Dict[str, Any]):
        """Validate criticality rules structure"""
        required_sections = {
            'vip_contacts': list,
            'action_defaults': dict,
            'keyword_patterns': dict,
            'time_sensitive': dict
        }
        
        # Check required sections
        for section, expected_type in required_sections.items():
            if section not in config:
                self.errors.append(f"Missing required section: {section}")
                continue
            
            if not isinstance(config[section], expected_type):
                self.errors.append(f"Section '{section}' must be {expected_type.__name__}")
                continue
            
            # Validate section content
            self._validate_section_content(section, config[section])
    
    def _validate_section_content(self, section: str, content: Any):
        """Validate content of specific sections"""
        if section == 'vip_contacts':
            self._validate_vip_contacts(content)
        elif section == 'action_defaults':
            self._validate_action_defaults(content)
        elif section == 'keyword_patterns':
            self._validate_keyword_patterns(content)
        elif section == 'time_sensitive':
            self._validate_time_sensitive(content)
    
    def _validate_vip_contacts(self, contacts: List[str]):
        """Validate VIP contacts list"""
        if not contacts:
            self.warnings.append("VIP contacts list is empty")
            return
        
        for contact in contacts:
            if not isinstance(contact, str):
                self.errors.append(f"VIP contact must be string: {contact}")
            elif not contact.strip():
                self.errors.append("VIP contact cannot be empty")
    
    def _validate_action_defaults(self, defaults: Dict[str, str]):
        """Validate action defaults"""
        valid_levels = {'low', 'medium', 'high'}
        
        if not defaults:
            self.errors.append("Action defaults cannot be empty")
            return
        
        for action, level in defaults.items():
            if not isinstance(action, str) or not action.strip():
                self.errors.append(f"Action name must be non-empty string: {action}")
            
            if level not in valid_levels:
                self.errors.append(f"Invalid criticality level '{level}' for action '{action}'. Must be: {valid_levels}")
    
    def _validate_keyword_patterns(self, patterns: Dict[str, List[str]]):
        """Validate keyword patterns"""
        valid_levels = {'low', 'medium', 'high'}
        
        for level, keywords in patterns.items():
            if level not in valid_levels:
                self.errors.append(f"Invalid pattern level: {level}. Must be: {valid_levels}")
                continue
            
            if not isinstance(keywords, list):
                self.errors.append(f"Keywords for level '{level}' must be a list")
                continue
            
            for keyword in keywords:
                if not isinstance(keyword, str) or not keyword.strip():
                    self.errors.append(f"Keyword must be non-empty string: {keyword}")
    
    def _validate_time_sensitive(self, time_config: Dict[str, Any]):
        """Validate time sensitive configuration"""
        required_fields = ['business_hours', 'increase_criticality_outside_hours']
        
        for field in required_fields:
            if field not in time_config:
                self.errors.append(f"Missing time_sensitive field: {field}")
        
        # Validate business hours
        if 'business_hours' in time_config:
            hours = time_config['business_hours']
            if not isinstance(hours, dict):
                self.errors.append("business_hours must be a dictionary")
            else:
                for key in ['start', 'end']:
                    if key not in hours:
                        self.errors.append(f"Missing business_hours field: {key}")
                    elif not isinstance(hours[key], int) or not 0 <= hours[key] <= 23:
                        self.errors.append(f"business_hours.{key} must be integer 0-23")
                
                if 'start' in hours and 'end' in hours:
                    if hours['start'] >= hours['end']:
                        self.errors.append("business_hours.start must be less than end")
    
    def validate_twin_config(self, config_path: Path) -> bool:
        """Validate twin configuration JSON file"""
        self.errors = []
        self.warnings = []
        
        if not config_path.exists():
            self.warnings.append(f"Config file not found: {config_path}, will use defaults")
            return True
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON syntax: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Cannot read config file: {e}")
            return False
        
        # Validate twin config structure
        self._validate_twin_config_structure(config)
        
        return len(self.errors) == 0
    
    def _validate_twin_config_structure(self, config: Dict[str, Any]):
        """Validate twin configuration structure"""
        expected_fields = {
            'auto_execute_threshold': (float, 0.0, 1.0),
            'max_concurrent_actions': (int, 1, 100),
            'timeout_hours': (int, 1, 168),  # 1 hour to 1 week
            'learning_enabled': (bool, None, None)
        }
        
        for field, (expected_type, min_val, max_val) in expected_fields.items():
            if field not in config:
                self.warnings.append(f"Optional config field missing: {field}")
                continue
            
            value = config[field]
            
            # Type check
            if not isinstance(value, expected_type):
                self.errors.append(f"Field '{field}' must be {expected_type.__name__}: {value}")
                continue
            
            # Range check
            if min_val is not None and value < min_val:
                self.errors.append(f"Field '{field}' must be >= {min_val}: {value}")
            
            if max_val is not None and value > max_val:
                self.errors.append(f"Field '{field}' must be <= {max_val}: {value}")
    
    def create_default_criticality_rules(self, output_path: Path):
        """Create default criticality rules file"""
        default_config = {
            'vip_contacts': [
                'CEO', 'CTO', 'Investor', 'Board Member', 'Legal'
            ],
            'action_defaults': {
                'email_send': 'medium',
                'email_reply': 'medium',
                'calendar_create': 'medium',
                'calendar_modify': 'high',
                'call_make': 'high',
                'sms_send': 'medium',
                'file_create': 'low',
                'file_modify': 'medium',
                'task_create': 'low',
                'reminder_set': 'low',
                'focus_session': 'low',
                'archive': 'low',
                'log': 'low'
            },
            'keyword_patterns': {
                'high': ['urgent', 'emergency', 'critical', 'asap', 'deadline'],
                'medium': ['important', 'priority', 'review', 'approve'],
                'low': ['fyi', 'archive', 'log', 'reminder']
            },
            'time_sensitive': {
                'business_hours': {
                    'start': 9,
                    'end': 18
                },
                'timezone': 'America/New_York',
                'increase_criticality_outside_hours': True
            }
        }
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Default criticality rules created: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to create default config: {e}")
    
    def create_default_twin_config(self, output_path: Path):
        """Create default twin configuration file"""
        default_config = {
            'auto_execute_threshold': 0.95,
            'max_concurrent_actions': 5,
            'timeout_hours': 24,  
            'learning_enabled': True,
            'log_level': 'INFO',
            'memory_buffer_size': 1000
        }
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info(f"Default twin config created: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to create default config: {e}")
    
    def print_validation_report(self):
        """Print formatted validation report"""
        print("\n⚙️  Configuration Validation Report")
        print("=" * 50)
        
        if not self.errors and not self.warnings:
            print("✅ Configuration is valid!")
            return
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print(f"\n📝 Status: {'❌ INVALID' if self.errors else '⚠️ VALID WITH WARNINGS'}")


def validate_all_configs():
    """Validate all configuration files"""
    validator = ConfigValidator()
    
    # Paths
    criticality_path = Path("backend/config/criticality_rules.yaml")
    twin_config_path = Path("backend/config/twin_config.json")
    
    print("🔍 Validating all configuration files...")
    
    # Validate criticality rules
    print(f"\n📋 Checking: {criticality_path}")
    criticality_valid = validator.validate_criticality_rules(criticality_path)
    
    if not criticality_valid:
        validator.print_validation_report()
        print(f"\n🛠️  Creating default criticality rules...")
        validator.create_default_criticality_rules(criticality_path)
    else:
        print("✅ Criticality rules are valid")
    
    # Validate twin config
    print(f"\n⚙️  Checking: {twin_config_path}")
    twin_valid = validator.validate_twin_config(twin_config_path)
    
    if not twin_valid:
        validator.print_validation_report()
        print(f"\n🛠️  Creating default twin config...")
        validator.create_default_twin_config(twin_config_path)
    else:
        print("✅ Twin configuration is valid")
    
    return criticality_valid and twin_valid


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-defaults':
        # Create default configs
        validator = ConfigValidator()
        criticality_path = Path("backend/config/criticality_rules.yaml")
        twin_config_path = Path("backend/config/twin_config.json")
        
        validator.create_default_criticality_rules(criticality_path)
        validator.create_default_twin_config(twin_config_path)
        print("✅ Default configuration files created!")
    else:
        # Run validation
        is_valid = validate_all_configs()
        sys.exit(0 if is_valid else 1)