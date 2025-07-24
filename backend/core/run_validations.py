#!/usr/bin/env python3
"""
Run All Validations - Complete system validation before startup
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from env_validator import EnvValidator
from config_validator import validate_all_configs
from safe_imports import importer


def main():
    """Run complete system validation"""
    print("🚀 Digital Twin Phase 8 - System Validation")
    print("=" * 60)
    
    all_valid = True
    
    # 1. Check package dependencies
    print("\n1️⃣  Checking Package Dependencies...")
    importer.print_package_status()
    missing_required = importer.get_missing_requirements()
    if missing_required:
        print(f"\n❌ Missing required packages: {missing_required}")
        all_valid = False
    
    # 2. Validate environment variables
    print("\n2️⃣  Validating Environment Variables...")
    env_validator = EnvValidator()
    env_valid, errors, warnings = env_validator.validate_all()
    env_validator.print_validation_report()
    
    if not env_valid:
        all_valid = False
    
    # 3. Validate configuration files
    print("\n3️⃣  Validating Configuration Files...")
    config_valid = validate_all_configs()
    
    if not config_valid:
        all_valid = False
    
    # 4. Final report
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ ALL VALIDATIONS PASSED!")
        print("\n🎯 System is ready to start:")
        print("   python twin_decision_loop.py")
        print("   python cli_extensions.py interactive")
    else:
        print("❌ VALIDATION FAILED!")
        print("\n🛠️  Next Steps:")
        
        if missing_required:
            print(f"   1. Install packages: pip install {' '.join(missing_required)}")
        
        if not env_valid:
            print("   2. Fix environment variables")
            print("   3. Create .env file with required credentials")
        
        if not config_valid:
            print("   4. Fix configuration files")
        
        print("\n💡 Tip: Run with --fix to auto-create missing files")
    
    return all_valid


def create_setup_script():
    """Create a setup script for easy installation"""
    setup_script = """#!/bin/bash
# Digital Twin Phase 8 Setup Script

echo "🚀 Setting up Digital Twin Phase 8..."

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install twilio plyer pyyaml tabulate numpy aiohttp python-dateutil jsonschema coloredlogs

# Create directories
echo "📁 Creating directories..."
mkdir -p backend/{data,logs,config}

# Create environment template
echo "📝 Creating environment template..."
python env_validator.py --create-template

# Create default configs
echo "⚙️  Creating default configurations..."
python config_validator.py --create-defaults

# Run validation
echo "🔍 Running validation..."
python run_validations.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.template with your Twilio credentials"
echo "2. Rename to .env: mv .env.template .env"
echo "3. Run validation: python run_validations.py"
echo "4. Start system: python twin_decision_loop.py"
"""
    
    setup_path = Path("backend/setup.sh")
    with open(setup_path, 'w') as f:
        f.write(setup_script)
    
    # Make executable
    import stat
    setup_path.chmod(setup_path.stat().st_mode | stat.S_IEXEC)
    
    print(f"📋 Setup script created: {setup_path}")
    print("   Run with: ./backend/setup.sh")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Digital Twin system")
    parser.add_argument('--fix', action='store_true', help='Auto-create missing files')
    parser.add_argument('--create-setup', action='store_true', help='Create setup script')
    
    args = parser.parse_args()
    
    if args.create_setup:
        create_setup_script()
        sys.exit(0)
    
    if args.fix:
        # Create missing files
        env_validator = EnvValidator()
        env_validator.create_env_template()
        
        from config_validator import ConfigValidator
        validator = ConfigValidator()
        validator.create_default_criticality_rules(
            Path("backend/config/criticality_rules.yaml")
        )
        validator.create_default_twin_config(
            Path("backend/config/twin_config.json")
        )
    
    # Run validation
    success = main()
    sys.exit(0 if success else 1)