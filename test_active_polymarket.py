#!/usr/bin/env python3
"""
Test script to verify we can fetch active Polymarket markets
"""

import sys
import os
import pandas as pd

# Add project root to path
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from polymarket_client import fetch_and_normalize_polymarket_markets

def test_active_markets():
    """Test fetching active Polymarket markets"""
    print("🧪 Testing Active Polymarket Markets Fetch")
    print("=" * 60)
    
    try:
        # Test 1: Fetch all markets (including closed)
        print("\n📊 Test 1: Fetching ALL markets...")
        all_markets = fetch_and_normalize_polymarket_markets(active_only=False)
        print(f"✅ All markets: {len(all_markets)}")
        
        if not all_markets.empty:
            closed_count = all_markets['closed'].sum()
            active_count = len(all_markets) - closed_count
            print(f"  📊 Closed markets: {closed_count}")
            print(f"  📊 Active markets: {active_count}")
        
        # Test 2: Fetch only active markets
        print("\n📊 Test 2: Fetching only ACTIVE markets...")
        active_markets = fetch_and_normalize_polymarket_markets(active_only=True)
        print(f"✅ Active markets: {len(active_markets)}")
        
        if not active_markets.empty:
            print(f"  📋 Columns: {list(active_markets.columns)}")
            
            # Show first few active markets
            print("\n🔍 First 3 Active Markets:")
            for i, (idx, market) in enumerate(active_markets.head(3).iterrows()):
                print(f"\n  Market {i+1}:")
                print(f"    Title: {market['title'][:80]}...")
                print(f"    Status: {market['status']}")
                print(f"    Closed: {market['closed']}")
                print(f"    Volume Total: ${market['volume_total']:,.2f}")
                print(f"    Outcomes: {market['outcomes']}")
        
        # Test 3: Show data structure differences
        print("\n📊 Test 3: Data Structure Analysis")
        if not active_markets.empty and not all_markets.empty:
            print(f"  All markets columns: {len(all_markets.columns)}")
            print(f"  Active markets columns: {len(active_markets.columns)}")
            print(f"  Same structure: {list(all_markets.columns) == list(active_markets.columns)}")
        
    except Exception as e:
        print(f"❌ Error testing active markets: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_active_markets()
