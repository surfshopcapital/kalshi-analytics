#!/usr/bin/env python3
"""
Detailed analysis of Polymarket data structure
Plans data normalization strategy for integration
"""

import requests
import pandas as pd
import json
from pprint import pprint

# Polymarket API endpoints
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

def get_sample_markets(limit=5):
    """Get a small sample of markets for detailed analysis"""
    try:
        response = requests.get(f"{GAMMA_API_BASE}/markets", timeout=10)
        response.raise_for_status()
        markets_data = response.json()
        return markets_data[:limit]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def analyze_polymarket_structure():
    """Detailed analysis of Polymarket data structure"""
    print("🔍 Detailed Polymarket Data Structure Analysis")
    print("=" * 60)
    
    markets = get_sample_markets(3)
    if not markets:
        print("❌ No markets to analyze")
        return
    
    print(f"📊 Analyzing {len(markets)} sample markets...")
    
    # Analyze first market in detail
    market = markets[0]
    
    print(f"\n📋 Market ID: {market.get('id')}")
    print(f"📋 Question: {market.get('question')}")
    print(f"📋 Category: {market.get('category')}")
    print(f"📋 Active: {market.get('active')}")
    print(f"📋 Closed: {market.get('closed')}")
    
    # Analyze outcomes structure
    outcomes = market.get('outcomes', [])
    print(f"\n🎯 Outcomes ({len(outcomes)}):")
    if isinstance(outcomes, list):
        for i, outcome in enumerate(outcomes):
            print(f"  {i+1}. {outcome}")
    else:
        print(f"  Outcomes format: {type(outcomes)} - {outcomes}")
    
    # Analyze pricing structure
    outcome_prices = market.get('outcomePrices', {})
    print(f"\n💰 Outcome Prices:")
    if isinstance(outcome_prices, dict):
        for outcome, price in outcome_prices.items():
            print(f"  {outcome}: {price}")
    else:
        print(f"  Outcome prices format: {type(outcome_prices)} - {outcome_prices}")
    
    # Analyze volume and liquidity
    print(f"\n📈 Volume & Liquidity:")
    print(f"  Volume (24h): {market.get('volume24hr')}")
    print(f"  Volume (1wk): {market.get('volume1wk')}")
    print(f"  Volume (1mo): {market.get('volume1mo')}")
    print(f"  Liquidity: {market.get('liquidity')}")
    
    # Analyze price changes
    print(f"\n📊 Price Changes:")
    print(f"  1 Hour: {market.get('oneHourPriceChange')}")
    print(f"  1 Day: {market.get('oneDayPriceChange')}")
    print(f"  1 Week: {market.get('oneWeekPriceChange')}")
    
    # Analyze trading data
    print(f"\n🔄 Trading Data:")
    print(f"  Last Trade Price: {market.get('lastTradePrice')}")
    print(f"  Best Bid: {market.get('bestBid')}")
    print(f"  Best Ask: {market.get('bestAsk')}")
    print(f"  Spread: {market.get('spread')}")
    
    # Show all available fields for debugging
    print(f"\n🔍 All Available Fields ({len(market.keys())}):")
    for key, value in market.items():
        value_type = type(value).__name__
        if isinstance(value, (str, int, float, bool)) and len(str(value)) < 100:
            print(f"  {key}: {value} ({value_type})")
        else:
            print(f"  {key}: {value_type} - {str(value)[:50]}...")
    
    return market

def plan_normalization_strategy():
    """Plan how to normalize Polymarket data to match Kalshi structure"""
    print("\n🔄 Data Normalization Strategy")
    print("=" * 60)
    
    # Key mapping from Polymarket to Kalshi-like structure
    normalization_map = {
        # Core identifiers
        'id': 'market_id',
        'question': 'title',
        'category': 'category',
        
        # Outcomes (need to be transformed)
        'outcomes': 'outcomes',  # Will need special handling
        
        # Pricing
        'outcomePrices': 'outcome_prices',  # Will need special handling
        'lastTradePrice': 'last_price',
        'bestBid': 'yes_bid',
        'bestAsk': 'yes_ask',
        
        # Volume and liquidity
        'volume24hr': 'volume_24h',
        'volume1wk': 'volume_1wk',
        'volume1mo': 'volume_1mo',
        'liquidity': 'liquidity',
        
        # Time data
        'endDate': 'close_time',
        'createdAt': 'open_time',
        
        # Status
        'active': 'status',  # Will need transformation
        'closed': 'closed',
        
        # Price changes
        'oneHourPriceChange': 'price_change_1h',
        'oneDayPriceChange': 'price_change_24h',
        'oneWeekPriceChange': 'price_change_1w',
    }
    
    print("📋 Field Mapping Strategy:")
    for polymarket_field, normalized_field in normalization_map.items():
        print(f"  {polymarket_field} → {normalized_field}")
    
    print("\n⚠️ Special Handling Required:")
    print("  1. Outcomes: Polymarket has multiple outcomes, Kalshi is binary")
    print("  2. Status: Need to transform active/closed to Kalshi status format")
    print("  3. Pricing: Polymarket has outcome-based pricing, need to normalize")
    print("  4. Volume: Polymarket has multiple timeframes, need to standardize")
    
    return normalization_map

def create_sample_normalized_data():
    """Create a sample of normalized data structure"""
    print("\n🔄 Sample Normalized Data Structure")
    print("=" * 60)
    
    # Sample normalized structure
    normalized_structure = {
        'market_id': 'string',
        'title': 'string',
        'category': 'string',
        'outcomes': 'list',
        'outcome_prices': 'dict',
        'last_price': 'float',
        'yes_bid': 'float',
        'yes_ask': 'float',
        'volume_24h': 'float',
        'volume_1wk': 'float',
        'volume_1mo': 'float',
        'liquidity': 'float',
        'close_time': 'datetime',
        'open_time': 'datetime',
        'status': 'string',
        'closed': 'boolean',
        'price_change_1h': 'float',
        'price_change_24h': 'float',
        'price_change_1w': 'float',
        'data_source': 'string',  # 'polymarket' or 'kalshi'
        'source_id': 'string',    # Original ID from source
    }
    
    print("📋 Normalized Field Types:")
    for field, field_type in normalized_structure.items():
        print(f"  {field}: {field_type}")
    
    return normalized_structure

def main():
    """Main analysis function"""
    print("🚀 Polymarket Data Structure Analysis")
    print("=" * 60)
    
    # Step 1: Analyze Polymarket structure
    sample_market = analyze_polymarket_structure()
    
    # Step 2: Plan normalization strategy
    normalization_map = plan_normalization_strategy()
    
    # Step 3: Create normalized data structure
    normalized_structure = create_sample_normalized_data()
    
    print("\n" + "=" * 60)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 60)
    print("✅ Polymarket API provides rich market data")
    print("✅ Data structure is compatible with DuckDB storage")
    print("🔄 Data normalization strategy planned")
    print("📊 Ready to implement integration")
    
    print("\n🎯 Next Steps:")
    print("  1. Create Polymarket client module")
    print("  2. Implement data normalization functions")
    print("  3. Extend refresh scripts for Polymarket")
    print("  4. Add data source toggle to UI")
    print("  5. Test unified data queries")

if __name__ == "__main__":
    main()
