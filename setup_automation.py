#!/usr/bin/env python3
"""
Setup script for the automated daily betting system
"""

import subprocess
import sys
import os

def install_required_packages():
    """Install required Python packages"""
    packages = [
        'schedule',
        'pytz',
        'requests',
        'beautifulsoup4',
        'flask'
    ]

    print("📦 Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")

def create_service_script():
    """Create a script to run the automated system as a service"""
    service_script = '''#!/bin/bash
# Automated Betting System Service Script

cd /Users/josephnardone/oddsshopper-bet-tracker
export PYTHONPATH=$PYTHONPATH:/Users/josephnardone/oddsshopper-bet-tracker

# Run the automated system
python3 automated_daily_system.py
'''

    with open('run_automation.sh', 'w') as f:
        f.write(service_script)

    # Make executable
    os.chmod('run_automation.sh', 0o755)
    print("✅ Created run_automation.sh service script")

def create_launchd_plist():
    """Create macOS LaunchAgent for automatic startup"""
    plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oddsshopper.bet-tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/josephnardone/oddsshopper-bet-tracker/run_automation.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/josephnardone/oddsshopper-bet-tracker/automation.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/josephnardone/oddsshopper-bet-tracker/automation_error.log</string>
</dict>
</plist>'''

    launchagents_dir = os.path.expanduser('~/Library/LaunchAgents')
    os.makedirs(launchagents_dir, exist_ok=True)

    plist_path = os.path.join(launchagents_dir, 'com.oddsshopper.bet-tracker.plist')
    with open(plist_path, 'w') as f:
        f.write(plist_content)

    print(f"✅ Created LaunchAgent at {plist_path}")
    print("💡 To start the service automatically, run:")
    print(f"   launchctl load {plist_path}")

def main():
    print("🚀 Setting up Automated Daily Betting System")
    print("="*50)

    # Install packages
    install_required_packages()

    # Create service files
    create_service_script()
    create_launchd_plist()

    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Test the system manually:")
    print("   python3 automated_daily_system.py")
    print("\n2. Start the automated service:")
    print("   ./run_automation.sh")
    print("\n3. Or enable automatic startup:")
    print("   launchctl load ~/Library/LaunchAgents/com.oddsshopper.bet-tracker.plist")
    print("\n📊 Dashboard available at:")
    print("   http://127.0.0.1:8080")
    print("\n⏰ Automatic schedule:")
    print("   📅 Daily scraping: 11:30 PM Eastern")
    print("   🔍 Daily verification: 3:00 AM Eastern")
    print("   🧹 Weekly cleanup: Sundays 4:00 AM Eastern")

if __name__ == "__main__":
    main()