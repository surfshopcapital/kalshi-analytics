#!/usr/bin/env python3
"""
Test script for unified data access functions
Tests the new Polymarket integration and unified data loading
"""

import sys
import os

# Add project root to path
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from utils import (
    get_unified_markets,
    get_markets_by_source,
    get_unified_summary,
    get_data_source_status
)

def test_unified_data_access():
    """Test the new unified data access functions"""
    print("🧪 Testing Unified Data Access Functions")
    print("=" * 60)
    
    # Test 1: Data source status
    print("\n📊 Testing Data Source Status...")
    status = get_data_source_status()
    
    for source, info in status.items():
        print(f"\n{source.upper()}:")
        print(f"  Available: {info['available']}")
        print(f"  Markets Count: {info['markets_count']}")
        print(f"  Summary Available: {info['summary_available']}")
        print(f"  Last Updated: {info['last_updated']}")
    
    # Test 2: Get markets by source
    print("\n📊 Testing Source-Specific Data Loading...")
    
    # Kalshi markets
    kalshi_markets = get_markets_by_source('kalshi')
    if not kalshi_markets.empty:
        print(f"✅ Kalshi markets loaded: {len(kalshi_markets)} markets")
        print(f"   Columns: {list(kalshi_markets.columns)}")
    else:
        print("⚠️ No Kalshi markets available")
    
    # Polymarket markets
    polymarket_markets = get_markets_by_source('polymarket')
    if not polymarket_markets.empty:
        print(f"✅ Polymarket markets loaded: {len(polymarket_markets)} markets")
        print(f"   Columns: {list(polymarket_markets.columns)}")
    else:
        print("⚠️ No Polymarket markets available")
    
    # Test 3: Unified markets
    print("\n📊 Testing Unified Markets Loading...")
    
    # All sources
    all_markets = get_unified_markets()
    if not all_markets.empty:
        print(f"✅ Unified markets loaded: {len(all_markets)} total markets")
        print(f"   Data sources: {all_markets['data_source'].value_counts().to_dict()}")
        print(f"   Columns: {list(all_markets.columns)}")
    else:
        print("❌ No unified markets available")
    
    # Test 4: Unified summary
    print("\n📊 Testing Unified Summary Loading...")
    
    all_summaries = get_unified_summary()
    if not all_summaries.empty:
        print(f"✅ Unified summary loaded: {len(all_summaries)} total summaries")
        print(f"   Data sources: {all_summaries['data_source'].value_counts().to_dict()}")
    else:
        print("⚠️ No unified summary available")
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if not all_markets.empty:
        print("✅ Unified data access functions working correctly")
        print(f"📊 Total markets available: {len(all_markets)}")
        print("🔄 Ready to integrate into UI")
    else:
        print("❌ Unified data access functions need debugging")
        print("🔍 Check data file availability and permissions")

if __name__ == "__main__":
    test_unified_data_access()
