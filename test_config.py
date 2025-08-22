#!/usr/bin/env python3
"""
Test script to verify Kalshi API configuration
Run this to check if your API keys are properly configured
"""

import os
import sys

def test_config():
    print("🔐 Kalshi API Configuration Test")
    print("=" * 50)
    
    # Test 1: Check if config.py exists and can be imported
    print("\n1. Testing config.py import...")
    try:
        import config
        print("✅ config.py imported successfully")
        
        # Check API Key ID
        if hasattr(config, 'KALSHI_API_KEY_ID') and config.KALSHI_API_KEY_ID:
            print(f"✅ API Key ID found: {config.KALSHI_API_KEY_ID[:20]}...")
        else:
            print("❌ API Key ID not found or empty")
            
        # Check Private Key
        if hasattr(config, 'KALSHI_PRIVATE_KEY') and config.KALSHI_PRIVATE_KEY:
            if config.KALSHI_PRIVATE_KEY.startswith('-----BEGIN'):
                print("✅ Private Key found and appears to be in PEM format")
            else:
                print("⚠️  Private Key found but may not be in PEM format")
        else:
            print("❌ Private Key not found or empty")
            
    except ImportError as e:
        print(f"❌ Failed to import config.py: {e}")
    except Exception as e:
        print(f"❌ Error reading config.py: {e}")
    
    # Test 2: Check environment variables
    print("\n2. Testing environment variables...")
    api_key_env = os.getenv('KALSHI_API_KEY_ID')
    private_key_env = os.getenv('KALSHI_PRIVATE_KEY')
    
    if api_key_env:
        print(f"✅ KALSHI_API_KEY_ID found in environment: {api_key_env[:20]}...")
    else:
        print("❌ KALSHI_API_KEY_ID not found in environment")
        
    if private_key_env:
        if private_key_env.startswith('-----BEGIN'):
            print("✅ KALSHI_PRIVATE_KEY found in environment and appears to be in PEM format")
        else:
            print("⚠️  KALSHI_PRIVATE_KEY found in environment but may not be in PEM format")
    else:
        print("❌ KALSHI_PRIVATE_KEY not found in environment")
    
    # Test 3: Check utils.py import and authentication
    print("\n3. Testing utils.py and authentication...")
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import utils
        print("✅ utils.py imported successfully")
        
        # Test authentication functions
        if hasattr(utils, 'has_portfolio_auth'):
            auth_status = utils.has_portfolio_auth()
            print(f"✅ Portfolio authentication check: {auth_status}")
        else:
            print("❌ has_portfolio_auth function not found in utils")
            
        if hasattr(utils, 'get_auth_status'):
            status = utils.get_auth_status()
            print("✅ Authentication status retrieved:")
            for key, value in status.items():
                if 'debug' not in key:  # Skip debug info
                    print(f"   {key}: {value}")
        else:
            print("❌ get_auth_status function not found in utils")
            
    except ImportError as e:
        print(f"❌ Failed to import utils.py: {e}")
    except Exception as e:
        print(f"❌ Error testing utils.py: {e}")
    
    # Test 4: Check Kalshi client
    print("\n4. Testing Kalshi client...")
    try:
        from kalshi_client import KalshiClient
        print("✅ KalshiClient imported successfully")
        
        # Try to create a client
        try:
            client = utils.get_client()
            print("✅ Kalshi client created successfully")
        except Exception as e:
            print(f"❌ Failed to create Kalshi client: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import KalshiClient: {e}")
    except Exception as e:
        print(f"❌ Error testing Kalshi client: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Configuration test completed!")
    
    # Summary and recommendations
    print("\n📋 Summary and Recommendations:")
    
    if api_key_env or (hasattr(config, 'KALSHI_API_KEY_ID') and config.KALSHI_API_KEY_ID):
        print("✅ API Key ID is configured")
    else:
        print("❌ API Key ID is missing - configure KALSHI_API_KEY_ID")
        
    if private_key_env or (hasattr(config, 'KALSHI_API_KEY_ID') and config.KALSHI_PRIVATE_KEY and config.KALSHI_PRIVATE_KEY.startswith('-----BEGIN')):
        print("✅ Private Key is configured")
    else:
        print("❌ Private Key is missing or invalid - configure KALSHI_PRIVATE_KEY")
        
    print("\n🔧 To fix issues:")
    print("1. Set environment variables KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY")
    print("2. Or run: python setup_api_keys.py")
    print("3. Or update config.py with your actual API keys")

if __name__ == "__main__":
    test_config()
