#!/usr/bin/env python3
"""
Setup script for Kalshi API keys
Run this script to securely configure your API keys
"""

import os
import sys

def setup_api_keys():
    print("🔐 Kalshi API Key Setup")
    print("=" * 50)
    
    # Check if config.py exists
    if os.path.exists('config.py'):
        print("⚠️  config.py already exists. This will overwrite it.")
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📝 Please provide your Kalshi API credentials:")
    
    # Get API Key ID
    api_key_id = input("Enter your Kalshi API Key ID: ").strip()
    if not api_key_id:
        print("❌ API Key ID is required!")
        return
    
    # Get Private Key
    print("\n🔑 Enter your Kalshi Private Key (PEM format):")
    print("   (Paste the entire key including -----BEGIN and -----END lines)")
    print("   Press Enter twice when done:")
    
    private_key_lines = []
    while True:
        line = input().strip()
        if line == "" and private_key_lines and private_key_lines[-1].startswith("-----END"):
            break
        private_key_lines.append(line)
    
    private_key = "\n".join(private_key_lines)
    
    if not private_key.startswith("-----BEGIN") or not private_key.endswith("-----END"):
        print("❌ Invalid private key format! Should start with -----BEGIN and end with -----END")
        return
    
    # Create config.py
    config_content = f'''# config.py - Kalshi API Configuration
# ⚠️  IMPORTANT: Never commit this file to version control!
# Add config.py to your .gitignore file

# Your Kalshi API Key ID (not the private key)
KALSHI_API_KEY_ID = "{api_key_id}"

# Your Kalshi Private Key (PEM format)
KALSHI_PRIVATE_KEY = """{private_key}"""

# Alternative: Store private key in a separate file
KALSHI_PRIVATE_KEY_PATH = "kalshi_private_key.pem"

# API Configuration
KALSHI_BASE_URL = "https://trading-api.kalshi.com"
KALSHI_SANDBOX_URL = "https://sandbox-api.kalshi.com"

# Environment detection
import os
IS_PRODUCTION = os.getenv('ENVIRONMENT') == 'production'
IS_SANDBOX = os.getenv('KALSHI_SANDBOX', 'false').lower() == 'true'

# Use environment variables if available (override config values)
if os.getenv('KALSHI_API_KEY_ID'):
    KALSHI_API_KEY_ID = os.getenv('KALSHI_API_KEY_ID')

if os.getenv('KALSHI_PRIVATE_KEY'):
    KALSHI_PRIVATE_KEY = os.getenv('KALSHI_PRIVATE_KEY')

if os.getenv('KALSHI_PRIVATE_KEY_PATH'):
    KALSHI_PRIVATE_KEY_PATH = os.getenv('KALSHI_PRIVATE_KEY_PATH')
'''
    
    # Write config.py
    with open('config.py', 'w') as f:
        f.write(config_content)
    
    # Create .gitignore if it doesn't exist
    if not os.path.exists('.gitignore'):
        gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class

# Environment variables and configuration
.env
config.py
kalshi_private_key.pem
*.pem
*.key

# API Keys and secrets
secrets.json
credentials.json
api_keys.txt

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/

# Data files
data/
*.parquet
*.csv
*.json

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
'''
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
    
    print("\n✅ Setup complete!")
    print("📁 Created config.py with your API credentials")
    print("📁 Created/updated .gitignore to protect sensitive files")
    print("\n⚠️  IMPORTANT:")
    print("   - Never commit config.py to version control")
    print("   - Keep your private key secure")
    print("   - The .gitignore file will prevent accidental commits")
    
    # Test the configuration
    print("\n🧪 Testing configuration...")
    try:
        from config import KALSHI_API_KEY_ID, KALSHI_PRIVATE_KEY
        print(f"✅ API Key ID: {KALSHI_API_KEY_ID[:8]}...{KALSHI_API_KEY_ID[-4:]}")
        print(f"✅ Private Key: {len(KALSHI_PRIVATE_KEY)} characters")
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")

if __name__ == "__main__":
    setup_api_keys()
