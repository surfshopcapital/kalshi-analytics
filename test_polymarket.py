#!/usr/bin/env python3
"""
Test script for Polymarket API integration
Tests data fetching, structure compatibility, and DuckDB storage
"""

import requests
import pandas as pd
import duckdb
import json
from datetime import datetime
import time

# Polymarket API endpoints
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

def test_polymarket_api():
    """Test basic API connectivity and data structure"""
    print("🔍 Testing Polymarket API connectivity...")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{GAMMA_API_BASE}/markets", timeout=10)
        response.raise_for_status()
        
        markets_data = response.json()
        print(f"✅ Successfully connected to Polymarket API")
        print(f"📊 Retrieved {len(markets_data)} markets")
        
        return markets_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
        return None

def analyze_market_structure(markets_data):
    """Analyze the structure of Polymarket data"""
    print("\n🔍 Analyzing market data structure...")
    
    if not markets_data:
        print("❌ No data to analyze")
        return None
    
    # Get first market as sample
    sample_market = markets_data[0] if markets_data else {}
    
    print(f"📋 Sample market keys: {list(sample_market.keys())}")
    
    # Check for key fields we'll need
    required_fields = ['id', 'question', 'outcomes', 'volume', 'liquidity']
    available_fields = []
    missing_fields = []
    
    for field in required_fields:
        if field in sample_market:
            available_fields.append(field)
            print(f"✅ Found: {field}")
        else:
            missing_fields.append(field)
            print(f"❌ Missing: {field}")
    
    print(f"\n📊 Data structure analysis:")
    print(f"   Available fields: {len(available_fields)}/{len(required_fields)}")
    print(f"   Missing fields: {missing_fields}")
    
    return sample_market

def test_duckdb_storage(markets_data):
    """Test storing Polymarket data in DuckDB"""
    print("\n🗄️ Testing DuckDB storage...")
    
    if not markets_data:
        print("❌ No data to store")
        return False
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(markets_data)
        print(f"📊 DataFrame created: {df.shape}")
        
        # Test DuckDB storage
        con = duckdb.connect(':memory:')
        
        # Create table
        con.execute("CREATE TABLE polymarket_markets AS SELECT * FROM df")
        
        # Test queries
        count = con.execute("SELECT COUNT(*) FROM polymarket_markets").fetchone()[0]
        print(f"✅ Stored {count} markets in DuckDB")
        
        # Test sample query
        sample = con.execute("SELECT * FROM polymarket_markets LIMIT 3").fetchdf()
        print(f"📋 Sample query successful: {len(sample)} rows")
        
        con.close()
        return True
        
    except Exception as e:
        print(f"❌ DuckDB storage test failed: {e}")
        return False

def test_data_compatibility():
    """Test how Polymarket data compares to current Kalshi structure"""
    print("\n🔄 Testing data compatibility with current Kalshi structure...")
    
    # Load a sample of current Kalshi data for comparison
    try:
        from utils import ACTIVE_MARKETS_PQ
        import os
        
        if os.path.exists(ACTIVE_MARKETS_PQ):
            kalshi_df = pd.read_parquet(ACTIVE_MARKETS_PQ)
            print(f"📊 Current Kalshi data: {kalshi_df.shape}")
            print(f"📋 Kalshi columns: {list(kalshi_df.columns)}")
            
            # This will help us plan the data normalization
            return kalshi_df
        else:
            print("⚠️ No existing Kalshi data found for comparison")
            return None
            
    except Exception as e:
        print(f"⚠️ Could not load Kalshi data for comparison: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting Polymarket API Integration Test")
    print("=" * 50)
    
    # Step 1: Test API connectivity
    markets_data = test_polymarket_api()
    
    if not markets_data:
        print("❌ Test failed at API connectivity step")
        return
    
    # Step 2: Analyze data structure
    sample_market = analyze_market_structure(markets_data)
    
    # Step 3: Test DuckDB storage
    storage_success = test_duckdb_storage(markets_data)
    
    # Step 4: Test compatibility with current structure
    kalshi_data = test_data_compatibility()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    if storage_success:
        print("✅ Polymarket API integration test PASSED")
        print("✅ Data can be stored in DuckDB")
        print("✅ Ready to proceed with full integration")
    else:
        print("❌ Polymarket API integration test FAILED")
        print("❌ Need to resolve issues before proceeding")
    
    if kalshi_data is not None:
        print(f"📊 Current Kalshi structure: {len(kalshi_data.columns)} columns")
        print("🔄 Data normalization planning needed for full integration")

if __name__ == "__main__":
    main()
